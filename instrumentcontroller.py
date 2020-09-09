import time

from os.path import isfile
from PyQt5.QtCore import QObject, pyqtSlot

from instr.instrumentfactory import NetworkAnalyzerFactory, mock_enabled
from measureresult import MeasureResult


MHz = 1_000_000
GHz = 1_000_000_000


class InstrumentController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.requiredInstruments = {
            'Анализатор': NetworkAnalyzerFactory('GPIB1::9::INSTR'),
        }

        self.deviceParams = {
            'А1449-01 (тип 1)': {
                'Fstart': 10 * MHz,
                'Fend': 9 * GHz,
                'Pin': -20,
            },
        }

        if isfile('./params.ini'):
            import ast
            with open('./params.ini', 'rt', encoding='utf-8') as f:
                raw = ''.join(f.readlines())
                self.deviceParams = ast.literal_eval(raw)

        self.secondaryParams = {
            'Pin': -10,
            'F1': 4,
            'F2': 8,
        }

        self.span = 0.1
        self.sweep_points = 12801
        self.cal_set = 'Upr_tst'

        self._instruments = dict()
        self.found = False
        self.present = False
        self.hasResult = False

        self.result = MeasureResult()

        self._freqs = list()
        self._mag_s11s = list()

    def __str__(self):
        return f'{self._instruments}'

    def connect(self, addrs):
        print(f'searching for {addrs}')
        for k, v in addrs.items():
            self.requiredInstruments[k].addr = v
        self.found = self._find()

    def _find(self):
        self._instruments = {
            k: v.find() for k, v in self.requiredInstruments.items()
        }
        return all(self._instruments.values())

    def check(self, params):
        print(f'call check with {params}')
        device, secondary = params
        self.present = self._check(device, secondary)
        print('sample pass')

    def _check(self, device, secondary):
        print(f'launch check with {self.deviceParams[device]} {self.secondaryParams}')
        return self._runCheck(self.deviceParams[device], self.secondaryParams, device)

    def _runCheck(self, param, secondary, device):
        print(f'run check with {param}, {secondary}')
        return self.result.readTaskTable(device)

    def measure(self, params):
        print(f'call measure with {params}')
        device, secondary = params
        self.result.raw_data = self.sweep_points, self._measure(device, secondary)
        self.hasResult = bool(self.result)

    def _measure(self, device, secondary):
        param = self.deviceParams[device]
        secondary = self.secondaryParams
        print(f'launch measure with {param} {secondary}')

        self._clear()
        self._init(param, secondary)

        res = self._measure_s_params(param, secondary)

        return res

    def _clear(self):
        self._freqs.clear()
        self._mag_s11s.clear()

    def _init(self, primary, secondary):
        pna = self._instruments['Анализатор']

        pna.send('SYST:PRES')
        pna.query('*OPC?')
        # pna.send('SENS1:CORR ON')

        pna.send('CALC1:PAR:DEF "CH1_S11",S11')

        pna.send(f'SENS1:SWE:POIN {self.sweep_points}')

        pna.send(f'SENS1:FREQ:STAR {primary["Fstart"]}GHz')
        pna.send(f'SENS1:FREQ:STOP {primary["Fend"]}GHz')
        pna.send(f'SENS1:POW:ATT AREC, {primary["Pin"]}')

        pna.send('SENS1:SWE:MODE CONT')
        pna.send(f'FORM:DATA ASCII')

    def _measure_s_params(self, param, secondary):
        pna = self._instruments['Анализатор']

        out = []

        for _ in range(10):
            pna.send(f'CALC1:PAR:SEL "CH1_S21"')
            pna.query('*OPC?')
            res = pna.query(f'CALC1:DATA:SNP? 2')

            if not mock_enabled:
                time.sleep(0.5)

            out.append(_)
            # out += parse_float_list(res)
        return out

    @pyqtSlot(dict)
    def on_secondary_changed(self, params):
        self.secondaryParams = params

    @property
    def status(self):
        return [i.status for i in self._instruments.values()]


def parse_float_list(lst):
    return [float(x) for x in lst.split(',')]
