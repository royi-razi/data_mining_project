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


create_titles_table = """
CREATE TABLE titles (
  title_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(20) UNIQUE
  );
 """

create_location_table = """
CREATE TABLE location (
  location_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  location_name VARCHAR(50) NOT NULL UNIQUE,
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6)
  );
 """

create_open_positions_table = """
CREATE TABLE open_positions (
  open_position_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title_id MEDIUMINT,
  location_id MEDIUMINT,
  job_description VARCHAR(40),
  company_name VARCHAR(20) NOT NULL,
  date_posted  DATETIME,
  CONSTRAINT fk_open_location_id
  FOREIGN KEY (location_id)
  REFERENCES location(location_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_open_title_id
    FOREIGN KEY (title_id)
    REFERENCES titles(title_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """

create_national_salaries_table = """
CREATE TABLE national_salaries (
  national_salary_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title_id MEDIUMINT NOT NULL,
  national_median_salary int,
  CONSTRAINT fk_national_title_id
    FOREIGN KEY (title_id)
    REFERENCES titles(title_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """

create_regional_job_salaries_table = """
CREATE TABLE regional_salaries (
  regional_salary_id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title_id MEDIUMINT,
  location_id MEDIUMINT,
  area_median_salary int,
  area_ninety_salary int,
  area_tenth_salary int,
  CONSTRAINT fk_regional_title_id
    FOREIGN KEY (title_id)
    REFERENCES titles(title_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_regional_location_id
    FOREIGN KEY (location_id)
    REFERENCES location(location_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=INNODB;
 """


connection = create_db_connection("localhost", "root", 'HelloWorld!', 'mining')  # Connect to the Database
execute_query(connection, create_titles_table)  # Execute defined query
execute_query(connection, create_location_table)
execute_query(connection, create_national_salaries_table)
execute_query(connection, create_regional_job_salaries_table)
execute_query(connection, create_open_positions_table)


