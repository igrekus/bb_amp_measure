import itertools
import math
import os
import random
import statistics


class MeasureResult:
    adjust_dirs = {
        1: 'data/+25',
        2: 'data/+85',
        3: 'data/-60',
    }

    def __init__(self, ):
        self.headers = ['h1', 'h2', 'h3']
        self._freqs = list()
        self._s21s = list()

    def _init(self):
        self._freqs.clear()
        self._s21s.clear()

    def _process(self):
        pass

    @property
    def raw_data(self):
        return True

    @raw_data.setter
    def raw_data(self, args):
        print('process result')
        self._init()

        points = int(args[0])
        s2p = list(args[1])
        self._process()

    @property
    def freqs(self):
        return self._freqs

    @property
    def s21(self):
        return self._s21s

    @property
    def data(self):
        return [1, 2, 3]
