"""
Power side mirrors: fold/unfold state (a real feature commonly tied to
central locking — folding on lock, unfolding on unlock, wired in
sim/simulation.py) plus heated-mirror state.
"""


class Mirrors:
    def __init__(self):
        self.folded = False
        self.heated = False

    def set_folded(self, folded):
        self.folded = folded

    def set_heated(self, heated):
        self.heated = heated
