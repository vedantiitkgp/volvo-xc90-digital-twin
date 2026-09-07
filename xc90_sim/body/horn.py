"""Horn: a real, if simple, momentary electrical circuit — on while pressed, off otherwise."""


class Horn:
    def __init__(self):
        self.honking = False

    def set_honking(self, honking):
        self.honking = honking
