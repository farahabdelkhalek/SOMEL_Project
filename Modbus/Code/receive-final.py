import paho.mqtt.client as mqtt
import time
import json
import pyodbc
import pytz
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from requests import ConnectionError




server = '10.64.6.103';
username = 'CapteursSoMel';
password = 'Capteurs_2020!';
database = 'Demonstrateur_Live_Tree_Database_test';




def Connect_SQL_Server(server,username,password,database):
   try:
      cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
      cursor = cnxn.cursor()
      return cursor,cnxn

   except ConnectionError:
      print ("Could Not Connect To MYSQL Server")



def on_message(client, userdata, message):
    print("Topic: " + message.topic)
    print("Message: " + message.payload.decode())
    cursor,cnxn = Connect_SQL_Server(server,username,password,database)
    b = message.payload.decode()
    b = message.payload.split(",")
    Timestamp_Init = datetime.utcnow()
    Timestamp_Init = Timestamp_Init.replace(tzinfo=pytz.utc)
    Timestamp_Init = Timestamp_Init.astimezone(pytz.timezone("Europe/Paris"))
    Timestamp_Init = Timestamp_Init.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("update Mesure set Final_Wireless=? where idMesure =?",Timestamp_Init,b[2])
    cnxn.commit()





cursor,cnxn = Connect_SQL_Server(server,username,password,database)
cursor.execute("Select Topic from Topics")
topics=cursor.fetchall()


client=mqtt.Client()
client.on_message = on_message
client.connect("10.64.253.10",1883)

for i in topics:
   client.subscribe("Final")
client.loop_forever()




