#!/bin/bash

# Simple script to retreive SIMD data for 2020. The zip archive can be downloaded
# from
#    https://simd.scot
# The 'Download all data & geographies' retrieves
#    https://simd.scot/data/simd2020_withgeog.zip
# The csv file in the zip archive has % and * symbols in some of the data fields
# which should be removed with sed.
# TODO: This script can be adapted to get SIMD data for other years by changing the
#  YEAR variable to 2016 or 2012. But an associated varmapping*.yaml file should
#  be created to import the data to the mapper.

YEAR=2020

DATA_DIR="simd${YEAR}_withgeog"
ZIP_FILE="${DATA_DIR}.zip"
DATA_URL="https://simd.scot/data/${ZIP_FILE}"
CSV_FILE="simd${YEAR}_withinds"
CLEANED_CSV_FILE="${CSV_FILE}_clean.csv"

if [ -f "$CSV_FILE" ]
then
    >&2 echo "The cleaned filename (${CSV_FILE}) already exist."
else
    wget ${DATA_URL}
    unzip ${ZIP_FILE}
    sed 's/[%*]//g' ${DATA_DIR}/${CSV_FILE}.csv > ${CLEANED_CSV_FILE}
fi
