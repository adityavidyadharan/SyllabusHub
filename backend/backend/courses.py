from flask import Blueprint, jsonify, request
from backend.supabase import supabase

courses = Blueprint('courses', __name__)

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

@courses.route('/details/<course_subject>/<course_number>', methods=['GET'])
def get_course_details(course_subject, course_number):
    data = supabase.table("courses").select("*").eq("course_subject", course_subject.upper()).eq("course_number", course_number).execute()
    if len(data.data) == 0:
        return jsonify({"error": "Course not found"}), 404
    details = data.data[0]
    return jsonify(details), 200