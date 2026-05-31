import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

server = os.getenv("SQLSERVER_HOST", r"localhost\SQLEXPRESS")
database = os.getenv("SQLSERVER_DB", "QuanLyDatLichKham")
username = os.getenv("SQLSERVER_USER", "sa")
password = os.getenv("SQLSERVER_PASSWORD", "YourStrongPassword")

try:
    conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row.TABLE_NAME for row in cursor.fetchall()]
    
    print(f"Database: {database}")
    print(f"Tables found: {len(tables)}\n")
    
    for table in tables:
        print(f"Table: {table}")
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col.COLUMN_NAME} ({col.DATA_TYPE}, max_len: {col.CHARACTER_MAXIMUM_LENGTH}, nullable: {col.IS_NULLABLE})")
        print()
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
