"""Built-in button (spec 5.6)."""


class Button:
    def __init__(self, session):
        self._session = session

    @property
    def is_pressed(self):
        return self._session.core.button_pressed()

    @property
    def is_released(self):
        return not self.is_pressed
