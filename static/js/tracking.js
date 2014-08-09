var map;
var centerOnBalloon = true;
var trackables = {}; // hash for identifier/poly for client updates
var hasReceivedPoints = false;

$(document).ready(function() {
    // Setup the Google Map
    map = initMap('map_canvas', {
        panControl: false,
        scaleControl: true,
        scaleControlOptions: {
            position: google.maps.ControlPosition.LEFT_BOTTOM
        },
        center: new google.maps.LatLng(38.874380, -104.409064),
        streetViewControl: false,
        zoom: 12,
        mapTypeId: google.maps.MapTypeId.TERRAIN
    });
    // createAutoCenterControl(map);

    initSocketIo();
});

var initSocketIo = function() {
    // Setup the websocket connection
    var socket = io.connect('http://localhost:5000/events');
    socket.on('connect', handleOnConnect);
    socket.on('disconnect', handleOnDisconnect);
    socket.on('points', handleInitialPoints);
    socket.on('point', handleNewPoint);
};

var handleOnConnect = function() {
    console.log('Connected to the EDGE-RL live stream.');
    for (var t in trackables) {
        t.clearPath();
    }
};

var handleOnDisconnect = function() {
    console.log('Disconnected form the EDGE-RL live stream.');
};

var handleInitialPoints = function(initial_points) {
    console.debug("Loading initial points." + initial_points);
    try {
        var points = JSON.parse(initial_points);
        for (var uuid in points) {
            console.debug("New trackable: " + uuid);
            trackables[uuid] = new Trackable(map, getDefaultPolyOpts());

            // Add all the points to the trackable.
            for (var i = 0; i < points[uuid].length; i++) {
                var thisPoint = points[uuid][i];

                // Set the map center to the first received point.
                if (!hasReceivedPoints) {
                    map.setCenter(new google.maps.LatLng(thisPoint['latitude'], thisPoint['longitude']));
                    hasReceivedPoints = true;
                }
                
                console.debug("Tracking point: " + JSON.stringify(thisPoint));
                trackables[uuid].addPoint(thisPoint['latitude'], thisPoint['longitude']);
            }
        }
    } catch (e) {
        console.error(e);
    }
};

var handleNewPoint = function(point_content) {
    try {
        var point = JSON.parse(point_content);

        for (var uuid in point) {
            if (!trackables[uuid]) {
                console.debug("New trackable:" + uuid);
                trackables[uuid] = new Trackable(map, getDefaultPolyOpts());
            }

            console.debug("New point for " + uuid);
            var points = point[uuid];
            for (var i = 0; i < points.length; i++) {
                console.debug("Tracking Point: " + JSON.stringify(points[i]));
                trackables[uuid].addPoint(points[i]['latitude'], points[i]['longitude']);
            }
        }
    } catch(e) {
        console.error(e);
    }
};

var initMap = function(map_id, map_options) {
    console.debug('Using map in #' + map_id + ".");
    var map_elem = $('#' + map_id).get(0);
    if (!map_elem) {
        console.error('Map Element not found.');
        throw new Error("Map Element '" + map_id + "' not found.");
    }
    return new google.maps.Map(map_elem, map_options);                                                                         
};

var createAutoCenterControl = function(gmap) {
    //Create a new control for auto centering the map
    var controlDiv = document.createElement('div');

    // Set CSS styles for the DIV containing the control
    // Setting padding to 5 px will offset the control
    // from the edge of the map.
    controlDiv.style.padding = '5px';

    // Create and set-up the control border.
    var controlUI = document.createElement('div');
    controlUI.style.backgroundColor = 'white';
    controlUI.style.borderStyle = 'solid';
    controlUI.style.borderWidth = '2px';
    controlUI.style.cursor = 'pointer';
    controlUI.style.textAlign = 'center';
    controlUI.title = 'Click to select which balloon to automatically center on.';
    controlDiv.appendChild(controlUI);

    // Create and set-up the control interiorS
    var controlText = document.createElement('div');
    controlText.style.fontFamily = 'Arial,sans-serif';
    controlText.style.fontSize = '12px';
    controlText.style.paddingLeft = '4px';
    controlText.style.paddingRight = '4px';
    controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">' + ((centerOnBalloon) ? 'ON' : 'OFF')  + '</span>';
    controlUI.appendChild(controlText);

    // Make the control clickable, toggle the text to reflect the current state.
    google.maps.event.addDomListener(controlDiv, 'click', function() {
        centerOnBalloon = !(centerOnBalloon);
        if (centerOnBalloon) {
            //change the message of controlDiv
            controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">ON</span>';
        } else {
            controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">OFF</span>';
        }
    });

    controlDiv.index = 1;
    gmap.controls[google.maps.ControlPosition.TOP_CENTER].push(controlDiv);
};

var getDefaultPolyOpts = function() {
    var opts = {
        strokeColor: generateRandomHexColor(),
        //strokeColor: '#000000',
        strokeOpacity: 1.0,
        strokeWeight: 4
    };
    return opts;
};

var generateRandomHexColor = function() {
    var chars = "ABCDEF0123456789";
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += chars[Math.floor(Math.random() * (chars.length))];
    }
    console.debug('Generated random color ' + color);
    return color;
};

function Trackable(gmap, polyOpts) {
    this.gmap = gmap;
    this.poly = Trackable._initPoly(gmap, polyOpts);
}

Trackable.prototype.addPoint = function(latitude, longitude) {
    var point = new google.maps.LatLng(latitude, longitude);
    var path = this.poly.getPath();
    path.push(point);
};

Trackable.prototype.clearPath = function() {
    this.poly.getPath().clear();
};

Trackable._initPoly = function(gmap, opts) {
    var poly = new google.maps.Polyline(opts);
    poly.setMap(gmap);
    return poly;
};