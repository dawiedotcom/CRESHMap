#!/bin/bash

export FLASK_APP=CHRESHMap
export SCRIPT_NAME=/dev/mhagdorn

gunicorn --log-level debug --bind 0.0.0.0:55401 CRESHMap.wsgi:app

