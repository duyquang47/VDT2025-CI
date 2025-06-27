from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
import jwt
from functools import wraps
from datetime import datetime, timedelta

option_a = os.getenv('OPTION_A', "Dogs")
option_b = os.getenv('OPTION_B', "Cats")
hostname = socket.gethostname()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-very-secret-key-for-jwt'
users = {
    "user_test": {
        "password": "user",
        "roles": ["user"]
    },
    "admin_test": {
        "password": "admin",
        "roles": ["admin", "user"]
    }
}

logger = logging.getLogger("vote-app")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

@app.after_request
def log_request_info(response):
    logger.info(
        "Request handled",
        extra={
            'request_path': request.path,
            'http_method': request.method,
            'response_code': response.status_code
        }
    )
    return response

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

# Vote count metric
VOTE_COUNT = Counter('vote_votes_total', 'Total votes cast', ['vote_option'])

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = users.get(auth.username)
    if not user or user['password'] != auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    token = jwt.encode({
        'user': auth.username,
        'roles': user['roles'],
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})

def token_required(required_role=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(" ")[1]

            if not token:
                return jsonify({'message': 'Token is missing!'}), 403 

            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user_roles = data['roles']
                
                if required_role and required_role not in current_user_roles:
                    return jsonify({'message': 'Cannot perform that function!'}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired!'}), 403
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Token is invalid!'}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route("/", methods=['POST','GET'])
@token_required('user')
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        app.logger.info('Received vote for %s', vote)
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)
        
        # Record vote metric
        VOTE_COUNT.labels(vote_option=vote).inc()

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

@app.route("/results", methods=['DELETE'])
@token_required('admin') 
def clear_results():
    try:
        redis = get_redis()
        redis.delete('votes')
        app.logger.info("All votes deleted by admin.")
        return jsonify({"message": "All votes cleared!"}), 200 
    except Exception as e:
        app.logger.error(f"Error clearing votes: {e}")
        return jsonify({"message": "Failed to clear votes"}), 500
    
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)