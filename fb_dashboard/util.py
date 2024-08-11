from datetime import datetime as dt, timedelta


def eval_padding(padding, box_size, root_size=None):
    if isinstance(padding, int):
        return padding
    elif isinstance(padding, str):
        if padding.endswith('vw'):
            if not root_size:
              raise ValueError("Root size not provided")
            return int(root_size[0] * float(padding[:-2]) / 100)
        elif padding.endswith('vh'):
            if not root_size:
              raise ValueError("Root size not provided")
            return int(root_size[1] * float(padding[:-2]) / 100)
        elif padding.endswith("%"):
            return int(box_size * float(padding[:-1]) / 100)
        elif padding.endswith("px"):
            return int(padding[:-2])

def eval_expr(expr, variables):
    """
    Evaluate an expression with variables
    """
    return eval(
        str(expr),
        {**variables, "false": False, "true": True, "dt": dt, "timedelta": timedelta},
    )


def parse_color(color: str) -> tuple:
    """
    Parse a color string into an RGB tuple
    """
    if color.startswith("#"):
        if len(color) == 4:
            r = int(color[1:2], 16) * 17
            g = int(color[2:3], 16) * 17
            b = int(color[3:4], 16) * 17
        else:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

        return (r, g, b)

    elif color.startswith("rgb"):
        return tuple(map(int, color[4:-1].split(",")))
