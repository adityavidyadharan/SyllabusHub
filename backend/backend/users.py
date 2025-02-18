from flask import Blueprint, jsonify, request
from firebase_admin import auth
from loguru import logger
import json
from backend.supabase import supabase

users = Blueprint('users', __name__)


def set_user_role(uid, role):
    auth.set_custom_user_claims(uid, {"role": role})
    logger.info(f"Role '{role}' set for user {uid}")

def user_to_dict(user):
    return {
        "uid": user.uid,
        "email": user.email,
        "custom_claims": user.custom_claims or {},
        "disabled": user.disabled,
        "photo_url": user.photo_url,
        "phone_number": user.phone_number,
        "provider_data": [p.provider_id for p in user.provider_data],
    }

@users.route('/new', methods=['POST'])
def new_user():
    data = request.json
    uid = data.get('user_id')
    email = data.get('email')
    name = data.get('name')
    # TODO determine user type (student, teacher)
    # for now, use local JSON
    role = ""
    with open("backend/config/account_type.json") as f:
        mapping = json.load(f)
        role = mapping.get(email, "student")
    logger.debug(f"Setting role {role} for user {uid} ({email})")
    set_user_role(uid, role)
    if role == "professor":
        # look for existing professor
        professors = supabase.table("professors").select("*").eq("firebase_id", uid).execute()
        print(professors)
        if professors.count != None and professors.count > 0:
            logger.info(f"Professor {uid} already exists")
            return jsonify(user_to_dict(auth.get_user(uid))), 200
        # insert new professor
        logger.info(f"Inserting new professor {uid}")
        supabase.table("professors").insert({
            "firebase_id": uid,
            "email": email,
            "name": name,
        }).execute()
    user = auth.get_user(uid)
    return jsonify(user_to_dict(user)), 200

    

@users.route('/<uid>', methods=['GET'])
def get_user(uid):
    user = auth.get_user(uid)
    logger.info(f"User {uid} found")
    return jsonify(user_to_dict(user)), 200