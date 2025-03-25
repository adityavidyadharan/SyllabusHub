from flask import Blueprint, jsonify, request
from flask_cors import CORS
from backend.supabase import supabase
from canvasapi import Canvas
from datetime import datetime
import random
import concurrent.futures
import re
import json

canvas = Blueprint('canvas', __name__)
CORS(canvas, resources={r"/*": {"origins": "*"}})

API_URL = "https://gatech.instructure.com"
with open("backend/config/CanvasAPIKey.json") as f:
    API_KEY = json.load(f)["api_key"]
canvas_client = Canvas(API_URL, API_KEY)

course_re = re.compile(r"\b([a-zA-Z]{2,4})[ -]?(\d{4})")

def fetch_syllabus(courseId):
    course = canvas_client.get_course(courseId, include="syllabus_body")
    if not course or not course.syllabus_body:
        return None
    syllabus = course.syllabus_body
    return syllabus

@canvas.route('/syllabus/<courseId>', methods=['GET'])
def get_syllabus(courseId):
    syllabus = fetch_syllabus(courseId)
    if not syllabus:
        return jsonify({"error": "No syllabus found for this course"}), 404
    return jsonify({"syllabus": syllabus})


def check_courses(courses):
    # use supabase to check if the course already has an upload
    print("Checking courses")
    for course in courses:
        subject, number, year, semester = course["subject"], course["number"], course["semester_year"], course["semester"]
        resp = supabase.table("uploads").select("id, semester, year, courses!inner(id)").eq("semester", semester).eq("year", year).eq("courses.course_subject", subject).eq("courses.course_number", number).execute()
        if resp.data:
            course["upload"] = True
            course["upload_id"] = resp.data[0]["id"]
        else:
            course["upload"] = False
    return courses

def fetch_assignments(course):
    try:
        print(f"Processing course {course.id}: {course.name}")

        # Fetch a limited number of assignments
        page = course.get_assignments(per_page=20)
        assignments = list(page)
        if not assignments:
            return None  # Skip courses without assignments

        # Randomly sample up to 5 assignments
        sample_size = min(5, len(assignments))
        selection = random.sample(assignments, sample_size)

        due_dates = []
        for assignment in selection:
            if assignment.due_at:
                tstamp = datetime.strptime(assignment.due_at, "%Y-%m-%dT%H:%M:%SZ")
                due_dates.append(tstamp)

        if not due_dates:
            return None

        due_dates.sort()
        middle_due_date = due_dates[len(due_dates) // 2]
        semester_year = middle_due_date.year
        semester = "Spring" if middle_due_date.month <= 8 else "Fall"

        link = f"https://gatech.instructure.com/courses/{course.id}/assignments"
        
        name = course.original_name if getattr(course, "original_name", None) else course.name
        
        code = course.course_code
        match = course_re.search(code)
        if match:
            subject = match.group(1)
            number = match.group(2)
        else:
            return None

        return {
            "canvas_course_id": course.id,
            "name": name,
            "created_at": course.created_at,
            "link": link,
            "semester_year": semester_year,
            "semester": semester,
            "code": course.course_code,
            "subject": subject,
            "number": number,
        }

    except AttributeError as e:
        print(f"Error processing course {course.id}: {e}")
        return None

@canvas.route('/courses', methods=['GET'])
def get_courses():
    courses = canvas_client.get_courses()
    course_list = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_assignments, course): course for course in courses}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                course_list.append(result)
                
    course_list = check_courses(course_list)
    # create a json groupped by year and semester
    course_dict = {}
    for course in course_list:
        year = course["semester_year"]
        semester = course["semester"]
        if year not in course_dict:
            course_dict[year] = {}
        if semester not in course_dict[year]:
            course_dict[year][semester] = []
        course_dict[year][semester].append(course)

    return jsonify(course_dict)