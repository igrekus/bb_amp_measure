import random
from os import listdir
from os.path import isfile, join

import openpyxl as openpyxl


class MeasureResult:
    adjust_dirs = {
        1: 'data/+25',
        2: 'data/+85',
        3: 'data/-60',
    }

    def __init__(self, ):
        self.headers = ['нет данных']
        self.gens = {}

    def _init(self):
        pass

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

    def readTaskTable(self, device):

        def getFileList(data_path):
            return [l for l in listdir(data_path) if isfile(join(data_path, l)) and '.xlsx' in l]

        files = getFileList('.')
        length = len(files)
        if length > 1:
            print('too many task tables, abort')
            return False
        elif length <= 0:
            print('no task table found, abort')
            return False

        fileName = files[0]
        print('using task table:', fileName, 'for device:', device)

        wb = openpyxl.load_workbook(fileName)
        ws = wb[device]

        headers = [ws._get_cell(1, col).value for col in range(2, ws.max_column + 1)]
        gens = []
        for i, _ in enumerate(headers):
            span = float(ws._get_cell(2, i + 2).value)
            step = float(ws._get_cell(3, i + 2).value)
            mean = float(ws._get_cell(4, i + 2).value)
            gens.append((span, step, mean))

        self.headers = headers
        self.gens = gens

        wb.close()
        print('done read')
        return True

    def generateValue(self, data):

        if not data or '-' in data or chr(0x2212) in data or not all(data):
            return '-'

        span, step, mean = data
        start = mean - span
        stop = mean + span
        return random.randint(0, int((stop - start) / step)) * step + start

    @property
    def data(self):
        if not self.gens:
            raise RuntimeError('No task table supplied')
        return [self.generateValue(v) for v in self.gens]
