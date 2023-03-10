import os
import drawSvg as draw

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

def make_legend(layer_name, colors, limits, width=150, border=10, box_size=25, font_size=16):
    height = (box_size) * len(colors) + border
    d = draw.Drawing(width, height)
    text_h_offset = (box_size - font_size)//2
    limits = format_limits(limits)
    for i, c in enumerate(colors):
        # Add 70% transparency to match the mapserver layer
        r = draw.Rectangle(0, border + i*box_size, box_size, box_size, fill=c + 'b2')
        #r.appendT
        i_limit = i if not has_grey(colors) else i-1
        if is_grey(c):
            limit_label = 'No data'
        elif i_limit == 0:
            limit_label = f' < {limits[i_limit+1]}'
        elif i_limit == len(limits)-2:
            limit_label = f' > {limits[i_limit]}'
        else:
            limit_label = f'{limits[i_limit]} - {limits[i_limit+1]}'

        t = draw.Text(
            limit_label,
            font_size,
            border + box_size,
            border + i*box_size + text_h_offset,
            font_family='sans-serif',
        )
        d.append(r)
        d.append(t)
    dirname = 'CRESHMap/static/images/legends'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = f'{dirname}/{layer_name}.svg'
    d.saveSvg(filename)
