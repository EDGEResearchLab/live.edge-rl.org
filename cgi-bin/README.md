# cgi-bin

Items here are either APIs or support for running the APIs.  Specifics can be found below under each header.

## vor.py (api)

This script will return an ordered list of VORS based on their distance (as computed using the [Haversine formula](http://en.wikipedia.org/wiki/Haversine_formula)) from the provided latitude/longitude.  This information is helpful for the FAA as all airplanes are routed utilizing this system.

*Note about vors.sqlite3: This is a non-comprehensive list of VORs in the United States and its territories.  It is compiled from sources deemed reliable.  However the current validity and future maintenance cannot be guaranteed.  This is provided solely as a service without warranty and should not solely be relied upon for tracking, guiding, or other precision directing.*

### Use

This is a CGI program that returns JSON data, you will get two keys back: `success` and `result`.

If the `success` value is `False`, then the `result` will not have much meaningful to say other than telling you that there was a "missing/invalid parameter".

Otherwise, you will get a JSONArray of objects with the following keys: 
* `state` - Two letter abbreviation for a state.  For example "CO" would be "Colorado"
* `call` - A three letter identifier for the VOR.
* `type_` - Type of VOR (Vortac, VOR/DME, NDB)
* `frequency` - Operating frequency in the VHF band (108 - 117.95MHz)
* `elevation` - Elevation in feet of the VOR AGL.
* `lat` - Latitude in decimal degrees.
* `lon` - Longitude in decimal degrees.
* `distance` - Distance in nautical miles (as preferred by the FAA) from the provided GPS lat/lon and the vor.

**Parameters**

These can be provided either via `GET` or `POST`.

* **Required**
    * `latitude` - Latitude in decimal degrees of your source object.
    * `longitude` - Longitude in decimal degrees of your source object.
* **Optional**
    * `state` - This is used as a filter, if you only want VORs in a single state, provide the two letter abbreviation ('CO' for "Colorado")
    * `vor_count` - Limit the list of returned items.  The FAA likes data relative to 2 of the closest VORs. Default is `-1` (or all).
