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
from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO, emit
import json
import threading
import time

from edge import gps
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
    page_title = dba.latest_flight()['name']
    java_scripts = ['static/js/common.js', 'static/js/map.js', 'static/js/live.js']
    return render_template('live.html', title=page_title, js=java_scripts)


@app.route('/vor')
def vor():
    '''Vor page'''
    page_title = 'Vor Tracking'
    java_scripts = ['static/js/common.js', 'static/js/map.js', 'static/js/vor.js']
    return render_template('vor.html', title=page_title, js=java_scripts)


@app.route('/predict')
def predict():
    '''Predictive landing page'''
    page_title = 'Predictive Landing'
    java_scripts = ['static/js/common.js', 'static/js/tracking.js']
    return render_template('live.html', title=page_title, js=java_scripts)


@app.route('/mobile')
def mobile():
    '''Mobile page (stripped to the minimum data required),
    and uses device sensors to point to balloon (if allowed)'''
    return render_template('mobile.html', title='EDGE Mobile')


@app.route('/disclaimer')
def disclaim():
    '''Disclaimer page'''
    return render_template('disclaimer.html', title='EDGE Disclaimer')


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

    # Save the point to the database, if success - an ID is returned
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
        point = prep_payload_for_publish(point)
        prep_dict[point['edge_id']]['points'].append(point)
    # Serialize all the values from the dict
    # Only send it to the new client.
    emit('points', json.JSONEncoder().encode([v for v in prep_dict.values()]))


@socketio.on('connect', namespace='/vor')
def vor_client_connected():
    '''On socket connection for the VOR site, only
    the most recent point with VOR info will be sent.
    '''
    current_flights_points = dba.this_flights_points()
    if len(current_flights_points) > 0:
        vor_new_point_handler(point={'points': [current_flights_points[-1]]})


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
        point_latlng = (point['latitude'], point['longitude'])

        # rank the vors based on distance
        vor_rankings = []
        # For most EDGE uses, the only VORs hit will be in
        # around CO (or nearby)
        filters = {
            'state': {
                '$in': ['CO', 'KS', 'NE']
            }
        }
        # Limit the 'rows' from the DB, similar to
        # Select latitude,longitude,call from ...
        projection = {
            '_id': 0,
            'latitude': 1,
            'longitude': 1,
            'call': 1
        }
        for vor in dba.get_vor_documents(filters=filters, projections=projection):
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
            'point': prep_payload_for_publish(point)
        }

        # calculate the bearing on the only 2 we care about
        # and filter out stuff that we don't need to send to the client
        for ranking in vor_rankings:
            lat_lng = (ranking['latitude'], ranking['longitude'])
            ranking['bearing'] = gps.bearing(point_latlng, lat_lng)
            emittable['vors'].append(ranking)

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
    # tell_all('point', point, '/predict')
    pass


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
    # Verify that all keys ^ are included.
    for key in required_keys:
        if key not in json_data:
            return False
        # And their data cannot be None or empty string.
        elif json_data[key] is None or json_data[key] is '':
            return False
    return True


def prep_payload_for_publish(payload):
    '''Strip out anything that doesn't need to/shouldn't be sent
    to the client'''
    strip_these_fields = [
        '_id',
        'receipt_time',
        'source'
    ]
    for key in payload.keys():
        if key in strip_these_fields:
            del payload[key]
    return payload


def tell_all(emit_type, emit_data, emit_namespace='/events'):
    '''Broadcast the emit_data to all clients on the emit_namespace.'''
    socketio.emit(emit_type, json.JSONEncoder().encode(emit_data), namespace=emit_namespace)


def main():
    # Set up all the known parties interested in point updates
    point_subscribers = [
        tracker_new_point_handler,
        vor_new_point_handler,
        prediction_new_point_handler
    ]
    for ps in point_subscribers:
        SubscriptionService.subscribe(POINT_RECEIPT_TOPIC, ps)

    print('Server started on localhost:5000')
    socketio.run(app)


if __name__ == '__main__':
    main()
