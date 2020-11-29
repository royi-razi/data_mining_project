import mysql.connector
from mysql.connector import Error
import pandas as pd


def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")


create_open_positions_table = """
CREATE TABLE open_positions (
  op_id INT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  company_name VARCHAR(20) NOT NULL,
  time_posted  DATETIME,
  loc_description VARCHAR(30)
  );
 """

connection = create_db_connection("localhost", "root", 'HelloWorld!', 'mining')  # Connect to the Database
execute_query(connection, create_open_positions_table)  # Execute defined query


create_title_locations_table = """
CREATE TABLE title_location (
  id INT PRIMARY KEY,
  job_description VARCHAR(20) NOT NULL,
  location_id int
  );
 """

create_location_table = """
CREATE TABLE location (
  location_id INT PRIMARY KEY,
  location_name VARCHAR(20) NOT NULL,
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6)
  );
 """

create_job_salaries_table = """
CREATE TABLE job_salaries (
  id INT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  location_id INT,
  area_median_salary int
  );
 """

create_national_job_salaries_table = """
CREATE TABLE national_job_salaries (
  id INT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  national_median_salary int
  );
 """

create_job_names_table = """
CREATE TABLE job_names (
  id INT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL
  );
 """


alter_title_location = """
ALTER TABLE title_location
ADD FOREIGN KEY(location_id)
REFERENCES location(location_id)
ON DELETE SET CASCADE;
"""

alter_job_salaries = """
ALTER TABLE job_salaries
ADD FOREIGN KEY(location_id)
REFERENCES location(location_id)
ON DELETE SET NULL;
"""

alter_title_location_job_des = """
ALTER TABLE title_location
ADD FOREIGN KEY(job_description)
REFERENCES open_positions(job_description)
ON DELETE SET null;
"""

alter_job_salaries_job_name = """
ALTER TABLE job_salaries
ADD FOREIGN KEY(job_name)
REFERENCES job_names(job_name)
ON DELETE SET null;
"""

alter_national_job_salaries_job_name = """
ALTER TABLE national_job_salaries
ADD FOREIGN KEY(job_name)
REFERENCES job_names(job_name)
ON DELETE SET null;
"""

alter_open_positions_job_name = """
ALTER TABLE open_positions
ADD FOREIGN KEY(job_name)
REFERENCES job_names(job_name)
ON DELETE SET null;
"""


connection = create_db_connection("localhost", "root", 'HelloWorld!', 'mining')  # Connect to the Database
execute_query(connection, create_title_locations_table)  # Execute defined query
execute_query(connection, create_location_table)
execute_query(connection, create_job_salaries_table)
execute_query(connection, create_national_job_salaries_table)
execute_query(connection, create_job_names_table)
execute_query(connection, alter_title_location)
# execute_query(connection, alter_job_salaries)
# execute_query(connection, alter_title_location_job_des)
# execute_query(connection, alter_job_salaries_job_name)
# execute_query(connection, alter_national_job_salaries_job_name)
# execute_query(connection, alter_open_positions_job_name)

