#!/usr/bin/env python
# encoding: utf-8
"""
generate_keys.py

Generate CSRF and Session keys, output to secret_keys.py file

Usage:
    generate_keys.py [-f]

Outputs secret_keys.py file in current folder

By default, an existing secret_keys file will not be replaced.
Use the '-f' flag to force the new keys to be written to the file


"""
import sys
import time
import string
import os.path
import hashlib
import base64
import MySQLdb
import config
from optparse import OptionParser
from random import choice
from string import Template
import warnings
warnings.filterwarnings('ignore')
# File settings
file_name = 'secret_keys.py'
file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), file_name)

file_template = Template('''# CSRF- and Session keys

CSRF_SECRET_KEY = '$csrf_key'
SESSION_KEY = '$session_key'
POST_KEY = '!@#123abcABC'
''')


# Get options from command line
parser = OptionParser()
parser.add_option(
    "-f",
    "--force",
    dest="force",
    help="force overwrite of existing secret_keys file",
    action="store_true")
parser.add_option(
    "-r",
    "--randomness",
    dest="randomness",
    help="length (randomness) of generated key; default = 24",
    default=24)
(options, args) = parser.parse_args()


def generate_randomkey(length):
    """Generate random key, given a number of characters"""
    chars = string.letters + string.digits
    return ''.join([choice(chars) for i in range(length)])


def write_file(contents):
    with open(file_path, 'wb') as f:
        f.write(contents)


def generate_keyfile(csrf_key, session_key):
    """Generate random keys for CSRF- and session key"""
    output = file_template.safe_substitute(dict(
        csrf_key=csrf_key, session_key=session_key
    ))
    if os.path.exists(file_path):
        if options.force is None:
            print("Warning: secret_keys.py file exists."
                  "Use 'generate_keys.py --force' to force overwrite.")
        else:
            write_file(output)
    else:
        write_file(output)


def generate_key():
    r = options.randomness
    csrf_key = generate_randomkey(r)
    session_key = generate_randomkey(r)
    generate_keyfile(csrf_key, session_key)

db = MySQLdb.connect(
    host=config.mysqlhost,
    user=config.username,
    passwd=config.password,
    port=config.port,
    db=config.database)


def get_user(username):
    conn = db.cursor()
    conn.execute("select * from user where username='"+username+"';")
    return conn.fetchall()


def create_user(username, password):
    # Create the table first if not exists
    conn = db.cursor()
    conn.execute("""
        create table if not exists user
                 (username varchar(20),
                 password varchar(256),
                 salt varchar(20),
                 config text,
                 primary key (username));
                 """)
    users = get_user(username)
    if len(users) > 0:
        print("user already exists")
        return
    sha512 = hashlib.sha512()
    salt = str(int(time.time()))
    sha512.update(salt.encode("utf8"))
    sha512.update(password.encode("utf8"))
    hashed_password = base64.urlsafe_b64encode(sha512.digest()).decode("utf8")

    conn = db.cursor()
    conn.execute(
        """insert into user (username, password, salt) values
        ('{username}','{password}','{salt}');""".format(
            username=username,
            password=hashed_password,
            salt=salt)
    )
    db.commit()
    print("create user Done")


def delete_user(username):
    conn = db.cursor()
    conn.execute(
        "delete from user where username='{username}';"
        .format(username=username))
    db.commit()
    print("delete user Done")


def backup_blog():
    """backup blog to uploads folder"""
    from app import app, register_manage_command
    app = register_manage_command(app)
    # open a context so as to invoke database model
    app.cli_backup_blog()

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2 and args[1] == "generatekey":
        generate_key()
    elif len(args) == 3 and args[1] == "deleteuser":
        username = args[2]
        delete_user(username)
    elif len(args) == 4 and args[1] == "createuser":
        username = args[2]
        password = args[3]
        create_user(username, password)
    elif len(args) == 2 and args[1] == "backup":
        backup_blog()
        pass
    else:
        print("""
        Run this script to create user and generate session_key
        useage:
            manage.py createuser <username> <password>
            manage.py deleteuser <username>
            manage.py generatekey
            manage.py backup
              """)
