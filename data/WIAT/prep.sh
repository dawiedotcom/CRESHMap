#!/bin/bash

if [ $# == 1 ]; then
    HOST=$1
else
    HOST=localhost
fi

md5sum -c WIAT_data.gpkg.md5sum

if [ ! $? == 0 ]; then
    echo "WIAT_data.gpkg is missing or corrupted"
    exit 1
fi

ogr2ogr -f ogr2ogr -f PostgreSQL "PG:dbname=cresh host=$HOST user=cresh password=$PGPASSWORD" -lco SCHEMA=cresh_new_model_test -lco GEOMETRY_NAME=geom -s_srs "EPSG:27700" -t_srs "EPSG:4326" WIAT_data.gpkg 'WIAT_woodlands — WIAT_fullset' 
psql options=--search_path=cresh_new_model_test -h $HOST -U cresh -a -f migrate_gpkg_to_postgis.sql 

sqlite3 -header -csv WIAT_data.gpkg < dz_query.sql > eligibility_priority.csv 
sqlite3 -header -csv WIAT_data.gpkg < create_wiat_woodlands_data.sql > wiat_woodlands_data.csv


