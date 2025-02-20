from flask import Blueprint, jsonify, request
from firebase_admin import auth
from loguru import logger
import json

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
    # TODO determine user type (student, teacher)
    # for now, use local JSON
    role = ""
    with open("backend/config/account_type.json") as f:
        mapping = json.load(f)
        role = mapping.get(email, "student")
    logger.debug(f"Setting role {role} for user {uid} ({email})")
    set_user_role(uid, role)
    user = auth.get_user(uid)
    return jsonify(user_to_dict(user)), 200

    

@users.route('/<uid>', methods=['GET'])
def get_user(uid):
    user = auth.get_user(uid)
    logger.info(f"User {uid} found")
    return jsonify(user_to_dict(user)), 200