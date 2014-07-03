<?php

/* vim: set expandtab tabstop=4 shiftwidth=4 */

/**
* add_user.php
*
* The script is used to add users to the server. You can call
* it with a POST call with the username and password for the account. 
* The script requires that the web server have permissions 
* to call /user/sbin/useradd and that php exec is callable.
*
* @author     Chris Powell <cpowell@avail-tvn.com>
* @version    v1.7
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

function createPassword() {
    // Creates a random 8 character password.
    $chars = "abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ023456789";
    srand((double)microtime()*1000000);
    $i = 0;
    $pass = '' ;
    while ($i <= 7) {
        $num = rand() % strlen($chars);
        $tmp = substr($chars, $num, 1);
        $pass = $pass . $tmp;
        $i++;
    }
    return $pass;
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

function createUser($username, $pass, $affiliate) {
    // create the ftp user
    $hash = shadow($pass);
    $cmd = "sudo /usr/sbin/useradd -N -m -s /bin/ftponly -c '$affiliate ftp account.' -p '$hash' $username 2>&1";
    exec($cmd, $output, $return);

    if ($return != 0) {
        $error = "User account creation failed: $output[0]";
        syslog(LOG_CRIT, $message . $error);
        respond("error", $error);
        exit();
    }
}

function userExists($username) {
    // Returns true if the user account already exists
    $lines = file("/etc/passwd");
    foreach ($lines as $line) {
        $fields = explode(":",$line);
        if ($fields[0] == $username) {
            return true;
        }
    }
    return false;
}

// Only act on POST requests
if ($_POST) {

    // syslog facility
    openlog("add_user.php", 0, LOG_LOCAL0);
    $message = "{$_SERVER['REMOTE_ADDR']}: ";

    // Ensure that only apache is running the script
    if(trim(shell_exec('whoami'))!='apache') {
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

    // if affiliate set it else use username
    if (!empty($_POST['affiliate'])) {
        $affiliate = $_POST['affiliate'];
    }
    else {
        $affiliate = $username;
    }

    // Check if the user already exists
    if (userExists($username)) {
        $error =  "The user '$username' already exists.";
        syslog(LOG_WARNING, $message . $error);
        respond("error", $error); 
        exit();
    }
    // Gentoo only let you use lowercase chars for user accounts
    if (strtolower($username) != $username) {
        respond("error", "The username must be all lowercase characters.");
        exit();
    }  

    // Attempt to create the user
    createUser($username, $pass, $affiliate);
    respond("ok");
    syslog(LOG_INFO, $message . "$username account created.");

    closelog();
}

?>
