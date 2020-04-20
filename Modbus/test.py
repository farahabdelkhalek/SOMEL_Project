#!/usr/bin/env python
import paho.mqtt.client as mqtt
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
import requests
from requests.exceptions import ConnectionError


# Requisites to connect to SQL server => used in function Connect_SQL_Server
server = '10.64.6.103'
username = 'CapteursSoMel'
password = 'Capteurs_2020!'
database = 'Demonstrateur_Live_Tree_Database_test'


class Error(Exception):
   """Base class for other exceptions"""
   pass

class ConnectionError(Error):
   pass

class ReturnError(Error):
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


# Contenates 2 register values to be stored in the modbus table later on
# => each register is a 16 bits word
def concatenate_list_data(list):
    result= ''
    for element in list:
        result += str(element)
    return result



# Connects to Modbus central measurement using the ip address 10.64.7.1 
# => returns the modbus client 
def Connect_Modbus():
   try:
      mclient = ModbusTcpClient('10.64.7.1')
      mclient.connect()
      print("Successfully Connected to MODBUS central measurement")
      return mclient

   except ConnectionError:
      print("Couldn't connected to 10.64.7.1")


# Get_Register(desc): Gets the register's address according for the description (the name)
# => a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
# => query to get the address according to the desc given to the function as a parameter
# => cursor.fetchone() returns a list
# => [0] returns the first element of the list that is the address as int
def Get_Register(desc):
   cursor,cnxn = Connect_SQL_Server(server,username,password,database)
   cursor.execute("SELECT Address FROM tampon WHERE Description=?",desc)
   register=cursor.fetchone()[0]
   return register



# Get_Length(desc) : Gets the register's length (Word_Count) according to the description 
# => a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
# => query to get the length according to the desc given to the function as a parameter
# => cursor.fetchone() returns a list
# => [0] returns the first element of the list that is the length as int
def Get_Length(desc):
   cursor,cnxn = Connect_SQL_Server(server,username,password,database)
   cursor.execute("SELECT Word_Count FROM tampon WHERE Description=?",desc)
   length=cursor.fetchone()[0]
   return length 



# Get_Modbus_Value(slave,mclient) : Gets the values of the modbus counters according to the slave's number
# => a connection to the sql server must be established first, we use the Connect_SQL_Server function that returns the cnxn and cursor
# => query to get the list of all the descriptions in the tampon table, therefore all the modbus counters
# => cursor.fetchall() returns all the list
# => loop to go threw all the list rows
# => in each row, mclient.read_holding_registers gets the register values with the corresponding :
# => address : Get_Register(i[0]) => i[0] stands for the address of the register in line i (the first parameter)
# => length : Get_Length(i[0]) => i[0] stands for the length of the register in line i (the first parameter)
# => unit is the slave number specified by the user when calling the function => it goes from 1 to 14
# => this function returns a list of all the register values captured by the counters
def Get_Modbus_Value(slave,mclient):
   cursor,cnxn = Connect_SQL_Server(server,username,password,database)
   cursor.execute("Select Description from tampon")
   values=[]
   row=cursor.fetchall()
   try:
      for i in row:
         data = mclient.read_holding_registers(Get_Register(i[0]),Get_Length(i[0]), unit=slave)
         reg = data.registers
         for j in range(0,2):
            val=(concatenate_list_data(reg))
         values.append(val)
      return values

   except ReturnError:
      print("Could not fetch any data from rows")


# Publish_MQTT(list): this function takes into parameter the list of values published by Get_Modbus_Value
# => Creates a client MQTT that connects to the broker on the local host on port 1883
# => Transforms the list of integers to json using the function json.dumps
# => Publishes it to the topic data_req
# On the other hand, a subscriber on the same topic must be listening when the client publishes the values
def Publish_MQTT(list):
   client=mqtt.Client()
   try:
      client.connect("localhost",1883)
      print("Successfully Connected to Database")
      client.publish("data_req",json.dumps(list))
      print("Data Published")
      client.disconnect()
   
   except ConnectionError:
      print("Could not connect to broker on localhost port 1883")


# Insert_Modbus_Values(list): the list of values returned by Get_Modbus_Value is used here as a parameter
# => 6 variables are created, and given a value of that list consecutively
# => a connection to SQL server is created with the function Connect_SQL_Server
# => query to insert into modbus table the variables created
# => cnxn.commit() is necessary to save the changes to modbus table
def Insert_Modbus_Values(list):
    I1,I2,I3,Total_positive_active_energy,Total_active_power,Total_power_factor = [list[i] for i in range(0,len((list)))]
    cursor,cnxn = Connect_SQL_Server(server,username,password,database)
    cursor.execute("insert into modbus(I1,I2,I3,Total_positive_active_energy,Total_active_power,Total_power_factor,TIMESTAMP) values (?,?,?,?,?,?,?)",I1,I2,I3,Total_positive_active_energy,Total_active_power,Total_power_factor,datetime.now())
    cnxn.commit()




# This part is the main, where the functions are called
# A loop is created so that the capturing, storing, and publishing with MQTT is continuous
client=Connect_Modbus()
#while(1==1):
values=Get_Modbus_Value(6,client)
Publish_MQTT(values)
Insert_Modbus_Values(values)


#Read data from onduleurs


def twos_complement(input_value, num_bits):
    """Calculates a two's complement integer from the given input value's bits."""
    mask = 2 ** (num_bits - 1)
    return -(input_value & mask) + (input_value & ~mask)

def signed(unsigned_num):
   comp=twos_complement(unsigned_num,16)
   return unsigned_num + comp


def Connect_Onduleur():
   mclient = ModbusTcpClient('10.64.6.12')
   mclient.connect()
   r=mclient.read_holding_registers(40090,2,unit=1)
   print(- signed(r.registers[0]),r.registers[1])
