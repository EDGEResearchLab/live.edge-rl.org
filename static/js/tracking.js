const MAP_OPTS = {
	panControl: false,
	scaleControl: true,
	scaleControlOptions: {
		position: google.maps.ControlPosition.LEFT_BOTTOM
	},
	streetViewControl: false,
	zoom: 14,
    //center: new google.maps.LatLng(38.874380, -104.409064), // COSPGS East
    center: new google.maps.LatLng(39.020540,-104.274317), // PaintMines
    mapTypeId: google.maps.MapTypeId.TERRAIN
};

var centerOnBalloon = true;
var trackables = {}; // hash for identifier/poly for client updates

$(document).ready(function() {
	// Setup Google Maps
	var map = initMap('map_canvas', MAP_OPTS);

	var socket = io.connect('http://localhost:5000/events');

	socket.on('connect', function() {
		console.log('Connected to the EDGE-RL\'s live stream.');
	});
	
	socket.on('points', function(initial_points) {
		try {
			points = JSON.parse(initial_points);
			console.log(points);
		} catch (e) {
			console.error(e);
		}
	});

	socket.on('point', function(point_content) {
		console.log('Received new point ' + point_content + '.');
		try {
			point = JSON.parse(point_content);
			// do things.
		} catch(e) {
			console.error(e);
		}
	});
});

/*
 * Initialize the Google Map element.
 * @return (google.maps.Map) - Map object.
 */
var initMap = function(map_id, map_options) {
    console.debug('Using map in #' + map_id);
    var map_elem = $('#' + map_id).get(0);
    if (!map_elem) {
        console.error('Map Element not found.');
        throw new Error("Map Element '" + map_id + "' not found.");
    }
    return new google.maps.Map(map_elem, map_options);                                                                         
};