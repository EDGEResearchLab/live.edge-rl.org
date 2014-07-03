// The client polling rate (ms)
const UPDATE_INTERVAL = 10000;
// Map Options/Configuration
const MAP_OPTS = {
    panControl: false,
    scaleControl: true,
    scaleControlOptions: {
        position: google.maps.ControlPosition.LEFT_BOTTOM
    },
    streetViewControl: false,
    zoom: 14,
    center: new google.maps.LatLng(38.874380, -104.409064), // COSPGS East
    mapTypeId: google.maps.MapTypeId.TERRAIN
};
var centerOnBalloon = false;

//====================================================
$(document).ready(function() {
    console.debug('document.ready');

    var map = initMap('map_canvas', MAP_OPTS);

    var trackables = [
        new Trackable(
            map,
            "satcom",
            {
                allPoints: 'http://localhost:8000/xml/live_satcom.xml',
                heartBeat: 'http://localhost:8000/xml/last3_satcom.xml'
            }
        ),
        new Trackable(
            map, 
            "aprs",
            {
                allPoints: 'http://localhost:8000/xml/live_aprs.xml',
                heartBeat: 'http://localhost:8000/xml/last3_aprs.xml'
            }
        )
    ];

    createAutoCenterControl(map, trackables);
});
//====================================================

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

var createAutoCenterControl = function(gmap, trackables) {
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
    controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">OFF</span>';
    controlUI.appendChild(controlText);

    // Make the control clickable, toggle the text to reflect the current state.
    google.maps.event.addDomListener(controlDiv, 'click', function() {
        if (trackables.length == 1) {
            centerOnBalloon = !(centerOnBalloon);
            if (centerOnBalloon) {
                //change the message of controlDiv
                controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">ON</span>';
            } else {
                controlText.innerHTML = 'Auto Center <span style="font-weight:bold;font-size:12px;">OFF</span>';
            }
        } else {
            
        }
    });

    controlDiv.index = 1;
    gmap.controls[google.maps.ControlPosition.TOP_CENTER].push(controlDiv);
};

/*
 * Get the default configuration for the poly line.
 * @return (Hash) - Required poly line options.
 */
var getDefaultPolyOpts = function() {
    var opts = {
        strokeColor: generateRandomHexColor(),
        strokeOpacity: 1.0,
        strokeWeight: 4
    };
    return opts;
};

/*
 * Get the default configuration for the prediction poly.
 * @return (Hash) - Required poly line options for a prediction line.
 */
var getDefaultPredictPolyOpts = function() {
    var opts = getDefaultPolyOpts();
    opts.strokeColor = '#0000DD'; // blue.
    opts.strokeWeight = 3,
    opts['icons'] = [{
        icon: {
            path: 'M 0,-1 0,1',
            strokeOpacity: 1,
            scale: 4
        },
        offset: '0',
        repeat: '20px'
    }];
    return opts;
};

/*
 * Generate a random HEX color.
 * @return (String) - HEX
 */
var generateRandomHexColor = function() {
    var chars = "ABCDEF0123456789";
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += chars[Math.floor(Math.random() * (chars.length + 1))];
    }
    console.debug('Generated random color ' + color);
    return color;
};

/*
 * Create an AJAX request to the url and call the successHandler when complete.
 * @param url (String) - Url to send the request to
 * @param successhandler (Function) - Method to call on success
 * @param context (Object) - Context that the Function is called in (usually 'this' if a method)
 * @param method (String) - Request method (GET or POST)
 * @param data (Hash) - Data to send to the server with the request.
 * @return (Void)
 */
var ajaxRequest = function(url, successHandler, context, method, data) {
    $.ajax({
        type: method,
        url: url,
        data: data,
        cache: false,
        success: function(data) {
            successHandler.call(context, data);
        },
        error: function() {
            console.error('Error running the ajaxRequest');
        }
    });
};

/*
 * An object CTOR that is "trackable" and will be placed on the map and constantly updated.
 *
 * @param gmap (google.maps.Map) - The map object the trackable should be placed on.
 * @param name (String) - A name for the trackable object, used mostly for debug logging..
 * @param dataUrls (Hash) - Hash of the urls used for both the initial points grabbing and heart beat checks.
 * This should be {allPoints: '', heartBeat: ''}
 * @param predict (Boolean) - True to run and show a prediction, False otherwise.
 * @param polyOpts (Hash) - Custom options to use for the Poly line.
 * @param predictPolyOpts (Hash) - Custom options to use for the Prediction Poly line.
 *
 * @return (Object) - this.
 */
function Trackable(gmap, name, dataUrls, predict, polyOpts, predictPolyOpts) {
    // Reference to the map this is on.
    this.map = gmap;
    // Name for logging
    this.name = name;
    // Urls for getting data and the heartbeat
    this.urls = dataUrls;
    // The line of the history
    this.poly = Trackable._initPoly(gmap, polyOpts || getDefaultPolyOpts());
    // Boolean, run/show the prediction (or don't)
    this.predict = predict;
    if (this.predict) {
        // The line of the prediction
        this.predictPoly = Trackable._initPoly(gmap, predictPolyOpts || getDefaultPredictPolyOpts());
    }
    // Markers for the line history.
    this.markers = [];
    // Latest lat/lon the trackable was at.
    this.last = {
        lat: 0,
        lon: 0,
        index: 0
    };

    this._loadPoints(dataUrls.allPoints);
    var self = this; // hold onto this object as the scope changes momentarily.
    // Run a heartbeat to make sure the trackable is always up-to-date
    setInterval(function() { self._pointCheck(dataUrls.heartBeat); }, UPDATE_INTERVAL);
}

/*
 * Initialize a poly line.
 *
 * @param gmap (google.maps.Map) - The map to attache the poly to.
 * @param options (Hash) - Hash of options used to instantiate the poly.
 *
 * @return (google.maps.Polyline) - Initialized poly line object, attached to a map.
 */
Trackable._initPoly = function(gmap, options) {
    var poly = new google.maps.Polyline(options);
    poly.setMap(gmap);
    return poly;
};

/*
 * Parse a node 
 */
Trackable.parseNode = function(node) {
    return {
        index: node.find('pointIndex').text(),
        time: node.find('time').text(),
        alt: node.find('altitude').text(),
        lat: node.find('latitude').text(),
        lon: node.find('longitude').text(),
        speed: node.find('speed').text()
    };
};

/*
 * Load all the points.
 *
 * @param dataUrl (String) - The URL resource get get all the points.
 *
 * @return (Void)
 */
Trackable.prototype._loadPoints = function(dataUrl) {
    ajaxRequest(dataUrl, this._handleInitialPoints, this, 'GET');
};

/*
 * Handle the successful GET of the initial points.
 *
 * @param data (Object) - The retrieved data from the GET
 *
 * @return (Void)
 */
Trackable.prototype._handleInitialPoints = function(data) {
    console.debug(this.name + ': Handling Initial Points.');

    var self = this;

    // Iterate over all the data, adding to the poly/path on the map.
    $(data).find('balloonOne').each(function(index) {
        var result = Trackable.parseNode($(this));
        if (result) {
            console.debug(self.name + ': Adding Point: ' + JSON.stringify(result));
            self.appendToPath(result.lat, result.lon);
            self.last.lat = result.lat;
            self.last.lon = result.lon;
            self.last.index = result.index;
        }
    });

    this._postReceipt();
};

/*
 * Check that we have all the points (heartbeat check, essentially)
 *
 * @param dataUrl (String) - Url to GET a heartbeat set of points.
 *
 * @return (Void)
 */
Trackable.prototype._pointCheck = function(dataUrl) {
    ajaxRequest(dataUrl, this._handlePointCheck, this, 'GET');
};

/*
 * Handle the successful GET of the heartbeat check.
 *
 * @param data (Object) - The retrieved data from the GET
 *
 * @return (Void)
 */
Trackable.prototype._handlePointCheck = function(data) {
    console.debug(this.name + ': Heartbeat Check');

    var self = this;

    // Iterate over the heartbeat points, checking if any were missed.  If so,
    // clear out the paths and get the whole dataset again.
    $(data).find('balloonOne').each(function(index) {
        var result = Trackable.parseNode($(this));
        if (result) {
            if (result.index > self.last.index) {
                // If more than 3 elements out of date, then get all points again.
                if (result.index - self.last.index > 3) {
                    console.debug(self.name + ': We missed a few points, restarting.');
                    self.clearPath(self.poly.getPath());
                    self.clearPath(self.predictPoly.getPath());
                    self._loadPoints(self.urls.allPoints);
                    return false; // breaks the .each loop
                } else {
                    console.debug(self.name + ': New Point: ' + JSON.stringify(result));
                    self.appendToPath(result.lat, result.lon);
                    self.last.lat = result.lat;
                    self.last.lon = result.lon;
                    self.last.index = result.index;
                }
            }
        }
    });

    this._postReceipt();
};

/*
 * Run after the points have been received (any time).
 */
Trackable.prototype._postReceipt = function() {
    if (this.predict && this.last.lat != 0 && this.last.lon != 0) {
        this.updatePrediction(this.last.lat, this.last.lon);
    }
    if (centerOnBalloon) {
        this.map.setCenter(new google.maps.LatLng(this.last.lat, this.last.lon));
    }
};

/*
 * Clear out the path for the given poly.
 * @param path - The poly's path to clear.
 */
Trackable.prototype.clearPath = function(path) {
    var workingPath = path || this.poly.getPath();
    workingPath.clear();
};

/*
 * Remove the last N items from the poly's path.
 * @param count (Integer) - The number to remove, defaults to 1.
 */
Trackable.prototype.removeLastFromPath = function(count) {
    var num = 0;
    if (count) {
        num -= Math.abs(count);
    } else {
        num -= 1;
    }

    var path = poly.getPath();
    for (num; num < 0; num++) {
        path.pop();
    }
};

/*
 * Add a lat/lon to the path.
 * @param latitude
 * @param longitude
 */
Trackable.prototype.appendToPath = function(latitude, longitude) {
    var point = new google.maps.LatLng(latitude, longitude);
    var path = this.poly.getPath();
    path.push(point);
    this.map.setCenter(point);
};

/*
 * Update the prediction line.
 */
Trackable.prototype.updatePrediction = function(newLatitude, newLongitude) {
    var predictPath = this.predictPath.getPath();
    this.clearPath(predictPath);
    var predLat = ((newLatitude - this.last.lat) + newLatitude);
    var predLat = ((newLongitude - this.last.lon) + newLongitude);
};
