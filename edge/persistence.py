from pymongo import MongoClient


class DBClient:
    def __init__(self, server, port, database, username, password):
        login_format = {
            'username': username,
            'password': password,
            'server': server,
            'port': port,
            'database': database
        }
        uri = 'mongodb://{username}:{password}@{server}:{port}/{database}'.format(**login_format)
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.flights_collection = self.db.flights
        self.tracking_collection = self.db.trackers
        self.vor_collection = self.db.vors

    def latest_flight(self):
        '''Grab the most recent flight'''
        return self.flights_collection.find_one(sort=[('start', -1)])

    def this_flights_points(self):
        '''Grab all the points for the most recent flight.'''
        this_flight = self.latest_flight()
        filters = {
            'transmit_time': {
                '$gt': this_flight['begin']
            }
        }
        cur = self.tracking_collection.find(filters).sort('transmit_time')
        return [x for x in cur]

    def get_vor_documents(self, filters=dict(), projections=None):
        '''Get the VOR documents according to the filters and projections.
        @param filters: Dictionary filtering the query
        @param projections: Enable/disable fields ("rows") to get.
        '''
        cur = self.vor_collection.find(filters, projections)
        return [x for x in cur]

    def specific_flights_points(self, flightname):
        pass

    def tracking_point_exists(self, identifier, transmit_time):
        filters = {
            'transmit_time': transmit_time,
            'edge_id': identifier
        }
        found = self.tracking_collection.find(filters)
        return True if found else False

    def save_tracking_point(self, tracking_point):
        '''Save a tracking point to the database.'''
        return self.tracking_collection.insert(tracking_point)

    def save_flight_info(self, flight_info):
        '''Save the information on a flight into the flights collection'''
        return self.flights_collection.insert(flight_info)
