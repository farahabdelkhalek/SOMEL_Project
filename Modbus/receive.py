import paho.mqtt.client as mqtt
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from send import Connect_SQL_Server



# Requisites to connect to SQL server => used in function Connect_SQL_Server
server = '10.64.6.103'
username = 'CapteursSoMel'
password = 'Capteurs_2020!'
database = 'Demonstrateur_Live_Tree_Database_test'





cursor,cnxn = Connect_SQL_Server(server,username,password,database)
cursor.execute("Select Topic from Register_Sensor")
topics=cursor.fetchall()
client=mqtt.Client()


def on_message(client, userdata, message):
    print("Topic: " + message.topic)
    print("Message: " + message.payload.decode())
    b= message.payload.decode()
    c=b.split(',')
    cursor,cnxn = Connect_SQL_Server(server,username,password,database)
    cursor.execute("select IDSensor,IDRegister from Register_Sensor where Topic=?",message.topic)
    v= cursor.fetchall()
    for i in range(0,len(v)):
      cursor.execute("insert into Value(IDSensor,IDRegister,Value,Timestamp) values (?,?,?,?)",v[i][0],v[i][1],c[0],c[2])
    cnxn.commit()


client.on_message = on_message
client.connect("localhost",1883)

for i in topics:
   client.subscribe(i[0])


client.loop_forever()






