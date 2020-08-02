#!/usr/bin/env python
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
from threading import Timer
from multiprocessing import Process
import json
import pyodbc
import pytz
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime, timedelta
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from getmac import get_mac_address
import requests
import serial

import time
import serial


ser = serial.Serial(
               port='/dev/ttyUSB0',
               baudrate = 115200,
               parity=serial.PARITY_NONE,
               stopbits=serial.STOPBITS_ONE,
               bytesize=serial.EIGHTBITS,
               timeout=3
           )



ser.flushInput()


def Connect_SQL_Server(server,username,password,database):
   try:
      cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
      cursor = cnxn.cursor()
      return cursor,cnxn

   except ConnectionError:
      print ("Could Not Connect To MYSQL Server")




# These classes are used to create an error
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ConnectionError(Error):
   """ Custom Error for Connection Problems """
   pass

class ReturnError(Error):
   """ Custom Error for Return Problems """
   pass



# Get each raspberry's mac addres
def Get_Mac():
   eth_mac = get_mac_address()
   mac = eth_mac.replace(":","")
   return mac



#Get_Modbus_Value(listS,mclient) : Gets the values of the modbus registers according to the list of sensors specified
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> Get_SensorAddr(listS) returns the addresses of all the sensors
#=> Get_Register(SensorAddr[i]) returns the list of registers for each sensor stored in a table registers
#=> Get_RegisterID(Registers[j][0]) returns the list of ids for each register stored in a table registre
#=> in each row, mclient.read_holding_registers(RegisterAddr[i][j],RegisterLength[i][j]), unit=Address[i])
#=> RegisterAddr: stands for the address of each register
#=> RegisterLength : stands for the length of each register
#=> unit : is the slave address
#=> this function returns a list of all the register values captured by the rasberry
#=> Decoder is used to format the output of each register
#=> query to get the type of each registre's value
#=> cursor.fetchone()[0] returns one element
#=> each type is tested, and given the right decoder format#=> Decoder is used to format the output of each register
#=> int types are converted to float to match the column data type in SQL Server
#=> converted values are appended in a table result
#=> datetime.now() returns the time when modbus data is captured
def Get_Modbus_Value(Sensors,IP,Address,RegisterID,RegisterAddr,RegisterLength,RegisterType,RegisterPeriod,P):
   try:
       result=[]
       for i in range (0,len(Sensors)):
            mclient = ModbusTcpClient(IP[i])
            mclient.connect()
            for j in range(0,len(RegisterID[i])):
		if(datetime.now()>=P[i][j]):
		   P[i][j] = P[i][j] + timedelta(seconds=RegisterPeriod[i][j])
		   data = mclient.read_holding_registers(RegisterAddr[i][j],RegisterLength[i][j], unit=Address[i])
		   reg = data.registers
                   decoder = BinaryPayloadDecoder.fromRegisters(reg,byteorder=Endian.Big,wordorder=Endian.Little)

                   if(RegisterType[i][j] == 1):
                     reg = float('{0:.2f}'.format(decoder.decode_16bit_uint()))
                   elif (RegisterType[i][j]==2):
                     reg = float('{0:.2f}'.format(decoder.decode_32bit_uint()))
                   elif (RegisterType[i][j]==3):
                     reg = float('{0:.2f}'.format(decoder.decode_16bit_int()))
                   elif (RegisterType[i][j]==4):
                     reg = float('{0:.2f}'.format(decoder.decode_32bit_int()))
                   elif (RegisterType[i][j]==5):
                     reg = float('{0:.2f}'.format(decoder.decode_32bit_float()))
                   result.append(reg)

       return result,P

   except ReturnError:
      print("Could not read modbus values from sensors",Sensors)



def Countdown(t):
	while t>0:
		time.sleep(1)
		t -= 1
	return t






#Publish_MQTT(list): this function takes into parameter the list of values published by Get_Modbus_Value
#=> Creates a client MQTT that connects to the broker on the local host on port 1883
#=> Publishes it to the right topic
#On the other hand, a subscriber on the same topic must be listening when the client publishes the values 
def Publish_MQTT(result,topic,IDRaspberry,IDMesure):
  message=[]
  for i in range (0,len(result)):
       client=mqtt.Client()
       try:
          client.connect("10.64.253.10",1883)
	  ID = int(str(IDMesure) + str(IDRaspberry))
	  Timestamp_Init = datetime.utcnow()
	  Timestamp_Init = Timestamp_Init.replace(tzinfo=pytz.utc)
	  Timestamp_Init = Timestamp_Init.astimezone(pytz.timezone("Europe/Paris"))
	  Timestamp_Init = Timestamp_Init.strftime("%Y-%m-%d %H:%M:%S")
	  message.append(result[i])
	  message.append(Timestamp_Init)
	  message.append(ID)
	  time.sleep(1)


	  client.publish(topic[i],payload=(str(result[i])+ ',' +str(Timestamp_Init)+ ',' +str(ID)+ ',' +str(IDRaspberry)))
	  x=ser.write(str(IDRaspberry) + "\r," + str(ID) + "\r,\n")
          client.disconnect()

       except ConnectionError:
         print("Could not connect to broker on localhost port 1883")



#Returns the credentials of each raspberry according to its MAC, from the web service
def Get_Info(Mac):
   response = requests.get(url = "http://10.64.253.10:80/webservice.php?mac="+Mac)

   try:
   	Sensors=[]
    	IP=[]
    	Address=[]
    	RegisterID=[]
    	RegisterAddr=[]
    	RegisterLength=[]
    	RegisterType=[]
	RegisterTopic=[]
	RegisterPeriod=[]
	Registers=[]
	RegAddress=[]
	RegLength=[]
	RegType=[]
	RegTopic=[]
	RegPeriod=[]

    	jsonResponse = json.loads(response.text)
    	arrayResponse = jsonResponse["arrayResponse"]
    	if (arrayResponse is not None):
		for i in range(0,len(arrayResponse)):
			IDRaspberry = arrayResponse["IDRaspberry"]
			IDMesure = arrayResponse["IDMesure"]
			Sensors.append(arrayResponse['Sensors'][i]['IDSensor'])
			IP.append(arrayResponse['Sensors'][i]['info']['IP'])
			Address.append(arrayResponse['Sensors'][i]['info']['SensorAddress'])
			for j in range(0,len(arrayResponse['Sensors'][i]['info']['Registers'])):
				RegisterID.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['ID'])
				RegisterAddr.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['RegisterAddress'])
				RegisterType.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['Type'])
				RegisterLength.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['Length'])
				RegisterTopic.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['Topic'])
				RegisterPeriod.append(arrayResponse['Sensors'][i]['info']['Registers'][j]['Period'])
			Registers.append(RegisterID)
			RegisterID=[]
			RegAddress.append(RegisterAddr)
			RegisterAddr=[]
			RegLength.append(RegisterLength)
			RegisterLength=[]
			RegType.append(RegisterType)
			RegisterType=[]
			RegPeriod.append(RegisterPeriod)
			RegisterPeriod=[]



        		return (IDRaspberry,IDMesure,Sensors,IP,Address,Registers,RegAddress,RegLength,RegType,RegisterTopic,RegPeriod)
	else:
		print jsonResponse["message"]


   except ValueError:
        print("No JSON returned")




#This part is the MAIN, where the functions are called
# A loop is created so that the capturing, storing, and publishing with MQTT is continuous

Mac = Get_Mac()

IDRaspberry,IDMesure,Sensors,IP,Address,RegisterID,RegisterAddr,RegisterLength,RegisterType,RegisterTopic,RegisterPeriod=Get_Info(Mac)


period=[]
P=[]
for i in range(0,len(Sensors)):
	for j in range(0,len(RegisterID[i])):
		period.append(datetime.now())
	P.append(period)
	period=[]

while(1==1):
     result,Temp = Get_Modbus_Value(Sensors,IP,Address,RegisterID,RegisterAddr,RegisterLength,RegisterType,RegisterPeriod,P)
     P=Temp
     Publish_MQTT(result,RegisterTopic,IDRaspberry,IDMesure)
     IDMesure = IDMesure + 1

#on the receiving edge
     if(ser.readline()):
           x=ser.readline()
           y = x.split(':')
           IDRaspberrySerial = (y[0].split(',')[0])
           IDValueSerial = (y[0].split(',')[1])
           print(IDRaspberrySerial,IDValueSerial)
           Publish_MQTT([0],"Final",IDRaspberrySerial,IDValueSerial)




