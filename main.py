import appdaemon.plugins.hass.hassapi as hass
import minimalmodbus
from victron import Vedirect as vict
import datetime
import renogy

class Vandiamo(hass.Hass):
    
    def runUpdates(self, kwargs):
        self.updateSolar(False)
        self.updateBattery(False)
      
    def updateSolar(self, kwargs):
      v = vict("/dev/serial/by-id/usb-VictronEnergy_BV_VE_Direct_cable_VE5BFHO8-if00-port0", 5)
      global VICTRON_ERROR
      pvData = v.read_data_single()
      #self.log(pvData)
      
      for k,v in pvData.items():
          if k == 'ERR':
            self.set_state("sensor.pvError", state = self.parseVictron(v,'err'), attributes = {"friendly_name": "Solar Error"})
          elif k == 'H19':
            self.set_state("sensor.totalPV", state = float(int(v)/100), attributes = {"friendly_name": "Total Solar", "unit_of_measurement": "kWh"})
          elif k == 'H20':
            self.set_state("sensor.dailyPV", state = float(int(v)/100), attributes = {"friendly_name": "Daily Solar", "unit_of_measurement": "kWh"})
          elif k == 'H21':
            self.set_state("sensor.maxWatts", state = float(v), attributes = {"friendly_name": "Max Daily Wattage", "unit_of_measurement": "W"})
          elif k == 'V':
            self.set_state("sensor.pvbattvolt", state = float(int(v)/1000), attributes = {"friendly_name": "PV Battery Voltage", "unit_of_measurement": "V"})
          elif k == 'VPV':
            self.set_state("sensor.panelVoltage", state = int(v)/1000, attributes = {"friendly_name": "Panel Voltage", "unit_of_measurement": "V"})
          elif k == 'PPV':
            self.set_state("sensor.panelWatt", state = int(v), attributes = {"friendly_name": "PanelWatts", "unit_of_measurement": "W"})
          elif k == 'CS':
            self.set_state("sensor.mpptState", state = self.parseVictron(v,'cs'), attributes = {"friendly_name": "MPPT State"})
      
      


    def updateBattery(self, kwargs):
        p = renogy.RenogySmartBattery("/dev/ttyUSB1")
        totalAH = 0
        totalCur = 0
        for i in range(49,54):
          totalCapacity = 0
          try:
            sensorName = "Battery" + str((i+2)%10)
            capacity = round(p.capacity(i),2)
            volts = round(p.volts(i),2)
            heater = p.heater(i)
            amps = round(p.amps(i),2)
            bstate = p.state(i)
            temp = p.batteryTemp(i)
            self.log(temp)
            temp = temp / 10
            temp = (temp * (9/5)) + 32
            
            self.set_state("sensor." + sensorName + "capacity", state = capacity, attributes = {"friendly_name": sensorName + " Capacity", "unit_of_measurement":"Ah"})
            self.set_state("sensor." + sensorName + "voltage", state = volts, attributes = {"friendly_name": sensorName + " Voltage", "unit_of_measurement":"V"})
            self.set_state("sensor." + sensorName + "current", state = amps, attributes = {"friendly_name": sensorName + " Current", "unit_of_measurement":"A"})
            self.set_state("sensor." + sensorName + "state", state = bstate, attributes = {"friendly_name": sensorName + " State"})
            self.set_state("sensor." + sensorName + "temp", state = round(temp,2), attributes = {"friendly_name": sensorName + " Temperature", "unit_of_measurement":"°F"})
            
                
            totalAH = totalAH + capacity
            totalCur = totalCur + amps
            
            if (heater > 10):
                heater = "On"
            else:
                heater = "Off"
            self.set_state("sensor." + sensorName + "Heater", state = heater, attributes = {"friendly_name": sensorName + " Heater Status"})
                
          except Exception as e:
            self.log(e)
            
        totalPercentage = round((totalAH / 500.0) * 100, 2)
            
        if(totalCur > 0):
            status = "Charging: " + str(round((500-totalAH) / totalCur,2)) + " Hours"
            
        elif(totalCur == 0):
            status = "Idle"
            
        elif(totalCur < 0):
            status = "Discharging: " + str(round((totalAH - 500*.2) / abs(totalCur),2)) + " Hours"
        else:
            status = "Error"        
        
        self.set_state("sensor.batterypercent", state = totalPercentage, attributes = {"friendly_name":"Total Battery Percentage", "unit_of_measurement":"%"})
        self.set_state("sensor.batterystatus", state = status, attributes = {"friendly_name": "Battery Status"})
        self.set_state("sensor.batterywatts", state = round((totalCur * volts),2), attributes = {"friendly_name":"Battery Wattage Use", "unit_of_measurement":"W"})
      
      
    def parseVictron(self,msg, msgType):
        VICTRON_ERROR = {
          '0': 'No error',
          '2': 'Battery voltage too high',
          '17': 'Charger temperature too high',
          '18': 'Charger over current',
          '19': 'Charger current reversed',
          '20': 'Bulk time limit exceeded',
          '21': 'Current sensor issue',
          '26': 'Terminals overheated',
          '28': 'Converter issue',  # (dual converter models only)
          '33': 'Input voltage too high (solar panel)',
          '34': 'Input current too high (solar panel)',
          '38': 'Input shutdown (excessive battery voltage)',
          '39': 'Input shutdown (due to current flow during off mode)',
          '65': 'Lost communication with one of devices',
          '66': 'Synchronised charging device configuration issue',
          '67': 'BMS connection lost',
          '68': 'Network misconfigured',
          '116': 'Factory calibration data lost',
          '117': 'Invalid/incompatible firmware',
          '119': 'User settings invalid'
    }

        # The state of operation
        VICTRON_CS = {
          '0': 'Off',
          '2': 'Fault',
          '3': 'Bulk',
          '4': 'Absorption',
          '5': 'Float',
          '7': 'Equalize (manual)',
          '245': 'Starting-up',
          '247': 'Auto equalize / Recondition',
          '252': 'External control'
    }

        # The possible values for the tracker operation
        VICTRON_MTTP = {
          '0': 'Off',
          '1': 'Limited',
          '2': 'Active'
    }

        # Off reason, this field described why a unit is switched off.
        #
        # Available on SmartSolar mppt chargers since firmware version v1.44 (VE.Direct models)
        # and v1.03 (SmartSolar VE.Can models)
        # FIXME: This might not work as a dictionary
        VICTRON_OFF_REASON = {
          "0x00000001": "No input power",
          "0x00000002": "Switched off (power switch)",
          "0x00000004": "Switched off (device mode register)",
          "0x00000008": "Remote input",
          "0x00000010": "Protection active",
          "0x00000020": "Paygo",
          "0x00000040": "BMS",
          "0x00000080": "Engine shutdown detection",
          "0x00000100": "Analysing input voltage"
    }
    
        if (msgType == 'err'):
          return VICTRON_ERROR.get(msg)
        elif (msgType == 'cs'):
          return VICTRON_CS.get(msg)
      
      
      
    def initialize(self):
      start_time=self.datetime()
      self.runUpdates(False)
      
      
      self.handle = self.run_every(self.runUpdates,start_time,15)
