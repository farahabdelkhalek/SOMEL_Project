import paho.mqtt.client as mqtt
import time
import json
import pyodbc
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from send import Connect_SQL_Server,Get_Mac
import requests


def on_message(client, userdata, message):
    print("Topic: " + message.topic)
    print("Message: " + message.payload.decode("utf-8"))
    b= message.payload.decode("utf-8")
    #c=b.split(',')
    cursor,cnxn = Connect_SQL_Server(server,username,password,database)
    cursor.execute("select idSensor from Topics where Topic=?",message.topic)
    sensor=cursor.fetchone()[0]
    cursor.execute("select Raspberry.idRaspberry from Raspberry,Sensor where Raspberry.idRaspberry = Sensor.idSensor and Sensor.idSensor = ?",sensor)
    raspberry = cursor.fetchone()[0]
    cursor.execute("select idTopic from Topics where Topic = ?",message.topic)
    topic = cursor.fetchone()[0]
    cursor.execute("insert into Mesure(Mesure,idRaspberry,idTopic) values (?,?,?)",b,raspberry,topic)
    cnxn.commit()





Mac = Get_Mac()
response = requests.get(url = "http://localhost:80/webservice.php?mac="+Mac)
try:
    jsonResponse = json.loads(response.text)
    arrayResponse = jsonResponse["arrayResponse"]

    if (arrayResponse is not None):

       server,username,password,database = arrayResponse["servername"], arrayResponse["username"], arrayResponse["password"], arrayResponse["dbname"]
       cursor,cnxn = Connect_SQL_Server(server,username,password,database)
       cursor.execute("Select Topic from Topics")
       topics=cursor.fetchall()
       client=mqtt.Client()
       client.on_message = on_message
       client.connect("localhost",1883)

       for i in topics:
          client.subscribe(i[0])
       client.loop_forever()

except ValueError:
        print("No JSON returned")






