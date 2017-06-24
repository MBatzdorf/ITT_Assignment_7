#!/usr/bin/env python3

import wiimote
import time
import sys
from random import randint
try:
    from PyQt5 import Qt, QtGui, QtCore, QtWidgets
except ImportError:
    print("Could not import PyQt!")


class SimonSaysWidget(QtWidgets.QWidget):

    BUTTONS = ["A", "One", "Two", "Up", "Down", "Right", "Left"]

    def __init__(self, wiimote):
        #super().__init__()
        super(SimonSaysWidget, self).__init__()
        self.wiimote = wiimote
        self.model = None
        self.instructions = None
        self.displayText = None
        self.isShaking = False
        self.level = 0
        self.elapsed = 0
        self.timer = Qt.QTimer()  # set up your QTimer
        self.timer.timeout.connect(self.hideDisplayText)  # connect it to your update function
        self.initUI()
        self.initGame()

    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        self.move(QtWidgets.QApplication.desktop().screen().rect().center()- self.rect().center())
        self.setWindowTitle('Simon Says')
        self.instructions = QtWidgets.QLabel("Press Space to start the game", self)
        self.displayText = QtWidgets.QLabel("Shake", self)
        self.displayText.setGeometry(0, 0, 500, 500)
        newFont = QtGui.QFont("Times", 120, QtGui.QFont.Bold)
        self.displayText.setFont(newFont)
        self.displayText.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.show()

    def initGame(self):
        self.displayText.hide()
        self.instructions.show()
        self.level = 3
        self.model = SimonSaysModel(1, self.level)

    def startRound(self):
        print("Starting Round")
        self.wiimote.accelerometer.unregister_callback(self.wiiMoveEvent)
        self.wiimote.buttons.unregister_callback(self.wiiButtonEvent)
        self.instructions.hide()
        self.displayText.setStyleSheet("QLabel { color : black; }");
        self.displayText.show()
        self.elapsed = 0
        self.isShaking = False
        for task in self.model.trials:
            print("Showing task")
            self.displayText.setText(task)
            QtWidgets.QApplication.processEvents()
            #self.repaint()
            time.sleep(self.model.speed)
        self.displayText.hide()
        self.wiimote.accelerometer.register_callback(self.wiiMoveEvent)
        self.wiimote.buttons.register_callback(self.wiiButtonEvent)
        print("Round started")
        return

    def registerInput(self, input):
        if self.model.trials[self.elapsed] is input:
            self.displayText.setStyleSheet("QLabel { color : green; }");
            print("Correct button pressed")
        else:
            print("Wrong button pressed")
            self.displayText.setStyleSheet("QLabel { color : red; }");
            self.showPressedButton(input)
            time.sleep(1)
            self.startRound()
            return
        self.showPressedButton(input)

        self.elapsed += 1
        if self.elapsed >= len(self.model.trials):
            self.model.add_trial()
            time.sleep(1)
            self.hideDisplayText()
            self.startRound()
            return

    def showPressedButton(self, button):
        self.displayText.setText(button)
        self.displayText.show()

    def hideDisplayText(self):
        self.displayText.hide()

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Space:
            self.startRound()

    def wiiMoveEvent(self, acc_data):
        if acc_data[0] > 750 or acc_data[1] > 750 or acc_data[2] > 750:
            if not self.isShaking:
                self.registerInput("Shake")
            time.sleep(0.1)
            self.isShaking = True
            self.hideDisplayText()
        else:
            self.isShaking = False


    def wiiButtonEvent(self, button):
        if len(button) is 0:
            return
        btn = button[0][0]
        btn_event = button[0][1]
        if btn not in self.BUTTONS:
            return

        if btn is "Up" or btn is "Down" or btn is "Left" or btn is "Right":
            btn = "Cross"
        if btn_event:
            self.registerInput(btn)
        else:
            self.hideDisplayText()


class SimonSaysModel:

    TRIALS = ["A", "One", "Two", "Cross"]

    def __init__(self, speed, starting_complexity):
        self.speed = speed
        self.starting_complexity = starting_complexity
        self.trials = []
        self.init_model()

    def init_model(self):
        for i in range(self.starting_complexity):
            self.add_trial()

    def add_trial(self):
        new_trial = self.TRIALS[randint(0, len(self.TRIALS) -1)]
        # Do not allow same trial twice in a row
        if len(self.trials) > 0:
            while self.trials[-1] is new_trial:
                new_trial = self.TRIALS[randint(0, len(self.TRIALS) -1)]
        self.trials.append(new_trial)
        print(new_trial)

def init_wiimote():
    input("Press the 'sync' button on the back of your Wiimote Plus " +
      "or buttons (1) and (2) on your classic Wiimote.\n" +
      "Press <return> once the Wiimote's LEDs start blinking.")

    if len(sys.argv) == 1:
        addr, name = wiimote.find()[0]
    elif len(sys.argv) == 2:
        addr = sys.argv[1]
        name = None
    elif len(sys.argv) == 3:
        addr, name = sys.argv[1:3]
    print(("Connecting to %s (%s)" % (name, addr)))
    wm = wiimote.connect(addr, name)
    return wm

def main():
    wiimote = init_wiimote()
    app = QtWidgets.QApplication(sys.argv)

    w = SimonSaysWidget(wiimote)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
