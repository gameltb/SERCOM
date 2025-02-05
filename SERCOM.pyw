from serial.tools.list_ports import comports
from serial import Serial
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore, QtGui, uic
import os
import sys
import configparser

import PyQt5.sip as sip
sip.setapi('QString', 2)

# from PyQt5. import QwtPlot, QwtPlotCurve


class SERCOM(QWidget):
    def __init__(self, parent=None):
        super(SERCOM, self).__init__(parent)

        uic.loadUi('SERCOM.ui', self)

        for port, desc, hwid in comports():
            self.cmbPort.addItem('%s (%s)' % (port, desc[:desc.index('(')]))

        self.ser = Serial()

        self.initSetting()

        self.buffer = ''  # 串口接收缓存

        self.tmrSer = QtCore.QTimer()
        self.tmrSer.setInterval(20)
        self.tmrSer.timeout.connect(self.on_tmrSer_timeout)
        self.tmrSer.start()

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w')

        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini')

        if not self.conf.has_section('serial'):
            self.conf.add_section('serial')
            self.conf.set('serial', 'port', 'COM0')
            self.conf.set('serial', 'baud', '9600')

            self.conf.add_section('history')
            self.conf.set('history', 'hist1', '')
            self.conf.set('history', 'hist2', '')

        self.txtSend.setPlainText(self.conf.get('history', 'hist1'))

        index = self.cmbPort.findText(self.conf.get('serial', 'port'))
        self.cmbPort.setCurrentIndex(index if index != -1 else 0)
        self.cmbBaud.setCurrentIndex(
            self.cmbBaud.findText(self.conf.get('serial', 'baud')))

    @QtCore.pyqtSlot()
    def on_btnOpen_clicked(self):
        if not self.ser.is_open:
            try:
                self.ser.timeout = 1
                self.ser.xonxoff = 0
                self.ser.port = self.cmbPort.currentText().split()[0]
                self.ser.parity = self.cmbChek.currentText()[0]
                self.ser.baudrate = int(self.cmbBaud.currentText())
                self.ser.bytesize = int(self.cmbData.currentText())
                self.ser.stopbits = int(self.cmbStop.currentText())
                self.ser.open()
            except Exception as e:
                print(e)
            else:
                self.cmbPort.setEnabled(False)
                self.btnOpen.setText('关闭串口')
        else:
            self.ser.close()

            self.cmbPort.setEnabled(True)
            self.btnOpen.setText('打开串口')

    @QtCore.pyqtSlot()
    def on_btnSend_clicked(self):
        if self.ser.is_open:
            text = self.txtSend.toPlainText()
            if self.chkHEXSend.isChecked():
                bytes = ' '.join([chr(int(x, 16)) for x in text.split()])
            else:
                bytes = text.replace('\n', '\r\n').encode('gbk')

            self.ser.write(bytes)

    def on_tmrSer_timeout(self):
        if self.ser.is_open:
            num = self.ser.in_waiting
            if num > 0:
                bytes = self.ser.read(num)

                if self.chkWavShow.checkState() == QtCore.Qt.Unchecked:
                    if self.chkHEXShow.isChecked():
                        text = ' '.join('%02X' % ord(c) for c in bytes) + ' '
                    else:
                        text = ''
                        self.buffer += bytes.decode("utf-8")
                        while len(self.buffer) > 1:
                            if ord(self.buffer[0]) < 0x7F:
                                text += self.buffer[0]
                                self.buffer = self.buffer[1:]
                            else:
                                try:
                                    hanzi = self.buffer[:2].decode('gbk')
                                except Exception as e:
                                    text += '\\x%02X' % ord(self.buffer[0])
                                    self.buffer = self.buffer[1:]
                                else:
                                    text += hanzi
                                    self.buffer = self.buffer[2:]

                        if len(self.buffer) > 0:
                            if ord(self.buffer[0]) < 0x7F:
                                text += self.buffer[0]
                                self.buffer = self.buffer[1:]

                    if len(self.txtMain.toPlainText()) > 25000:
                        self.txtMain.clear()
                    self.txtMain.moveCursor(QtGui.QTextCursor.End)
                    self.txtMain.insertPlainText(text)
                else:
                    self.PlotBuff += bytes
                    if self.PlotBuff.rfind(',') == -1:
                        return
                    try:
                        d = [
                            int(x) for x in self.PlotBuff[0:self.PlotBuff.rfind(',')].split(',')]
                        for x in d:
                            self.PlotData.pop(0)
                            self.PlotData.append(x)
                    except:
                        self.PlotBuff = ''
                    else:
                        self.PlotBuff = self.PlotBuff[self.PlotBuff.rfind(
                            ',')+1:]

                    self.PlotCurve.setData(
                        list(range(1, len(self.PlotData)+1)), self.PlotData)
                    self.qwtPlot.replot()

    @QtCore.pyqtSlot(int)
    def on_chkWavShow_stateChanged(self, state):
        return
        self.qwtPlot.setVisible(state == QtCore.Qt.Checked)
        self.txtMain.setVisible(state == QtCore.Qt.Unchecked)

    @QtCore.pyqtSlot(str)
    def on_cmbBaud_currentIndexChanged(self, text):
        self.ser.baudrate = int(text)

    @QtCore.pyqtSlot(str)
    def on_cmbData_currentIndexChanged(self, text):
        self.ser.bytesize = int(text)

    @QtCore.pyqtSlot(str)
    def on_cmbChek_currentIndexChanged(self, text):
        self.ser.parity = text[0]

    @QtCore.pyqtSlot(str)
    def on_cmbStop_currentIndexChanged(self, text):
        self.ser.stopbits = int(text)

    @QtCore.pyqtSlot()
    def on_btnClear_clicked(self):
        self.txtMain.clear()

    def closeEvent(self, evt):
        self.ser.close()

        self.conf.set('serial', 'port', self.cmbPort.currentText())
        self.conf.set('serial', 'baud', self.cmbBaud.currentText())
        self.conf.set('history', 'hist1', self.txtSend.toPlainText())
        self.conf.write(open('setting.ini', 'w'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ser = SERCOM()
    ser.show()
    app.exec_()
