<?php

/* vim: set expandtab tabstop=4 shiftwidth=4 */

/**
* update_user.php
*
* Script to update a user's password. The script requires 
* that the apache service has sudo permission to excute
* the usermod command.
*
* @author     Chris Powell <cpowell@avail-tvn.com>
* @version    v1.1
*/

function shadow ($input){
    // Hashes the password MD5 style for Unix shadow file
    $s = null;
    for ($n = 0; $n < 9; $n++){
        $s .= chr(rand(64,126));
    }
    $seed =  "$1$".$s."$";
    $return = crypt($input,$seed);
    return $return;
}

function userExists($username) {                                                                                      
    // Returns true if the user account already exists
    $lines = file("/etc/passwd");
    foreach ($lines as $line) {
        $fields = explode(":", $line);
        if ($fields[0] == $username) {
            return true;
        }
    }
    return false;
}

function approvedUser($username) {
    // Ensures that it is an approved user account
    $lines = file("/etc/passwd");
    foreach ($lines as $line) {
        $fields = explode(":",$line);
        if (($fields[0] == $username) && ($fields[2] >= 1000)) {
            return true;
        }
    }
    return false;
}

function respond($result, $errorMessage = "") {                                                                       
    // xml response
    // result: 'ok' or 'error'
    // error_message: if error
    header("Content-type: text/xml");
    echo "<?xml version='1.0' encoding='ISO-8859-1'?>";
    echo "<userRequest>";
    echo "<result>$result</result>";
    echo "<error_message>$errorMessage</error_message>";
    echo "</userRequest>";
}

function resetPassword($username, $password) {
    // resets the given user's password
    $hash = shadow($password);
    $cmd = "sudo /usr/sbin/usermod -p '$hash' $username 2>&1";
    exec($cmd, $output, $return);

    if ($return != 0) {
        $error = "Password rest failed. $output[0]";
        syslog(LOG_CRIT, $message . $error);
        respond("error", $error);
        exit();
    }
}

// Only act on POST requests
if ($_POST) {

    // syslog facility
    openlog("update_user.php", 0, LOG_LOCAL0);
    $message = "{$_SERVER['REMOTE_ADDR']}: ";

    // Ensure that only apache is running the script
    if(trim(shell_exec('whoami')) != 'apache') {
        $error =  "Unauthorized account executing script.";
        syslog(LOG_CRIT, $message . $error);
        respond("error", $error); 
        exit();
    }

    // Ensure that in the POST var usrname is set
    if (!isset($_POST['username']) or empty($_POST['username']))
    {
        $error =  "Invalid POST request. Username field empty or missing.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
        exit();
    }

    // Ensure that password is set and valid
    if (!isset($_POST['password']) or empty($_POST['password'])) {
        $error =  "Invalid POST request. Password field empty or missing.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
        exit();
    }

    $username = $_POST['username']; 
    $pass = $_POST['password'];

    if (!userExists($username)) {
        $error =  "Username: $username, was not found.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
        exit();
    }

    // only change approved user accounts
    if (approvedUser($username)) {
        resetPassword($username, $pass);
        respond("ok");
        syslog(LOG_INFO, $message . "$username: password change sucessful.");
    }
    else {
        $error =  "The $username account may not be reset.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
    }

    closelog();

}
?>
