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
            "id" : "identifier", // This is a correlation id, so something
            //that tags points together in a relationship.
            "points" : [
                {
                    "latitude" : 0,
                    "longitude" : 0
                }
            ]
        }
'''

from __future__ import print_function
from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO, emit
import json
import threading
import time

from edge import gps
from edge.collections import filter_dict
from edge.flaskies import endpoint, WebException
from edge.persistence import DBClient
from edge.service import SubscriptionService


CONFIG = json.load(open('config.json'))
POINT_RECEIPT_TOPIC = 'point_received'

app = Flask(__name__)
socketio = SocketIO(app)
dba = DBClient(**CONFIG['mongo'])

# Subscribers to this will receive `point={payload}` on each point update.
# It's suggested to accept *args, **kwargs in case extra params are added
# in the future.
SubscriptionService.create_topic(POINT_RECEIPT_TOPIC)


@app.route('/')
@app.route('/live')
def index():
    '''Live tracking page'''
    return render_template('live.html', title=dba.latest_flight()['name'], js='static/js/tracking.js')


@app.route('/vor')
def vor():
    '''Vor page'''
    return render_template('live.html', title='Vor Tracking', js='static/js/vor.js')


@app.route('/predict')
def predict():
    '''Predictive landing page'''
    return render_template('live.html', title='Predictive Landing', js='static/js/predict.js')


@app.route('/mobile')
def mobile():
    '''Mobile page (stripped to the minimum data required),
    and uses device sensors to point to balloon (if allowed)'''
    return render_template('mobile.html', title='EDGE Mobile')


@app.route('/disclaimer')
def disclaim():
    '''Disclaimer page'''
    return render_template('disclaimer.html', title='EDGE Research Lab Disclaimer')


@app.route('/report', methods=['POST'])
@endpoint(consumes='application/json')
def receive_report():
    '''Receive a report on a trackable, verify that it's valid
    and broadcast it if so.
    '''
    # # Assume a successful result.
    # if not 'Edge-Key' in request.headers \
    # or not request.headers['Edge-Key'] == CONFIG['secretkey']:
    #     raise WebException("Unauthorized", 403)
    if not is_valid_payload(request.json):
        raise WebException('Bad Request', 400)

    payload = request.json
    # use UTC, seconds since epoch
    payload['receipt_time'] = int(time.time())

    # Save the point to the payload
    identifier = dba.save_tracking_point(payload)
    if identifier:
        payload['_id'] = str(payload['_id'])  # Convert ObjectId to string
        emittable = {
            'id': payload['edge_id'],
            'points': [payload]
        }
        SubscriptionService.broadcast(POINT_RECEIPT_TOPIC, point=emittable)
    else:
        raise WebException('Conflict', 409)

    return 201, None


@socketio.on('connect', namespace='/events')
def client_connected():
    '''On socket connection, all points for the
    most recent flight will be sent to the client.
    '''
    # create a dict to use in formatting data for website consumption.
    prep_dict = {}
    for point in dba.this_flights_points():
        point['_id'] = str(point['_id'])  # convert ObjectID() to string
        if not point['edge_id'] in prep_dict:
            prep_dict[point['edge_id']] = {
                'id': point['edge_id'],
                'points': []
            }
        prep_dict[point['edge_id']]['points'].append(point)
    # Serialize all the values from the dict
    # Only send it to the new client.
    emit('points', json.JSONEncoder().encode([v for v in prep_dict.values()]))


@socketio.on('connect', namespace='/vor')
def vor_client_connected():
    '''On socket connection for the VOR site, only
    the most recent point with VOR info will be sent.
    '''
    # TODO
    pass


@socketio.on('connect', namespace='/predict')
def predict_client_connected():
    '''On socket connection for prediction clients...'''
    # TODO - Run calcs, publish result.
    pass


def tracker_new_point_handler(point, *args, **kwargs):
    '''Handler for new points on the tracking page.'''
    tell_all('point', point, '/events')


def vor_new_point_handler(point, *args, **kwargs):
    '''Handler for sending new points to VOR interested
    parties. Threads out the calcs to not block server
    activities.
    '''
    def runnable(point):
        keys_to_strip = ['elevation', 'state', 'frequency', '_id', 'type']

        point_latlng = (point['latitude'], point['longitude'])

        # rank the vors based on distance
        vor_rankings = []
        for vor in dba.get_vor_points():
            vor_latlng = (vor['latitude'], vor['longitude'])
            vor['distance'] = gps.distance_between(point_latlng, vor_latlng)
            vor_rankings.append(vor)

        # TODO - Maybe publish an alert?
        if len(vor_rankings) < 2:
            return

        # the faa cares about the closest 2
        vor_rankings = sorted(vor_rankings, key=lambda k: k['distance'])[:2]

        emittable = {
            'vors': [],
            'point': point
        }

        # calculate the bearing on the only 2 we care about
        # and filter out stuff that we don't need to send to the client
        for ranking in vor_rankings:
            lat_lng = (ranking['latitude'], ranking['longitude'])
            ranking['bearing'] = gps.bearing(point_latlng, lat_lng)
            emittable['vors'].append(filter_dict(ranking, keys_to_strip))

        # Publish the update.
        tell_all('point', emittable, '/vor')

    # If the point is as expected and there is data, use the latest point.
    # The operation is sent to the background to not block.
    if 'points' in point and len(point['points']) > 0:
        thread = threading.Thread(target=runnable, args=(point['points'][-1],))
        thread.start()


def prediction_new_point_handler(point, *args, **kwargs):
    '''Handler for sending new points to prediction interested
    parties.
    '''
    # TODO - Run calc, publish result.
    tell_all('point', point, '/predict')


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


def tell_all(emit_type, emit_data, emit_namespace='/events'):
    '''Broadcast the emit_data to all clients on the emit_namespace.'''
    socketio.emit(emit_type, json.JSONEncoder().encode(emit_data), namespace=emit_namespace)


def main():
    point_subscribers = [
        tracker_new_point_handler,
        vor_new_point_handler,
        prediction_new_point_handler
    ]
    for ps in point_subscribers:
        SubscriptionService.subscribe(POINT_RECEIPT_TOPIC, ps)

    print('Server started on localhost:5000')
    socketio.run(app)
    # app.run(debug=True)

if __name__ == '__main__':
    main()
