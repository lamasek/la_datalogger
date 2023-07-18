#!python3

# 
# https://www.pythonguis.com/pyqt5-tutorial/

import importlib.util
import pip


def lib_check_install(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(package_name +" is not installed, trying to install...")
        pip.main(['install', package_name])

lib_check_install('pyserial')
import serial ### FIX it by: pip install pyserial
import serial.tools.list_ports ### FIX it by: pip install pyserial

lib_check_install('time')
import time

lib_check_install('datetime')
#import datetime
from datetime import datetime

lib_check_install('numpy')
import numpy as np ### FIX it by: pip install numpy

lib_check_install('sys')
import sys

lib_check_install
import base64


 
# https://www.pythonguis.com/pyqt5-tutorial/

lib_check_install('PyQt6')

from PyQt6 import QtWidgets ### FIX it by: pip install pyqt6
from PyQt6 import QtGui
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QWidget,
    QPlainTextEdit,
    QSlider,
    QScrollArea,
    QSpinBox,
)

lib_check_install('pyqtdarktheme')
import qdarktheme ### FIX it by: pip install pyqtdarktheme


lib_check_install('pyqtgraph')
import pyqtgraph as pg ### FIX it by: pip install pyqtgraph
from pyqtgraph import PlotWidget, plot
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph import AxisItem


import sys  # We need sys so that we can pass argv to QApplication
lib_check_install('os')
import os


# MS windows only - 'FIX' the apllication logo in the taskbar 
# sets grouping this script as unique app - not Pythonw.exe with python logo
# see https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
try:
    import ctypes
    myappid = u'LaMasek.laDatalogger' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except all:
    pass


verbose = 100
    
# if verbose >= VALUE: print() 
#        200 all parsed and not ignored data from serial 
#        250 all data from serial 



###### GLOBAL variables ####################################################


#src_map_graph = {
#    #TODO not yet'srcDev': 'e.g. COM5'
#    #'item_name': {
#    #   'graphID' = INT   # 0, ...   = ID of graph
#    #   'Ignore' = True/False
#}

data = { # all measured data
    #item_name : { #item is added when new
    #   data: (value1, value2, ...)
    #   time:   (time1, time2, ...)
    #   graphID: graphID
}

##################################################################


serial_logger_line_startwith = 'LOGGER/DATA '

class InputSerial: # all stuf related to COM/Serial port input

    
    def __init__(self):
        if verbose >= 200: print('InputSerial: __init__ started.')

        self.serials = {
            #'device': {
            #    'Serial': 'object serial.Serial()',
            #    'Ignore' : True, # if True, then ignore during reading data
            #    'Buffer' : '', #handle partial read lines
            #}
    }


    def serial_refresh(self):
        if verbose >= 200: print('Serial ports refresh.') 

        listSerialPorts = serial.tools.list_ports.comports()
        
        for p in listSerialPorts:
            if p.device not in self.serials: #new port found
                print('New serial port found: ' + str(p.device) + '   VID: ' + str(p.vid) + ',  PID: ' + str(p.pid))
                foundport = None
                if 0x2E8A == p.vid and 0x0005 == p.pid:
                    print(" USB serial with VID:PID of RPI PICO/MicroPython found at "+p.device)
                    foundport = p.device
                    speed = 9600
                elif 9114 == p.vid and 33012 == p.pid:
                    print(" USB serial with VID:PID of RPI PICO/CircuitPython found at "+p.device)
                    foundport = p.device
                    speed = 115200
                elif 9114 == p.vid and 33016 == p.pid:
                    print(" USB serial with VID:PID of Adafruit QT PI (RP2040) with CircuitPython found at "+p.device)
                    foundport = p.device
                    speed = 115200
                else:
                    print(' Unknown serial port - Ignoring.')
                    self.serials[p.device] = {'Ignore':  True}

                if foundport is not None:
                    print (" Trying to open serial port "+ foundport)
                    try:
                        ser = serial.Serial(foundport, speed)

                    except Exception as E:
                        print(' Exception: ' + str(E))
                        continue
                    print('   Done.')
                    self.serials[p.device] =  {'Ignore':  False}
                    self.serials[p.device]['Serial'] =  ser
                    self.serials[p.device]['Buffer'] =  ''


    def list_serials(self):
        return(self.serials)


    def readData(self):
        #global data
        # read data from serials - 1 reading per each known port, next in next calling function
        # polling this function has to be more often then USB LOgger produces - typically 1 second, otherwise buffers are still more full
        # nonblocking function

        if verbose >= 299: print('InputSerial: readData()')

        dataUpdated = False
        dataRowsUpdated = False
        for portname in self.serials.copy(): #we need to delete keys - so we have to make copy for iterating
            curPort = self.serials[portname]
            if curPort['Ignore'] == True:
                continue
            ser = curPort['Serial']

            try:
                if (ser.inWaiting() > 0):
                        readed = ser.read(ser.inWaiting()).decode('ascii') 
                        curPort['Buffer'] += readed
                        if verbose >= 240: print('InputSerial: Readed RAW string"' + readed + '"')

                else:
                    if curPort['Buffer'] == '': continue #nothing to process
            except: #problem during reading - broken serial? --> remove serial port
                del self.serials[portname] #TODO zkontrolovat jestli to pujde i objektove
                continue
            
            if verbose >= 500: print('InputSerial: whole string buffer: "' + curPort['Buffer'] + '"')
            if '\n' not in curPort['Buffer']:
                continue
            nextLine, curPort['Buffer'] = curPort['Buffer'].split('\n', 1)

            readed = nextLine.strip()
            if verbose >= 290: print('InputSerial: nextLine: "' + readed + '"')

            if readed.startswith(serial_logger_line_startwith): # "LOGGER/DATA "
                sreaded = readed[len(serial_logger_line_startwith):]
                if verbose >= 220: print('InputSerial: sreaded:' + sreaded)
                junks = sreaded.split(' ', 1)
                item = junks[0].strip()
                try:
                    value = float(junks[1].strip())
                except Exception as E:
                    print('InputSerial: Exception: ' + str(E) + '; Broken serial data: "' + readed + '"')
                    continue
                if verbose >= 210: print('InputSerial: data parsed: item="' + str(item) + '", value="' + str(value) + '"')

                if item not in data:
                    if verbose >= 200: print('InputSerial: New item found: item="' + str(item) + '"')
                    data[item] = {
                        'data': [],
                        'time': [],
                        'graphID': None,
                    }
                    dataRowsUpdated = True
                data[item]['data'].append(value)
                data[item]['time'].append(time.time())
                dataUpdated = True
        return(dataUpdated, dataRowsUpdated)


class tab_datasources(QWidget):
    def __init__(self, inputSerial):
        super().__init__()

        self.layout = QVBoxLayout()


        label_serials = QLabel("Serial Interfaces:")
        self.layout.addWidget(label_serials)
        #label1.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        #label1.setText("Serial Interfaces:")
        #label1.setAlignment(Qt.AlignBottom | Qt.AlignRight)

        plainText1 = QPlainTextEdit()
        #plainText1.setPlaceholderText("Serial Interfaces:" + '\r\n')

        self.serials = inputSerial
        #print(InputSerial)
        ser = self.serials.list_serials()
        for portname in ser: #we need to delete keys - so we have to make copy for iterating
            curPort = ser[portname]
            plainText1.appendPlainText(portname + ' ' + str(curPort) + '\n')

        plainText1.setReadOnly(True)
        self.layout.addWidget(plainText1)

        label_ignore_items = QLabel("Ignore items:")
        label_ignore_items.setToolTip('List of ignored items (e.g."C LUX Vshut"). It is applied only during reading data from serials. Case sensitive. Delimiter is space.')
        self.layout.addWidget(label_ignore_items)

        self.ignore_items = QLineEdit('')
        self.ignore_items.setPlaceholderText('List of ignored items (e.g."C LUX Vshut").')
        #self.dataAggregate.setInputMask('NNNN') #when used is cripled editing
        #self.dataAggregate.maxLength = 4

        self.layout.addWidget(self.ignore_items)


        dataAggregate_tooltip='Aggregation of input data points. 10 means from every 10 readed data is made average and put as 1 data into graph. It influence only incoming data - not already stored and showed data.'

        dataAggregate_label = QLabel("Data aggregation:")
        dataAggregate_label.setToolTip(dataAggregate_tooltip)
        self.layout.addWidget(dataAggregate_label)


        self.dataAggregate = QSpinBox(self)
        self.dataAggregate.setMinimum(1)
        self.dataAggregate.setMaximum(9999)
        #self.spin.setGeometry(100, 100, 100, 40)
        #self.dataAggregate.setDisplayIntegerBase(1)
        self.dataAggregate.setToolTip(dataAggregate_tooltip)
        self.dataAggregate.valueChanged.connect(self.dataAggregate_valueChanged)
        self.layout.addWidget(self.dataAggregate)


        #label2 = QLabel("Source to Graph:")
        #self.layout.addWidget(label2)
        ##label1.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        ##label1.setText("Serial Interfaces:")
        ##label1.setAlignment(Qt.AlignBottom | Qt.AlignRight)

        #plainText2 = QPlainTextEdit()
        #plainText2.setPlaceholderText('')

        ##self.serials = inputSerial
        ##print(InputSerial)
        ##for portname in ser: #we need to delete keys - so we have to make copy for iterating
        ##    curPort = ser[portname]
        ##    plainText1.appendPlainText(portname + ' ' + str(curPort) + '\n')

        #plainText2.setReadOnly(True)
        #self.layout.addWidget(plainText2)

        self.setLayout(self.layout)
        
        self.show() # show all the widgets

    def dataAggregate_valueChanged(self):
        print(self.dataAggregate.value())


class tab_graphs(QWidget):
    def __init__(self):
        super().__init__()


        #stuff for all graphs:
        self.penColor = color=(205, 205, 205)
        self.pen = pg.mkPen(self.penColor, width=1)

        self.layout = QVBoxLayout() # do Vertical layoutu davam jeden graf za druhym
        self.setLayout(self.layout)

        self.cursor = Qt.CursorShape.CrossCursor


        self.show() # show all the widgets


        ##onclick event
        #self.data_line.scene().sigMouseClicked.connect(self.onClick)


    def add_graph(self, item_name):

        #https://www.pythonguis.com/tutorials/plotting-pyqtgraph/
        data[item_name]['date_axis'] = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation='bottom')
        data[item_name]['graphWidget'] = pg.PlotWidget(axisItems = {'bottom': data[item_name]['date_axis']})
        data[item_name]['graphWidget'].setMinimumSize(300, 200)

        #self.graphWidget.setMouseTracking(True)

        #self.graphWidget.setBackground(QtGui.QColor('DarkGrey'))

        #labelFont = QtGui.QFont()
        #labelFont.setPointSize(34)
        #self.graphWidget.getAxis('left').tickFont = labelFont

        data[item_name]['graphWidget'].showGrid(x=True, y=True)

        # Set the cursor for the plotwidget. The mouse cursor will change when over the plot.
        data[item_name]['graphWidget'].setCursor(self.cursor)

        data[item_name]['graphWidget'].setLabel('left', item_name)

        # plot empty data: x, y values
        data[item_name]['data_line'] =  data[item_name]['graphWidget'].plot((), (), pen=self.pen)

        self.layout.addWidget(data[item_name]['graphWidget'])


    def update_graphs(self):
        
        for item_name in data.keys():
            #key = list(data.keys())[0]
            if data[item_name]['graphID'] == None:
                data[item_name]['graphID'] = 0
                self.add_graph(item_name)
            
            # https://www.geeksforgeeks.org/pyqtgraph-symbols/
            data[item_name]['data_line'].setData(data[item_name]['time'], data[item_name]['data'], symbol ='o', symbolSize = 5, symbolBrush =(0, 114, 189))  # Update the data.
            #self.date_axis.setData()

            #
            if False: # LaAutorange - 0 is always visible on Y plus show min/max                
                timeMin = min(data[item_name]['time'])
                timeMax = max(data[item_name]['time'])
                if timeMax - timeMin < 10:
                    timeMax += 10 - (timeMax - timeMin)
                elif timeMax - timeMin <20:
                    timeMax += 20 - (timeMax - timeMin)

                data[item_name]['graphWidget'].setXRange(timeMin, timeMax)

                dataMin = 0
                dataMin = min(data[item_name]['data'])
                if dataMin > 0:
                    dataMin = 0
                dataMax = 0
                dataMax = max(data[item_name]['data'])
                if dataMax < 0:
                    dataMax = 0
                if dataMin == dataMax:
                    dataMax = -1
                    dataMax = 1
                data[item_name]['graphWidget'].setYRange(dataMin, dataMax)


    def onClick(self, event):
        #items = p1.scene().items(event.scenePos())

        if verbose > 200:
            print('onClick: clicked plot 0x{:x}, event: {}'.format(id(self), event))

        vb = self.vb

        mousePoint = vb.mapSceneToView(event._scenePos)
        print('Mouse clicked at _scenePos() X Y: ' + str(mousePoint.x()) + ' ' + str(mousePoint.y()))
        if self.data_line.sceneBoundingRect().contains(event._scenePos):
            mousePoint = vb.mapSceneToView(event._scenePos)
            index = int(round(mousePoint.x()))
            if index > 0 and index < len(data1):
                print('   corresponding Y data in graph: ' + str(data1[index]))


class tab_exports(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel('There will be extra export,\n now you can use use only pygraph default export ---  In Graph, Mouse Right click, --> Exports...', self)
  
        # show all the widgets
        self.show()


class tab_settings(QWidget):
    def __init__(self):
        super().__init__()

  
        self.layout = QFormLayout()

        #self.dataAggregate = QLineEdit('1')
        #self.dataAggregate.setInputMask('NNNN') #when used is cripled editing
        #self.dataAggregate.maxLength = 4
        #self.onlyInt = QIntValidator()
        #self.onlyInt.setRange(0, 9999)

        #moved to datasources
        dataAggregate_tooltip='Aggregation of input data points. 10 means from every 10 readed data is made average and put as 1 data into graph. It influence only incoming data - not already stored and showed.'
        dataAggregate_label = QLabel("Data aggregation:")
        dataAggregate_label.setToolTip(dataAggregate_tooltip)
        self.dataAggregate = QSpinBox(self)
        self.dataAggregate.setMinimum(1)
        self.dataAggregate.setMaximum(9999)
        #self.spin.setGeometry(100, 100, 100, 40)
        #self.dataAggregate.setDisplayIntegerBase(1)
        self.dataAggregate.setToolTip(dataAggregate_tooltip)
        self.dataAggregate.valueChanged.connect(self.dataAggregate_valueChanged)


        self.layout.addRow(dataAggregate_label, self.dataAggregate)

        self.setLayout(self.layout)

        self.show() # show all the widgets

    def dataAggregate_valueChanged(self):
        print(self.dataAggregate.value())


class tab_help(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        #self.label = QLabel('xxx')
        #self.layout.addWidget(self.label)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)

        self.text.appendPlainText("""
LaDatalogger

Author:
    Josef la Masek masek2050@gmail.com

Basic description:
Each probe (LUXmeter, thermometer, ..) sends periodically measurings as serial output over USB.
This app collects the data over all serials and show them as graphs.

It data from well known USB serial adapters (PID and VID of Raspberry PI Pico with micropython or circuitpython).
Data is timestamped after reading from serial (so there is small time shift from real measuring) and showed in graphs.
Usual period is 1 second, but can be adjusted on probe.

Graph controls:
    Mouse control (mouse pointer have to be on graph):
        Right click --- Menu
        Left Button AND Drag ---  Move
        Right Button AND Drag --- Resize
        Wheeel --- Resize Y

    Howto:
        Restart auto fit after manual change --- Click to A in left down corner of the graph

Misc:
UI with graphs begans to be nonresponsive since 100 000 data points. So consider to use Data Aggregation.
""")

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)
        self.show() # show all the widgets

#https://www.base64encode.org/
logo_png_base64Encoded = '''
PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+Cjwh
LS0gQ3JlYXRlZCB3aXRoIElua3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoK
PHN2ZwogICB3aWR0aD0iNTEyIgogICBoZWlnaHQ9IjUxMiIKICAgdmlld0JveD0iMCAwIDUxMiA1
MTIiCiAgIHZlcnNpb249IjEuMSIKICAgaWQ9InN2ZzUiCiAgIGlua3NjYXBlOnZlcnNpb249IjEu
MiAoZGMyYWVkYWYwMywgMjAyMi0wNS0xNSkiCiAgIHNvZGlwb2RpOmRvY25hbWU9IkFQUGxvZ28u
c3ZnIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNl
cy9pbmtzY2FwZSIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3Jn
ZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAw
MC9zdmciCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxzb2Rp
cG9kaTpuYW1lZHZpZXcKICAgICBpZD0ibmFtZWR2aWV3NyIKICAgICBwYWdlY29sb3I9IiM1MDUw
NTAiCiAgICAgYm9yZGVyY29sb3I9IiNlZWVlZWUiCiAgICAgYm9yZGVyb3BhY2l0eT0iMSIKICAg
ICBpbmtzY2FwZTpzaG93cGFnZXNoYWRvdz0iMCIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0i
MCIKICAgICBpbmtzY2FwZTpwYWdlY2hlY2tlcmJvYXJkPSIwIgogICAgIGlua3NjYXBlOmRlc2tj
b2xvcj0iIzUwNTA1MCIKICAgICBpbmtzY2FwZTpkb2N1bWVudC11bml0cz0icHgiCiAgICAgc2hv
d2dyaWQ9ImZhbHNlIgogICAgIGlua3NjYXBlOnpvb209IjEuNDE4MzU2OCIKICAgICBpbmtzY2Fw
ZTpjeD0iMTYuMjE1OTQ4IgogICAgIGlua3NjYXBlOmN5PSIyMTMuNjI3NDkiCiAgICAgaW5rc2Nh
cGU6d2luZG93LXdpZHRoPSIyNTYwIgogICAgIGlua3NjYXBlOndpbmRvdy1oZWlnaHQ9IjE0MDYi
CiAgICAgaW5rc2NhcGU6d2luZG93LXg9Ii0xMSIKICAgICBpbmtzY2FwZTp3aW5kb3cteT0iLTEx
IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVu
dC1sYXllcj0ibGF5ZXIxIiAvPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMyIj4KICAgIDxtYXJrZXIK
ICAgICAgIHN0eWxlPSJvdmVyZmxvdzp2aXNpYmxlIgogICAgICAgaWQ9IkRvdCIKICAgICAgIHJl
Zlg9IjAiCiAgICAgICByZWZZPSIwIgogICAgICAgb3JpZW50PSJhdXRvIgogICAgICAgaW5rc2Nh
cGU6c3RvY2tpZD0iRG90IgogICAgICAgbWFya2VyV2lkdGg9IjMyIgogICAgICAgbWFya2VySGVp
Z2h0PSIzMiIKICAgICAgIHZpZXdCb3g9IjAgMCA1LjY2NjY2NjcgNS42NjY2NjY3IgogICAgICAg
aW5rc2NhcGU6aXNzdG9jaz0idHJ1ZSIKICAgICAgIGlua3NjYXBlOmNvbGxlY3Q9ImFsd2F5cyIK
ICAgICAgIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIgogICAgICAgbWFya2VyVW5pdHM9
InVzZXJTcGFjZU9uVXNlIj4KICAgICAgPHBhdGgKICAgICAgICAgdHJhbnNmb3JtPSJzY2FsZSgw
LjUpIgogICAgICAgICBzdHlsZT0iZmlsbDpjb250ZXh0LXN0cm9rZTtmaWxsLXJ1bGU6ZXZlbm9k
ZDtzdHJva2U6Y29udGV4dC1zdHJva2U7c3Ryb2tlLXdpZHRoOjFwdCIKICAgICAgICAgZD0iTSA1
LDAgQyA1LDIuNzYgMi43Niw1IDAsNSAtMi43Niw1IC01LDIuNzYgLTUsMCBjIDAsLTIuNzYgMi4z
LC01IDUsLTUgMi43NiwwIDUsMi4yNCA1LDUgeiIKICAgICAgICAgaWQ9IkRvdDEiCiAgICAgICAg
IHNvZGlwb2RpOm5vZGV0eXBlcz0ic3Nzc3MiIC8+CiAgICA8L21hcmtlcj4KICAgIDxtYXJrZXIK
ICAgICAgIHN0eWxlPSJvdmVyZmxvdzp2aXNpYmxlIgogICAgICAgaWQ9Im1hcmtlcjE0MjY0Igog
ICAgICAgcmVmWD0iMCIKICAgICAgIHJlZlk9IjAiCiAgICAgICBvcmllbnQ9ImF1dG8iCiAgICAg
ICBpbmtzY2FwZTpzdG9ja2lkPSJEb3QiCiAgICAgICBtYXJrZXJXaWR0aD0iMzIiCiAgICAgICBt
YXJrZXJIZWlnaHQ9IjMyIgogICAgICAgdmlld0JveD0iMCAwIDUuNjY2NjY2NyA1LjY2NjY2Njci
CiAgICAgICBpbmtzY2FwZTppc3N0b2NrPSJ0cnVlIgogICAgICAgaW5rc2NhcGU6Y29sbGVjdD0i
YWx3YXlzIgogICAgICAgcHJlc2VydmVBc3BlY3RSYXRpbz0ieE1pZFlNaWQiCiAgICAgICBtYXJr
ZXJVbml0cz0idXNlclNwYWNlT25Vc2UiPgogICAgICA8cGF0aAogICAgICAgICB0cmFuc2Zvcm09
InNjYWxlKDAuNSkiCiAgICAgICAgIHN0eWxlPSJmaWxsOmNvbnRleHQtc3Ryb2tlO2ZpbGwtcnVs
ZTpldmVub2RkO3N0cm9rZTpjb250ZXh0LXN0cm9rZTtzdHJva2Utd2lkdGg6MXB0IgogICAgICAg
ICBkPSJNIDUsMCBDIDUsMi43NiAyLjc2LDUgMCw1IC0yLjc2LDUgLTUsMi43NiAtNSwwIGMgMCwt
Mi43NiAyLjMsLTUgNSwtNSAyLjc2LDAgNSwyLjI0IDUsNSB6IgogICAgICAgICBpZD0icGF0aDE0
MjYyIgogICAgICAgICBzb2RpcG9kaTpub2RldHlwZXM9InNzc3NzIiAvPgogICAgPC9tYXJrZXI+
CiAgICA8aW5rc2NhcGU6cGF0aC1lZmZlY3QKICAgICAgIGVmZmVjdD0icG93ZXJzdHJva2UiCiAg
ICAgICBpZD0icGF0aC1lZmZlY3Q2MzIiCiAgICAgICBpc192aXNpYmxlPSJ0cnVlIgogICAgICAg
bHBldmVyc2lvbj0iMSIKICAgICAgIG9mZnNldF9wb2ludHM9IjQsMTguODY3OTI1IgogICAgICAg
bm90X2p1bXA9ImZhbHNlIgogICAgICAgc29ydF9wb2ludHM9InRydWUiCiAgICAgICBpbnRlcnBv
bGF0b3JfdHlwZT0iQ3ViaWNCZXppZXJKb2hhbiIKICAgICAgIGludGVycG9sYXRvcl9iZXRhPSIw
LjIiCiAgICAgICBzdGFydF9saW5lY2FwX3R5cGU9Inplcm93aWR0aCIKICAgICAgIGxpbmVqb2lu
X3R5cGU9ImV4dHJwX2FyYyIKICAgICAgIG1pdGVyX2xpbWl0PSI0IgogICAgICAgc2NhbGVfd2lk
dGg9IjEiCiAgICAgICBlbmRfbGluZWNhcF90eXBlPSJ6ZXJvd2lkdGgiIC8+CiAgICA8aW5rc2Nh
cGU6cGF0aC1lZmZlY3QKICAgICAgIGVmZmVjdD0ic2tlbGV0YWwiCiAgICAgICBpZD0icGF0aC1l
ZmZlY3Q2MjgiCiAgICAgICBpc192aXNpYmxlPSJ0cnVlIgogICAgICAgbHBldmVyc2lvbj0iMSIK
ICAgICAgIHBhdHRlcm49Ik0gMCwxOC44Njc5MjUgQyAwLDguNDUyODMwMiA4LjQ1MjgzMDIsMCAx
OC44Njc5MjUsMCBjIDEwLjQxNTA5NCwwIDE4Ljg2NzkyNCw4LjQ1MjgzMDIgMTguODY3OTI0LDE4
Ljg2NzkyNSAwLDEwLjQxNTA5NCAtOC40NTI4MywxOC44Njc5MjQgLTE4Ljg2NzkyNCwxOC44Njc5
MjQgQyA4LjQ1MjgzMDIsMzcuNzM1ODQ5IDAsMjkuMjgzMDE5IDAsMTguODY3OTI1IFoiCiAgICAg
ICBjb3B5dHlwZT0ic2luZ2xlX3N0cmV0Y2hlZCIKICAgICAgIHByb3Bfc2NhbGU9IjEiCiAgICAg
ICBzY2FsZV95X3JlbD0iZmFsc2UiCiAgICAgICBzcGFjaW5nPSIwIgogICAgICAgbm9ybWFsX29m
ZnNldD0iMCIKICAgICAgIHRhbmdfb2Zmc2V0PSIwIgogICAgICAgcHJvcF91bml0cz0iZmFsc2Ui
CiAgICAgICB2ZXJ0aWNhbF9wYXR0ZXJuPSJmYWxzZSIKICAgICAgIGhpZGVfa25vdD0iZmFsc2Ui
CiAgICAgICBmdXNlX3RvbGVyYW5jZT0iMCIgLz4KICAgIDxpbmtzY2FwZTpwYXRoLWVmZmVjdAog
ICAgICAgZWZmZWN0PSJwb3dlcnN0cm9rZSIKICAgICAgIGlkPSJwYXRoLWVmZmVjdDYyMCIKICAg
ICAgIGlzX3Zpc2libGU9InRydWUiCiAgICAgICBscGV2ZXJzaW9uPSIxIgogICAgICAgb2Zmc2V0
X3BvaW50cz0iMCwxOC44Njc5MjUiCiAgICAgICBub3RfanVtcD0iZmFsc2UiCiAgICAgICBzb3J0
X3BvaW50cz0idHJ1ZSIKICAgICAgIGludGVycG9sYXRvcl90eXBlPSJDdWJpY0JlemllckpvaGFu
IgogICAgICAgaW50ZXJwb2xhdG9yX2JldGE9IjAuMiIKICAgICAgIHN0YXJ0X2xpbmVjYXBfdHlw
ZT0iemVyb3dpZHRoIgogICAgICAgbGluZWpvaW5fdHlwZT0iZXh0cnBfYXJjIgogICAgICAgbWl0
ZXJfbGltaXQ9IjQiCiAgICAgICBzY2FsZV93aWR0aD0iMSIKICAgICAgIGVuZF9saW5lY2FwX3R5
cGU9Inplcm93aWR0aCIgLz4KICAgIDxpbmtzY2FwZTpwYXRoLWVmZmVjdAogICAgICAgZWZmZWN0
PSJmaWxsX2JldHdlZW5fbWFueSIKICAgICAgIG1ldGhvZD0iYnNwbGluZXNwaXJvIgogICAgICAg
bGlua2VkcGF0aHM9IiNwYXRoNjE4LDAsMSIKICAgICAgIGlkPSJwYXRoLWVmZmVjdDYyMiIgLz4K
ICAgIDxpbmtzY2FwZTpwYXRoLWVmZmVjdAogICAgICAgZWZmZWN0PSJmaWxsX2JldHdlZW5fbWFu
eSIKICAgICAgIG1ldGhvZD0iYnNwbGluZXNwaXJvIgogICAgICAgbGlua2VkcGF0aHM9IiNwYXRo
NjMwLDAsMSIKICAgICAgIGlkPSJwYXRoLWVmZmVjdDYzNCIgLz4KICAgIDxpbmtzY2FwZTpwYXRo
LWVmZmVjdAogICAgICAgZWZmZWN0PSJmaWxsX2JldHdlZW5fbWFueSIKICAgICAgIG1ldGhvZD0i
b3JpZ2luYWxkIgogICAgICAgbGlua2VkcGF0aHM9IiNwYXRoMjc1NDAtMiwwLDF8IgogICAgICAg
aWQ9InBhdGgtZWZmZWN0MjkxMjgiIC8+CiAgPC9kZWZzPgogIDxnCiAgICAgaW5rc2NhcGU6bGFi
ZWw9IlZyc3R2YSAxIgogICAgIGlua3NjYXBlOmdyb3VwbW9kZT0ibGF5ZXIiCiAgICAgaWQ9Imxh
eWVyMSI+CiAgICA8cmVjdAogICAgICAgc3R5bGU9ImZpbGw6IzAwMDAwMDtmaWxsLW9wYWNpdHk6
MTtzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MTg7c3Ryb2tlLWxpbmVjYXA6cm91bmQ7c3Ry
b2tlLWxpbmVqb2luOmJldmVsO3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpu
b25lO3N0cm9rZS1kYXNob2Zmc2V0OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAgICAgIGlkPSJyZWN0
MTA1MTYiCiAgICAgICB3aWR0aD0iNTAyLjY5NDQiCiAgICAgICBoZWlnaHQ9IjUwMS4yODQzIgog
ICAgICAgeD0iMCIKICAgICAgIHk9IjAuNzA1MDQxMjMiIC8+CiAgICA8cGF0aAogICAgICAgc3R5
bGU9Im1peC1ibGVuZC1tb2RlOm5vcm1hbDtmaWxsOm5vbmU7ZmlsbC1vcGFjaXR5OjE7c3Ryb2tl
OiNmZmZmZmY7c3Ryb2tlLXdpZHRoOjE4O3N0cm9rZS1saW5lY2FwOnJvdW5kO3N0cm9rZS1saW5l
am9pbjpiZXZlbDtzdHJva2UtbWl0ZXJsaW1pdDo0O3N0cm9rZS1kYXNoYXJyYXk6bm9uZTtzdHJv
a2UtZGFzaG9mZnNldDowO3N0cm9rZS1vcGFjaXR5OjE7bWFya2VyLXN0YXJ0OnVybCgjRG90KTtt
YXJrZXItbWlkOnVybCgjbWFya2VyMTQyNjQpO21hcmtlci1lbmQ6dXJsKCNtYXJrZXIxNDI2NCki
CiAgICAgICBkPSJNIDQ2My45MTcxMywyMTIuOTIyNDYgMzUzLjkzMDcxLDE5Mi40NzYyNiAzMTMu
MDM4MywxMDkuOTg2NDQgMjE5Ljk3Mjg2LDYyLjA0MzYyOSAxMzUuMzY3OTEsMjMwLjU0ODQ4IDg5
LjU0MDIzNiw0MTcuMzg0NDEiCiAgICAgICBpZD0icGF0aDE1MTgiCiAgICAgICBzb2RpcG9kaTpu
b2RldHlwZXM9ImNjY2NjYyIgLz4KICAgIDxwYXRoCiAgICAgICBzdHlsZT0iZmlsbDpub25lO2Zp
bGwtb3BhY2l0eToxO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxOC41O3N0cm9rZS1saW5l
Y2FwOmJ1dHQ7c3Ryb2tlLWxpbmVqb2luOmJldmVsO3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tl
LWRhc2hhcnJheTpub25lO3N0cm9rZS1kYXNob2Zmc2V0OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAg
ICAgIGQ9Im0gNDIuMzAyNDczLDM2LjY2MjE0NCAxMGUtNyw0MzYuNDIwNTI2IDQ1MS4yMjYzODYs
LTAuNzA1MDUiCiAgICAgICBpZD0icGF0aDk5NDYiCiAgICAgICBzb2RpcG9kaTpub2RldHlwZXM9
ImNjYyIgLz4KICAgIDxwYXRoCiAgICAgICBpbmtzY2FwZTpvcmlnaW5hbC1kPSJNIDAsMCIKICAg
ICAgIGlua3NjYXBlOnBhdGgtZWZmZWN0PSIjcGF0aC1lZmZlY3QyOTEyOCIKICAgICAgIGQ9Ik0g
MTAzLjA0NzU3LDQxNC45MTY3OSBBIDExLjAzOTY3MSwxMS4wMzk2NzEgMCAwIDEgOTIuMDA3OSw0
MjUuOTU2NDcgMTEuMDM5NjcxLDExLjAzOTY3MSAwIDAgMSA4MC45NjgyMjksNDE0LjkxNjc5IDEx
LjAzOTY3MSwxMS4wMzk2NzEgMCAwIDEgOTIuMDA3OSw0MDMuODc3MTIgYSAxMS4wMzk2NzEsMTEu
MDM5NjcxIDAgMCAxIDExLjAzOTY3LDExLjAzOTY3IHoiCiAgICAgICBpZD0icGF0aDI5MTMwIgog
ICAgICAgY2xhc3M9IlVub3B0aW1pY2VkVHJhbnNmb3JtcyIgLz4KICAgIDxjaXJjbGUKICAgICAg
IHN0eWxlPSJmaWxsOiM4MGIzZmY7ZmlsbC1vcGFjaXR5OjE7c3Ryb2tlOiM4MGIzZmY7c3Ryb2tl
LXdpZHRoOjE4O3N0cm9rZS1saW5lY2FwOnJvdW5kO3N0cm9rZS1saW5lam9pbjpiZXZlbDtzdHJv
a2UtbWl0ZXJsaW1pdDo0O3N0cm9rZS1kYXNoYXJyYXk6bm9uZTtzdHJva2UtZGFzaG9mZnNldDow
O3N0cm9rZS1vcGFjaXR5OjEiCiAgICAgICBpZD0icGF0aDI3NTQwLTIiCiAgICAgICBjeD0iOTAu
MjQ1MjkzIgogICAgICAgY3k9IjQxNi42NzkzOCIKICAgICAgIHI9IjguNDc1MTcwMSIKICAgICAg
IGNsYXNzPSJVbm9wdGltaWNlZFRyYW5zZm9ybXMiCiAgICAgICB0cmFuc2Zvcm09Im1hdHJpeCgx
LjMwMjU4OTksMCwwLDEuMzAyNTg5OSwtMjUuNTQ0NzA3LC0xMjcuODQ1NTYpIiAvPgogICAgPGNp
cmNsZQogICAgICAgc3R5bGU9ImZpbGw6IzgwYjNmZjtmaWxsLW9wYWNpdHk6MTtzdHJva2U6Izgw
YjNmZjtzdHJva2Utd2lkdGg6MTg7c3Ryb2tlLWxpbmVjYXA6cm91bmQ7c3Ryb2tlLWxpbmVqb2lu
OmJldmVsO3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpub25lO3N0cm9rZS1k
YXNob2Zmc2V0OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAgICAgIGlkPSJwYXRoMjc1NDAtMi0yIgog
ICAgICAgY3g9IjkwLjI0NTI5MyIKICAgICAgIGN5PSI0MTYuNjc5MzgiCiAgICAgICByPSI4LjQ3
NTE3MDEiCiAgICAgICBjbGFzcz0iVW5vcHRpbWljZWRUcmFuc2Zvcm1zIgogICAgICAgdHJhbnNm
b3JtPSJtYXRyaXgoMS4zMDI1ODk5LDAsMCwxLjMwMjU4OTksMTcuODE1MzA5LC0zMTIuOTE4OTIp
IiAvPgogICAgPGNpcmNsZQogICAgICAgc3R5bGU9ImZpbGw6IzgwYjNmZjtmaWxsLW9wYWNpdHk6
MTtzdHJva2U6IzgwYjNmZjtzdHJva2Utd2lkdGg6MTg7c3Ryb2tlLWxpbmVjYXA6cm91bmQ7c3Ry
b2tlLWxpbmVqb2luOmJldmVsO3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpu
b25lO3N0cm9rZS1kYXNob2Zmc2V0OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAgICAgIGlkPSJwYXRo
Mjc1NDAtMi04IgogICAgICAgY3g9IjkwLjI0NTI5MyIKICAgICAgIGN5PSI0MTYuNjc5MzgiCiAg
ICAgICByPSI4LjQ3NTE3MDEiCiAgICAgICBjbGFzcz0iVW5vcHRpbWljZWRUcmFuc2Zvcm1zIgog
ICAgICAgdHJhbnNmb3JtPSJtYXRyaXgoMS4zMDI1ODk5LDAsMCwxLjMwMjU4OTksMTAzLjgzMDM0
LC00NzkuMzA4NjQpIiAvPgogICAgPGNpcmNsZQogICAgICAgc3R5bGU9ImZpbGw6IzgwYjNmZjtm
aWxsLW9wYWNpdHk6MTtzdHJva2U6IzgwYjNmZjtzdHJva2Utd2lkdGg6MTg7c3Ryb2tlLWxpbmVj
YXA6cm91bmQ7c3Ryb2tlLWxpbmVqb2luOmJldmVsO3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tl
LWRhc2hhcnJheTpub25lO3N0cm9rZS1kYXNob2Zmc2V0OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAg
ICAgIGlkPSJwYXRoMjc1NDAtMi01IgogICAgICAgY3g9IjkwLjI0NTI5MyIKICAgICAgIGN5PSI0
MTYuNjc5MzgiCiAgICAgICByPSI4LjQ3NTE3MDEiCiAgICAgICBjbGFzcz0iVW5vcHRpbWljZWRU
cmFuc2Zvcm1zIgogICAgICAgdHJhbnNmb3JtPSJtYXRyaXgoMS4zMDI1ODk5LDAsMCwxLjMwMjU4
OTksMTk2Ljg5NTc4LC00MzIuNzc1OTIpIiAvPgogICAgPGNpcmNsZQogICAgICAgc3R5bGU9ImZp
bGw6IzgwYjNmZjtmaWxsLW9wYWNpdHk6MTtzdHJva2U6IzgwYjNmZjtzdHJva2Utd2lkdGg6MTg7
c3Ryb2tlLWxpbmVjYXA6cm91bmQ7c3Ryb2tlLWxpbmVqb2luOmJldmVsO3N0cm9rZS1taXRlcmxp
bWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpub25lO3N0cm9rZS1kYXNob2Zmc2V0OjA7c3Ryb2tlLW9w
YWNpdHk6MSIKICAgICAgIGlkPSJwYXRoMjc1NDAtMi0xIgogICAgICAgY3g9IjkwLjI0NTI5MyIK
ICAgICAgIGN5PSI0MTYuNjc5MzgiCiAgICAgICByPSI4LjQ3NTE3MDEiCiAgICAgICBjbGFzcz0i
VW5vcHRpbWljZWRUcmFuc2Zvcm1zIgogICAgICAgdHJhbnNmb3JtPSJtYXRyaXgoMS4zMDI1ODk5
LDAsMCwxLjMwMjU4OTksMjM4LjQ5MzIyLC0zNTEuNjk2MTgpIiAvPgogICAgPGNpcmNsZQogICAg
ICAgc3R5bGU9ImZpbGw6IzgwYjNmZjtmaWxsLW9wYWNpdHk6MTtzdHJva2U6IzgwYjNmZjtzdHJv
a2Utd2lkdGg6MTg7c3Ryb2tlLWxpbmVjYXA6cm91bmQ7c3Ryb2tlLWxpbmVqb2luOmJldmVsO3N0
cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpub25lO3N0cm9rZS1kYXNob2Zmc2V0
OjA7c3Ryb2tlLW9wYWNpdHk6MSIKICAgICAgIGlkPSJwYXRoMjc1NDAtMi0xMSIKICAgICAgIGN4
PSI5MC4yNDUyOTMiCiAgICAgICBjeT0iNDE2LjY3OTM4IgogICAgICAgcj0iOC40NzUxNzAxIgog
ICAgICAgY2xhc3M9IlVub3B0aW1pY2VkVHJhbnNmb3JtcyIKICAgICAgIHRyYW5zZm9ybT0ibWF0
cml4KDEuMzAyNTg5OSwwLDAsMS4zMDI1ODk5LDM0NC45NTQ0NCwtMzI5LjgzOTkpIiAvPgogIDwv
Zz4KPC9zdmc+Cg=='''

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        if verbose >= 100: print('MainWndow started')

        inputSerial = InputSerial()
        inputSerial.serial_refresh()


        self.setWindowTitle("LaDatalogger")
        self.setMinimumSize(QSize(800, 400))

        #this method of embedded PNG logo is tested and works on:
        #   MS Win 10 (Application window logo and for icon in the taskbar) - statement try import ctypes is needed
        #   Linux Ubuntu (adds taskbar icon, does not work for the icon on app window)
        pm = QtGui.QPixmap()
        pm.loadFromData(base64.b64decode(logo_png_base64Encoded))
        i = QtGui.QIcon()
        i.addPixmap(pm)
        #i.addPixmap(pm.scaled(16,16))
        #i.addPixmap(pm.scaled(24,24))
        #i.addPixmap(pm.scaled(32,32))
        #i.addPixmap(pm.scaled(48,48))
        #i.addPixmap(pm.scaled(256,256))
        #print(i.availableSizes())

        self.setWindowIcon(i)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setMovable(True)

        tabDatasources = tab_datasources(inputSerial)
        tabs.addTab(tabDatasources, 'DataSources')

        self.tabGraphs = tab_graphs()


        #self.tabGraphs_scrollAreaLayout = QVBoxLayout()
        #self.tabGraphs_scrollAreaLayout(self.tabGraphs)

        #self.tabGraphs_scrollAreaWidget = QWidget()
        #self.tabGraphs_scrollAreaWidget.setLayout(self.tabGraphs_scrollAreaLayout)


        self.tabGraphs_scroll = QScrollArea()
        #Scroll Area Properties
        #self.tabGraphs_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        #self.tabGraphs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabGraphs_scroll.setWidgetResizable(True)
        self.tabGraphs_scroll.setWidget(self.tabGraphs)

        #self.layout.addWidget(self.scroll)
        tabs.addTab(self.tabGraphs_scroll, 'GRAPHs')

        #tabExports = tab_exports()
        #tabs.addTab(tabExports, 'Exports')

        #tabSettings = tab_settings()
        #tabs.addTab(tabSettings, 'Settings')

        tabHelp = tab_help()
        tabs.addTab(tabHelp, 'Help')

        tabs.setCurrentIndex(1)   

        self.setCentralWidget(tabs)
        #.setFixedSize()
        
        self.show()


        # schedule detect serial ports
        self.timer_serRefresh = QtCore.QTimer()
        self.timer_serRefresh.setInterval(1000) # each second
        self.timer_serRefresh.timeout.connect(inputSerial.serial_refresh)
        self.timer_serRefresh.start()

        # schedule read data from serial ports
        self.timer_serRead = QtCore.QTimer()
        self.timer_serRead.setInterval(10) # every 10 ms to minimize time shift (timestamps are currently during reading from serial)
        self.timer_serRead.timeout.connect(inputSerial.readData)
        self.timer_serRead.start()

        # schedule Refresh data in graphs
        self.timer_updateGraphs = QtCore.QTimer()
        self.timer_updateGraphs_interval = 50  # each 50ms at the beginnig, is increased with larger data amount
        self.timer_updateGraphs.setInterval(self.timer_updateGraphs_interval)
        self.timer_updateGraphs.timeout.connect(self.tabGraphs.update_graphs)
        self.timer_updateGraphs.start()

        # schedule adjust timer for refreshing data in graph
        self.timer_updateGraphs_timer = QtCore.QTimer()
        self.timer_updateGraphs_timer.setInterval(1000) # each 1s adjust timer
        self.timer_updateGraphs_timer.timeout.connect(self.timer_adjust_timer)
        self.timer_updateGraphs_timer.start()


    def timer_adjust_timer(self):
        datalen_max = 0
        for item_name in data.keys():
            datalen = len(data[item_name]['data'])
            if datalen > datalen_max:
                datalen_max = datalen
        if datalen_max > 3600 and self.timer_updateGraphs_interval <500:
            if verbose > 90:
                print('MainWindow.timer_updateGraphs_interval = 500')
            #after 1 hours of second measurings we slow down graph refresh to 500ms to save CPU
            self.timer_updateGraphs_interval = 500
            self.timer_updateGraphs.setInterval(self.timer_updateGraphs_interval)
        if datalen_max > 36000 and self.timer_updateGraphs_interval <5000:
            if verbose > 90:
                print('MainWindow.timer_updateGraphs_interval = 5000')
            #after 10 hours of second measurings we slow down graph refresh to 5s to save CPU
            self.timer_updateGraphs_interval = 5000
            self.timer_updateGraphs.setInterval(self.timer_updateGraphs_interval)


    #def mousePressEvent(self, e):
    #    if e.button() == Qt.LeftButton:
    #        print(self.pos())


def main():
    global data
    print("Hello DATALoggerWorld!")


    # for PyQT6 is obsolette
    #use only for PyQT6 for Hight DPI monitors

    #for High DPI monitors with scaling enabled
    # pygraph DOC https://pyqtgraph.readthedocs.io/en/latest/how_to_use.html
    #but seems does not work ME (pyqt 5.15.7 on windows 10)

    # workaround for pygraph on pyqt >5.14 and <6
    #os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    #QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # workaeround for pygraph If you are on Qt >= 5.6 and < 5.14; you can get near ideal behavior with the following lines:
    #QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
    #QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons


    app = QtWidgets.QApplication(sys.argv)
    # Apply dark theme to Qt application
    app.setStyleSheet(qdarktheme.load_stylesheet())


    mainWindow = MainWindow()
    mainWindow.show()

    retcode = app.exec()
    sys.exit(retcode)


if __name__ == "__main__":
    main()

# TODO
# knizka o pyqt https://pythoncourses.gumroad.com/l/pysqtsamples za 10+USD