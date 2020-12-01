import sys
import argparse
from bs4 import BeautifulSoup
import requests
import pandas as pd
from city_state import city_to_state_dict
import datetime
import json
import mysql.connector
from opencage.geocoder import OpenCageGeocode


def get_parameters():
    """
    This function gets the parameters needed for the web scraping to take place.
    :return:  the job name, city and state as titles.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('vars', nargs='*', type=str)
    args = " ".join(parser.parse_args().vars).split(",")
    if len(args) != 3:
        print("Incorrect number of parameters")
        sys.exit(1)
    job_name = args[0].strip().title()
    city = args[1].strip().title()
    state = args[2].strip().title()
    return job_name, city, state


def check_validity_location(city, state, places_dict):
    """
    This function makes sure the input data of the location is valid
    :param city: the city to do the query at.
    :param state: the state to do the query at.
    :param places_dict: a dictionary of all the main cities in the US.
    :return: nothing, but ends the program if the data is not valid.
    """
    states_abb = ["AK", "AL", "AR", "AS", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "GU", "HI", "IA", "ID", "IL",
                  "IN", "KS",
                  "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV",
                  "NY", "OH",
                  "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VI", "VT", "WA", "WI", "WV", "WY"]
    states_long = ["Alaska", "Alabama", "Arkansas", "American Samoa", "Arizona", "California", "Colorado",
                   "Connecticut",
                   "District of Columbia", "Delaware", "Florida", "Georgia", "Guam", "Hawaii", "Iowa", "Idaho",
                   "Illinois",
                   "Indiana", "Kansas", "Kentucky", "Louisiana", "Massachusetts", "Maryland", "Maine", "Michigan",
                   "Minnesota", "Missouri", "Mississippi", "Montana", "North Carolina", "North Dakota", "Nebraska",
                   "New Hampshire", "New Jersey", "New Mexico", "Nevada", "New York", "Ohio", "Oklahoma", "Oregon",
                   "Pennsylvania", "Puerto Rico", "Rhode Island", "South Carolina", "South Dakota", "Tennessee",
                   "Texas",
                   "Utah", "Virginia", "Virgin Islands", "Vermont", "Washington", "Wisconsin", "West Virginia",
                   "Wyoming"]
    zip_iterator = zip(states_abb, states_long)
    abb_dict = dict(zip_iterator)
    # Check if the state is a valid state name:
    if state.upper() not in states_abb and state not in states_long:
        print("Not a valid state name.")
        sys.exit(1)
    # Convert abbreviation state name to full stat name
    if state.upper() in states_abb:
        state = abb_dict[state.upper()]
    # Check if the city name is valid.
    if city not in places_dict.keys():
        print("This city doesn't exist in the USA.")
        sys.exit(1)
    # check if there is a match between city and state:
    if not places_dict[city] == state:
        print("City is not located in specific state.")
        sys.exit(1)


def check_validity_jobname(job_name):
    """
    This function makes sure the input job parameters are only data science type jobs.
    :param job_name: the input parameter
    :return: nothing, exits the program if the job name is not within the optional jobs list.
    """
    optional_jobs = ["data scientist", "data analyst", "data engineer", "statistician", "big data architect",
                     "senior data scientist"]
    if job_name.lower() not in optional_jobs:
        print("job name not acceptable.")
        sys.exit(1)


def monster_get_content(job, location):
    """
    This function gets a job title and a location, and returns a page content of the desired url in the monster website.
    The search gets up to 250 searches (the maximum amount of searches the page can display)
    """
    monster_site = 'https://www.monster.com/jobs/search'  # name of the site
    payload = {'q': job, 'where': location, 'page': '10'}  # parameters to insert the url in the request.
    page = requests.get(monster_site, params=payload)
    return page


def monster_get_salaries(city, state, job_name):
    """
    This function gets a job title and a location, and returns a page content of the desired url of salary tool in the
    monster website.
    """
    salaries_site = 'https://www.monster.com/salary/q-{}-l-{}-{}' \
        .format("-".join(job_name.lower().split()), "-".join(city.lower().split()), "-".join(state.lower().split()))
    return salaries_site


def get_salaries_page_data(salaries_site):
    """
    This function takes the page of the site with the salaries of the specific job in the specific city, and returns
    the job salaries in that city (10%, median, 90%) and also the median salary for the job national.
    """
    page = requests.get(salaries_site)
    soup = BeautifulSoup(page.text, 'html.parser')
    salaries = json.loads(soup.find('script').string)  # a section inside the html that contains the salaries data.
    # Salaries of the city that was searched in the search engine:
    prc90 = int(salaries["estimatedSalary"][0]["percentile90"])  # 90th percentile
    med = int(salaries["estimatedSalary"][0]["median"])  # median value
    prc10 = int(salaries["estimatedSalary"][0]["percentile10"])  # 10th percentile
    national = int([item.get_text() for item in soup.select("td.jsx-944507022")][-3].replace("$", "").replace(",", ""))
    # the national mean salary in the field.
    return prc90, med, prc10, national


def get_jobs_page_data(page):
    """
    This function takes the page of the site with the specific job and place and name, and output a list of lists where
    each list contains the name of the job offer company, specific location and title.
    """
    soup = BeautifulSoup(page.text, 'html.parser')
    jobs = soup.find_all('section', class_="card-content")  # Searching all the card contents of jobs
    jobs_output = []
    present_time = datetime.datetime.now()
    for job in jobs:
        if job.find('div', class_='company') is not None:
            cur_results = []
            cur_results.append(job.find('div', class_='company').span.text.replace("\n", "").replace("\r", ""))
            cur_results.append(job.find('div', class_='location').span.text.replace("\n", "").replace("\r", ""))
            cur_results.append(job.div.h2.a.text.replace("\r", "").replace("\n", "").replace("\r", ""))
            date_str = job.find('div', class_='meta flex-col').time.text.replace("\n", "").replace("\r", "")
            if date_str == "Posted today":
                posted_time = datetime.datetime.now().isoformat().split("T")[0]
            else:
                posted_time = (present_time - datetime.timedelta(int(date_str.split(" ")[0]))).isoformat()
            cur_results.append(posted_time.split("T")[0])
            jobs_output.append(cur_results)
    return jobs_output


def get_lat_lon(place):
    key = "3fca2a04b0d44770bf76fdd15c56e628"
    geocoder = OpenCageGeocode(key)
    query = place
    results = geocoder.geocode(query)
    lat = results[0]['geometry']['lat']
    lng = results[0]['geometry']['lng']
    return lat, lng


def update_mysql_tables(host_name, user_name, user_password, db_name, jobs_output, job_name, place, lat, lon, prc90, med, prc10, national):
    """

    :param host_name: (of the mysql account).
    :param user_name: (of the mysql account).
    :param user_password: (of the mysql account).
    :param db_name: the database to load onto the data.
    :param jobs_output: a nested list of the scraped data.
    :param job_name: the job name as appeared in the search.
    :return: Nothing.
    """
    connection = None
    try:
        connection = mysql.connector.connect(host=host_name,
                                             database=db_name,
                                             user=user_name,
                                             password=user_password)
        cursor = connection.cursor()
        # adding values to titles table:
        mysql_insert_query1 = """INSERT IGNORE INTO titles (title) 
                                VALUES (%s)"""  # Update auto increment on location id?
        recordtuple1 = (job_name,)
        cursor.execute(mysql_insert_query1, recordtuple1)
        title_id = cursor.lastrowid
        # adding values to location table:
        mysql_insert_query2 = """INSERT IGNORE INTO location (location_name, latitude, longitude) 
                                VALUES (%s, %s, %s)"""  # Update auto increment on location id?
        recordtuple2 = (place, lat, lon)
        cursor.execute(mysql_insert_query2, recordtuple2)
        location_id = cursor.lastrowid
        # adding values to national_salaries table:
        mysql_insert_query3 = """INSERT IGNORE INTO national_salaries (title_id, national_median_salary) 
                                VALUES (%s, %s)"""  # Update auto increment on location id?
        recordtuple3 = (title_id, national)
        cursor.execute(mysql_insert_query3, recordtuple3)
        # adding values to national_salaries table:
        mysql_insert_query4 = """INSERT IGNORE INTO regional_salaries (title_id, location_id, area_median_salary, area_ninety_salary, area_tenth_salary) 
                                VALUES (%s,%s,%s,%s,%s)"""  # Update auto increment on location id?
        recordtuple4 = (title_id, location_id, med, prc90, prc10)
        cursor.execute(mysql_insert_query4, recordtuple4)
        for line in jobs_output:
            # adding values to open_positions table:
            mysql_insert_query5 = """INSERT IGNORE INTO open_positions (title_id, location_id, job_description, company_name, date_posted) 
                                    VALUES (%s, %s, %s, %s, %s)"""  # Update auto increment on location id?
            recordtuple3 = (title_id, location_id, line[2], line[0], line[3])
            cursor.execute(mysql_insert_query5, recordtuple3)
        connection.commit()
        print("Record inserted successfully into table")

    except mysql.connector.Error as error:
        print("Failed to insert into MySQL table {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


def export_data_to_csv(jobs_output, job_name, place):
    """
    This function creates a directory and places in it a csv file with the data regarding all the jobs in the query.
    """
    jobs_pd = pd.DataFrame(jobs_output, columns=["Name", "Location", "Title", "Time Applied"])
    jobs_pd.to_csv("output_data_" + job_name + "_" + place + ".csv")


def main():
    job_name, city, state = get_parameters()  # gets the parameters from the CLI.
    check_validity_location(city, state, city_to_state_dict)  # Verifying data is suitable.
    check_validity_jobname(job_name)  # checks if the job is within the list of jobs allowed.
    place = city + ", " + state
    lat, lon = get_lat_lon(place)  # get latitude and longitude of the place being searched.
    salaries_site = monster_get_salaries(city, state, job_name)  # Getting salaries url.
    prc90, med, prc10, national = get_salaries_page_data(
        salaries_site)  # Getting salaries stats in the city and the US.
    page = monster_get_content(job_name, place)  # Using the function on the monster URL.
    jobs_output = get_jobs_page_data(page)  # creating a list of all the retrieved data
    # loading data to tables:
    update_mysql_tables("localhost", "eyal88", 'Barak2020!', 'mining', jobs_output, job_name, place, lat, lon, prc90, med, prc10, national)
    # export_data_to_csv(jobs_output, job_name, place)  # Exporting the data to csv file.


if __name__ == '__main__':
    main()

