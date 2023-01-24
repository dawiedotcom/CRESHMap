from . import db
from .models import (
    Geography,
    GeographyTypes,
    Lookup,
    #Variables
)

import pandas as pd

class AggregateBy:

    def _select_children(self, parent):
        geotype = db.session.query(GeographyTypes).where(
            GeographyTypes.gss_code == parent.gss_code
        ).one()
        id_col = getattr(Lookup, geotype.column_name)
        children = db.session.query(Lookup.dz).where(
            id_col == parent.gss_id
        ).all()
        children = [c[0] for c in children] # unpack the first (and only) element of tubles
        return children

    def aggregate(self, composite_geographies, population, year, variable_id):
        values = [0] * composite_geographies.count()
        for i, parent in enumerate(composite_geographies):
            children = self._select_children(parent)
            c_population = population.loc[children, ('population', 'value')]
            values[i] = self._calc_parent_quantity(parent, children, c_population)

        # Put the result in a DataFrame
        gss_ids = [g.gss_id for g in composite_geographies]
        result = pd.DataFrame(
            zip(*[gss_ids, values]),
            columns=['gss_id', 'value'],
        )
        result['year'] = year
        result['variable_id'] = variable_id
        return result

    def _calc_parent_quantity(self, parent, children):
        return 0

class AggregatePopulationDensity(AggregateBy):
    def _calc_parent_quantity(self, parent, children, popval):
        popval['area'] = popval['population'] / popval['value']
        parent_area = popval['area'].sum()
        parent_population = popval['population'].sum()
        return parent_population / parent_area

class AggregatePerCapita(AggregateBy):
    def __init__(self, n):
        self.n = n
    def _calc_parent_quantity(self, parent, children, popval):
        popval['per_n'] = popval['population'] / self.n
        popval['abs_value'] = popval['value'] * popval['per_n']
        parent_per_n = popval['per_n'].sum()
        parent_abs_value = popval['abs_value'].sum()
        return parent_abs_value / parent_per_n

class AggregatePercentage(AggregateBy):
    # For if we know the population, but not the number of things in the category
    def _calc_parent_quantity(self, parent, children, popval):
        popval['abs_value'] = popval['value'] / 100 * popval['population']
        parent_total = popval['abs_value'].sum()
        parent_population = popval['population'].sum()
        return (100.0 * parent_total / parent_population)

class AggregatePercentageWithCount(AggregateBy):
    # For if we know the number of things in the category, but not the total
    def _calc_parent_quantity(self, parent, children, popval):
        popval['abs_value'] = popval['population']
        popval['population'] = popval['abs_value'] / (popval['value'] / 100)
        parent_total = popval['abs_value'].sum()
        parent_population = popval['population'].sum()
        return (100.0 * parent_total / parent_population)


class Aggregator:
    _dispatch = {
        'population_density': AggregatePopulationDensity(),
        'per_1000_capita': AggregatePerCapita(1000),
        'per_10000_capita': AggregatePerCapita(10000),
        'percentage': AggregatePercentage(),
        'percentage_with_count': AggregatePercentageWithCount(),
    }
    def aggregate(self, agg_method, composite_geographies, population, year, variable_id):
        if not agg_method in self._dispatch:
            print(f'Invalid aggregate method: {agg_method}')
            print(' pick on of:', list(self._dispatch.keys()))
            exit(1)
        return self._dispatch[agg_method].aggregate(
            composite_geographies,
            population,
            year,
            variable_id,
        )

