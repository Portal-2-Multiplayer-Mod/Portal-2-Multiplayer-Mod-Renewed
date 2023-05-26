from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from modules.exportedui import Ui_MainWindow
import sys, os
import threading, ctypes
import modules.launcher as launcher
import modules.functions as functions
from modules.logging import log
from modules.logging import getnewlines
from time import sleep
import multiprocessing

def terminate(): # we need something to terminate the whole file in the case of a fault
    launcher.handlelockfile(True)
    sys.exit(0)

class NewlineThread(threading.Thread):
    curgloballine = 0

    def run(self):
        global ui
        if os.path.exists(launcher.bsdir + "portal2" + os.sep + "console.log"):
            os.remove(launcher.bsdir + "portal2" + os.sep + "console.log")
        
        scrollbar = ui.console_output.verticalScrollBar()
        while True:
            output = getnewlines(self.curgloballine)
            self.curgloballine = output[1]
            newlines = output[0]

            # jankily append console newlines to newlines
            for line in launcher.getnewconsolelines(launcher.bsdir + "portal2" + os.sep + "console.log"): newlines.append(line)
            
            is_at_bottom = False
            for line in newlines:
                ui.console_output.append(line)
                sleep(0.08)
                is_at_bottom = scrollbar.value() >= scrollbar.maximum() - 30
                if is_at_bottom:
                    scrollbar.setValue(scrollbar.maximum())

            sleep(0.05) # we need to have a delay or else it fills up the loggers function calls

class LaunchThread(threading.Thread):         
    def run(self):
        # target function of the thread class
        launcher.launchgame(rconpasswdlocal=functions.rconpasswd)
        print("done")

launcherthread = None

def stop_game():
    global launcherthread
    launcher.handlelockfile()
    sys.exit(0)
    ui.start_button.setText("Start")
    ui.start_button.clicked.connect(launch_game)

def launch_game():
    global launcherthread
    launcherthread = LaunchThread()
    launcherthread.daemon = True
    launcherthread.start()
    ui.start_button.setText("Stop")
    ui.start_button.clicked.connect(stop_game)

commandlistpos = -1
def send_rcon():
    global commandlistpos
    if launcher.gameisrunning:
        text = ui.command_line.text()
        output = functions.sendrcon(text, functions.rconpasswd, hist=True)
        ui.command_line.setText("")
        commandlistpos = -1
        if len(output.strip()) > 0:
            log(output.strip(), "rcon")
    else:
        log("user attempted to send command while game is closed")

ui = None
def gui_main():
    global ui

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QWidget()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    newlinethread = NewlineThread()
    newlinethread.daemon = True
    newlinethread.start()
    
    ### UI LINKING

    def handle_key_press(event): # cycle previous commands when arrows are pressed
        global commandlistpos
        if event.key() == Qt.Key_Up:
            if len(functions.userrconhist) == 0:
                commandlistpos = -1
                return
            
            commandlistpos += 1
            if commandlistpos > len(functions.userrconhist) - 1:
                commandlistpos = len(functions.userrconhist) - 1

            ui.command_line.setText(functions.userrconhist[commandlistpos])
        elif event.key() == Qt.Key_Down:
            if len(functions.userrconhist) == 0:
                commandlistpos = -1
                return
            
            commandlistpos -= 1
            if commandlistpos < 0:
                ui.command_line.setText("")
                commandlistpos = -1
                return
            
            ui.command_line.setText(functions.userrconhist[commandlistpos])
        else:
            # allow the widget to process other key events normally
            QtWidgets.QLineEdit.keyPressEvent(ui.command_line, event)

    ui.send_button.clicked.connect(send_rcon)
    ui.command_line.returnPressed.connect(send_rcon)
    ui.command_line.keyPressEvent = handle_key_press

    ui.start_button.clicked.connect(launch_game)

    ###

    MainWindow.show()
    app.exec_()
    terminate()