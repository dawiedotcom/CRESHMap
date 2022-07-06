/**
 * Elements that make up the popup.
 */
const container = document.getElementById('popup');
const content = document.getElementById('popup-content');
const closer = document.getElementById('popup-closer');

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

const wmsSource = new ol.source.TileWMS({
    url: mapserverurl,
    params: {'LAYERS': 'datazones', 'STYLES': 'alcohol'},
    crossOrigin: 'anonymous',
    transition: 0,
});

const view = new ol.View({
    center: ol.proj.fromLonLat([-3.184111, 55.948162]),
    zoom: 12
});

var map = new ol.Map({
    target: 'map',
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM()
        }),           
        new ol.layer.Tile({
            source: wmsSource
        })
    ],
    overlays: [overlay],
    view: view,
});

map.on('singleclick', function (evt) {
    //document.getElementById('info').innerHTML = '';
    const coordinate = evt.coordinate;
    const viewResolution = /** @type {number} */ (view.getResolution());
    const url = wmsSource.getFeatureInfoUrl(
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
});
