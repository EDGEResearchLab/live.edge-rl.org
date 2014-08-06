'''
    @author Matt Rasband
    @description Live tracking page for edge research lab's high altitude balloon operations.
    @license tbd
    @disclaimer /disclaimer
'''

from __future__ import print_function
from flask import Flask, render_template, request, Response
from flask.ext.socketio import SocketIO, emit
from flask.ext.pymongo import PyMongo
import json

app = Flask(__name__)

CONFIG = json.load(open('config.json'))

app.config['MONGO_HOST'] = CONFIG['mongo']['host']
app.config['MONGO_PORT'] = int(CONFIG['mongo']['port'])
app.config['MONGO_DBNAME'] = CONFIG['mongo']['db']
app.config['MONGO_USERNAME'] = CONFIG['mongo']['user']
app.config['MONGO_PASSWORD'] = CONFIG['mongo']['pass']

mongo = PyMongo(app, config_prefix='MONGO')
socketio = SocketIO(app)

@app.route('/')
@app.route('/index.html')
@app.route('/live')
def index():
    '''Index page for the deployed site'''
    return render_template('home.html', title='EDGE12', js='static/js/tracking.js') # TODO - dynamic page title


@app.route('/vor')
def vor():
    return render_template('home.html', title='Vor Tracking', js='static/js/tracking.js')


@app.route('/predict')
def predict():
    return render_template('home.html', title='Predictive Landing', js='static/js/tracking.js')


@app.route('/chase')
def chase():
    return "chase page"


@app.route('/disclaimer')
def disclaim():
    '''Disclaimer page for the deployed site'''
    return render_template('disclaimer.html', title='EDGE Research Lab Disclaimer')


@app.route('/satcom', methods = ['POST'])
def receive_satcom():
    '''Getting up and going this is bootstrapped to give us the right format.'''
    if request.headers['Content-Type'] != 'application/json':
        return Response(status=400)
    data = request.json



@app.route('/aprs', methods = ['POST'])
def receive_aprs():
    if request.headers['Content-Type'] != 'application/json':
        return Response(json.dumps({'error' : 'Content type must be application/json'}, status=400, mimetype='application/json'))
    pass


@socketio.on('connect', namespace='/events')
def client_connected():
    # give all points on connection
    emit('points', json.JSONEncoder().encode([{'pointIndex' : 1, 'stuff' : 'yeah'}, {'pointIndex' : 2, 'stuff' : 'no'}]))


def tell_all(emit_type, emit_dict, namespace='/events'):
    socketio.emit(emit_type, json.JSONEncoder().encode(emit_dict), namespace=namespace)


if __name__ == '__main__':
    socketio.run(app)

