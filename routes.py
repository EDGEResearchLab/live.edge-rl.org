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

    Payload minimum data to publish to the socket:
        {
            "id" : "identifier", // This is a correlation id, so something that tags points together in a relationship.
            "points" : [
                {
                    "latitude" : 0,
                    "longitude" : 0
                }
            ]
        }
'''

from __future__ import print_function
from flask import Flask, render_template, request, Response
from flask.ext.socketio import SocketIO, emit
import json

from edge.persistence import DBClient
from edge import vor
from edge.flaskies import endpoint, WebException


CONFIG = json.load(open('config.json'))


app = Flask(__name__)
socketio = SocketIO(app)
dba = DBClient(**CONFIG['mongo'])


@app.route('/')
@app.route('/index.html')
@app.route('/live')
def index():
    '''Live tracking page'''
    return render_template('home.html', title=dba.latest_flight()['name'], js='static/js/tracking.js')


@app.route('/predict')
def predict():
    '''Predictive landing page'''
    return render_template('home.html', title='Predictive Landing', js='static/js/predict.js')


@app.route('/disclaimer')
def disclaim():
    '''Disclaimer page'''
    return render_template('disclaimer.html', title='EDGE Research Lab Disclaimer')


@app.route('/mobile')
def mobile():
    '''Mobile page (stripped to the minimum required)'''
    return render_template('mobile.html', title='EDGE Mobile')


@app.route('/vor', methods=['GET'])
def vor():
    '''Vor page'''
    return render_template('home.html', title='Vor Tracking', js='static/js/vor.js')


@app.route('/vor', methods=['POST'])
@endpoint(consumes='application/json', produces='application/json')
def vor_api():
    '''Run the VOR goodies'''
    return 200, {"message" : "hello"}


# API Route: Receive a report (some type of tracking thing happened)
@app.route('/report', methods=['POST'])
@endpoint(consumes='application/json')
def receive_report():
    '''Receive a report on a trackable, verify that it's valid.'''
    # Assume a successful result.
    result_status = 200

    if not 'Edge-Key' in request.headers or not request.headers['Edge-Key'] == CONFIG['secretkey']:
        raise WebException("Unauthorized", 403)
    elif not is_valid_payload(request.json):
        raise WebException("Bad Request", 400)

    if result_status == 200:
        if received_new_point(request.json):
            result_status = 201
        else:
            raise WebException("Conflict", 409)

    return result_status


@app.errorhandler(404)
def not_found(error):
    # return render_template('error.html'), 404
    return "Page not found"


@socketio.on('connect', namespace='/events')
def client_connected():
    '''On socket connection, all points for the
    most recent flight will be sent to the client.
    '''
    # create a dict to use in formatting data for website consumption.
    prep_dict = {}
    for point in dba.this_flights_points():
        point['_id'] = str(point['_id']) # convert ObjectID() to string
        if not point['edge_id'] in prep_dict:
            prep_dict[point['edge_id']] = {
                'id' : point['edge_id'],
                'points' : []
            }
        prep_dict[point['edge_id']]['points'].append(point)
    # Serialize all the values from the dict (the keys were just used as a pseudo hash table)
    emit('points', json.JSONEncoder().encode([v for v in prep_dict.values()]))


def is_valid_payload(json_data):
    '''Verify that the payload includes all necessary data for edge uses.'''
    required_keys = [
        'edge_id',
        'latitude',
        'longitude',
        'altitude',
        'speed',
        'time',
        'source'
    ]
    for key in required_keys:
        # All keys are required
        if key not in json_data:
            return False
        # And their data cannot be None or empty string.
        elif json_data[key] is None or json_data[key] is '':
            return False
    return True


def received_new_point(point):
    '''Handle storing and saving the new point.'''
    identifier = dba.save_tracking_point(point)
    if identifier:
        print(identifier, point)
        point['_id'] = str(point['_id'])
        emittable = {'id' : point['edge_id'], 'points' : [point]}
        # broadcasts to all clients on /events
        tell_all('point', emittable, '/events')
        #socketio.emit('point', json.JSONEncoder().encode(emittable), namespace='/events')
        return True
    return False


def tell_all(emit_type, emit_data, emit_namespace='/events'):
    socketio.emit(emit_type, json.JSONEncoder().encode(emit_data), emit_namespace)


if __name__ == '__main__':
    socketio.run(app)
