from datetime import datetime as dt, timedelta
from threading import Thread


class WidgetBase:
    def __init__(self, x, y, width, height, config):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

        if config.get("refresh_interval"):
            self.refresh_interval = int(config["refresh_interval"])
        else:
            self.refresh_interval = 60

        # refresh state
        self.last_refresh = None
        self.has_refreshed = False
        self._refresh_thread = None

    def refresh(self):
        """
        Refresh the widget
        """
        # print('Refreshed widget %s @ %s' % (self.__class__.__name__, dt.now()))
        self.last_refresh = dt.now()
        self.has_refreshed = True

    def refresh_in_bg_if_needed(self):
        # if the thread is still running, skip the refresh
        if self._refresh_thread and self._refresh_thread.is_alive():
            # print('Thread is still running, skipping refresh for %s' % self.__class__.__name__)
            return

        """
      Refresh the widget if it's time
    """
        if not self.last_refresh:
            self._refresh_thread = Thread(target=self.refresh)
            self._refresh_thread.start()

        elif dt.now() - self.last_refresh > timedelta(seconds=self.refresh_interval):
            self._refresh_thread = Thread(target=self.refresh)
            self._refresh_thread.start()
