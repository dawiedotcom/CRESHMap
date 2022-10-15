from . import init_app, db
from .models import Variables

import argparse
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import pandas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path, help="name of configuration file")
    args = parser.parse_args()

    app = init_app()

    # read configuration
    with open(args.config) as f:
        cfg = yaml.load(f, Loader=SafeLoader)

    # read data
    if cfg["type"] == "excel":
        data = pandas.read_excel(cfg["path"])
    elif cfg["type"] == "csv":
        data = pandas.read_csv(cfg["path"])
    else:
        parser.error(f"unkown data type {cfg['type']}")

    with app.app_context():
        # check datafile
        error = False
        for variable in cfg["variables"]:
            if variable["geometry"] not in data.columns:
                print(f'Error: geometry column {variable["geometry"]}'
                      ' not in file')
                error = True
            if variable["file_var"] not in data.columns:
                print(f'Error: geometry column {variable["file_var"]}'
                      ' not in file')
                error = True
            v = db.session.query(Variables).filter(
                Variables.id == variable["db_var"])
            if v.one_or_none() is None:
                print(f'Error: db variable {variable["db_var"]} not defined')
                error = True
        if error:
            parser.error(f'errors in variable description file {cfg["path"]}')

        for variable in cfg["variables"]:
            print(variable['db_var'])
            values = data[[variable["geometry"], variable["file_var"]]]
            values = values.rename(columns={variable["geometry"]: 'gss_id',
                                            variable["file_var"]: 'value'})
            values["year"] = variable["year"]
            values["variable_id"] = variable["db_var"]
            values.to_sql("data", con=db.session.get_bind(),
                          index=False, if_exists="append", method="multi")


if __name__ == "__main__":
    main()
