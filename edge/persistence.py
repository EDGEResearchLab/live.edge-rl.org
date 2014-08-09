from pymongo import MongoClient

class DBClient:
    def __init__(self, server, port, database, username, password):
        uri = "mongodb://{user}:{password}@{server}:{port}/{database}".format(user=username, password=password, server=server, port=port, database=database)
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.flights_collection = self.db.flights
        self.tracking_collection = self.db.trackers

    def latest_flight(self):
        '''Grab the most recent flight'''
        return self.flights_collection.find_one(sort=[("start", -1)])

    def this_flights_points(self):
        '''Grab all the points for the most recent flight.'''
        this_flight = self.latest_flight()
        cur = self.tracking_collection.find({"transmit_time" : {"$gt" : this_flight['begin']}}).sort("transmit_time")
        return [x for x in cur]

    def specific_flights_points(self, flightname):
        pass

    def tracking_point_exists(self, identifier, transmit_time):
        found = self.tracking_collection.find({"transmit_time" : transmit_time, "edge_id" : identifier})
        return True if found else False

    def save_tracking_point(self, tracking_point):
        '''Save a tracking point to the database.'''
        # TODO - Enforce a minimum schema (even though that isn't required for mongo)
        return self.tracking_collection.insert(tracking_point)