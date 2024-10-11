# Woodlands in and around towns 

Adding data for Woodlands in and around towns (WIAT) dataset.

## Importing the data

### The geopackage

Get the geopackage with the data. Check with:
```bash
md5sum -c WIAT_data.gpkg.md5sum
# WIAT_data.gpkg: OK
```

### Migrate Woodlands geometries

Import Woodlands shapes to postgres:
```bash
ogr2ogr -f PostgreSQL "PG:dbname=cresh host=172.18.0.2 user=cresh password=testingtesting" -lco GEOMETRY_NAME=geom -s_srs "EPSG:27700" -t_srs "EPSG:4326" WIAT_data.gpkg 'WIAT_woodlands — WIAT_fullset'
psql -h <host_name> -U cresh -a -f migrate_gpkg_to_postgis.sql
```
Note the `—` in the geopackage table name is a special character.

### Export to CSV

Export the Data Zone layers:
```bash
sqlite3 -header -csv WIAT_data.gpkg < dz_query.sql > eligibility_priority.csv
sqlite3 -header -csv WIAT_data.gpkg < create_wiat_woodlands_data.sql > wiat_woodlands_data.csv
```

### Import data

Loads data and generate legends:
```bash
creshmap-load-variables varmapping_wiat_dz.yml
creshmap-load-variables varmapping_wiat_woodlands.yml
```

Update the mapserver mapfile:
```bash
creshmap-genmap -o <path_to_output> creshmap.cfg
```


## Notes

### Data model

Mapping between geopackage woodlands table and Creshmap's PostGIS schema

| Geopackage  | PostGIS     | Table                 |                  |
|-------------|-------------|-----------------------|------------------|
| SF_ID       | gss_id      | cresh_geography       |                  |
| scheme_name | name        |                       |                  |
|             | gss_code    |                       | 'W01'            |
| geom        | geometry    |                       |                  |
|-------------|-------------|-----------------------|------------------|
| approv_yr   | year        | data                  |                  |
|             | color       |                       |                  |
|             | data        |                       |                  |
|             | gss_id      |                       | 'WIAT'           |
|-------------|-------------|-----------------------|------------------|
|             | variable    | variables             | wait_woodlands   |
|             | domain      |                       | 'WIAT'           |
|             | description |                       |                  |
|-------------|-------------|-----------------------|------------------|
|             | name        | cresh_geography_types | 'WIAT Woodlands' |
|             | gss_code    |                       | 'W01'            |
|-------------|-------------|-----------------------|------------------|

### Delete WIAT woodlands data

psql:
```sql
delete from data where variable_id = 'wiat_woodlands';
delete from cresh_geography where gss_code = 'W01';
delete from cresh_geography_types where gss_code = 'W01';
```
