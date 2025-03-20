from flask import Blueprint, jsonify, request
from backend.courses import _course_details, find_or_create_professor_supabase, get_course_professor
from backend.supabase import supabase
from backend.canvas import fetch_syllabus
from weasyprint import HTML
import io
from datetime import datetime
from loguru import logger

upload = Blueprint('upload', __name__)

@upload.route('/check', methods=['POST'])
def check_upload():
    data = request.json
    resp = supabase.table("uploads").select("id, semester, year, courses!inner(id)").eq("semester", data["semester"]).eq("year", data["year"]).eq("courses.course_subject", data["subject"]).eq("courses.course_number", data["number"]).execute()
    if resp.data:
        return jsonify({"upload": True}), 200
    return jsonify({"upload": False}), 200

@upload.route('/syllabus/preview', methods=['POST'])
def preview_syllabus():
    data = request.json
    canvas_course_id = data["canvas_course_id"]
    semester, year, subject, number = data["semester"], data["year"], data["subject"], data["number"]
    resp = supabase.table("uploads").select("id, semester, year, courses!inner(id)").eq("semester", semester).eq("year", year).eq("courses.course_subject", subject).eq("courses.course_number", number).execute()
    if resp.data:
        return jsonify({"error": "Syllabus already uploaded for this course"}), 400
    syllabus = fetch_syllabus(canvas_course_id)
    if not syllabus:
        return jsonify({"error": "No syllabus found for this course"}), 404
    pdf_file = io.BytesIO()
    print("Converting syllabus to pdf")
    HTML(string=syllabus).write_pdf(pdf_file)
    print("Syllabus converted to pdf")
    pdf_file.seek(0)
    pdf_filename = f"syllabus_{semester}_{year}_{subject}_{number}.pdf"
    return pdf_file, 200, {"Content-Disposition": f"attachment; filename={pdf_filename}", "Content-Type": "application/pdf"}

def sanitize_filename(filename):
    return filename.replace(r"[\[\](){}:;*?/\\<>|#%&]", "_").replace(r"\s+", "_")

@upload.route('/syllabus/import', methods=['POST'])
def import_syllabus():
    data = request.json
    canvas_course_id = data["canvas_course_id"]
    semester, year, subject, number = data["semester"], data["semester_year"], data["subject"], data["number"]
    section = data["section"]
    resp = supabase.table("uploads").select("id, semester, year, courses!inner(id)").eq("semester", semester).eq("year", year).eq("courses.course_subject", subject).eq("courses.course_number", number).execute()
    if resp.data:
        return jsonify({"error": "Syllabus already uploaded for this course"}), 400
    syllabus = fetch_syllabus(canvas_course_id)
    logger.debug("Fetched syllabus from Canvas")
    if not syllabus:
        return jsonify({"error": "No syllabus found for this course"}), 404
    pdf_file = io.BytesIO()
    logger.debug("Converting syllabus to pdf")
    HTML(string=syllabus).write_pdf(pdf_file)
    pdf_file.seek(0)
    pdf_filename = f"syllabus_{semester}_{year}_{subject}_{number}.pdf"
    pdf_path = f"course_syllabuses/IMPORT{datetime.now().timestamp()}-{sanitize_filename(pdf_filename)}"
    pdf_data = pdf_file.read()
    pdf_file.close()
    pdf_upload = supabase.storage.from_("Course Syllabuses").upload(file=pdf_data, path=pdf_path, file_options={"content-type": "application/pdf"})
    pdf_url = pdf_upload.full_path
    url_base = "https://tsbrojrazwcsjqzvnopi.supabase.co/storage/v1/object/public/"
    pdf_url = url_base + pdf_url
    logger.debug(f"Uploaded syllabus to Supabase at {pdf_url}")
    
    professor, status = get_course_professor(semester, year, section, number, subject)
    if status != 200:
        logger.error(f"Error fetching professor for {subject} {number}")
        return jsonify({"error": "Error fetching professor"}), 500
    prof_id, _name = find_or_create_professor_supabase(professor)
    course_details, status = _course_details(subject, number)
    if status != 200:
        logger.error(f"Error fetching course details for {subject} {number}")
        return jsonify({"error": "Error fetching course details"}), 500
    course_id = course_details["id"]
    upload_data = {
        "fileurl": pdf_url,
        "semester": semester,
        "year": year,
        "professor_id": prof_id,
        "course_id": course_id
    }
    resp = supabase.table("uploads").insert([upload_data]).execute()
    upload_id = resp.data[0]["id"]
    logger.info(f"Uploaded syllabus with id {upload_id}")
    upload_data["upload_id"] = upload_id
    return jsonify(upload_data), 200

