<?php

include 'connect.php';

header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");



function Get_Mac(){
	$conn = Connect_Sql_Server();
	if(!$conn)
	{
		//STATUS = 500 Internal Error
		return json_encode(array("message"=>"error connection", "arrayResponse"=>NULL));
	}


	else
	{
		$sql = "SELECT Mac_Address FROM Raspberry where Mac_Address='0242ac130002'";
		// $sql = "SELECT Mac_Address FROM Raspberry where Mac_Address='".$_GET['mac']."'";
 		$result = sqlsrv_query($conn, $sql); $row = sqlsrv_fetch($result);
		$arrayRegisters=array();
		$arraySensorstemp=array();
		$arraySensors=array();

		if( $row != NULL) {
			$IDRasp = Get_RaspberryID();
			$IDMesure = Get_IDMesure();
        		$Sensors = Get_Sensor();

			if($Sensors != NULL){
				$Sensor_Val = array_values($Sensors);

				for($i=0;$i<sizeof($Sensor_Val);$i++){
					$IP = Get_IP($Sensor_Val[$i]);
					$Registers = Get_Register($Sensor_Val[$i]);
					$SensorAddress = Get_SensorAddr($Sensor_Val[$i]);

					for($j=0;$j<sizeof($Registers);$j++){
                        			$Registers_Val = array_values($Registers);
						$Length = Get_Length($Registers_Val[$j]);
						$RegisterAddress = Get_Register_Addr($Registers_Val[$j]);
						$Type = Get_Type($Registers_Val[$j]);
						$Topic = Get_Topic($Sensor_Val[$i],$Registers_Val[$j]);
						$Periode = Get_PullingPeriod($Registers_Val[$j]);


		$arrayReg = array('ID'=>$Registers_Val[$j], 'Length'=>$Length,'Type'=>$Type,'RegisterAddress'=>$RegisterAddress,'Topic'=>$Topic,'Period'=>$Periode);
		array_push($arrayRegisters,$arrayReg);
		$arrayReg=array(); $arraySensor = array('IP'=>$IP, 'SensorAddress'=>$SensorAddress,'Registers'=>$arrayRegisters);
					}
		$arrayRegisters=array();
 		$arraySensorstemp = array("IDSensor"=>$Sensor_Val[$i],"info"=>$arraySensor);
		array_push($arraySensors,$arraySensorstemp);
		$arraySensor=array();
		$arraySensortemp=array();
				}
		$arrayResponse = array("IDRaspberry"=>$IDRasp,"IDMesure"=>$IDMesure, "Sensors"=>$arraySensors);
		// STATUS = 200 OK
		return json_encode(array("message"=>"mac found", "arrayResponse"=>$arrayResponse));
		   }
	else return json_encode(array("message"=>"no sensors found", "arrayResponse"=>NULL));
}
else
		// STATUS = 404 Not Found
               return json_encode(array("message"=>"mac not found", "arrayResponse"=>NULL));
}
}




function Get_PullingPeriod($register){
	$conn = Connect_Sql_Server();
	$sql = ("select Periode.Periode from Periode,Register where Register.idPeriode = Periode.idPeriode and Register.idRegister=".+$register);
	$result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array($result,SQLSRV_FETCH_ASSOC);
        return $row['Periode'];

}



function Get_IDMesure(){
	$conn = Connect_Sql_Server();
	$sql = "select count(*) as IDMesure from Mesure";
	$result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array($result,SQLSRV_FETCH_ASSOC);
	return $row['IDMesure'];

}

function Get_RaspberryID(){
	$conn = Connect_Sql_Server();
//	$sql = "SELECT idRaspberry FROM Raspberry where Mac_Address='".$_GET['mac']."'";
	$sql = "SELECT idRaspberry FROM Raspberry where Mac_Address='0242ac130002'";
	$result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array($result,SQLSRV_FETCH_ASSOC);
	return $row['idRaspberry'];
}



function Get_Sensor(){
	$conn = Connect_Sql_Server();
	// $sql = "SELECT Sensor.idSensor FROM Sensor,Raspberry where Sensor.idRaspberry=Raspberry.idRaspberry and Raspberry.Mac_Address='".$_GET['mac']."'";
 	$sql = "SELECT Sensor.idSensor FROM Sensor,Raspberry where Sensor.idRaspberry=Raspberry.idRaspberry and Raspberry.Mac_Address='0242ac130002'";
	$result = sqlsrv_query($conn, $sql);
 	$a=array();
  	while($row = sqlsrv_fetch_array( $result, SQLSRV_FETCH_ASSOC)){
		array_push($a,$row['idSensor']);
	}
 	return $a;
}


function Get_SensorAddr($SensorID){
	$conn = Connect_Sql_Server();
	$sql = ("SELECT Address FROM Sensor WHERE idSensor=".+$SensorID);
	$result = sqlsrv_query($conn,$sql);
	$row = sqlsrv_fetch_array($result,SQLSRV_FETCH_ASSOC);
	return $row['Address'];
}


function Get_IP($sensor){
	$conn = Connect_Sql_Server();
	$sql = ("select IPAddress.IP_Address from Sensor,IPAddress where Sensor.ID_IPAddress = IPAddress.ID_IPAddress and Sensor.idSensor=".+$sensor);
	$result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array( $result, SQLSRV_FETCH_ASSOC);
	return $row['IP_Address'];
}



function Get_Register($sensor) {
	$conn = Connect_Sql_Server();
	$register=array();
	$sql = ("SELECT Register.idRegister FROM Register,Sensor,Topics WHERE Register.idRegister=Topics.idRegister and Sensor.IDSensor=Topics.idSensor and Sensor.idSensor=".+$sensor);
	$result = sqlsrv_query($conn , $sql);
	while($row = sqlsrv_fetch_array( $result, SQLSRV_FETCH_ASSOC)){
		array_push($register,$row['idRegister']);
	}
      return ($register);
}



function Get_Register_Addr($register) {
	$conn = Connect_Sql_Server();
	$sql = ("SELECT Register.Register FROM Register WHERE Register.idRegister=".+$register);
	$result = sqlsrv_query($conn , $sql);
	$row = sqlsrv_fetch_array( $result, SQLSRV_FETCH_ASSOC);
	return ($row['Register']);
}



function Get_Length($register){
	$conn = Connect_Sql_Server();
	$sql = ("SELECT RegisterCount FROM Register WHERE idRegister=".+$register);
	$result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array($result, SQLSRV_FETCH_ASSOC);
	return ($row['RegisterCount']);
}


function Get_Type($register){
	$conn = Connect_Sql_Server();
	$sql = ("select Register.IDType from Register,TypeRegister where Register.IDType = TypeRegister.idTypeRegister and Register.idRegister =".+$register);
	$result = sqlsrv_query($conn,$sql);
	$row = sqlsrv_fetch_array($result,SQLSRV_FETCH_ASSOC);
	return ($row['IDType']);
}



function Get_Topic($sensor,$register){
	$conn = Connect_Sql_Server();
	$sql = ("select Topic from Topics,Sensor,Register where Sensor.IDSensor=Topics.idSensor and Register.IDRegister=Topics.idRegister and Sensor.IDSensor=".+$sensor ."and Register.IDRegister=".+$register); $result = sqlsrv_query($conn, $sql);
	$row = sqlsrv_fetch_array($result , SQLSRV_FETCH_ASSOC);
	return ($row['Topic']);
}

echo Get_Mac();

?>
