
def eval_expr(expr, variables):
  """
    Evaluate an expression with variables
  """
  return eval(expr, {**variables, 'false': False, 'true': True})

def parse_color(color: str) -> tuple:
  """
    Parse a color string into an RGB tuple
  """
  if color.startswith('#'):
    if len(color) == 4:
      r = int(color[1:2], 16) * 17
      g = int(color[2:3], 16) * 17
      b = int(color[3:4], 16) * 17
    else:
      r = int(color[1:3], 16)
      g = int(color[3:5], 16)
      b = int(color[5:7], 16)

    return (r, g, b)

  elif color.startswith('rgb'):
    return tuple(map(int, color[4:-1].split(',')))
