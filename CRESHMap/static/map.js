/**
 * Elements that make up the popup.
 */
const containerHist = document.getElementById('popup');
const popupTable = document.getElementById('popup-data');
const containerQual = document.getElementById('qual-popup');
const closerHist = document.getElementById('popup-closer');
const closerQual = document.getElementById('qual-popup-closer');
const layerSelector = document.getElementById('layer');
const domainSelector = document.getElementById('domain');
const attribSelector = document.getElementById('attrib');
const yearSelector = document.getElementById('year');
const searchPostcodeButton = document.getElementById('button-search-postcode');
const searchPostcode = document.getElementById('search-postcode');
const attribDescription = document.getElementById('attrib_description');
//const histogramPlot = document.getElementById("histogram");

var layers = {};

const baselayer = new ol.layer.Tile({
    source: new ol.source.Stamen({
        layer: 'toner-lite'
    })
});

function getStatistic(stat_name, layer_name, attribute, year){
    const attrib_index = attribute + '_' + year;
    if (stat_name in layers[layer_name][attrib_index])
        return;
    const url = encodeURI(
        window.location.href + '/' + stat_name + '/' + layer_name + '/' + attribute + '/' + year
    );
    fetch(url)
        .then((response) => response.text())
        .then((data) => {
            const stat_data = JSON.parse(data);
            layers[layer_name][attrib_index][stat_name] = stat_data;
        });
}

function getHistogram(layer_name, attribute, year) {
    getStatistic('histogram', layer_name, attribute, year);
}
function getQuintile(layer_name, attribute, year) {
    getStatistic('quintile', layer_name, attribute, year);
}

function removeAllOptions(selector) {
    while (selector.firstChild)
        selector.removeChild(selector.lastChild);
}

function addOptions(selector, options) {
    for (i in options) {
        var option = document.createElement("option");
        option.text = options[i].text;
        option.value = options[i].value;
        selector.appendChild(option);
    }
}

function updateAttributeOptions() {
    removeAllOptions(attribSelector);
    const domain_name = domainSelector.value;
    const domain_data = mapattribs[domainSelector.value];
    attributes = [];
    for (a in domain_data) {
        attributes.push({
            'text': domain_data[a].name,
            'value': domain_data[a].id,
        });
    }
    addOptions(attribSelector, attributes);
}

function updateYearOptions() {
    removeAllOptions(yearSelector);
    const domain_name = domainSelector.value;
    const attrib_id = attribSelector.value;
    const attrib_data = mapattribs[domainSelector.value][attrib_id];
    var years = [];
    for (year in attrib_data.id_year) {
        const id_year = attrib_data.id_year[year];
        years.unshift({
            'text': year,
            'value': id_year,
        });
    }
    addOptions(yearSelector, years);
}

function updateLayerOptions() {
    removeAllOptions(layerSelector);
    const domain_name = domainSelector.value;
    const attrib_id = attribSelector.value;
    const year = yearSelector.value;
    const data_zones = mapattribs[domainSelector.value][attrib_id]['data_zones'];
    const layer_options = data_zones.map( data_zone => ({
        'text': data_zone.name,
        'value': data_zone.gss_code,
    }));
    addOptions(layerSelector, layer_options);
}

function updateLegend() {
    const filename = window.location.href + '/static/images/legends/' + yearSelector.value + '_' + layerSelector.value + '.svg';
    const img = document.getElementById('legendimg');
    img.src = filename;
}

/* get capabilities */
async function capsListener () {
    var wmsCapabilitiesFormat = new ol.format.WMSCapabilities();
    var c = wmsCapabilitiesFormat.read(this.responseText);
    c.Capability.Layer.Layer.forEach( (item, index) => {
        layers[item.Name] = {Title: item.Title};
        item.Style.forEach(function(st_item,st_index) {
            var wmsSource = new ol.source.TileWMS({
                url: mapserverurl,
                params: {
                    'LAYERS': item.Name, //+",Quotes,Images",
                    'STYLES': st_item.Name, //+",Quotes,Images",
                },
                crossOrigin: 'anonymous',
                transition: 0,
            });
            layers[item.Name][st_item.Title] = new ol.layer.Tile({
                source: wmsSource
            });
        });
    });

    updateAttributeOptions();
    updateYearOptions();
    updateLayerOptions();
    setLayer(layerSelector.value, yearSelector.value);
}

var capsRequest = new XMLHttpRequest();
capsRequest.addEventListener("load", capsListener);
capsRequest.open("GET", mapserverurl + 'version=1.3.0&request=GetCapabilities&amp&service=WMS');
capsRequest.send();

/* the layer changed */
layerSelector.onchange = function() {
    setLayer(layerSelector.value, yearSelector.value);
}

/* the attribute changed */
attribSelector.onchange = function() {
    updateYearOptions();
    updateLayerOptions();
    setLayer(layerSelector.value, yearSelector.value);
}

/* the domain changed */
domainSelector.onchange = function() {
    updateAttributeOptions();
    updateYearOptions();
    updateLayerOptions();
    setLayer(layerSelector.value, yearSelector.value);
}

/* the year changed */
yearSelector.onchange = function() {
    updateLayerOptions();
    setLayer(layerSelector.value, yearSelector.value);
}


function setLayer(l,a) {
    //map.setLayers([baselayer, layers[l][a], layers["Quotes"]["Quotes"], layers["Images"]["Images"]]);
    map.setLayers([baselayer, layers[l][a]]);
    map.CRESHattrib = layers[l][a];
    const mapattrib = mapattribs[domainSelector.value][attribSelector.value];
    attribDescription.innerHTML = mapattrib.description;
    updateLegend();
    //getHistogram(l, mapattribs[a].id, mapattribs[a].year);
    getQuintile(l, mapattrib.id, mapattrib.year_id[yearSelector.value]);
}

/**
 * Add a click handler to hide the histogram popup.
 * @return {boolean} Don't follow the href.
 */
closerHist.onclick = function () {
    overlayHist.setPosition(undefined);
    closerHist.blur();
    return false;
};

/**
 * Add a click handler to hide the qualitative data popup.
 * @return {boolean} Don't follow the href.
 */
closerQual.onclick = function () {
    overlayQual.setPosition(undefined);
    closerQual.blur();
    return false;
};


/**
 * Create an overlay to anchor the histogram popup to the map.
 */
const overlayHist = new ol.Overlay({
    element: containerHist,
    autoPan: {
        animation: {
            duration: 250,
        },
    },
});

/**
 * Create an overlay to anchor the qualitative popup to the map.
 */
const overlayQual = new ol.Overlay({
    element: containerQual,
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
    overlays: [overlayHist, overlayQual],
    view: view,
});

map.on('singleclick', function (evt) {
    const coordinate = evt.coordinate;
    //showQualitative(coordinate);
    showInfo(coordinate);
});

function geography_plural(geography) {
    if (geography === "Data Zone")
        return "Data Zones";
    if (geography === "Intermediate Zone")
        return "Intermediate Zones";
    if (geography === "Local Authority")
        return "Local Authorities";
    if (geography === "NHS Health Board")
        return "NHS Health Boards";
    return geography;
}

function make_count_blurb(popup_data) {
    return '<div></div>';
}

function num_description(i) {
    if (i == 1) return '1st';
    if (i == 2) return '2nd';
    if (i == 3) return '3rd';
    if (i == 4) return '4th';
    if (i == 5) return '5th';
}
function make_stat_blurb(popup_data, a) {

    if (popup_data.attributes[a].value === '')
        return '<div>No data available</div>';

    const is_all_zeros = map.CRESHattrib.quintile.bins.reduce( (accum, value) => !accum && (value == 0), false);
    if (is_all_zeros)
        return '<div></div>';

    var i_quintile=1;
    while (popup_data.attributes[a].value > map.CRESHattrib.quintile.bins[i_quintile])
        i_quintile++;
    const geography = layerSelector.options[layerSelector.selectedIndex].text;
    const geography_pl = geography_plural(geography);
    return (
        '<div>' + popup_data.name + ' is in the ' +
            num_description(i_quintile) + ' quintile of ' +
            geography_pl + ' in Scotland.</div>'
    );
}

function showInfo(coordinate) {
    const viewResolution = /** @type {number} */ (view.getResolution());
    const url = map.CRESHattrib.A.source.getFeatureInfoUrl(
        coordinate,
        viewResolution,
        'EPSG:3857',
        {'INFO_FORMAT': 'text/html'}
    );
    if (url) {
        fetch(url)
            .then((response) => response.text())
            .then((data) => {
                if (data === '') return;
                closerQual.onclick();
                const popup_data = JSON.parse(data);
                var old_thead = popupTable.getElementsByTagName("thead")[0];
                var thead = document.createElement('thead');
                var row = thead.insertRow(-1);
                attribName = document.createElement('th');
                row.appendChild(attribName);
                attribName.innerHTML = popup_data.name;
                attribName.colspan = "2";
                attribName.scope="col";
                popupTable.replaceChild(thead, old_thead);

                var old_tbody = popupTable.getElementsByTagName("tbody")[0];
                var tbody = document.createElement('tbody');
                for (a in popup_data.attributes) {
                    if (a != yearSelector.value)
                        continue;
                    var row = tbody.insertRow(-1);
                    var name = document.createElement('th');
                    row.appendChild(name);
                    var value = row.insertCell(1);
                    name.innerHTML = popup_data.attributes[a].name + " (" + popup_data.attributes[a].year + ")";
                    name.scope="row";
                    value.innerHTML = popup_data.attributes[a].value;
                    break;
                }
                popupTable.replaceChild(tbody, old_tbody);
                var popupInfoText = document.getElementById('popupInfoText');
                popupInfoText.innerHTML = make_count_blurb(popup_data);
                popupInfoText.innerHTML += make_stat_blurb(popup_data, a);
                /*Plotly.newPlot(histogramPlot, [{
                    type: 'bar',
                    x: map.CRESHattrib.histogram.x,
                    y: map.CRESHattrib.histogram.y }], {
                        autosize: true,
                        title: {
                            text: mapattribs[attribSelector.value].name,
                            font: {
                                size: 24
                            },
                            xref: 'paper',
                            x: 0.05,
                        },
                        shapes: [{
                            type: 'line',
                            xref: 'x',
                            yref: 'paper',
                            y0: 0,
                            y1: 1,
                            x0: popup_data.attributes[attribSelector.value].value ,
                            x1: popup_data.attributes[attribSelector.value].value ,
                            line: {
                                color: 'rgb(255, 0, 0)',
                                width: 2
                            }}
                                ],
                        margin: {
                            l: 35,
                            r: 5,
                            b: 25,
                            t: 35,
                            pad: 4
                        },
                        width: 250,
                        height:300}) ;*/
                overlayHist.setPosition(coordinate);
            });
    }
}

async function showQualitative(coordinate) {
    const viewResolution = /** @type {number} */ (view.getResolution());
    const qualLayers = [layers["Images"]["Images"], layers["Quotes"]["Quotes"]];
    const urls = qualLayers.map(
        layer => layer.A.source.getFeatureInfoUrl(
            coordinate,
            3*viewResolution,
            'EPSG:3857',
            {'INFO_FORMAT': 'text/html'}
        )
    );
    const qualDataP = await Promise.all(
        urls.map(url =>
            fetch(url)
                .then(response => response.json())
                .then(data => data)
                .catch(error => {})
        )
    );
    const qualData = qualDataP.filter(d => d);

    if (qualData.length == 0) {
        showInfo(coordinate);
        return;
    }
    closerHist.onclick();
    // Set the heading text in the popup to the data zone's name
    var popup_data = qualData[0];
    var popupTable = containerQual.getElementsByTagName("table")[0];
    var old_thead = popupTable.getElementsByTagName("thead")[0];
    var thead = document.createElement('thead');
    var row = thead.insertRow(-1);
    attribName = document.createElement('th');
    row.appendChild(attribName);
    attribName.innerHTML = popup_data.name;
    attribName.colspan = "2";
    attribName.scope="col";
    popupTable.replaceChild(thead, old_thead);

    // New content for the popup
    const old_tbody = popupTable.getElementsByTagName("tbody")[0];
    var tbody = document.createElement('tbody');

    // Populate with quotes and images
    qualData.forEach( popup_data => {
        const quotes = popup_data["Quotes"].split("|");
        quotes.forEach( q => {
            var row = tbody.insertRow(-1);
            row.appendChild(document.createElement('th'));
            var quote = row.insertCell(1);
            row.appendChild(quote);
            if (q.includes("static/images/qual/")) {
                row.innerHTML = "<div><img src=\"" + window.location.href + "/" + q + "\"/></div>";
            }
            else {
                row.innerHTML = q;
            }
        });
    });
    popupTable.replaceChild(tbody, old_tbody);
    overlayQual.setPosition(coordinate);
}

/*******************/
/* search postcode */
/*******************/
searchPostcodeButton.onclick = function () {
    var postcode = searchPostcode.value;

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

searchPostcode.addEventListener("keyup", function(event) {
    event.preventDefault();
    if (event.keyCode === 13) {
        searchPostcodeButton.click();
    }
});

function resizeMap() {
    const nav_height = document.getElementsByClassName('navbar')[0].clientHeight;

    const mapDiv = document.getElementById('map');
    mapDiv.style.height = window.innerHeight-nav_height + 'px';
    map.updateSize();
}


window.onload = resizeMap;
window.onresize = resizeMap;
