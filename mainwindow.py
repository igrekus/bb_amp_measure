from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QModelIndex

from formlayout.formlayout import fedit
from instrumentcontroller import InstrumentController
from connectionwidget import ConnectionWidget
from measuremodel import MeasureModel
from measurewidget import MeasureWidgetWithSecondaryParameters


class MainWindow(QMainWindow):

    instrumentsFound = pyqtSignal()
    sampleFound = pyqtSignal()
    measurementFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_QuitOnClose)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # create instance variables
        self._ui = uic.loadUi('mainwindow.ui', self)
        self._instrumentController = InstrumentController(parent=self)
        self._connectionWidget = ConnectionWidget(parent=self, controller=self._instrumentController)
        self._measureWidget = MeasureWidgetWithSecondaryParameters(parent=self, controller=self._instrumentController)
        self._measureModel = MeasureModel(parent=self, controller=self._instrumentController)

        # init UI
        self._ui.layInstrs.insertWidget(0, self._connectionWidget)
        self._ui.layInstrs.insertWidget(1, self._measureWidget)

        self._init()

    def _init(self):
        self._connectionWidget.connected.connect(self.on_instrumens_connected)
        self._connectionWidget.connected.connect(self._measureWidget.on_instrumentsConnected)

        self._measureWidget.secondaryChanged.connect(self._instrumentController.on_secondary_changed)

        self._measureWidget.measureStarted.connect(self.on_measureStarted)
        self._measureWidget.measureComplete.connect(self._measureModel.update)
        self._measureWidget.measureComplete.connect(self.on_measureComplete)

        self._ui.tableMeasure.setModel(self._measureModel)

        self.refreshView()

        self._measureWidget.on_params_changed(1)

    # UI utility methods
    def refreshView(self):
        self.resizeTable()

    def resizeTable(self):
        pass
        # self._ui.tableMeasure.resizeRowsToContents()
        # self._ui.tableMeasure.resizeColumnsToContents()

    # event handlers
    def resizeEvent(self, event):
        self.refreshView()

    @pyqtSlot()
    def on_instrumens_connected(self):
        print(f'connected {self._instrumentController}')

    @pyqtSlot()
    def on_measureComplete(self):
        print('meas complete')

    @pyqtSlot()
    def on_measureStarted(self):
        pass

    @pyqtSlot()
    def on_actParams_triggered(self):
        only_main_states = False
        data = [
            ('Корректировка', self._instrumentController.result.adjust),
            ('Калибровка', self._instrumentController.cal_set),
            ('Только основные', only_main_states),
            ('Набор для коррекции', [1, '+25', '+85', '-60']),
        ]

        values = fedit(data=data, title='Параметры')
        if not values:
            return

        adjust, cal_set, only_main_states, adjust_set = values

        self._instrumentController.result.adjust = adjust
        self._instrumentController.result.adjust_set = adjust_set
        self._instrumentController.cal_set = cal_set
