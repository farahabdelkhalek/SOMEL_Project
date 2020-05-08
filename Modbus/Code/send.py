#!/usr/bin/env python
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from getmac import get_mac_address
import requests




# These classes are used to create an custom error
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



# Connects to SQL server => returns the connection and the cursor to be used for queries
def Connect_SQL_Server(server,username,password,database):
   try:
      cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
      cursor = cnxn.cursor()
      return cursor,cnxn

   except ConnectionError :
      print ("Could Not Connect To MYSQL Server")
 



# Get_Register(addr): Gets the registers according for the sensor address given
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> query to get the registers according to the addr given to the function as a parameter
#=> cursor.fetchall() returns a list
#=> the list is stored in a table result and returned by the function 
def Get_Register(sensor):
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      ID=[]
      register=[]
      cursor.execute("SELECT Register.idRegister FROM Register,Sensor,Topics WHERE Register.idRegister=Topics.idRegister and Sensor.IDSensor=Topics.idSensor and Sensor.idSensor=?",sensor)
      id = cursor.fetchall()
      for j in range (0,len(id)):
         ID.append(id[j][0])
         cursor.execute("select Register from Register where IDRegister=?",ID[j])
         reg = cursor.fetchone()[0]
         register.append(reg)
      return ID,register





#Get_Length(desc) : Gets the register's length (Word_Count) according to the register given as a parameter
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> query to get the length according to the register given to the function as a parameter
#=> cursor.fetchone() returns a list
#=> [0] returns the first element of the list that is the length as int
def Get_Length(register):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT RegisterCount FROM Register WHERE Register=?",register)
      length=cursor.fetchone()[0]
      return length

   except ReturnError:
      print("Nothing to Fetch from register",register)



#Get_SensorAddr(SensorID): Gets the sensor's address from the table Sensor according to its ID
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> query to get the length according to the desc given to the function as a parameter
#=> cursor.fetchone() returns a list
#=> [0] returns the first element of the list that is the length as int 
def Get_SensorAddr(SensorID):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT Address FROM Sensor WHERE idSensor=?",SensorID)
      sensorAddr=cursor.fetchone()[0]
      return sensorAddr

   except ReturnError:
      print("Nothing to Fetch from sensor",SensorID)



# Get the IP Address by which the sensor is reached
def Get_IP(Addr):
   cursor,cnxn = Connect_SQL_Server(server,username,password,database)
   cursor.execute("select IP_Address from Sensor,IPAddress where Sensor.ID_IPAddress = IPAddress.ID_IPAddress and Sensor.Address=?",Addr)
   ip = cursor.fetchone()[0]
   return ip



#Get_Modbus_Value(listS,mclient) : Gets the values of the modbus values according to the list of sensors specified
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> Get_SensorAddr(listS) returns the addresses of all the sensors
#=> Get_Register(SensorAddr[i]) returns the list of registers for each sensor stored in a table registers
#=> Get_RegisterID(Registers[j][0]) returns the list of ids for each register stored in a table registre
#=> in each row, mclient.read_holding_registers(Registers[k][0],Get_Length(Registers[k][0]), unit=SensorAddr[i])
#=> address : Get_Register(k[0]) => i[0] stands for the address of the register in line i (the first parameter)
#=> length : Get_Length(k[0]) => i[0] stands for the length of the register in line i (the first parameter)
#=> unit : SensorAddr[i] => is the slave address from the list SensorAddr
#=> this function returns a list of all the register values captured by the counters
#=> Decoder is used to format the output of each register
#=> query to get the type of each registre's value
#=> cursor.fetchone()[0] returns one element
#=> each type is tested, and given the right decoder format#=> Decoder is used to format the output of each register
#=> int types are converted to float to match the column data type in SQL Server
#=> converted values are appended in a table result
#=> sensor ids are appended in a table sensor
#=> datetime.now() returns the time when modbus data is captured
def Get_Modbus_Value(listS):
   try:
       cursor,cnxn = Connect_SQL_Server(server,username,password,database)
       result=[]
       ID=[]
       for i in range (0,len(listS)):
            id, value = Get_Register(listS[i])
            cursor.execute("select IP_Address from IPAddress,Sensor where IPAddress.ID_IPAddress=Sensor.ID_IPAddress and Sensor.Address=?",Get_SensorAddr(listS[i]))
            ip = cursor.fetchone()[0]
            mclient = ModbusTcpClient(ip)
            mclient.connect()
            for j in range(0,len(id)):
               data = mclient.read_holding_registers(value[j],Get_Length(value[j]), unit=Get_SensorAddr(listS[i]))
               reg = data.registers
               decoder = BinaryPayloadDecoder.fromRegisters(reg,byteorder=Endian.Big,wordorder=Endian.Little)
               cursor.execute("select Register.IDType from Register,TypeRegister where Register.IDType = TypeRegister.idTypeRegister and Register.Register = ?",value[j])
               type = cursor.fetchone()[0]

               if(type == 1):
                  reg = float('{0:.2f}'.format(decoder.decode_16bit_uint()))
               elif (type==2):
                  reg = float('{0:.2f}'.format(decoder.decode_32bit_uint()))
               elif (type==3):
                  reg = float('{0:.2f}'.format(decoder.decode_16bit_int()))
               elif (type==4):
                  reg = float('{0:.2f}'.format(decoder.decode_32bit_int()))
               elif (type==5):
                  reg = float('{0:.2f}'.format(decoder.decode_32bit_float()))
               result.append(reg)
            ID.append(id)
       date=datetime.now()
       return result,listS,ID,date

   except ReturnError:
      print("Could not read modbus values from sensors",listS)




#Publish_MQTT(list): this function takes into parameter the list of values published by Get_Modbus_Value
#=> Creates a client MQTT that connects to the broker on the local host on port 1883
#=> Transforms the list of integers to json using the function json.dumps
#=> Publishes it to the topic data_req
#On the other hand, a subscriber on the same topic must be listening when the client publishes the values 
def Publish_MQTT(value,sensor,register,date):
  cursor,cnxn = Connect_SQL_Server(server,username,password,database)
  for i in range (0,len(sensor)):
    for j in range (0,len(register[i])):
       topic = Get_Topic(sensor[i],register[i][j])
       client=mqtt.Client()
       try:
          client.connect("localhost",1883)
          client.publish(topic,payload=json.dumps(value[j]))
          #+ "," + " Reading Time: " + "," + str(date.hour)+ ":" + str(date.minute) +  ":" + str(date.second))
          client.disconnect()

       except ConnectionError:
         print("Could not connect to broker on localhost port 1883")




# Get_Sensor(sensor) : Connects to the sensor according to the user's input, either PV or Onduleur,
#=> Connects to SQL Server
#=> and gets the list of addresses for the corresponding sensor
#=> Get_SensorID(i) returns the ID of each address
def Get_Sensor(raspberry):
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT Sensor.idSensor FROM Sensor,Raspberry where Sensor.idRaspberry=Raspberry.idRaspberry and Raspberry.idRaspberry=?",raspberry)
      row=cursor.fetchall()
      values=[]
      for i in row:
         values.append(i[0])
      return values





# Write_Register(register,data) : Write data specified by the user to specified register
# Each command should be followed by a rising edge of bit 40246
def Write_Register(register,data):
   try:
      client = Connect_Onduleur()
      client.write_registers(register,data)
      Activation_Bit(client)
      print("Writing to register",register,"successfull")

   except ReturnError:
      print("Could not Write to register")



# Actiation_Bit : Modifying the bit 40246 from 0 to 1 for validating the command given 
def Activation_Bit(client):
   try:
      client.write_registers(40246,0)
      client.write_registers(40246,1)

   except ReturnError:
      print("Could not activate bit 40246")



def Get_Topic(sensor,register):
   cursor,cnxn = Connect_SQL_Server(server,username,password,database)
   cursor.execute("select Topic from Topics,Sensor,Register where Sensor.IDSensor=Topics.idSensor and Register.IDRegister=Topics.idRegister and Sensor.IDSensor=? and Register.IDRegister=?",sensor,register)
   topic=cursor.fetchone()[0]
   return topic


#This part is the MAIN, where the functions are called
# A loop is created so that the capturing, storing, and publishing with MQTT is continuous

#while(1==1):

Mac = Get_Mac()
response = requests.get(url = "http://localhost:80/webservice.php?mac="+Mac)
try:
 
    jsonResponse = json.loads(response.text) 
    print jsonResponse
    arrayResponse = jsonResponse["arrayResponse"] 
    if (arrayResponse is not None):
       server,username,password,database = arrayResponse["servername"], arrayResponse["username"], arrayResponse["password"], arrayResponse["dbname"]
       Sensor_IDs=Get_Sensor(2)
       value,sensor,register,date=Get_Modbus_Value(Sensor_IDs)
       Publish_MQTT(value,sensor,register,date)
       #Write_Register(40242,10000)

except ValueError:
        print("No JSON returned")

