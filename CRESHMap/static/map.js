/**
 * Elements that make up the popup.
 */
const container = document.getElementById('popup');
const content = document.getElementById('popup-content');
const closer = document.getElementById('popup-closer');
const attribSelector = document.getElementById('attrib');
const searchPostcodeButton = document.getElementById('button-search-postcode');
const searchPostcode = document.getElementById('search-postcode');

var layers = {};

const baselayer = new ol.layer.Tile({
    source: new ol.source.OSM()});

/* get capabilities */
function capsListener () {
    var wmsCapabilitiesFormat = new ol.format.WMSCapabilities();
    var c = wmsCapabilitiesFormat.read(this.responseText);
    c.Capability.Layer.Layer[0].Style.forEach(function(item,index) {
	var option = document.createElement("option");
	option.text = item.Name;
	option.value = item.Name;
	attribSelector.appendChild(option);

	var wmsSource = new ol.source.TileWMS({
	    url: mapserverurl,
	    params: {'LAYERS': 'datazones', 'STYLES': item.Name},
	    crossOrigin: 'anonymous',
	    transition: 0,
	});
	layers[item.Name] = new ol.layer.Tile({
	    source: wmsSource});
    });
    map.once('postrender', function(event) {
	var layer = Object.keys(layers)[0];
	setAttributeLayer(layer);
    });
}

var capsRequest = new XMLHttpRequest();
capsRequest.addEventListener("load", capsListener);
capsRequest.open("GET", mapserverurl + 'version=1.3.0&request=GetCapabilities&amp&service=WMS');
capsRequest.send();

/* the attribute changed */
attribSelector.onchange = function() {
    setAttributeLayer(this.value);
}

function setAttributeLayer(l) {
    map.setLayers([baselayer, layers[l]]);
    map.CRESHlayer = l;
}

/**
 * Add a click handler to hide the popup.
 * @return {boolean} Don't follow the href.
 */
closer.onclick = function () {
    overlay.setPosition(undefined);
    closer.blur();
    return false;
};

/**
 * Create an overlay to anchor the popup to the map.
 */
const overlay = new ol.Overlay({
    element: container,
    autoPan: {
	animation: {
	    duration: 250,
	},
    },
});

const view = new ol.View({
    center: ol.proj.fromLonLat([-4.352258, 57.009659]),
    zoom: 7
});


var map = new ol.Map({
    target: 'map',
    layers: [baselayer],
    overlays: [overlay],
    view: view,
});

map.on('singleclick', function (evt) {
    const coordinate = evt.coordinate;
    showInfo(coordinate);
});

function showInfo(coordinate) {
    const viewResolution = /** @type {number} */ (view.getResolution());
    const url = layers[map.CRESHlayer].A.source.getFeatureInfoUrl(
	coordinate,
	viewResolution,
	'EPSG:3857',
	{'INFO_FORMAT': 'text/html'}
    );
    if (url) {
	fetch(url)
	    .then((response) => response.text())
	    .then((data) => {
		content.innerHTML = data;
		overlay.setPosition(coordinate);
	    });
    }
}

/*******************/
/* search postcode */
/*******************/
searchPostcodeButton.onclick = function () {
    var postcode = searchPostcode.value;
    console.log('search');

    var postcodeRequest = new XMLHttpRequest();
    postcodeRequest.addEventListener("load", postcodeListener);
    postcodeRequest.open("GET", "https://api.postcodes.io/postcodes/" + postcode);
    postcodeRequest.send();
}

function postcodeListener () {
    const response = JSON.parse(this.responseText);
    if (response.status != 200) {
	console.log('error');
	searchPostcode.style.color = 'red';
    }
    else {
	searchPostcode.style.color = 'black';
	const coords = ol.proj.fromLonLat(
	    [response.result.longitude, response.result.latitude]);
	showInfo(coords);
	const nview = new ol.View({
	    center: coords,
	    zoom: 14
	});
	map.setView(nview);
    }
}

function resizeMap() {
    const nav_height = document.getElementsByClassName('navbar')[0].clientHeight;

    const mapDiv = document.getElementById('map');
    mapDiv.style.height = window.innerHeight-nav_height + 'px';
    map.updateSize();
}


window.onload = resizeMap;
window.onresize = resizeMap;
