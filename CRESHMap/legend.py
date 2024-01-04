import os
import drawsvg as draw

def format_limits(limits):
    fmt = 0
    str_limits = ['{0:d}'.format(int(lim)) for lim in limits]
    while len(set(str_limits)) < len(str_limits):
        fmt += 1
        str_limits = [f'{{0:.{fmt}f}}'.format(lim) for lim in limits]
    return str_limits

def is_grey(colorcode):
    if not colorcode[0] == '#' and len(colorcode) == 7:
        return False
    r = colorcode[1:3]
    b = colorcode[3:5]
    g = colorcode[5:7]
    return (r == b) and (r == g)

def has_grey(colors):
    return is_grey(colors[0])

def limit_to_str(i, limits):
    interval = float(limits[i+1]) - float(limits[i])
    # Limits with only one value
    is_single_value = interval == 1.0 and limits[i].isnumeric()

    # Single value limits should display as '= <lower bound>'
    if is_single_value:
        return f'{limits[i]}'

    # Upper limit
    if i==0:
        return f' < {limits[i+1]}'

    # Lower limit
    if i == len(limits)-2:
        return f' > {limits[i]}'

    # Limits in the middle of the range
    return f'{limits[i]} - {limits[i+1]}'

def make_labeled_legend(layer_name, colors, limits, width=150, border=10, box_size=25, font_size=16):
    height = (box_size) * len(colors) + border
    d = draw.Drawing(width, height)
    text_h_offset = (box_size + font_size)//2
    for i, c in enumerate(colors):
        y_pos = (len(colors) - i - 1) * box_size
        # Add 70% transparency to match the mapserver layer
        r = draw.Rectangle(0, y_pos, box_size, box_size, fill=c + 'b2')
        limit_label = limits[i]

        t = draw.Text(
            limit_label,
            font_size,
            border + box_size,
            y_pos + text_h_offset,
            font_family='sans-serif',
        )
        d.append(r)
        d.append(t)
    dirname = 'CRESHMap/static/images/legends'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = f'{dirname}/{layer_name}.svg'
    d.save_svg(filename)

def make_numerical_legend(layer_name, colors, limits, width=150, border=10, box_size=25, font_size=16):
    # TODO refactor to call make_labeled_legend
    height = (box_size) * len(colors) + border
    d = draw.Drawing(width, height)
    text_h_offset = (box_size + font_size)//2
    limits = format_limits(limits)
    for i, c in enumerate(colors):
        y_pos = (len(colors) - i - 1)*box_size
        # Add 70% transparency to match the mapserver layer
        r = draw.Rectangle(0, y_pos, box_size, box_size, fill=c + 'b2')
        #r.appendT
        i_limit = i if not has_grey(colors) else i-1
        if is_grey(c):
            limit_label = 'No data'
        else:
            limit_label = limit_to_str(i_limit, limits)

        t = draw.Text(
            limit_label,
            font_size,
            border + box_size,
            y_pos + text_h_offset,
            font_family='sans-serif',
        )
        d.append(r)
        d.append(t)
    dirname = 'CRESHMap/static/images/legends'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = f'{dirname}/{layer_name}.svg'
    d.save_svg(filename)
