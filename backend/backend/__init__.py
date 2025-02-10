from flask import Flask
from flask_cors import CORS
from backend.firebase import initialize_firebase
from backend.users import users

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return 'Healthy'

initialize_firebase()
app.register_blueprint(users, url_prefix='/users')
