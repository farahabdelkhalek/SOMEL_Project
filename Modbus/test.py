#!/usr/bin/env python
import paho.mqtt.client as mqtt
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder




# Requisites to connect to SQL server => used in function Connect_SQL_Server 
server = '10.64.6.103'
username = 'CapteursSoMel'
password = 'Capteurs_2020!'
database = 'Demonstrateur_Live_Tree_Database_test'



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



# Connects to SQL server => returns the connection and the cursor to be used for queries
def Connect_SQL_Server(server,username,password,database):
   try:
      cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
      cursor = cnxn.cursor()
      return cursor,cnxn

   except ConnectionError :
      print ("Could Not Connect To MYSQL Server")
      print ("Make sure you used the right credentials") 



# Connect_Onduleur(): Create a connection with SQL Server, Gets the IP Address of the Onduleur from the database,
# and uses this IP (10.64.6.12) to connect to Modbus
def Connect_Onduleur():
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute('select IPAddress.IP_Address from IPAddress,Sensor where Sensor.ID_IPAddress = IPAddress.ID_IPAddress and Sensor.Description=?',"Onduleur") 
      addr = cursor.fetchone()[0]
      mclient = ModbusTcpClient("10.64.6.12")
      mclient.connect()
      return mclient

   except ConnectionError:
      print("Could not connect to 10.64.6.12")



# Connect_Onduleur(): Create a connection with SQL Server, Gets the IP Address of the PV from the database,
# and uses this IP (10.64.7.1) to connect to Modbus
def Connect_PV():
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute('select IPAddress.IP_Address from IPAddress,Sensor where Sensor.ID_IPAddress = IPAddress.ID_IPAddress and Sensor.Description=?',"PV")
      addr = cursor.fetchone()[0]
      mclient = ModbusTcpClient("10.64.7.1")
      mclient.connect()
      return mclient
   
   except ConnectionError:
      print("Could not connect to 10.64.7.1")


# Get_Register(addr): Gets the registers according for the sensor address given
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> query to get the registers according to the addr given to the function as a parameter
#=> cursor.fetchall() returns a list
#=> the list is stored in a table result and returned by the function 
def Get_Register(addr):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT Register.Register FROM Register,Sensor,Register_Sensor WHERE Register.idRegister=Register_Sensor.IDRegister and Sensor.IDSensor=Register_Sensor.IDSensor and Sensor.Address=?",addr)
      register=cursor.fetchall()
      result=[]
      for i in range (0,len(register)):
         result.append(register[i])
      return result
   
   except ReturnError:
      print("Nothing to Fetch from address",addr)



#Get_RegisterID(register): Gets the given register its ID
#=> a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
#=> query to get the address according to the register's name given to the function as a parameter
#=> cursor.fetchone() returns a list
#=> [0] returns the first element of the list that is the address as int
def Get_RegisterID(register):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT idRegister FROM Register where Register=?",register)
      result = cursor.fetchone()[0]
      return result

   except ReturnError:
      print("Nothing to Fetch from register",register)



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
      list=[]
      for i in range (0,len(SensorID)):
         cursor.execute("SELECT Address FROM Sensor WHERE idSensor=?",SensorID[i])
         sensorAddr=cursor.fetchone()[0]
         list.append(sensorAddr)
      return list

   except ReturnError:
      print("Nothing to Fetch from sensor",SensorID) 



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
def Get_Modbus_Value(listS,mclient):
   try:
       cursor,cnxn = Connect_SQL_Server(server,username,password,database)
       result=[]
       registre=[]
       sensor=[]
       SensorAddr=Get_SensorAddr(listS)
       for i in range (0,len(SensorAddr)):
         Registers=Get_Register(SensorAddr[i])

         for j in range (0,len(Registers)):
            registre.append(Get_RegisterID(Registers[j][0]))

         for k in range (0,len(Registers)):
            data = mclient.read_holding_registers(Registers[k][0],Get_Length(Registers[k][0]), unit=SensorAddr[i])
            reg = data.registers
            decoder = BinaryPayloadDecoder.fromRegisters(reg,byteorder=Endian.Big,wordorder=Endian.Little)
            cursor.execute("select Register.IDType from Register,TypeRegister where Register.IDType = TypeRegister.idTypeRegister and Register.Register = ?",Registers[k][0])
            type= cursor.fetchone()[0]

            if(type==1):
               val=float('{0:.2f}'.format(decoder.decode_16bit_uint()))
            elif (type==2):
               val = float('{0:.2f}'.format(decoder.decode_32bit_uint()))
            elif (type==3):
               val = float('{0:.2f}'.format(decoder.decode_16bit_int()))
            elif (type==4):
               val = float('{0:.2f}'.format(decoder.decode_32bit_int()))
            elif (type==5):
               val = float('{0:.2f}'.format(decoder.decode_32bit_float()))
            result.append(val)
            sensor.append(listS[i])
       date=datetime.now()
       return result,registre,sensor,date

   except ReturnError:
      print("Could not read modbus values from sensors",listS)




#Publish_MQTT(list): this function takes into parameter the list of values published by Get_Modbus_Value
#=> Creates a client MQTT that connects to the broker on the local host on port 1883
#=> Transforms the list of integers to json using the function json.dumps
#=> Publishes it to the topic data_req
#On the other hand, a subscriber on the same topic must be listening when the client publishes the values 
def Publish_MQTT(list):
   client=mqtt.Client()
   try:
      client.connect("localhost",1883)
      client.publish("data_req",json.dumps(list))
      print("Data Successfully Published Via MQTT")
      client.disconnect()
      
   except ConnectionError:
      print("Could not connect to broker on localhost port 1883")




# Get_Sensor(sensor) : Connects to the sensor according to the user's input, either PV or Onduleur,
#=> Connects to SQL Server
#=> and gets the list of addresses for the corresponding sensor
#=> Get_SensorID(i) returns the ID of each address
def Get_Sensor(sensor):
   try:
      if (sensor=="PV"):
         client = Connect_PV()
      elif (sensor=="Onduleur"):
         client = Connect_Onduleur()
      else :
         print ("No such sensor ")

      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("SELECT Sensor.Address FROM Sensor where Sensor.Description=?",sensor)
      row=cursor.fetchall()
      values=[]
      for i in row:
         values.append(Get_SensorID(i))
      return values,client

   except ReturnError:
      print("Nothing to Fetch from Sensor",sensor)



# Get_SensorID(sensor): returns the ID of each sensor address
def Get_SensorID(sensor):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      cursor.execute("Select idSensor from Sensor where Address=?",sensor)
      SensorID=cursor.fetchone()[0]
      return SensorID

   except ReturnError:
      print("Nothing to Fetch from Sensor",sensor)




# Insert_Modbus_Values(values,registre,sensor,date): the list of values,registers,and sensors returned by Get_Modbus_Value is used here as a parameter
#=> a connection to SQL server is created with the function Connect_SQL_Server
#=> query to insert into modbus table the variables given in the parameter
#=> cnxn.commit() is necessary to save the changes to modbus table 
def Insert_Modbus_Values(values,registre,sensor,date):
   try:
      cursor,cnxn = Connect_SQL_Server(server,username,password,database)
      for i in range (0,len(values)):
           val=cursor.execute("insert into Value(IDSensor,IDRegister,Value,Timestamp) values (?,?,?,?)",sensor[i],registre[i],values[i],date)
           cnxn.commit()
      print ("Insert was successfull")
      print ("Values : ",values)
      return val

   except ReturnError:
      print("Could not Insert any value into table Value")



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





#This part is the MAIN, where the functions are called
# A loop is created so that the capturing, storing, and publishing with MQTT is continuous

#while(1==1):
Sensor_IDs,client=Get_Sensor("PV")
values,registre,sensor,date=Get_Modbus_Value(Sensor_IDs,client)
Insert_Modbus_Values(values,registre,sensor,date)
Publish_MQTT(values)
#Write_Register(40242,10000)




