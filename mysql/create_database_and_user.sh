#!/bin/bash

# Author: Chris Powell
# Date: 8/21/2013
#
# Description: Script to create a new database and user account. 
# The useraccount will have fill administrative privileges on the 
# created dataase.
#

MYSQL="/usr/bin/mysql"
USER="root"
RAND_PASS=`cat /dev/urandom | tr -dc A-Za-z0-9 | head -c8`

function usage
{
    echo
    echo "$0 -u <username> -d <database_name>"
    echo
    echo -e "\tCreate a new database and user account for it."
    echo -e "\tIt will return a random password for the user."
    echo
    exit
}

if [ $# -eq 0 ]; then
    usage
    echo "You must provide a username and database."
    exit
fi

while getopts ":u:d:h" opt; do
    case $opt in
        u)
            DB_USER=$OPTARG
            ;;
        d)
            DB_NAME=$OPTARG
            ;;
        h)
            usage
            ;;
        \?)
            usage
            echo "Invalid option: -$OPTARG" >&2
            ;;
        :)
            usage
            echo "Option -$OPTARG requires an argument."
            ;;
    esac
done

if [ -z $DB_USER ] || [ -z $DB_NAME ]; then
    usage
    echo "You must provide a username and database."
    exit
fi

$MYSQL -u $USER -p -e "CREATE DATABASE $DB_NAME; GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%' IDENTIFIED BY '$RAND_PASS'"
if [ $? -ne 0 ]; then
    echo
    echo "There was a error, please execute the following commands from the CLI to debug:"
    echo
    echo "$MYSQL -u $USER -p -e \"CREATE DATABASE $DB_NAME\""
    echo "$MYSQL -u $USER -p -e \"GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%' IDENTIFIED BY '$RAND_PASS'\""
    echo
    exit
fi

echo
echo "Created database: $DB_NAME"
echo "Created user:     $DB_USER"
echo "User password:    $RAND_PASS"
echo


