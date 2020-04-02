#!/usr/bin/env python
import paho.mqtt.client as mqtt
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient

#Contenate 2 register values
def concatenate_list_data(list):
    result= ''
    for element in list:
        result += str(element)
    return result

#Connecting to Modbus central measurement
def ConnectModbus():
   mclient = ModbusTcpClient('10.64.7.1')
   mclient.connect()
   print("Modbus TCP Client Connected")
   return mclient

#Capturing the correct data
def CaptureData(slave,mclient):
   data1 = mclient.read_holding_registers(18458,2, unit=slave)
   reg1 = data1.registers
   for i in range(0,2):
      I1=(concatenate_list_data(reg1))



   data2 = mclient.read_holding_registers(18460,2, unit=slave)
   reg2=data2.registers
   for i in range(len(reg2)):
      I2=(concatenate_list_data(reg2))



   data3 = mclient.read_holding_registers(18462,2, unit=slave)
   reg3=data3.registers
   for i in range(len(reg3)):
      I3=(concatenate_list_data(reg3))



   data4 = mclient.read_holding_registers(19843,2,unit=slave)
   reg4 = data4.registers
   for i in range(len(reg4)):
      Total_Positive_Active_Energy=(concatenate_list_data(reg4))


   data5 = mclient.read_holding_registers(18476,2,unit=slave)
   reg5 = data5.registers
   for i in range(len(reg5)):
      Total_Active_Power=(concatenate_list_data(reg5))


   data6 = mclient.read_holding_registers(18487,1,unit=slave)
   reg6 = data6.registers
   for i in range(len(reg6)):
      Total_Power_Factor=(concatenate_list_data(reg6))


   return(I1,I2,I3,Total_Positive_Active_Energy,Total_Active_Power,Total_Power_Factor)


#Publishing data with MQTT
def ConnectMQTT(I1,I2,I3,Ea,Power,Factor):
   client=mqtt.Client()
   if(client.connect("localhost",1883)==0):
      print("Connected to Database")
      msgs=[]
      msgs.append(I1)
      msgs.append(I2)
      msgs.append(I3)
      msgs.append(Ea)
      msgs.append(Power)
      msgs.append(Factor)
      client.publish("data_req",json.dumps(msgs))
      print("Data Published")
   client.disconnect()

#Store the captured values in modbus table
def ConnectDB(I1,I2,I3,Total_Positive_Active_Energy,Total_Active_Power,Total_Power_Factor):
   server = '10.64.6.103'
   username = 'CapteursSoMel'
   password = 'Capteurs_2020!'
   database = 'Demonstrateur_Live_Tree_Database_test'
   cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
   cursor = cnxn.cursor()
   cursor.execute("insert into modbus(I1,I2,I3,Total_positive_active_energy,Total_active_power,Total_power_factor) values (?,?,?,?,?,?)",(I1,I2,I3,Total_Positive_Active_Energy,Total_Active_Power,Total_Power_Factor))
   cnxn.commit()



#Main
client=ConnectModbus()
MQTTClient=mqtt.Client()
#while(1==1):
I1,I2,I3,Ea,Power,Factor=CaptureData(5,client)
ConnectMQTT(I1,I2,I3,Ea,Power,Factor)
ConnectDB(I1,I2,I3,Ea,Power,Factor)
