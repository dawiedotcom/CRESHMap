from setuptools import setup, find_packages

name = 'CRESHMap'
version = '1.1.1'
author = 'Magnus Hagdorn'

setup(
    name=name,
    packages=find_packages(),
    version=version,
    include_package_data=True,
    install_requires=[
        "sqlalchemy",
        "flask>=1.0",
        "flask_sqlalchemy",
        "Flask-FlatPages",
        "geoalchemy2",
        "psycopg2",
        "fiona",
        "shapely",
        "pandas",
    ],
    package_data={
        'CRESHMap': [
            'templates/*.html', 'templates/cresh.map', 'templates/*.js',
            'static/favicon.ico', 'static/map.js', 'static/images/*', 
            'data/Creshmap_Dataset_Tobacco_Alhocol.xlsx']},
    extras_require={
        'lint': [
            'flake8>=3.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'creshmap-load-geographies=CRESHMap.load_geographies:main',
            'creshmap-define-variables=CRESHMap.define_variables:main',
            'creshmap-load-variables=CRESHMap.load_variables:main',
            # 'creshmap-manage=CRESHMap.manage:main',
            'creshmap-genmap=CRESHMap.genmap:main',
            'creshmap-load-qualitative=CRESHMap.load_qualitative:main',
        ],
    },
    author=author,
    description=("CRESHMap webmap application"),
)
