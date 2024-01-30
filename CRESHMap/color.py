import colorbrewer
import pandas
import numpy as np

def color_to_str(rgb, alpha=200):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}' #{alpha:02x}'

def get_cmap(cmap_name, nbins, reverse_colors):
    cmap = getattr(colorbrewer, cmap_name)
    cmap = cmap[nbins]
    cmap = list(map(color_to_str, cmap)) # Convert list rgb tuples to hex format strings
    if reverse_colors:
        cmap.reverse()
    return cmap


def quantile_color_map(cmap_name, values, nbins=5, reverse_colors=False, no_data_value=None):
    # Result buffer
    result = pandas.DataFrame(['']*values.size, columns=['color'])
    # Find the data range. Note, some values are nonsensical such as negative numbers or NaN.
    idx = (values == values) & (values != no_data_value)
    v_min = max(values[idx].min(), 0)
    v_max = values[idx].max()
    nbins = min(nbins, 9)
    # Create color labels
    cmap = get_cmap(cmap_name, nbins, reverse_colors)
    # Assign colors for interval limits
    result.loc[values <= v_min, 'color'] = cmap[0]
    result.loc[values == v_max, 'color'] = cmap[-1]
    # Assign colors according to quantiles everywhere else. Limits are not included, because
    # for some quantities the vast majority of values can be at the limits.
    result.loc[(values <= v_max) & (values > v_min), 'color'], bins = pandas.qcut(
        values[(values <= v_max) & (values > v_min)],
        nbins,
        labels=cmap,
        retbins=True,
    )
    if np.any(~idx):
        result.loc[~idx, 'color'] = '#aaaaaa';
        cmap.insert(0, '#aaaaaa')
    return result, cmap, bins

def manual_color_map(cmap_name, values, bin_values=[], reverse_colors=False):
    nbins = len(bin_values) - 1
    if nbins > 9:
        print('Colorbrewer support at most 9 different colors')
        nbins = 9
        print('  The following bins will be ignored:', bin_values[nbins:])
    # Create color labels
    cmap = get_cmap(cmap_name, nbins, reverse_colors)
    # Find values in the specified intervals
    result = pandas.DataFrame(['']*values.size, columns=['color'])
    for i in range(nbins):
        idx = (values >= bin_values[i]) & (values < bin_values[i+1])
        result.loc[idx, 'color'] = cmap[i]
    return result, cmap, bin_values

def labeled_color_map(cmap_name, values, bin_values, reverse_colors=False):
    nbins = bin_values.size
    if nbins > 9:
        print('Colorbrewer support at most 9 different colors')
        nbins = 9
        print('  The following bins will be ignored:', bin_values[nbins:])

    if nbins == 2:
        cmap = get_cmap(cmap_name, 3, reverse_colors)
        cmap = [cmap[0], cmap[2]]
    else:
        cmap = get_cmap(cmap_name, nbins, reverse_colors)

    result = pandas.DataFrame(['']*values.size, columns=['color'])
    for i, value in enumerate(bin_values):
        idx = values == value
        result.loc[idx, 'color'] = cmap[i]

    return result, cmap, bin_values

def color(cfg_variable_entry, values):
    # Assign color values based on data values and specifications in the
    # config file
    colormethod = cfg_variable_entry.get('colormethod', '')
    no_data_value = cfg_variable_entry.get('no_data_value', None)
    if colormethod == "quantile":
        if not "nclasses" in cfg_variable_entry:
            print("nclasses should be specified for quantile colormothed")
            exit(1)
        return quantile_color_map(
            cfg_variable_entry["colormap"],
            values,
            nbins=cfg_variable_entry["nclasses"],
            reverse_colors=cfg_variable_entry.get("reverse_color", False),
            no_data_value=no_data_value,
        )
    elif colormethod == "manual":
        if not "break_values" in cfg_variable_entry:
            print("{db_var}: break_values should be specified for manual colormethod".format(**cfg_variable_entry))
            exit(1)
        return manual_color_map(
            cfg_variable_entry["colormap"],
            values,
            bin_values=cfg_variable_entry["break_values"],
            reverse_colors=cfg_variable_entry.get("reverse_color", False)
        )
    else:
        print('Color method {0} not supported.'.format(colormethod))
        exit(1)
