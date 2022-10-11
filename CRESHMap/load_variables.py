from . import init_app, db
from .models import Variables

import argparse
from pathlib import Path
import yaml
from yaml.loader import SafeLoader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path, help="name of configuration file")
    args = parser.parse_args()

    app = init_app()

    # read configuration
    with open(args.config) as f:
        cfg = yaml.load(f, Loader=SafeLoader)

    with app.app_context():
        for variable in cfg["variables"]:
            if isinstance(variable["id"], list):
                assert isinstance(variable["name"], list)
                assert len(variable["id"]) == len(variable["name"])
                for i in range(len(variable["id"])):
                    v = Variables(id=variable["id"][i],
                                  variable=variable["name"][i],
                                  domain=variable["domain"],
                                  description=variable["description"])
                    db.session.merge(v)
            else:
                v = Variables(id=variable["id"],
                              variable=variable["name"],
                              domain=variable["domain"],
                              description=variable["description"])
                db.session.merge(v)
        db.session.commit()


if __name__ == '__main__':
    main()
