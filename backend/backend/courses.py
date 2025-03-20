from typing import Tuple
from flask import Blueprint, jsonify, request
from backend.supabase import supabase
import requests
from loguru import logger

courses = Blueprint('courses', __name__)

crawler_mapping = {
    "Spring": "02",
    "Summer": "05",
    "Fall": "08"
}

def get_crawler_url(semester, year):
    base_url = "https://gt-scheduler.github.io/crawler-v2/{}{}.json"
    return base_url.format(year, crawler_mapping[semester])

def get_course_professor(semester, year, section, course_number, course_subject):
    url = get_crawler_url(semester, year)
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Crawler data not found"}, 404
    data = response.json()
    courses = data["courses"]
    course = courses[f"{course_subject.upper()} {course_number}"]
    sections = course[1]
    section = sections[section]
    professor = section[1][0][4][0]
    logger.info(f"Professor for {course_subject} {course_number} section {section} is {professor}")
    return professor, 200

def convert_name(name):
    """Convert 'First Last' to 'Last, First'."""
    if name.endswith(" (P)"):
        name = name[:-4]
    parts = name.split()
    return f"{parts[-1]}, {parts[0]}"


def find_or_create_professor_supabase(professor) -> Tuple[int, str]:
    converted_name = convert_name(professor)
    data = supabase.table("professors").select("id, name").ilike("name", f"%{converted_name}%").execute()
    if data.data:
        return data.data[0]["id"], data.data[0]["name"]
    logger.info(f"Creating professor {converted_name}")
    resp = supabase.table("professors").insert([{"name": converted_name}]).execute()
    logger.info(f"Created professor {converted_name} with id {resp.data[0]['id']}")
    return resp.data[0]["id"], converted_name

@courses.route('/valid', methods=['GET'])
def get_valid_courses():
    subject = request.args.get("subject")
    if subject:
        subject = subject.upper()
        data = supabase.table("courses").select("id, course_number, course_subject, name, uploads!inner(id)").eq("course_subject", subject.upper()).execute()
        valid_courses = [{
                            "course_number": d["course_number"],
                            "course_subject": d["course_subject"],
                            "name": d["name"],
                        } for d in data.data]
        return jsonify(valid_courses), 200
    data = supabase.table("courses").select("id, course_number, course_subject, name, uploads!inner(id)").execute()
    valid_courses = [{
                        "course_number": d["course_number"],
                        "course_subject": d["course_subject"],
                        "name": d["name"],
                    } for d in data.data]
    return jsonify(valid_courses), 200

@courses.route('/valid/subjects', methods=['GET'])
def get_valid_subjects():
    data = supabase.table("courses").select("course_subject, uploads!inner(id)").execute()
    subjects = sorted(list(set([d["course_subject"] for d in data.data])))
    return jsonify(subjects), 200

@courses.route('/professors', methods=['GET'])
def get_professors():
    data = supabase.table("professors").select(" name").execute()
    professors = sorted(list(set([d["name"] for d in data.data])))
    return jsonify(professors), 200

@courses.route('/subjects', methods=['GET'])
def get_subjects():
    data = supabase.table("courses").select("course_subject").execute()
    subjects = sorted(list(set([d["course_subject"] for d in data.data])))
    return jsonify(subjects), 200


@courses.route('/numbers', methods=['GET'])
def get_courses():
    subject = request.args.get("subject")
    data = supabase.table("courses").select("id, course_number").eq("course_subject", subject).execute()
    numbers = {d["id"]: d["course_number"] for d in data.data}
    return jsonify(numbers), 200

def _course_details(course_subject, course_number):
    data = supabase.table("courses").select("*").eq("course_subject", course_subject.upper()).eq("course_number", course_number).execute()
    if len(data.data) == 0:
        return {"error": "Course not found"}, 404
    details = data.data[0]
    return details, 200

@courses.route('/details/<course_subject>/<course_number>', methods=['GET'])
def get_course_details(course_subject, course_number):
    details, status = _course_details(course_subject, course_number)
    return jsonify(details), status