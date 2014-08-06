# coding: utf-8

class Storable:
	def to_json(self):
		raise NotImplementedError('to_json method not implemented')


class TrackingPoint(Storable):
	'''Anything trackable is sent over the socket as JSON
	and is stored in the database in the same way and should
	have at least these fields.
	'''
	# _id will be given by the database and will be a UUID
	identifier = None # imei, call, etc.
	latitude = None # decimal degrees
	longitude = None # decimal degrees
	altitude = None # meters
	speed = None # meters/second
	report_time = None # utc, seconds since epoch
	receipt_time = None # utc, seconds since epoch
	source = None # satcom, aprs, etc.

	def to_json(self):
		pass


class Flight(Storable):
	# _id will be given by the database and will be a UUID
	name = None # human readable flight name (generall EDGE#)
	begin = None # utc, seconds since epoch
	end = None # utc, seconds since epoch
	description = None # string, anything noteworthy

	def to_json(self):
		pass


class Vor(Storable):
	# _id will be given by the database and will be a UUID
	state = None
	call = None
	vtype = None
	frequency = None
	elevation = None
	latitude = None
	longitude = None

	def to_json(self):
		pass