import firebase_admin
from firebase_admin import credentials
from loguru import logger

def initialize_firebase():
    cred = credentials.Certificate("backend/config/SyllabusHubFirebaseSA.json")
    firebase_admin.initialize_app(cred)

    logger.info("Firebase initialized")
