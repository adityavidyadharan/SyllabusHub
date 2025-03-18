from flask import Flask
from flask_cors import CORS
from backend.courses import courses
from backend.firebase import initialize_firebase
from backend.users import users
from backend.tag_api import tags  # Make sure this import works

app = Flask(__name__)
CORS(app)

'''
# Apply CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
'''
@app.route('/health', methods=['GET'])
def health():
    return 'Healthy'

initialize_firebase()
app.register_blueprint(users, url_prefix='/users')
app.register_blueprint(courses, url_prefix='/courses')
app.register_blueprint(tags, url_prefix='/tags')  # This registers the tags blueprint

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)