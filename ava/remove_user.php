<?php

/* vim: set expandtab tabstop=4 shiftwidth=4 */

/**
* remove_user.php
*
* Script to remove a user account. The script requires 
* that the apache service has sudo permission to excute
* the userdel command.
*
* @author     Chris Powell <cpowell@avail-tvn.com>
* @version    v1.1
*/

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

function removeUser($username) {
    // removes the give user account from the system
    $cmd = "sudo /usr/sbin/userdel -r $username 2>&1";
    exec($cmd, $output, $return);

    if ($return != 0) {
        $error = "User account removal failed: $output[0]";
        syslog(LOG_CRIT, $message . $error);
        respond("error", $error);
        exit();
    }
}

// Act on POST requests
if ($_POST) {

    // syslog facility
    openlog("remove_user.php", 0, LOG_LOCAL0);
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

    $username = $_POST['username'];

    // Check if the user exists
    if (!userExists($username)) {
        $error =  "The user '$username' not found.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
        exit();
    }

    // only remove approved user accounts
    if (approvedUser($username)) {
        removeUser($username);
        syslog(LOG_INFO, $message . "The $username account was removed.");
        respond("ok");
    }
    else {
        $error =  "The $username account may not be removed.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
    }

    closelog();
}

?>
