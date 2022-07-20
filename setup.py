from setuptools import setup, find_packages

name = 'CRESHMap'
version = '0.0'
release = '0.0.1'
author = 'Magnus Hagdorn'

setup(
    name=name,
    packages=find_packages(),
    version=release,
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
            'templates/*.html', 'templates/cresh.map',
            'static/favicon.ico', 'static/map.js', 'static/images/*']},
    extras_require={
        'lint': [
            'flake8>=3.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'creshmap-manage=CRESHMap.manage:main',
            'creshmap-genmap=CRESHMap.genmap:main',
        ],
    },
    author=author,
    description=("CRESHMap webmap application"),
)
