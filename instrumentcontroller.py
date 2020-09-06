import time

from os.path import isfile
from PyQt5.QtCore import QObject, pyqtSlot

from instr.instrumentfactory import NetworkAnalyzerFactory, mock_enabled
from measureresult import MeasureResult


class InstrumentController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.requiredInstruments = {
            'Анализатор': NetworkAnalyzerFactory('GPIB1::9::INSTR'),
        }

        self.deviceParams = {
            'Усилитель 1': {
                'F': [1.15, 1.35, 1.75, 1.92, 2.25, 2.54, 2.7, 3, 3.47, 3.86, 4.25],
                'mul': 2,
                'P1': 15,
                'P2': 21,
                'Istat': [None, None, None],
                'Idyn': [None, None, None]
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
        self.sweep_points = 81
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
        return self._runCheck(self.deviceParams[device], self.secondaryParams)

    def _runCheck(self, param, secondary):
        print(f'run check with {param}, {secondary}')
        return True

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
        self._init(secondary)

        res = self._measure_s_params(param, secondary)

        return res

    def _clear(self):
        self._freqs.clear()
        self._mag_s11s.clear()

    def _init(self, params):
        pna = self._instruments['Анализатор']

        pna.send('SYST:PRES')
        pna.query('*OPC?')
        # pna.send('SENS1:CORR ON')

        pna.send('CALC1:PAR:DEF "CH1_S21",S21')

        # c:\program files\agilent\newtowrk analyzer\UserCalSets
        pna.send(f'SENS1:CORR:CSET:ACT "{self.cal_set}",1')
        # pna.send('SENS2:CORR:CSET:ACT "-20dBm_1.1-1.4G",1')

        pna.send(f'SENS1:SWE:POIN {self.sweep_points}')

        pna.send(f'SENS1:FREQ:STAR {params["F1"]}GHz')
        pna.send(f'SENS1:FREQ:STOP {params["F2"]}GHz')

        pna.send('SENS1:SWE:MODE CONT')
        pna.send(f'FORM:DATA ASCII')

    def _measure_s_params(self, param, secondary):
        pna = self._instruments['Анализатор']

        out = []

        values = [1, 2, 3]
        if mock_enabled:
            values = [0.1, 0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 1, 10.25, 10.5, 10.75, 10, 11.25, 11.5, 11.75, 11, 12,
                      2.25, 2.5, 2.75, 2, 3.25, 3.5, 3.75, 3, 4.25, 4.5, 4.75, 4, 5.25, 5.5, 5.75, 5, 6.25, 6.5, 6.75,
                      6, 7.25, 7.5, 7.75, 7, 8.25, 8.5, 8.75, 8, 9.25, 9.5, 9.75, 9]

        for ucontrol in values:
            pna.send(f'CALC1:PAR:SEL "CH1_S21"')
            pna.query('*OPC?')
            res = pna.query(f'CALC1:DATA:SNP? 2')

            pna.send(f'CALC:DATA:SNP:PORTs:Save "1,2", "d:/ksa/psm_analog_s2p/s{str(f"{ucontrol:.01f}").replace(".", "_")}.s2p"')
            pna.send(f'MMEM:STOR "d:/ksa/psm_analog_ports2/s{str(f"{ucontrol:.01f}").replace(".", "_")}.s2p"')

            if not mock_enabled:
                time.sleep(0.5)

            out = [1, 2, 3]
        return out

    @pyqtSlot(dict)
    def on_secondary_changed(self, params):
        self.secondaryParams = params

    @property
    def status(self):
        return [i.status for i in self._instruments.values()]


def parse_float_list(lst):
    return [float(x) for x in lst.split(',')]
