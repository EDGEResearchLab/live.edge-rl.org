from pymongo import MongoClient

class DBClient:
    def __init__(self, server, port, database, username, password):
        uri = "mongodb://{user}:{password}@{server}:{port}/{database}".format(user=username, password=password, server=server, port=port, database=database)
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.flights_collection = self.db.flights
        self.tracking_collection = self.db.tracking

    def latest_flight(self):
        return self.flights_collection.find_one(sort=[("start", -1)])

    def this_flights_points(self):
        return []