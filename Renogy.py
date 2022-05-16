import minimalmodbus
import serial.tools.list_ports
import argparse
import time

#Creates a new instance of a minimal modbus connection
#Change portname to whatever you're using (/dev/USB0, COM4, etc)
#Or just change it when you create the new serial object
#247 is the default address for Renogy devices
class RenogySmartBattery(minimalmodbus.Instrument):
    def __init__(self, portname="/dev/USB0", slaveaddress=247, baudrate=9600, timeout=0.5):
          minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
          self.serial.baudrate = baudrate
          self.serial.timeout = timeout
          self.address = slaveaddress
          self.amps = 0
          self.unitVolts = 0
          self.cellVolts = []
          self.numCells = 4
          self.capacity = 0
          self.maxCapacity = 0
          self.percentage = 0
          self.state = "Error"
          self.heater = False
          self.cellTemp = []
          self.cycles = 0
          self.batSerial = ""

          #Reads number of Cells
          try:
            self.numCells = self.read_register(5000)
          except Exception as e:
            print("Error getting number of cells")

          #Reads the Serial Number
          try:
            self.batSerial = self.read_registers(5110,6)
          except Exception as e:
            print("Error reading the serial number")
          

    def update(self):
      #Gets unit current flow in A (0), unit voltage (1), capacity in AH (2,3), max capacity (4,5), cycle nums (6)
      try:
        battInfo = self.read_registers(5042,7)
        
        self.amps = battInfo[0] / 100 if battInfo[0] < 61440 else (battInfo[0] - 65535) / 100
        self.unitVolts = battInfo[1] / 10
        self.capacity = ( battInfo[2] << 15 | (battInfo[3] >> 1) ) * 0.002
        self.Maxcapacity = ( battInfo[4] << 15 | (battInfo[5] >> 1) ) * 0.002
        self.cycles = battInfo[6]
      except Exception as e:
        print("Error getting Unit info" + e)

      #Gets heater status
      try:
        heaterInfo = self.read_register(5013)
        self.heater = (heaterInfo / 255) * 100
      except Exception as e:
        print("Error getting heater info" + e)

      #Get individual cell info
      try:
        self.cellTemp = self.read_registers(5018, self.numCells)
        self.cellVolts = self.read_registers(5001, self.numCells)
      except Exception as e:
        print("Error getting individual cell info")

    def getNumCells(self):
      return self.numCells
    
    #sets the address of the battery
    def setAddress(self, address):
       self.address = address

    #Gets the amperage flow of the battery
    def getAmps(self):
        return self.amps
    #Returns a list of the cell voltages
    def getCellVolts(self):
        return [x / 19 for x in self.cellVolts]
    #Returns number of cycles on the battery
    def getCycles(self):
        return self.cycles
    #Returns the serial number
    def getSerial(self):
        return ''.join(self.batSerial)

    #Gets the voltage of the battery
    def getUnitVolts(self):
        return self.unitVolts

    #Gets the current AH of the battery
    def getCapacity(self):
        return self.capacity

    #Gets the max capacity of the battery
    def getMax_capacity(self):
        return self.maxCapacity

    #Gets the percentage full of the battery
    def getPercentage(self):
        return self.capacity / self.maxCapacity

    #Gets the state of the battery (Charging, Discharging, or Error)
    def getState(self):
          if self.amps < 0: return "DISCHARGING"
          elif self.amps > 0: return "CHARGING"
          return "IDLE"

    #For the self-heating batteries, gets if the battery is on and how much (0-100)
    def getHeater(self):
        return self.heater
        
    #Gets the overall temperature of the battery by getting the average temperature of the cells
    def getBatteryTemp(self):
      return sum(self.cellTemp) / len(self.cellTemp)
    
    #Reads a specific register
    def readRegister(self, register):
      try:
        return  self.read_register(register)
      except Exception as e:
        print(e)

    def readRegisters(self, startRegister, numRegisters):
      try:
        return self.read_registers(startRegister, numRegisters)
      except Exception as e:
        print(e)
        
    #Writes a specific register
    def writeRegister(self, register, value):
      try:
        return self.write_register(register, value)
      except Exception as e:
        print(e)

    #Utilizes the write register to change the slave address of the battery
    def changeAddress(self, value, address):
      try:
        return self.writeRegister(5223,value, address)
      except Exception as e:
        print(e)



#Main Method for demonstration
def main():
  #main two arguments are the identifier of the USB connection and the address to connect to. 
  renogy = RenogySmartBattery("/dev/USB0", 50)
  print(renogy.volts(51))
  print(renogy.amps(51))
 

if __name__ == "__main__":
  main()