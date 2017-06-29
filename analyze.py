#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

from pyqtgraph.flowchart import Flowchart, Node
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import wiimote_node


class LogNode(Node):
    """
    Logs the last sample from the accelerometer to stdout
    """
    nodeName = "Logging"

    def __init__(self, name):
        print("Acceleration Values:")
        terminals = {
            'accelXIn': dict(io='in'),
            'accelYIn': dict(io='in'),
            'accelZIn': dict(io='in'),
        }
        self._acc_vals = []
        Node.__init__(self, name, terminals=terminals)

    def process(self, **kwds):
        x = str(kwds['accelXIn'][0])
        y = str(kwds['accelYIn'][0])
        z = str(kwds['accelZIn'][0])
        print("X: " + x + " Y: " + y + " Z: " + z)

fclib.registerNodeType(LogNode, [('AccValues',)])


class NormalVectorNode(Node):
    """
    Creates tuples for x-acceleration and z-acceleration values
    """
    nodeName = "NormalVector"

    def __init__(self, name):
        terminals = {
            'accelXIn': dict(io='in'),
            'accelZIn': dict(io='in'),
            'normalVectorX': dict(io='out'),
            'normalVectorZ': dict(io='out'),
        }
        Node.__init__(self, name, terminals=terminals)

    def process(self, **kargs):
        zVal = kargs['accelXIn'] - 521
        xVal = kargs['accelZIn'] - 521
        print(((0, xVal), (0, zVal)))
        return {'normalVectorX': (0, xVal), 'normalVectorZ': (0, zVal)}

fclib.registerNodeType(NormalVectorNode, [('Normal',)])


def createPlotXWidget(layout, wiiNode):
    """
        Adds a plot widget to a layout that will show the acceleration's x values
    :param layout: the layout the widget has to be added to
    :param wiiNode: wiimote node that receives the acceleration input
    """
    pwX = pg.PlotWidget()
    layout.addWidget(pwX, 0, 1)
    pwX.setYRange(0, 1024)
    pwXNode = fc.createNode('PlotWidget', 'PlotWidgetX', pos=(0, -150))
    pwXNode.setPlot(pwX)
    bufferNodeX = fc.createNode('Buffer', 'BufferX')
    fc.connectTerminals(wiiNode['accelX'], bufferNodeX['dataIn'])
    fc.connectTerminals(bufferNodeX['dataOut'], pwXNode['In'])


def createPlotYWidget(layout, wiiNode):
    """
        Adds a plot widget to a layout that will show the acceleration's y values
    :param layout: the layout the widget has to be added to
    :param wiiNode: wiimote node that receives the acceleration input
    """
    pwY = pg.PlotWidget()
    layout.addWidget(pwY, 1, 1)
    pwY.setYRange(0, 1024)
    pwYNode = fc.createNode('PlotWidget', 'PlotWidgetY', pos=(0, -150))
    pwYNode.setPlot(pwY)
    bufferNodeY = fc.createNode('Buffer', 'BufferY')
    fc.connectTerminals(wiiNode['accelY'], bufferNodeY['dataIn'])
    fc.connectTerminals(bufferNodeY['dataOut'], pwYNode['In'])


def createPlotZWidget(layout, wiiNode):
    """
        Adds a plot widget to a layout that will show the acceleration's Z values
    :param layout: the layout the widget has to be added to
    :param wiiNode: wiimote node that receives the acceleration input
    """
    pwZ = pg.PlotWidget()
    layout.addWidget(pwZ, 2, 1)
    pwZ.setYRange(0, 1024)
    pwZNode = fc.createNode('PlotWidget', 'PlotWidgetZ', pos=(0, -150))
    pwZNode.setPlot(pwZ)
    bufferNodeZ = fc.createNode('Buffer', 'BufferZ')
    fc.connectTerminals(wiiNode['accelZ'], bufferNodeZ['dataIn'])
    fc.connectTerminals(bufferNodeZ['dataOut'], pwZNode['In'])


def createNormalWidget(layout, wiiNode):
    pwN = pg.PlotWidget()
    layout.addWidget(pwN, 0, 2, 3, 1)
    pwN.setYRange(-100, 100)
    pwNNode = fc.createNode('PlotWidget', 'PlotWidgetNormal', pos=(0, -150))
    pwNNode.setPlot(pwN)
    normalNode = fc.createNode('NormalVector', 'NormalVector', pos=(150, 0))
    fc.connectTerminals(wiiNode['accelX'], normalNode['accelXIn'])
    fc.connectTerminals(wiiNode['accelZ'], normalNode['accelZIn'])

    curve = fc.createNode('PlotCurve', 'PlotCurve', pos=(0, -150))

    fc.connectTerminals(normalNode['normalVectorZ'], curve['x'])
    fc.connectTerminals(normalNode['normalVectorX'], curve['y'])

    fc.connectTerminals(curve['plot'], pwNNode['In'])


def createLogNode(wiiNode):
    """ Creates a node that outputs all acceleration events to stdout"""
    logNode = fc.createNode('Logging', 'Logging', pos=(150, 0))
    fc.connectTerminals(wiiNode['accelX'], logNode['accelXIn'])
    fc.connectTerminals(wiiNode['accelY'], logNode['accelYIn'])
    fc.connectTerminals(wiiNode['accelZ'], logNode['accelZIn'])


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.setWindowTitle('Analyse Wiimote')
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    layout = QtGui.QGridLayout()
    cw.setLayout(layout)

    # Create an empty flowchart with a single input and output
    fc = Flowchart(terminals={
    })

    layout.addWidget(fc.widget(), 0, 0, 2, 1)

    wiimoteNode = fc.createNode('Wiimote', 'Wiimote', pos=(0, 0))

    createPlotXWidget(layout, wiimoteNode)
    createPlotYWidget(layout, wiimoteNode)
    createPlotZWidget(layout, wiimoteNode)
    createNormalWidget(layout, wiimoteNode)
    createLogNode(wiimoteNode)

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
