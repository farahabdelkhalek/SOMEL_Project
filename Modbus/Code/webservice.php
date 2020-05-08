<?php
include 'connect.php';

header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");



function Get_Mac(){

$conn = Connect_Sql_Server();

if(!$conn )
{
	//STATUS = 500 Internal Error
	return json_encode(array("message"=>"error connection", "arrayResponse"=>NULL));
}

else{

 $sql = "SELECT Mac_Address FROM Raspberry where Mac_Address='".$_GET['mac']."'";
 $result = sqlsrv_query($conn, $sql);

  $row = sqlsrv_fetch($result);

  if( $row != NULL) {
                $arrayResponse = array('servername'=>servername, 'username'=>username, 'password'=>password, 'dbname'=>dbname);

		// STATUS = 200 OK
		return json_encode(array("message"=>"mac found", "arrayResponse"=>$arrayResponse));
		   }
  else
		// STATUS = 404 Not Found
               return json_encode(array("message"=>"mac not found", "arrayResponse"=>NULL));

}
}

echo Get_Mac();







?>

