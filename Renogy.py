import minimalmodbus
import serial.tools.list_ports
import argparse
import time


class RenogySmartBattery(minimalmodbus.Instrument):
    def __init__(self, portname="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AR0KLG4F-if00-port0", slaveaddress=50, baudrate=9600, timeout=0.5):
          minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
          self.serial.baudrate = baudrate
          self.serial.timeout = timeout
        

    def amps(self, address):
        try:
          self.address = address
          r = self.read_register(5042)
          return r / 100.0 if r < 61440 else (r - 65535) / 100.0
        except Exception as e:
          print(e)
          return 0

    def volts(self, address):
        try:
          self.address = address
          return self.read_register(5043) / 10.0
        except Exception as e:
          print(e)
          return 0

    def capacity(self, address):
        try:
          self.address = address
          r = self.read_registers(5044, 2)
          return ( r[0] << 15 | (r[1] >> 1) ) * 0.002
        except Exception as e:
          print(e)
          return 0

    def max_capacity(self, address):
        try:
          self.address = address
          r = self.read_registers(5046, 2)
          return ( r[0] << 15 | (r[1] >> 1) ) * 0.002
        except Exception as e:
          print(e)
          return 0

    def percentage(self, address):
        try:
          self.address = address
          return self.capacity(address) / self.max_capacity(address) * 100
        except Exception as e:
          print(e)
          return 0

    def state(self, address):
        try:
          a = self.amps(address)
          if a < 0: return "DISCHARGING"
          elif a > 0: return "CHARGING"
          return "IDLE"
        except Exception as e:
          print(e)
          return "ERROR"
          
    def heater(self, address):
        try:
          self.address = address
          a = self.read_register(5103)
          return ( a / 255) * 100
        except Exception as e:
          print(e)
          a = 0
          return a
        

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

    def readRegister(self, register, address):
      try:
        self.address = address
        return  self.read_register(register)
      except Exception as e:
        print(e)
        
    def writeRegister(self, register, value, address):
      try:
        self.address = address
        return self.write_register(register, value)
      except Exception as e:
        print(e)

    def totalAH(self):
      a = 0
      for i in range(49,54):
        try:
          a = a + self.capacity(i)
        except:
          a = a + 0
      return a

    def totalCurrent(self):
      c = 0.0
      for i in range(49,54):
        try:
          c = c + self.amps(i)
        except:
          c = c + 0.0
      return c

    def batRate(self):
      total = 0
      rate = 0
      total = self.totalAH()
      cur = self.totalCurrent()

      if( cur > 0):
        rate = ((500 - total) / cur) * -1
      else:
        rate = abs(total/cur)
      return rate
      
    def avgVolt(self):
      v = 0
      n = 0
      for i in range(49,54):
        vi = self.volts(i)
        if (vi > 0):
          n = n + 1
          v = v + vi
      return v / n
