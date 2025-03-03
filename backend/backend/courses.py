from flask import Blueprint, jsonify, request
from backend.supabase import supabase

courses = Blueprint('courses', __name__)

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

@courses.route('/details/<course_subject>/<course_number>', methods=['GET'])
def get_course_details(course_subject, course_number):
    data = supabase.table("courses").select("*").eq("course_subject", course_subject.upper()).eq("course_number", course_number).execute()
    if len(data.data) == 0:
        return jsonify({"error": "Course not found"}), 404
    details = data.data[0]
    return jsonify(details), 200