<?php

header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");



function Connect_Sql_Server($servername, $dbname, $username, $password){


  $connectionInfo = array( "Database"=>$dbname, "UID"=>$username, "PWD"=>$password);
  $connection = sqlsrv_connect( $servername, $connectionInfo);
  //$connection = new mysqli('10.64.6.123','CapteursSoMel', 'Capteurs_2020!', 'Demonstrateur_Live_Tree_Database_test');$GLOBALS['servername'] = '10.64.6.103';

  /*
   try {
        $connection = new PDO(
            "sqlsrv:server=$servername;Database=$dbname",
            $username,
            $password,
            array(
                //PDO::ATTR_PERSISTENT => true,
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            )
        );
    }
    catch(PDOException $e) {
        echo "Error connecting to SQL Server: " . $e->getMessage() ."\n";
    }

    echo "Connected to SQL Server\n";


µ*/

  if( $connection ) {
             return ($connection);
                    }

  else {
	return NULL;
	}




}




function Get_Mac(){


$servername = '10.64.6.103';
$username = 'CapteursSoMel';
$password = 'Capteurs_2020!';
$dbname = 'Demonstrateur_Live_Tree_Database_test';


$conn = Connect_Sql_Server($servername, $dbname, $username, $password);

if(!$conn )
{
	//STATUS = 500 Internal Error
	return json_encode(array("message"=>"error connection", "arrayResponse"=>NULL));
}

else{

  $sql = "SELECT Mac_Address FROM Raspberry ";
  $result = sqlsrv_query($conn, $sql);

  while($row = sqlsrv_fetch_array($result, SQLSRV_FETCH_ASSOC)) {

        $data = $row['Mac_Address'];
	$Mac = $_GET['mac'];

        if( $data == 125) { //$_GET['mac']
                $arrayResponse = array('servername'=>$servername, 'username'=>$username, 'password'=>$password, 'dbname'=>$dbname);

		// STATUS = 200 OK
		return json_encode(array("message"=>"mac found", "arrayResponse"=>$arrayResponse));
                                               }
}
		// STATUS = 404 Not Found
               return json_encode(array("message"=>"mac not found", "arrayResponse"=>NULL));
     }

}

echo Get_Mac();







?>

