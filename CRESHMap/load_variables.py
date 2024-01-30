from . import init_app, db
from .models import Variables
from .models import Geography
from .models import GeographyTypes
from .aggregate import Aggregator
from .color import (color, labeled_color_map)
from .legend import (make_numerical_legend, make_labeled_legend)

import argparse
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import pandas

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-legends', action='store_true', default=False,
                        help="don't perform database commits, only update legends")
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

        agg = Aggregator()
        for variable in cfg["variables"]:
            print(variable['db_var'])
            values = data[[variable["geometry"], variable["file_var"]]]
            values = values.rename(columns={variable["geometry"]: 'gss_id',
                                            variable["file_var"]: 'value'})
            values["year"] = variable["year"]
            values["variable_id"] = variable["db_var"]

            # Calculate color values
            layer_name = '{db_var}_{year}_S01'.format(**variable)
            if variable["colormethod"] == 'labeled':
                # TODO check that 'label_var' is provided in variable
                values_and_labels = data[[variable['file_var'], variable['label_var']]]
                values_and_labels = values_and_labels.rename(columns={
                    variable['file_var']: 'value',
                    variable['label_var']: 'label',
                })
                values_and_labels = values_and_labels.drop_duplicates()
                values_and_labels.sort_values('value', inplace=True)
                values["color"], cmap, limits = labeled_color_map(
                    variable['colormap'],
                    values['value'].to_numpy(),
                    values_and_labels['value'],
                    reverse_colors=variable.get('reverse_color', False),
                )
                make_labeled_legend(layer_name, cmap, values_and_labels['label'].to_numpy(), width=240)
            else:
                values["color"], cmap, limits = color(variable, values["value"].to_numpy())
                no_data_label = variable.get('no_data_label', 'No Data')
                make_numerical_legend(layer_name, cmap, limits, no_data_label=no_data_label)

            # Aggregate data for composite geometries
            if 'aggregatemethod' in variable:
                meta_column_label = variable.get("aggregatemeta", "population")
                meta_column = cfg["metadata"][meta_column_label][variable["year"]]
                population = data[[
                    variable["geometry"],
                    variable["file_var"],
                    meta_column,
                   ]]
                population = population.rename(columns={
                    variable["geometry"]: 'gss_id',
                    variable["file_var"]: 'value',
                    meta_column: 'population'
                   })
                population.set_index('gss_id', inplace=True)

                geography_types = db.session.query(GeographyTypes).where(
                    (GeographyTypes.column_name != None),
                    (GeographyTypes.gss_code != 'S01')
                )
                for geo_type in geography_types:
                    print( 'aggregate {db_var} in {0} using {aggregatemethod}'.format(
                        geo_type.gss_code,
                        **variable,
                    ))
                    composite_geographies = db.session.query(Geography).where(
                        Geography.gss_code == geo_type.gss_code
                    )
                    agg_values = agg.aggregate(
                        variable['aggregatemethod'],
                        composite_geographies,
                        population,
                        variable["year"],
                        variable["db_var"],
                    )
                    agg_values['color'], cmap, limits = color(
                        variable,
                        agg_values['value'].to_numpy(),
                    )
                    layer_name = '{db_var}_{year}_{0}'.format(geo_type.gss_code, **variable)
                    no_data_label = variable.get('no_data_label', 'No Data')
                    make_numerical_legend(layer_name, cmap, limits, no_data_label=no_data_label)
                    values = pandas.concat((values, agg_values))

            if not args.update_legends:
                values.to_sql("data", con=db.session.get_bind(),
                              index=False, if_exists="append", method="multi")



if __name__ == "__main__":
    main()
