import minimalmodbus
import serial.tools.list_ports
import argparse
import time

#Creates a new instance of a minimal modbus connection
#Change portname to whatever you're using (/dev/USB0, COM4, etc)
#Or just change it when you create the new serial object
class RenogySmartBattery(minimalmodbus.Instrument):
    def __init__(self, portname="COM5", slaveaddress=247, baudrate=9600, timeout=0.5):
          minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
          self.serial.baudrate = baudrate
          self.serial.timeout = timeout
        
    #Gets the amperage flow of the battery specified
    def amps(self, address):
        try:
          self.address = address
          r = self.read_register(5042)
          return r / 100.0 if r < 61440 else (r - 65535) / 100.0
        except Exception as e:
          print(e)
          return 0

    #Gets the voltage of the battery specified
    def volts(self, address):
        try:
          self.address = address
          return self.read_register(5043) / 10.0
        except Exception as e:
          print(e)
          return 0

    #Gets the current AH of the battery specified
    def capacity(self, address):
        try:
          self.address = address
          r = self.read_registers(5044, 2)
          return ( r[0] << 15 | (r[1] >> 1) ) * 0.002
        except Exception as e:
          print(e)
          return 0

    #Gets the max capacity of the battery specified
    def max_capacity(self, address):
        try:
          self.address = address
          r = self.read_registers(5046, 2)
          return ( r[0] << 15 | (r[1] >> 1) ) * 0.002
        except Exception as e:
          print(e)
          return 0

    #Gets the percentage full of the battery specified
    def percentage(self, address):
        try:
          self.address = address
          return self.capacity(address) / self.max_capacity(address) * 100
        except Exception as e:
          print(e)
          return 0

    #Gets the state of the battery specified (Charging, Discharging, or Error)
    def state(self, address):
        try:
          a = self.amps(address)
          if a < 0: return "DISCHARGING"
          elif a > 0: return "CHARGING"
          return "IDLE"
        except Exception as e:
          print(e)
          return "ERROR"

    #For the self-heating batteries, gets if the battery is on and how much (0-100)
    def heater(self, address):
        try:
          self.address = address
          a = self.read_register(5103)
          return ( a / 255) * 100
        except Exception as e:
          print(e)
          a = 0
          return a
        
    #Gets the overall temperature of the battery by getting the average temperature of the cells
    def batteryTemp(self, address):
      try:
        self.address = address
        c1 = self.read_register(5018)
        c2 = self.read_register(5019)
        c3 = self.read_register(5020)
        c4 = self.read_register(5021)
        batTemp = ((c1 + c2 + c3 + c4) / 4)
        
        return batTemp
      except Exception as e:
        print(e)
        return 0

    #Reads a specific register
    def readRegister(self, register, address):
      try:
        self.address = address
        return  self.read_register(register)
      except Exception as e:
        print(e)
        
    #Writes a specific register
    def writeRegister(self, register, value, address):
      try:
        self.address = address
        return self.write_register(register, value)
      except Exception as e:
        print(e)

    #Utilizes the write register to change the slave address of the battery
    def changeAddress(self, value, address):
      try:
        return self.writeRegister(5226,value, address)
      except Exception as e:
        print(e)

    #Gets the totalAH of all the batteries ---- CHANGE THE RANGE FOR YOUR BATTERY ADDRESSES. Mine are 49,50,51,52,53
    def totalAH(self):
      a = 0
      for i in range(49,54):
        try:
          a = a + self.capacity(i)
        except:
          a = a + 0
      return a

    #Gets the total current flow (in A) of all the batteries ---- CHANGE THE RANGE FOR YOUR BATTERY ADDRESSES. Mine are 49,50,51,52,53
    def totalCurrent(self):
      c = 0.0
      for i in range(49,54):
        try:
          c = c + self.amps(i)
        except:
          c = c + 0.0
      return c

    #Utilizes total AH and total current to get an estimate on how long till discharged to 20% or how long till charged to 100%
    #CHANGE MAXTOTAL TO MATCH YOUR TOTAL - MINE IS 500
    def batRate(self):
      total = 0
      rate = 0
      total = self.totalAH()
      cur = self.totalCurrent()
      maxTotal = 500

      if( cur > 0):
        rate = ((maxTotal - total) / cur) * -1
      else:
        rate = abs(total/cur)
      return rate
      
    #Gets the average voltage of all batteries ---- CHANGE THE RANGE FOR YOUR BATTERY ADDRESSES. Mine are 49,50,51,52,53
    def avgVolt(self):
      v = 0
      n = 0
      for i in range(49,54):
        vi = self.volts(i)
        if (vi > 0):
          n = n + 1
          v = v + vi
      return v / n

#Main Method for demonstration
def main():
  renogy = RenogySmartBattery()
  print(renogy.volts(51))
  print(renogy.amps(51))
 

if __name__ == "__main__":
  main()