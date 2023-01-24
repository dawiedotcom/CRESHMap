import colorbrewer
import pandas

def color_to_str(rgb, alpha=200):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{alpha:02x}'

def quantile_color_map(cmap_name, values, nbins=5, reverse_colors=False):
    # Result buffer
    result = pandas.DataFrame(['']*values.size, columns=['color'])
    # Find the data range. Note, some values are nonsensical such as negative numbers or NaN.
    v_min = max(values[values == values].min(), 0)
    v_max = values[values==values].max()
    nbins = min(nbins, 9)
    # Create color labels
    cmap = getattr(colorbrewer, cmap_name)
    cmap = cmap[nbins]
    cmap = list(map(color_to_str, cmap)) # Convert list rgb tuples to hex format strings
    if reverse_colors:
        cmap.reverse()
    # Assign colors for interval limits
    result.loc[values <= v_min, 'color'] = cmap[0]
    result.loc[values == v_max, 'color'] = cmap[-1]
    # Assign colors according to quantiles everywhere else. Limits are not included, because
    # for some quantities the vast majority of values can be at the limits.
    result.loc[(values <= v_max) & (values > v_min), 'color'] = pandas.qcut(
        values[(values <= v_max) & (values > v_min)],
        nbins,
        labels=cmap
    )
    return result

def manual_color_map(cmap_name, values, bin_values=[], reverse_colors=False):
    nbins = len(bin_values) - 1
    if nbins > 9:
        print('Colorbrewer support at most 9 different colors')
        nbins = 9
        print('  The following bins will be ignored:', bin_values[nbins:])
    # Create color labels
    cmap = getattr(colorbrewer, cmap_name)
    cmap = cmap[nbins]
    cmap = list(map(color_to_str, cmap))
    if reverse_colors:
        cmap.reverse()
    # Find values in the specified intervals
    result = pandas.DataFrame(['']*values.size, columns=['color'])
    for i in range(nbins):
        idx = (values >= bin_values[i]) & (values < bin_values[i+1])
        result.loc[idx, 'color'] = cmap[i]
    return result

def color(cfg_variable_entry, values):
    # Assign color values based on data values and specifications in the
    # config file
    colormethod = cfg_variable_entry.get('colormethod', '')
    if colormethod == "quantile":
        if not "nclasses" in cfg_variable_entry:
            print("nclasses should be specified for quantile colormothed")
            exit(1)
        return quantile_color_map(
            cfg_variable_entry["colormap"],
            values,
            nbins=cfg_variable_entry["nclasses"],
            reverse_colors=cfg_variable_entry.get("reverse_color", False)
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



