/* This file is used in order to establish a connection with the database running on the server side.
The servername, username, password, dbname are predefined. */


<?php


define("servername",'10.64.6.103');
define("username" ,'CapteursSoMel');
define("password",'Capteurs_2020!');
define("dbname" ,'Demonstrateur_Live_Tree_Database_test');




function Connect_Sql_Server(){


  $connectionInfo = array( "Database"=>dbname, "UID"=>username, "PWD"=>password);
  $connection = sqlsrv_connect( servername, $connectionInfo);
  if( $connection ) {
             return ($connection);
                    }

  else {
        return NULL;
        }

}


?>