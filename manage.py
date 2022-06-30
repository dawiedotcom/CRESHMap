from CRESHMap import init_app, db
from CRESHMap.models import DataZone, Data
import argparse
import fiona
from shapely.geometry import shape
from pathlib import Path
import pandas, geopandas


MAPPING = {2020: {
    "Data_Zone": "datazone_id",
    "Total_population": "total_population",
    "Working_Age_population": "working_age_population",
    "ALCOHOL": "alcohol",
    "DRUG": "drug",
    "SIMD2020v2_Rank": "rank",
    "SIMD_2020v2_Percentile": "percentile",
    "SIMD2020v2_Income_Domain_Rank": "income_domain_rank",
    "SIMD2020_Employment_Domain_Rank": "employment_domain_rank",
    "SIMD2020_Health_Domain_Rank": "health_domain_rank",
    "SIMD2020_Education_Domain_Rank": "education_domain_rank",
    "SIMD2020_Access_Domain_Rank": "access_domain_rank",
    "SIMD2020_Crime_Domain_Rank": "crime_domain_rank",
    "SIMD2020_Housing_Domain_Rank": "housing_domain_rank"}}


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--init-db', default=False, action='store_true',
                       help="initialise tables")
    group.add_argument('--delete-db', default=False, action='store_true',
                       help="drop tables")
    group.add_argument('--datazones', type=Path,
                       help="load datazones from shapefile DATAZONES")
    group.add_argument('--data', type=Path,
                       help="CSV file containing data")
    parser.add_argument('-y', '--year', type=int, help="the year")
    args = parser.parse_args()

    app = init_app()

    if args.init_db:
        with app.app_context():
            db.create_all()
    elif args.delete_db:
        with app.app_context():
            db.drop_all()
    elif args.datazones is not None:
        with app.app_context():
            with fiona.open(args.datazones, 'r') as datazones:
                for dz in datazones:
                    dz = DataZone(
                        datazone=dz['properties']['DataZone'],
                        name=dz['properties']['Name'],
                        geometry=shape(dz['geometry']).wkt)
                    db.session.add(dz)
            db.session.commit()
    elif args.data is not None:
        if args.year is None:
            parser.error('need to specify year')
        if args.year not in MAPPING:
            parser.error(f'no mapping for {args.year}')
        mapping = MAPPING[args.year]
        data = pandas.read_csv(args.data)
        to_drop = [k for k in data.keys() if k not in mapping]
        data.drop(to_drop, axis=1, inplace=True)
        data.rename(columns=mapping, inplace=True)
        data['year'] = args.year
        with app.app_context():
            db.session.bulk_insert_mappings(
                Data, data.to_dict(orient='records'))
            db.session.commit()
    else:
        with app.app_context():
            engine = db.get_engine()
            df = geopandas.read_postgis(
                "SELECT geometry, name, data.alcohol FROM datazone join data on datazone.datazone=data.datazone_id", con=engine, geom_col="geometry")
            print(df)


if __name__ == '__main__':
    main()
