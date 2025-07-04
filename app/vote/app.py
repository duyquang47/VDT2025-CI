from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger

option_a = os.getenv('OPTION_A', "Dogs")
option_b = os.getenv('OPTION_B', "Cats")
hostname = socket.gethostname()

app = Flask(__name__)

logger = logging.getLogger("vote-app")

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
app.logger.addHandler(logHandler)
app.logger.setLevel(logging.INFO)

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

@app.route("/", methods=['POST','GET'])
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

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)