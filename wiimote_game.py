#!/usr/bin/env python3

import wiimote
import time
import sys
from random import randint
try:
    from PyQt5 import Qt, QtGui, QtCore, QtWidgets
except ImportError:
    print("Could not import PyQt!")


class BopItWiiWidget(QtWidgets.QWidget):

    """ BoptItWii is a simple game where the users have to follow and imitate
        several actions that are shown to them at the beginning of each round
    """

    BUTTONS = ["A", "One", "Two", "B"]

    def __init__(self, wiimote):
        super(BopItWiiWidget, self).__init__(None)
        self.model = None
        self.wiimote = wiimote
        self.instructions = None
        self.displayText = None
        self.levelText = None
        self.level = 0
        self.elapsed = -1

        self.thread = QtCore.QThread()
        self.thread.start()
        self.inputHandler = BopItWiiInputEventHandler(wiimote)
        self.inputHandler.moveToThread(self.thread)

        self.inputHandler.buttonInputReceived.connect(self.wiiButtonEventReceived)
        self.inputHandler.accInputReceived.connect(self.wiiMoveEventReceived)

        self.initUI()
        self.initGame()

    ''' Set up all UI elements'''
    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        self.move(QtWidgets.QApplication.desktop().screen().rect().center() - self.rect().center())
        self.setWindowTitle('BopItWii')
        self.instructions = QtWidgets.QLabel("Instructions:\n"
                                             "Try to follow the sequence of Buttons and Actions\n"
                                             "that are presented each round.\n"
                                             "But beware, complexity and speed are increasing!\n\n"
                                             "Controls:\n"
                                             "Space to start the game | R to reset | ESC to quit", self)
        self.displayText = QtWidgets.QLabel("", self)
        self.levelText = QtWidgets.QLabel("", self)
        self.displayText.setGeometry(0, 0, 500, 500)
        newFont = QtGui.QFont("Times", 120, QtGui.QFont.Bold)
        self.displayText.setFont(newFont)
        self.displayText.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.show()

    ''' Starts the game's main menu'''
    def initGame(self):
        self.displayText.hide()
        self.levelText.hide()
        self.instructions.show()
        self.level = 1
        self.elapsed = -1
        self.model = BopItWiiModel(2, self.level)

    ''' Start the current turn saved within the model'''
    def startTurn(self):
        self.elapsed = -1
        self.instructions.hide()
        self.levelText.setText("Level " + str(self.level))
        self.levelText.show()
        self.showSequence()
        # Ignore all input events that occurred during sequence displaying
        QtWidgets.QApplication.processEvents()
        self.elapsed = 0
        return

    ''' Iterates through the trial list inside the model
        and presents it to the user
        How fast this sequence is shown is also defined by the model
    '''
    def showSequence(self):
        self.displayText.setStyleSheet("QLabel { color : black; }")
        self.displayText.show()
        for task in self.model.trials:
            self.displayText.setText(task)
            self.repaint()
            time.sleep(self.model.speed)
        self.displayText.hide()

    ''' Tells the game about the user input and evaluates its correctness'''
    def registerInput(self, buttonInput):
        if self.elapsed < 0:
            return
        if self.model.trials[self.elapsed] != buttonInput:
            self.wrongButtonPressed(buttonInput)
            return
        self.displayText.setStyleSheet("QLabel { color : green; }")
        self.showPressedButton(buttonInput)
        self.elapsed += 1
        if self.elapsed >= len(self.model.trials):
            self.prepareNextTurn()
            return

    ''' The user failed a challenge
        Go back to main menu
    '''
    def wrongButtonPressed(self, button):
        self.displayText.setStyleSheet("QLabel { color : red; }")
        self.wiimote.speaker.beep()
        self.wiimote.rumble(0.1)
        self.showPressedButton(button)
        time.sleep(1)
        self.initGame()

    ''' The user completely absolved a turn successfully
        Proceed with a new and more complex one
    '''
    def prepareNextTurn(self):
        self.model.add_trial()
        self.model.decrease_speed(0.25)
        self.level += 1
        time.sleep(0.2)
        self.hideDisplayText()
        time.sleep(0.5)
        self.startTurn()

    ''' Tells the user which button he pressed'''
    def showPressedButton(self, button):
        self.displayText.setText(button)
        self.displayText.show()
        self.repaint()

    ''' Hides the central text widget'''
    def hideDisplayText(self):
        self.displayText.hide()
        self.repaint()

    ''' Key event handler'''
    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Space and self.elapsed < 0:
            self.startTurn()
        if ev.key() == QtCore.Qt.Key_Escape:
            sys.exit(0)
        if ev.key() == QtCore.Qt.Key_R:
            self.initGame()

    ''' Acceleration values changed in the wiimote'''
    def wiiMoveEventReceived(self, acc_data):
        if acc_data[0] > 750 or acc_data[1] > 750 or acc_data[2] > 750:
            self.inputHandler.accInputReceived.disconnect()
            self.registerInput("Shake")
            time.sleep(0.2)
            self.hideDisplayText()
            self.inputHandler.accInputReceived.connect(self.wiiMoveEventReceived)

    ''' Key event handler concerning wiimote buttons'''
    def wiiButtonEventReceived(self, button, eventPress):
        if button not in self.BUTTONS:
            return
        if eventPress:
            self.registerInput(button)
        else:
            self.hideDisplayText()


class BopItWiiInputEventHandler(Qt.QObject):

    """ Event handler for receiving input signals from the Wiimote
        It provides to signals both firing when updated values are received

         Warning: Should be run it its own QThread to avoid timer errors
    """

    buttonInputReceived = QtCore.pyqtSignal(str, bool, name='buttonInputReceived')
    accInputReceived = QtCore.pyqtSignal(list, name='accInputReceived')

    def __init__(self, wiimote):
        super(BopItWiiInputEventHandler, self).__init__()
        self.wiimote = wiimote
        self.registerInput()

    '''Subscribe to the callbacks from the wiimote'''
    def registerInput(self):
        self.wiimote.accelerometer.register_callback(self.wiiMoveEvent)
        self.wiimote.buttons.register_callback(self.wiiButtonEvent)

    '''Unsubscribe from the wiimote callbacks'''
    def unregisterInput(self):
        self.wiimote.accelerometer.unregister_callback(self.wiiMoveEvent)
        self.wiimote.buttons.unregister_callback(self.wiiButtonEvent)

    '''Called when new data is available from the accelerometer'''
    def wiiMoveEvent(self, acc_data):
        self.accInputReceived.emit(acc_data)

    ''' Called when a button is pressen on the wiimote'''
    def wiiButtonEvent(self, button):
        if len(button) is 0:
            return
        btn = button[0][0]
        btn_event = button[0][1]
        self.buttonInputReceived.emit(btn, btn_event)


class BopItWiiModel:

    """ Initializes and keeps track of the game state
        Stores the sequence to imitate and the speed how fast it is iterated
    """

    TRIALS = ["A", "One", "Two", "B", "Shake"]
    MIN_SPEED = 0.25

    def __init__(self, speed, starting_level):
        self.speed = speed
        self.level = starting_level
        self.trials = []
        self.init_model()

    ''' Adds as many trials to the list as given via starting_level parameter'''
    def init_model(self):
        for i in range(self.level):
            self.add_trial()

    ''' Extend the trial list by one random trial'''
    def add_trial(self):
        new_trial = self.TRIALS[randint(0, len(self.TRIALS) - 1)]
        # Do not allow same trial twice in a row for display purposes
        if len(self.trials) > 0:
            while self.trials[-1] is new_trial:
                new_trial = self.TRIALS[randint(0, len(self.TRIALS) - 1)]
        self.trials.append(new_trial)
        self.level = len(self.trials)

    ''' Decreasing the speed variable by a given amount'''
    def decrease_speed(self, time_in_seconds):
        self.speed -= time_in_seconds
        if self.speed < self.MIN_SPEED:
            self.speed = self.MIN_SPEED


def init_wiimote():
    """
    Tries to connect to a wiimote with the Mac-Addresss given via command line parameter
    :return: The successfully connected wiimote object
    """
    input(
        "Press the 'sync' button on the back of your Wiimote Plus " +
        "or buttons (1) and (2) on your classic Wiimote.\n" +
        "Press <return> once the Wiimote's LEDs start blinking."
    )

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
    w = BopItWiiWidget(wiimote)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
