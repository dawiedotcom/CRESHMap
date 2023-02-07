from . import init_app, db
from .models import TextQuotes
#from .models import Images

import argparse
from pathlib import Path
import pandas
#import yaml

def main():
    parser = argparse.ArgumentParser("Load qualitative data into the database")
    parser.add_argument('datafile', type=Path, help="Name of an Excel file mapping Data Zones to text or images")
    args = parser.parse_args()

    app = init_app()

    data = pandas.read_excel(args.datafile)

    # Make sure all the table exist
    with app.app_context():
        db.create_all()

        # Load text columns
        data_zone_id = data.columns[0]
        text_data = pandas.DataFrame(columns=['gss_id', 'value'])
        for column in data.columns[1:]:
            idx = data.loc[:, column] == data.loc[:, column]
            new_data = data.loc[idx, [data_zone_id, column]]
            new_data = new_data.rename(columns={
                data_zone_id: 'gss_id',
                column: 'value'
            })
            print(new_data)
            text_data = pandas.concat((text_data, new_data))
        print(text_data)
        text_data.to_sql(
            'cresh_text_quotes',
            con=db.session.get_bind(),
            index=False,
            if_exists='append',
            method='multi',
        )


