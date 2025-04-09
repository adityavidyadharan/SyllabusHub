from flask import Flask
from flask_cors import CORS
import redis.exceptions
import requests_cache
import requests
from loguru import logger
import redis
from backend.recommendations_api import rec 

def filter_canvas_request(response: requests.Response) -> bool:
    return 'gatech.instructure.com' in response.url

redis_backend = requests_cache.RedisCache(ttl=False)
sqlite_backend = requests_cache.SQLiteCache(ttl=172800) # 2 days
backend = sqlite_backend
try:
    redis_backend.clear()
    backend = redis_backend
    logger.info('Using Redis cache')
except redis.exceptions.ConnectionError:
    logger.warning('Using SQLite cache, see README for Redis setup')
requests_cache.install_cache('canvas_cache', backend=backend, expire_after=172800, # 2 days
                             allowable_methods=('GET', 'POST'), filter_fn=filter_canvas_request)


from backend.courses import courses
from backend.firebase import initialize_firebase
from backend.users import users
from backend.tag_api import tags  
from backend.canvas import canvas
from backend.upload import upload
from backend.recommendations_api import rec

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
# Add this at the top with your other routes
@app.route('/debug', methods=['GET'])
def debug():
    # Print all registered rules for debugging
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "rule": str(rule)
        })
    return jsonify({"routes": routes})

initialize_firebase()
app.register_blueprint(users, url_prefix='/users')
app.register_blueprint(courses, url_prefix='/courses')
app.register_blueprint(tags, url_prefix='/tags')  
app.register_blueprint(canvas, url_prefix='/canvas')
app.register_blueprint(upload, url_prefix='/upload')
app.register_blueprint(rec, url_prefix='/rec')  

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
