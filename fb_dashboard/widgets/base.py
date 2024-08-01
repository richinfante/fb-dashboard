from datetime import datetime as dt, timedelta

class WidgetBase:
  def __init__(self, x, y, width, height, config):
    self.x = int(x)
    self.y = int(y)
    self.width = int(width)
    self.height = int(height)

    if config.get('refresh_interval'):
      self.refresh_interval = int(config['refresh_interval'])
    else:
      self.refresh_interval = 60

    self.last_refresh = None


  def refresh(self):
    """
      Refresh the widget
    """
    # print('Refreshing widget %s' % self.__class__.__name__)
    self.last_refresh = dt.now()

  def refresh_if_needed(self):
    """
      Refresh the widget if it's time
    """
    if not self.last_refresh:
      self.refresh()

    elif dt.now() - self.last_refresh > timedelta(seconds=self.refresh_interval):
      self.refresh()
