from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QRunnable, QThreadPool
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox

from deviceselectwidget import DeviceSelectWidget


class MeasureTask(QRunnable):

    def __init__(self, fn, end, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.end = end
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)
        self.end()


class MeasureWidget(QWidget):

    selectedChanged = pyqtSignal(str)
    sampleFound = pyqtSignal()
    measureComplete = pyqtSignal()
    measureStarted = pyqtSignal()

    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)

        self._ui = uic.loadUi('measurewidget.ui', self)
        self._controller = controller
        self._threads = QThreadPool()

        self._devices = DeviceSelectWidget(parent=self, params=self._controller.deviceParams)
        self._ui.layParams.insertWidget(0, self._devices)
        self._devices.selectedChanged.connect(self.on_selectedChanged)

        self._selectedDevice = self._devices.selected

    def check(self):
        print('checking...')
        self._modeDuringCheck()
        self._threads.start(MeasureTask(self._controller.check,
                                        self.checkTaskComplete,
                                        self._selectedDevice))

    def checkTaskComplete(self):
        print('check complete')
        if not self._controller.present:
            print('sample not found')
            # QMessageBox.information(self, 'Ошибка', 'Не удалось найти образец, проверьте подключение')
            self._modePreCheck()
            return

        print('found sample')
        self._modePreMeasure()
        self.sampleFound.emit()

    def measure(self):
        print('measuring...')
        self._modeDuringMeasure()
        self._threads.start(MeasureTask(self._controller.measure,
                                        self.measureTaskComplete,
                                        self._selectedDevice))

    def measureTaskComplete(self):
        print('measure complete')
        # TODO check if measure completed successfully?
        if not self._controller.hasResult:
            print('error during measurement')
            return

        self._modePreCheck()
        self.measureComplete.emit()

    @pyqtSlot()
    def on_instrumentsConnected(self):
        self._modePreCheck()

    @pyqtSlot()
    def on_btnCheck_clicked(self):
        print('checking sample presence')
        self.check()

    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        print('start measure')
        self.measureStarted.emit()
        self.measure()

    @pyqtSlot(str)
    def on_selectedChanged(self, value):
        self._selectedDevice = value
        self.selectedChanged.emit(value)

    def _modePreConnect(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = True

    def _modePreCheck(self):
        self._ui.btnCheck.setEnabled(True)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = True

    def _modeDuringCheck(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = False

    def _modePreMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(True)
        self._devices.enabled = False

    def _modeDuringMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = False


class MeasureWidgetWithSecondaryParameters(MeasureWidget):
    secondaryChanged = pyqtSignal(dict)

    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent, controller=controller)

        self._params = 0

        self._spinPowIn = QDoubleSpinBox(parent=self)
        self._spinPowIn.setMinimum(-50)
        self._spinPowIn.setMaximum(50)
        self._spinPowIn.setSingleStep(1)
        self._spinPowIn.setValue(-21)
        self._spinPowIn.setSuffix(' дБм')
        self._spinPowIn.setEnabled(False)
        self._devices._layout.addRow('Pвх=', self._spinPowIn)

        self._spinFreqStart = QDoubleSpinBox(parent=self)
        self._spinFreqStart.setMinimum(0)
        self._spinFreqStart.setMaximum(20)
        self._spinFreqStart.setSingleStep(1)
        self._spinFreqStart.setValue(0.01)
        self._spinFreqStart.setSuffix(' ГГц')
        self._spinFreqStart.setEnabled(False)
        self._devices._layout.addRow('Fнач=', self._spinFreqStart)

        self._spinFreqEnd = QDoubleSpinBox(parent=self)
        self._spinFreqEnd.setMinimum(0)
        self._spinFreqEnd.setMaximum(20)
        self._spinFreqEnd.setSingleStep(1)
        self._spinFreqEnd.setValue(9)
        self._spinFreqEnd.setSuffix(' ГГц')
        self._spinFreqEnd.setEnabled(False)
        self._devices._layout.addRow('Fкон=', self._spinFreqEnd)

        self._connectSignals()

    def _connectSignals(self):
        self._spinPowIn.valueChanged.connect(self.on_params_changed)
        self._spinFreqStart.valueChanged.connect(self.on_params_changed)
        self._spinFreqEnd.valueChanged.connect(self.on_params_changed)

    def _modePreConnect(self):
        super()._modePreConnect()
        # self._spinFreq.setEnabled(True)

    def _modePreCheck(self):
        super()._modePreCheck()
        # self._spinFreq.setEnabled(True)

    def _modeDuringCheck(self):
        super()._modeDuringCheck()
        # self._spinFreq.setEnabled(False)

    def _modePreMeasure(self):
        super()._modePreMeasure()
        # self._spinFreq.setEnabled(False)

    def _modeDuringMeasure(self):
        super()._modeDuringMeasure()
        # self._spinFreq.setEnabled(False)

    def check(self):
        print('subclass checking...')
        self._modeDuringCheck()
        self._threads.start(MeasureTask(self._controller.check,
                                        self.checkTaskComplete,
                                        [self._selectedDevice, self._params]))

    def measure(self):
        print('subclass measuring...')
        self._modeDuringMeasure()
        self._threads.start(MeasureTask(self._controller.measure,
                                        self.measureTaskComplete,
                                        [self._selectedDevice, self._params]))

    def on_params_changed(self, value):
        params = {
            'Pin': self._spinPowIn.value(),
            'F1': self._spinFreqStart.value(),
            'F2': self._spinFreqEnd.value(),
        }
        self.secondaryChanged.emit(params)
