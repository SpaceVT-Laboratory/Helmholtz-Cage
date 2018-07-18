
#   File type:              Sim Lab Python Source File
#   File name:              Helmholtz Cage Controller (HelmholtzCageController.py)
#   Description:            This is the main file used to control the HHC as well as control the GUI.
#   Inputs/Resources:       A .csv file, HelmholtzCageController.ui
#   Output/Created files:   Arduino Mega with 8-Relays
#                           3x Keithley 2260B PSU
#                           HelmHoltz Cage
#                           Magnetometer
#
#   Originally Written by:  Keith Tiemann
#   Created:                7/16/2015
#
#   Further Developments:   Gaeron Friedrichs
#   Last modified:          5/19/2018
#   Version:                6.0.1
#   Notes:                  This a beta version adapted for Python 3.6 and PyQT5

# NOTES: Must say COM3 instead of 3 when inputting
# Must have NI Visa installed (http://www.ni.com/download/ni-visa-5.4.1/4626/en/) and then py visa
# for NI visa you might need to install Visual Studio .nET 2003



# Make arduino comm specificaly for each arduino

# treat pause and stop as interrupts, change a flag value 

#=============================================================================#
#                                     Setup                                   #
#=============================================================================#
import sys
import csv
import os
import serial
import time
import visa
from PyQt5 import QtGui, uic, QtWidgets, QtCore
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
qtCreatorFile = "HelmholtzCageController.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):

#=============================================================================#
#                                Initialization                               #
#=============================================================================#

    # Initializes the GUI and setups some class variables
    def __init__(self):
    # WARNING - Edits here can break the program!
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.path = None
        self.bfield_data = []
        self.sim_data = []
        self.V_data = []
        self.I_data = []

        self.rm = None
        self.keithleyX = None
        self.keithleyY = None
        self.keithleyZ = None
        self.Arduino = None

        self.voltage = 30;
        self.stop_flag = 0

        self.roc_line.textChanged.connect(self.setRoC)
        self.arduino_line.textChanged.connect(self.checkArduino)
        self.PSUX_line.textChanged.connect(self.checkPSUX)
        self.PSUY_line.textChanged.connect(self.checkPSUY)
        self.PSUZ_line.textChanged.connect(self.checkPSUZ)
        self.xoffset_line.textChanged.connect(self.setXOffset)
        self.yoffset_line.textChanged.connect(self.setYOffset)
        self.zoffset_line.textChanged.connect(self.setZOffset)
        
        self.browse_button.clicked.connect(self.Browse)
        self.extract_button.clicked.connect(self.Extract)
        self.connect_button.clicked.connect(self.Connect)
        self.disconnect_button.clicked.connect(self.Disconnect)
        self.run_button.clicked.connect(self.activateSim)

        #test this out
        self.roc_unit_combobox.activated.connect(self.setRoC)
        
#=============================================================================#
#                                General Methods                              #
#=============================================================================#
    # Converts the string into an interger based on the unit given relative to the base unit
    def ConvertUnit(self,unit_name):
        # Base units are milliseconds and nanoTeslas
        if unit_name == 'nT': return 1
        elif unit_name == 'T': return 10^9
        elif unit_name == 'G': return 10^5
        elif unit_name == 'second(s)': return 1000
        elif unit_name == 'millisecond(s)': return 1
        elif unit_name == 'minute(s)': return 60000
        else: return -1

    # Check if a number is negative
    def isNegative(self,number):
        if number >= 0: return 0
        else: return 1

    def isfloat(self, value):
        try:
            float(value)
            return True
        except: return False

    # Check if a string is empty
    def isEmpty(self,string): return 0 if '' == string else 1
        #if '' == string: return 1
        #else: return 0

    # Set the status box to say a given string
    def setStatus(self,string): self.status_box.setText(string)

    # Check if all ports have been setup
    def checkPortFlags(self):
        return (self.PSUX_flag_checkbox.isChecked() and
        self.PSUY_flag_checkbox.isChecked() and
        self.PSUZ_flag_checkbox.isChecked() and
        self.arduino_flag_checkbox.isChecked())

    # Check if all offsets have been setup aswell as the rate of change
    def checkSimFlags(self):
        return (self.xoffset_flag_checkbox.isChecked() and
        self.yoffset_flag_checkbox.isChecked() and
        self.zoffset_flag_checkbox.isChecked() and
        self.roc_flag_checkbox.isChecked())

    # Set a flag to a given state
    def setFlag(self,flag,state):
    # Enables and disables different boxes or buttons based on flag states
        if flag == 1 : 
            self.extract_button.setEnabled(state) 
            self.browse_flag_checkbox.setChecked(state)
        
        elif flag == 2 : 
            self.extract_flag_checkbox.setChecked(state)
            self.run_button.setEnabled(self.connect_flag_checkbox.isChecked() and self.checkSimFlags() and state)
            self.roc_line.setEnabled(state)
            self.arduino_line.setEnabled(state)
            self.PSUX_line.setEnabled(state)
            self.PSUY_line.setEnabled(state)
            self.PSUZ_line.setEnabled(state)
            self.xoffset_line.setEnabled(state)
            self.yoffset_line.setEnabled(state)
            self.zoffset_line.setEnabled(state)
            self.roc_unit_combobox.setEnabled(state)
        
        elif flag == 3 : 
            self.connect_button.setEnabled(self.checkPortFlags()) 
            self.PSUX_flag_checkbox.setChecked(state)
        elif flag == 4 : 
            self.connect_button.setEnabled(self.checkPortFlags()) 
            self.PSUY_flag_checkbox.setChecked(state)
        elif flag == 5 : 
            self.connect_button.setEnabled(self.checkPortFlags()) 
            self.PSUZ_flag_checkbox.setChecked(state)
        elif flag == 6 : 
            self.connect_button.setEnabled(self.checkPortFlags()) 
            self.arduino_flag_checkbox.setChecked(state)
        
        elif flag == 7 : 
            self.connect_flag_checkbox.setChecked(state)
            self.connect_button.setEnabled(not state)
            self.arduino_line.setEnabled(not state)
            self.PSUX_line.setEnabled(not state)
            self.PSUY_line.setEnabled(not state)
            self.PSUZ_line.setEnabled(not state)
            self.disconnect_button.setEnabled(state)
            self.run_button.setEnabled(self.extract_flag_checkbox.isChecked() and self.checkSimFlags() and state)
        
        elif flag == 8 : 
            self.run_button.setEnabled(self.extract_flag_checkbox.isChecked() and self.checkSimFlags() and state) 
            self.xoffset_flag_checkbox.setChecked(state)
        
        elif flag == 9 : 
            self.run_button.setEnabled(self.extract_flag_checkbox.isChecked() and self.checkSimFlags() and self.connect_flag_checkbox.isChecked()) 
            self.yoffset_flag_checkbox.setChecked(state)
        
        elif flag == 10 : 
            self.run_button.setEnabled(self.extract_flag_checkbox.isChecked() and self.checkSimFlags() and self.connect_flag_checkbox.isChecked()) 
            self.zoffset_flag_checkbox.setChecked(state)
        
        elif flag == 11 : 
            self.run_button.setEnabled(self.extract_flag_checkbox.isChecked() and self.checkSimFlags() and self.connect_flag_checkbox.isChecked())  
            self.roc_flag_checkbox.setChecked(state)
        
        elif flag == 12 : 
            self.active_flag_checkbox.setChecked(state)
            self.run_button.setEnabled(not state)
            self.disconnect_button.setEnabled(not state)
            self.extract_button.setEnabled(not state)
            self.browse_button.setEnabled(not state)
            self.xoffset_line.setEnabled(not state)
            self.yoffset_line.setEnabled(not state)
            self.zoffset_line.setEnabled(not state)
            self.roc_line.setEnabled(not state)
            self.roc_unit_combobox.setEnabled(not state)
            self.pause_button.setEnabled(state)
            self.stop_button.setEnabled(state)
            self.setFlag(13,False)
        
        elif flag == 13 : self.pause_flag_checkbox.setChecked(state)
        elif (flag == 'clear') and (state == False): 
            for index in range(1,13): self.setFlag(index,False)

    # Writes to the Arduino a command type and the command itself before delaying for a specific amount of time and returning what the Arduino replys
    def ArduinoComm(self,command,state):
        if not self.debug_flag_checkbox.isChecked(): self.Arduino.write(chr(command+state+100).encode('UTF-8'))
#=============================================================================#
#                                Data Extraction                              #
#=============================================================================#
    # Setups the browse button
    def Browse(self):
    # Lets user select file path and disables or enables extract button based on if the file is valid
        self.path = QtWidgets.QFileDialog.getOpenFileName(self)
        self.path = self.path[0]
        axis_r = ['x','y','z']
        axis = ['','','']
        unit = ['','','']
        coordiSystem = ['','','']
        try:
            _basefilename , ext = os.path.splitext(os.path.basename(self.path))
            if '.csv' != ext: raise Exception('Incorrect File Type')
            with open(os.path.relpath(self.path), 'r', encoding='UTF-8') as file: header = next(csv.reader(file))
            # Checks the headers
            for i in range(0,3):
                trans = str.maketrans('','','-=+,.~`*&^%$#@!{}[]()')
                string = header[i].translate(trans)
                string = string.replace('_', ' ')
                string = string.replace('  ', ' ')
                array = string.split()
                #if len(array) != 5: raise Exception('Incorrect Header or Data Order')
                if len(array) != 2: raise Exception('Incorrect Header or Data Order')
                #coordiSystem[i] = array[2]
                unit[i] = array[1]
                axis[i] = array[0]
                string = string.replace(' ', '')
                #if string != ('BField'+coordiSystem[i]+axis_r[i]+unit[i]): raise Exception('Incorrect Header or Data Order')
            if (unit[0] != unit[1] or unit[0] != unit[2] or not(unit[0] != 'nT' or unit[0] != 'T' or unit[0] != 'G')): raise Exception('Incorrect Units')
            #if (coordiSystem[0] != coordiSystem[1] or coordiSystem[0] != coordiSystem[2] or not(coordiSystem[0] != 'ECF' or coordiSystem[0] != 'ECI')): raise Exception('Incorrect Coordinate System')
            self.setStatus('File is supported')
            self.unit_box.setText(unit[0])
            #self.coordinate_system_box.setText(coordiSystem[0])
            self.path_box.setText(os.path.basename(self.path))
            self.setFlag(1,True)

        except Exception as etype:
            error = ''
            if etype.args[0] == 'Incorrect File Type': error = 'Error: ' + etype.args[0] + ' - File must be a csv file'
            elif etype.args[0] == 'Incorrect Header or Data Order': error = 'Error: ' + etype.args[0] + ' - The each column in the first row of the file must have something similar to "B Field - ECF x (nT)" or "B Field - ECI z (G) and must be ordered as x, y and z"'
            elif etype.args[0] == 'Incorrect Units': error = 'Error: ' + etype.args[0] + ' - The only supported units are nT, T and G'
            elif etype.args[0] == 'Incorrect Coordinate System':  error = 'Error: ' + etype.args[0] + ' - The only supported coordinate systems are ECI and ECF'
            else: error = 'Error: ' + str(etype.args[0])
            self.setStatus(error)
            self.unit_box.setText("N/A")
            self.coordinate_system_box.setText("N/A")
            self.path_box.setText("")
            self.setFlag(1,False)
        except:
            self.setStatus("Error: Unknown")
            self.unit_box.setText("N/A")
            self.coordinate_system_box.setText("N/A")
            self.path_box.setText("")
            self.setFlag(1,False)

    # Setups the extract button
    def Extract(self):
    # Creates variables with the data of the field after extracting the data from the file
        try:
            with open(os.path.relpath(self.path), 'r', encoding='UTF-8') as file:
                fileData = csv.reader(file);
                next(fileData) # Throws away header data since we already know it
                self.bfield_data[:] = []
                for currentline in fileData:
                    if currentline != []:
                        if '' in currentline: raise Exception('Unbalanced Data')
                        self.bfield_data.append([float(currentline[0]), float(currentline[1]), float(currentline[2]),
                        self.isNegative(float(currentline[0])), self.isNegative(float(currentline[1])), self.isNegative(float(currentline[2]))])
            self.num_of_data_points_box.setText(str(len(self.bfield_data)))
            self.setStatus("Data extracted!")
            self.setFlag(2,True)
        except Exception as etype:
            error = ''
            if etype.args[0] == 'Unbalanced Data': error = 'Error: ' + etype.args[0] + ' - The amount of data for each axis is unbalanced'
            self.setStatus(error)
            self.unit_box.setText("N/A")
            self.coordinate_system_box.setText("N/A")
            self.path_box.setText("")
            self.setFlag(1,False)
        except: self.setStatus("Error: Unknown - Retry extraction or reselect a file")
#=============================================================================#
#                       Data transfer directly from STK                       #
#=============================================================================#
# This version of the code doesn't support direct STK data transfer
#=============================================================================#
#                           PSU Connection Controls                           #
#=============================================================================#

    # Checks what port is being used for PSU
    def checkPSUX(self): self.setFlag(3, not self.isEmpty(self.PSUX_line.text()))
    def checkPSUY(self): self.setFlag(4, not self.isEmpty(self.PSUY_line.text()))
    def checkPSUZ(self): self.setFlag(5, not self.isEmpty(self.PSUZ_line.text()))
    def checkArduino(self): self.setFlag(6, not self.isEmpty(self.arduino_line.text()))

    # Setups the ports and connects the computer to the PSUs and the Arduino
    def Connect(self):
    # Connects to the PSUs and Arduino via ports.
        try:

            self.Arduino = serial.Serial(self.arduino_line.text(), 9600, timeout=0.1)
            time.sleep(.25)
            self.ArduinoComm(2,1)
            self.rm = visa.ResourceManager()
            
            self.keithleyX = self.rm.open_resource(self.PSUX_line.text())
            self.keithleyY = self.rm.open_resource(self.PSUY_line.text())
            self.keithleyZ = self.rm.open_resource(self.PSUZ_line.text())
            
            self.keithleyX.write("ABORt ; SYST:PRES ; DISPlay:MENU:NAME 3") # Makes it so the PSU_connect_portdata shows values for what V/I is currently being outputted
            self.keithleyY.write("ABORt ; SYST:PRES ; DISPlay:MENU:NAME 3")
            self.keithleyZ.write("ABORt ; SYST:PRES ; DISPlay:MENU:NAME 3")
            
            self.keithleyX.write("OUTP:STAT ON")
            self.keithleyY.write("OUTP:STAT ON")
            self.keithleyZ.write("OUTP:STAT ON")
            
            self.setStatus("Connection active!")
            self.setFlag(7, True)
        
        except serial.SerialTimeoutException:
            self.setStatus("Error: No Arduino Communication or Unknown - Make sure the Arduino is connected to the right port")
            self.setFlag(7, False)

        except:
            self.setStatus("Error: No Communication or Unknown - Make sure the ports are correct via Device Manager")
            self.setFlag(7, False)

    
    # Disconnects the computer from the PSUs
    def Disconnect(self):
    # The connection isn't taken from the Arduino but the port can be changed and restarted
        try:
            self.setFlag(7, False)
            
            self.keithleyX.close()
            self.keithleyY.close()
            self.keithleyZ.close()
            
            self.setStatus("Connection no longer active!")
        except:
            self.setStatus("Error: Unknown")
            self.setFlag(7, True)

#=============================================================================#
#                               Power Controls                                #
#=============================================================================#

    # Checks if the rate of change is above 0 and then checks if all flags are up
    def setRoC(self):
        if self.isfloat(self.roc_line.text()):
            if(float(self.roc_line.text()) > 0):
                self.setFlag(11, True)
                self.sim_time_box.setText(str(format(.001*self.ConvertUnit(self.roc_unit_combobox.currentText())*int(self.num_of_data_points_box.text())*float(self.roc_line.text()), '5.2f')))
            else: self.setFlag(11, False)      
        else: self.setFlag(11, False)

    # Obtains the xoffset from GUI and checks the flags
    def setXOffset(self):
        if self.isfloat(self.xoffset_line.text()): self.setFlag(8, abs(float(self.xoffset_line.text()))>=0)
        else: self.setFlag(8, False)
    
    # Obtains the yoffset from GUI and checks the flags
    def setYOffset(self):
        if self.isfloat(self.yoffset_line.text()): self.setFlag(9, abs(float(self.yoffset_line.text()))>=0)
        else: self.setFlag(9, False)
    
    # Obtains the zoffset from GUI and checks the flags
    def setZOffset(self):
        if self.isfloat(self.zoffset_line.text()): self.setFlag(10, abs(float(self.zoffset_line.text()))>=0)
        else: self.setFlag(10, False)
   
    def setupSim(self):
        self.V_data[:] = []
        self.I_data[:] = []
        self.sim_data[:] = []

        for x in range(0,int(self.num_of_data_points_box.text())):
            # The number 613647 is from the constant values from the equations for the cage.
            IvalueX = 613647*(self.bfield_data[x][0]*.000000001*self.ConvertUnit(self.unit_box.text())+.000000001*float(self.xoffset_line.text()))*1.4492/35; #X Middle Coil 1.4492 35 Coils
            IvalueY = 613647*(self.bfield_data[x][1]*.000000001*self.ConvertUnit(self.unit_box.text())+.000000001*float(self.yoffset_line.text()))*1.3984/35; #Y Small Coil 1.3984 35 Coils
            IvalueZ = 613647*(self.bfield_data[x][2]*.000000001*self.ConvertUnit(self.unit_box.text())+.000000001*float(self.zoffset_line.text()))*1.5/35;    #Z Large Coil 1.5 35 Coils
            
            self.V_data.append([self.voltage,self.voltage,self.voltage])
            self.I_data.append([round(IvalueX,2),round(IvalueY,2),round(IvalueZ,2)])
            self.sim_data.append([('APPL '+str(self.V_data[x][0])+','+str(self.I_data[x][0])),('APPL '+str(self.V_data[x][1])+','+str(self.I_data[x][1])),('APPL '+str(self.V_data[x][2])+','+str(self.I_data[x][2]))])

    # Activates the simulation. Also is used to resume the simulation
    def activateSim(self):
        try: # Sets up the simluation

            delay = self.ConvertUnit(self.roc_unit_combobox.currentText())*float(self.roc_line.text())
            self.setupSim()
            self.setStatus("Simulation about to begin! Keep away from open wires!")
            time.sleep(1);
            self.setFlag(12, True)
            try: # Starts the simulation
                self.setStatus("Simulation is Running! Keep away from open wires!")
                for x in range (0,int(self.num_of_data_points_box.text())):
                    
                    for y in range(0,3): self.ArduinoComm((y+1)*2,self.bfield_data[x][y+3])

                    self.keithleyX.write(self.sim_data[x][0])
                    self.keithleyY.write(self.sim_data[x][1])
                    self.keithleyZ.write(self.sim_data[x][2])

                    self.xfield_box.setText(str(round(self.bfield_data[x][0])))
                    self.yfield_box.setText(str(round(self.bfield_data[x][1])))
                    self.zfield_box.setText(str(round(self.bfield_data[x][2])))

                    self.xcurrent_box.setText(str(self.I_data[x][0]))
                    self.ycurrent_box.setText(str(self.I_data[x][1]))
                    self.zcurrent_box.setText(str(self.I_data[x][2]))

                    delay_raw = delay
                    while delay_raw > 100:
                        if not self.stop_button.isChecked():
                            time.sleep(.1)
                            delay_raw = delay_raw - 100
                        else:
                            self.stop_flag = 1
                            break
                        x = self.pauseSim(x)
                    x = self.pauseSim(x)

                    if self.stop_button.isChecked() or self.stop_flag:
                        self.stop_flag = 0
                        self.clearSim()
                        self.setStatus("Simulation Stopped!")
                        self.progress_bar.reset()
                        self.setFlag(12, False)
                        break
                    time.sleep(delay_raw/1000)
                    self.progress_bar.setValue(100*x/int(self.num_of_data_points_box.text()))
                self.setStatus("Simulation Complete!")
                self.clearSim()
                self.progress_bar.reset()
                self.setFlag(12, False)
            except:
                self.setStatus("Error: Unknown - 1")
                self.setFlag(12, False)
        except:
            self.setStatus("Error: Unknown - 2")
            self.setFlag(12, False)


    def pauseSim(self, index):
        if self.pause_button.isChecked():
            self.pause_button.setEnabled(False)
            self.clearSim()
            self.setStatus("Simulation Paused!")
            self.setFlag(13, True)
            index = index - 1
            while self.pause_button.isChecked():
                if self.stop_button.isChecked():
                    self.stop_flag = 1
                time.sleep(1)
            self.pause_button.setEnabled(True)
        return index


    def clearSim(self):
            #self.ArduinoComm('0','0') #Pins 8:13
        self.ArduinoComm(4,4) #Pins 8:13
        self.keithleyX.write('APPL 0.00,0.00')
        self.keithleyY.write('APPL 0.00,0.00')
        self.keithleyZ.write('APPL 0.00,0.00')
        self.xfield_box.setText('0')
        self.yfield_box.setText('0')
        self.zfield_box.setText('0')
        self.xvoltage_box.setText('0')
        self.yvoltage_box.setText('0')
        self.zvoltage_box.setText('0')
        self.xcurrent_box.setText('0')
        self.ycurrent_box.setText('0')
        self.zcurrent_box.setText('0')


        #def closeEvent(self, *args, **kwargs):
        #    super(QtGui.QMainWindow, self).closeEvent(*args, **kwargs)
        #    print "you just closed the pyqt window!!! you are awesome!!!"

#=============================================================================#
#                                  Main Method                                #
#=============================================================================#

# This allows the script to run for the GUI when ran from a console
if __name__ == "__main__":
# WARNING - Editting this can break the code!
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
    #sys.exit(shutDown())