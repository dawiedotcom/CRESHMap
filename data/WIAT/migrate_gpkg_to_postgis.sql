-- rename the new table
alter table "wiat_woodlands — wiat_fullset" rename to wiat_woodlands;

-- add an entry for the new geography type
insert into cresh_geography_types (gss_code, name) values ('W01', 'WIAT Woodlands');

-- Copy geographies
insert into cresh_geography (gss_id, name, gss_code, GEOMETRY) select 'W01' || fid, scheme_name, 'W01', geom from wiat_woodlands;

-- Copy data
--insert into data (gss_id, year, variable_id, color, value) select 'W01' || fid, 2024, 'wiat_woodlands', '#c51b8a', approv_yr from wiat_woodlands;

-- Remove temporary tables
drop table wiat_woodlands;
