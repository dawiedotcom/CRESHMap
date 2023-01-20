from . import init_app, db
from .models import Variables

import argparse
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import pandas
import colorbrewer

def quantile_color_map(cmap_name, values, nbins=5):
    def to_str(rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    # Result buffer
    result = pandas.DataFrame(['']*values.size, columns=['color'])
    # Find the data range. Note, some values are nonsensical such as negative numbers or NaN.
    v_min = max(values[values == values].min(), 0)
    v_max = values[values==values].max()
    nbins = min(nbins, 9)
    # Create color labels
    cmap = getattr(colorbrewer, cmap_name)
    cmap = cmap[nbins]
    cmap = list(map(to_str, cmap)) # Convert list rgb tuples to hex format strings
    # Assign colors for interval limits
    result.loc[values <= v_min, 'color'] = cmap[0]
    result.loc[values == v_max, 'color'] = cmap[-1]
    # Assign colors according to quantiles everywhere else. Limits are not included, because
    # for some quantities the vast majority of values can be at the limits.
    result.loc[(values < v_max) & (values > v_min), 'color'] = pandas.qcut(
        values[(values < v_max) & (values > v_min)],
        nbins,
        labels=cmap
    )
    return result

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

            colormethod = variable.get('colormethod', '')
            if colormethod == "quantile":
                values["color"] = quantile_color_map(
                    variable["colormap"],
                    values["value"].to_numpy(),
                    nbins=variable["nclasses"]
                )
            else:
                print('Color method {0} not supported.'.format(colormethod))

            values.to_sql("data", con=db.session.get_bind(),
                          index=False, if_exists="append", method="multi")


if __name__ == "__main__":
    main()
