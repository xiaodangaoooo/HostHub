import mysql.connector
from flask import g, current_app
from config import Config
import os

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB']
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database by creating all tables."""
    db = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )
    cursor = db.cursor()
    
    # First create the database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
    cursor.execute(f"USE {Config.MYSQL_DB}")
    
    # Get the absolute path to schema.sql
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              'database', 'schema.sql')
    
    # Read and execute schema.sql
    with open(schema_path, 'r') as f:
        # Split the file into individual statements
        statements = f.read().split(';')
        
        for statement in statements:
            # Skip empty statements
            if statement.strip():
                cursor.execute(statement)
    
    db.commit()
    cursor.close()
    db.close()

def test_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("select database();")
            database_name = cursor.fetchone()
            print("Connected to MySQL Server version", db_info)
            print("You're connected to database:", database_name[0])
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
            return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False