# CRESHMap
CHRESMap is a web application written in python using the [flask framework](https://flask.palletsprojects.com/en/2.1.x/). It uses a [postgis](https://postgis.net/) database for storing the data. The data map layer is generated using [mapserver](https://mapserver.org/) and displayed using [OpenLayers](https://openlayers.org/). Static pages are produced from [markdown](https://www.markdownguide.org/basic-syntax/) input files kept in the [CRESHMap/pages/](CRESHMap/pages/) directory.

## Setup
Install all the requirements into a python virtual envrionment.

### Database Setup
Install postgis, create a database (let's call it `cresh`) with support for spatial data and create a read-write (`cresh`) and a read-only user (`creshro`). The actual user names and database names can be different. 

The application uses an evnironment variable to figure out how to connect to the database:
```
export DATABASE_URL='postgresql://cresh:PASSWORD@pow/cresh
```

### Loading Data
There are multiple programs involved loading data:
1. `creshmap-load-geographies` creates all tables (after dropping them if they already exist). Geographies are loaded following the plan in [data.yaml](data.yaml). Compound geographies are aggregated from the smallest ones.
2. `creshmap-define-variables` reads the variable definition file [variables.yaml](variables.yaml) and updates the database with any changes. Variable IDs should not change.
3. `creshmap-load-variables` reads in data from either and excel or csv file. The mapping of column names to data base names is defined in the [config file](varmapping1.yml).

### Generating the mapserver map file
The mapserver is controlled via a [mapfile](https://mapserver.org/mapfile/index.html). This file is generated using the [genmap.py](genmap.py) script together with a [configuration file](creshmap.cfg). The script also configures the database connection for mapserver. Use the read-only user.

```
export DATABASE_URL='postgresql://creshro:PASSWORD@pow/cresh?options=-c%20search_path=cresh,public,topology'
creshmap-genmap creshmap.cfg -o /path/to/webdir
```

Note, that the read-ony user needs access to all database schemas to work correctly. The script will put the mapfile and template into the `/path/to/webdir` directory. Attributes that can be displayed by the map are configured in the configuration file.


## References
 * This application follows the [flask application factory pattern](https://hackersandslackers.com/flask-application-factory/).
 * The web app uses [postcodes.io](https://postcodes.io/) for geolocating postcodes.
 * [local authority areas - Scotland]( https://spatialdata.gov.scot/geonetwork/srv/api/records/1cd57ea6-8d6e-412b-a9dd-d1c89a80ad62)
 * [UK Parliamentary Constituencies - Scotland](https://spatialdata.gov.scot/geonetwork/srv/api/records/8d1a56f5-a943-42ad-8cff-c808a50b8f10)

