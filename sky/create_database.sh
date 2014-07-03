#!/bin/bash

# database name
db='mon_sky.db'

# delete the old one
if [ -e "$db" ]; then
    #rm -f $db
    echo 'There is an existing database!!. Please remove it first.'
    exit 1
fi

DATE=`date +%s`

# SQLITE Datatypes
# Each value stored in an SQLite database (or manipulated by the database engine)
# has one of the following storage classes:
#
#    NULL. The value is a NULL value.
#    INTEGER. The value is a signed integer, stored in 1, 2, 3, 4, 6, or 8 bytes depending on the magnitude of the value.
#    REAL. The value is a floating point value, stored as an 8-byte IEEE floating point number.
#    TEXT. The value is a text string, stored using the database encoding (UTF-8, UTF-16BE or UTF-16LE).
#    BLOB. The value is a blob of data, stored exactly as it was input.

sqlite3 $db "create table Transfers( 
    name TEXT,    
    src_agent TEXT,
    dest_agent TEXT,
    remote_start_time INT, 
    remote_end_time INT
);"

