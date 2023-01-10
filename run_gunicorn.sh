#!/bin/bash

export FLASK_APP=CRESHMap
export SCRIPT_NAME=/dev/cresh

gunicorn --log-level debug --bind 0.0.0.0:55405 CRESHMap.wsgi:app

