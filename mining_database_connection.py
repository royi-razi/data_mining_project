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


create_job_names_table = """
CREATE TABLE job_names (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  job_name VARCHAR(20) UNIQUE
  );
 """

create_location_table = """
CREATE TABLE location (
  location_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  location_name VARCHAR(20) NOT NULL,
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6)
  );
 """

create_open_positions_table = """
CREATE TABLE open_positions (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  job_description VARCHAR(20) UNIQUE,
  company_name VARCHAR(20) NOT NULL,
  time_posted  DATETIME,
  loc_description VARCHAR(30),
  CONSTRAINT fk_job_names
  FOREIGN KEY (job_name)
  REFERENCES job_names(job_name)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """

create_title_locations_table = """
CREATE TABLE title_location (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  job_description VARCHAR(20) NOT NULL,
  location_id MEDIUMINT NOT NULL,
  CONSTRAINT fk_open_positions_job_description
    FOREIGN KEY (job_description)
    REFERENCES open_positions(job_description)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_location_id
    FOREIGN KEY (location_id)
    REFERENCES location(location_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """

create_national_job_salaries_table = """
CREATE TABLE national_job_salaries (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  national_median_salary int,
  CONSTRAINT fk_job_names_job_name
    FOREIGN KEY (job_name)
    REFERENCES job_names(job_name)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """

create_job_salaries_table = """
CREATE TABLE job_salaries (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  job_name VARCHAR(20) NOT NULL,
  location_id MEDIUMINT,
  area_median_salary int,
  CONSTRAINT fk_job_names_salaries
    FOREIGN KEY (job_name)
    REFERENCES job_names(job_name)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_location_location_id
    FOREIGN KEY (location_id)
    REFERENCES location(location_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """


connection = create_db_connection("localhost", "root", 'HelloWorld!', 'mining')  # Connect to the Database
execute_query(connection, create_job_names_table)  # Execute defined query
execute_query(connection, create_open_positions_table)
execute_query(connection, create_title_locations_table)
execute_query(connection, create_location_table)
execute_query(connection, create_job_salaries_table)
execute_query(connection, create_national_job_salaries_table)


