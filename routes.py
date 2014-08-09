'''
    @author
        Matt Rasband, David Hughes
    @description
        Live tracking page for edge research lab's high altitude balloon
        operations.
    @license
        tbd
    @disclaimer
        /disclaimer
'''

from __future__ import print_function
from flask import Flask, render_template, request, Response
from flask.ext.socketio import SocketIO, emit
import json
from threading import Thread
from time import sleep

from edge.persistence import DBClient


CONFIG = json.load(open('config.json'))


app = Flask(__name__)
socketio = SocketIO(app)
dba = DBClient(**CONFIG['mongo'])


@app.route('/')
@app.route('/index.html')
@app.route('/live')
def index():
    '''Index page for the deployed site'''
    return render_template('home.html', title=dba.latest_flight()['name'].upper(), js='static/js/tracking.js')


@app.route('/vor')
def vor():
    '''Vor page'''
    return render_template('home.html', title='Vor Tracking', js='static/js/vor.js')


@app.route('/predict')
def predict():
    '''Predictive landing page'''
    return render_template('home.html', title='Predictive Landing', js='static/js/predict.js')


@app.route('/disclaimer')
def disclaim():
    '''Disclaimer page for the deployed site'''
    return render_template('disclaimer.html', title='EDGE Research Lab Disclaimer')


@app.route('/mobile')
def mobile():
    '''Mobile site'''
    return render_template('mobile.html', title='EDGE Mobile')


# API Route
@app.route('/satcom', methods=['POST'])
def receive_satcom():
    '''Getting up and going this is bootstrapped to give us the right format.'''
    if request.headers['Content-Type'] != 'application/json':
        return Response(status=400)
    received_new_point(request.json)
    return Response(status=200)


# API Route
@app.route('/aprs', methods=['POST'])
def receive_aprs():
    '''Endpoint to receive APRS updates.'''
    if request.headers['Content-Type'] != 'application/json':
        return Response(json.dumps({'error' : 'Content type must be application/json'}, status=400, mimetype='application/json'))
    received_new_point(request.json)
    return Response(status=200)


@socketio.on('connect', namespace='/events')
def client_connected():
    '''On socket connection, all points for the
    most recent flight will be sent to the client.
    '''
    emit('points', json.JSONEncoder().encode(dba.this_flights_points()))


def received_new_point(point):
    '''stuff'''
    # insert into db
    socketio.emit('point', json.JSONEncoder().encode(point), namespace='/events')


if __name__ == '__main__':
    socketio.run(app)
