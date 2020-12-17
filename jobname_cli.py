import sys
import argparse
from bs4 import BeautifulSoup
import requests
from city_state import city_to_state_dict, states_abb, states_long
import datetime
import mysql.connector
from geopy.geocoders import Nominatim
from selenium import webdriver
import os
from urllib.request import urlopen
import json
import logging

formatter = logging.Formatter('%(asctime)s-%(levelname)s-FILE:%(filename)s-FUNC:%(funcName)s-LINE:'
                              '%(lineno)d-%(message)s')


def setup_logger(name, log_file, level='INFO'):
    """
    the function sets up loggers.
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)

    return log


logger = setup_logger('info_logger', 'stout.log')
error_logger = setup_logger('error_logger', 'errors.log')
error_logger.error('error message: ')


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


def check_validity_location(city, state, places_dict, states_abb, states_long):
    """
    This function makes sure the input data of the location is valid
    :param city: the city to do the query at.
    :param state: the state to do the query at.
    :param places_dict: a dictionary of all the main cities in the US.
    :return: nothing, but ends the program if the data is not valid.
    """
    zip_iterator = zip(states_abb, states_long)
    abb_dict = dict(zip_iterator)
    # Check if the state is a valid state name:
    if state.upper() not in states_abb and state not in states_long:
        print("Not a valid state name.")
        error_logger.error("Wrong State! Not a valid state name.")
        sys.exit(1)
    # Convert abbreviation state name to full stat name
    if state.upper() in states_abb:
        state = abb_dict[state.upper()]
    # Check if the city name is valid.
    if city not in places_dict.keys():
        print("This city doesn't exist in the USA.")
        error_logger.error("Wrong city! This city doesn't exist in the USA.")
        sys.exit(1)
    # check if there is a match between city and state:
    if not places_dict[city] == state:
        print("City is not located in specific state.")
        error_logger.error("Wrong city or state! There is no matching city in this state.")
        sys.exit(1)
    logger.info("location - {},{} is valid".format(city, state))
    return state


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
    logger.info("job name - {} is valid".format(job_name))


def monster_get_content(job, location):
    """
    This function gets a job title and a location, and returns a page content of the desired url in the monster website.
    The search gets up to 250 searches (the maximum amount of searches the page can display)
    """
    monster_site = 'https://www.monster.com/jobs/search'  # name of the site
    payload = {'q': job, 'where': location, 'page': '10'}  # parameters to insert the url in the request.
    page = requests.get(monster_site, params=payload)
    logger.info("Got Monster jobs list.")
    return page


def monster_get_salaries(city, state, job_name):
    """
    This function gets a job title and a location, and returns a page content of the desired url of salary tool in the
    monster website.
    """
    states_dict = dict(zip(states_long, states_abb))
    salaries_site = 'https://www.monster.com/salary/q-{}-l-{}-{}' \
        .format("-".join(job_name.lower().split()), "-".join(city.lower().split()), states_dict[state].lower())
    logger.info("Got Monster salaries data.")
    return salaries_site


def get_salaries_page_data(salaries_site):
    """
    This function takes the page of the site with the salaries of the specific job in the specific city, and returns
    the job salaries in that city (10%, median, 90%) and also the median salary for the job national.
    """
    browser = webdriver.PhantomJS(os.path.join(os.getcwd(), "phantomjs-2.1.1-macosx/bin/phantomjs"))
    browser.get(salaries_site)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    salaries = soup.find('script').string  # a section inside the html that contains the salaries data.
    # Salaries of the city that was searched in the search engine:
    med = int(soup.find('span', {'class': 'avgSalary'}).text.replace(",", ""))
    prc90 = int(soup.find('span', {'class': 'maxSalary'}).text.replace(",", ""))  # need to change to max
    prc10 = int(soup.find('span', {'class': 'minSalary'}).text.replace(",", ""))  # need to change to min
    national = int(soup.find('span', {'class': 'jsx-944507022 nationalSalary'}).text.replace(",", ""))
    logger.info("Salaries data is valid - median = {}, 10th percentile = {}, "
                "90th percentile = {},national = {}.".format(med, prc10, prc90, national))
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


def use_adzuna_api(job_name, location):
    """
    This function extracts jobs data using the api of adzuna
    :param job_name: the job name requested
    :param location:  location of desired job
    :return: output a list of lists where each list contains the name of the job offer company,
     specific location and title.
    """
    app_key = 'c54b61864d1a48221053a5bf3093674d'
    app_id = '356aad97'
    job_name_query = "%20".join(job_name.split())
    location_query = "%20".join(location.split())

    url = 'https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={}&app_key={}&' \
          'what={}&where={}&content-type=application/json'.format(app_id, app_key, job_name_query, location_query)
    response = urlopen(url)
    results = json.loads(response.read())
    jobs_output_api = []
    for item in results["results"]:
        cur_results = []
        cur_results.append(item['company']['display_name'])
        cur_results.append(item['location']['display_name'])
        cur_results.append(item['title'].replace("<strong>", "").replace("</strong>", ""))
        cur_results.append(item['created'].split('T')[0].replace("-", "/"))
        jobs_output_api.append(cur_results)
    logger.info("retrieved Adzuna web API information successfully")
    return jobs_output_api


def get_lat_lon(place):
    """
    This function gets the latitude and longitude of the city in which the job is searched.
    :param place: the city and state
    :return: latitude and longitude as a tuple.
    """
    geolocator = Nominatim(user_agent="my_user_agent")
    results = geolocator.geocode(place)
    return results.latitude, results.longitude


def update_mysql_tables(host_name, user_name, user_password, db_name, jobs_output,
                        job_name, place, lat, lon, prc90, med, prc10, national):
    """
    This function injects the values retrieved from the web scraping into the mysql tables.
        :param host_name: (of the mysql account).
    :param user_name: (of the mysql account).
    :param user_password: (of the mysql account).
    :param db_name: the database to load onto the data.
    :param jobs_output: a nested list of the scraped data.
    :param job_name: the job name as appeared in the search.
    :param place: name of the place typed in the query.
    :param lat: latitude of place typed in the query.
    :param lon: longitude of place typed in the query.
    :param prc90: the 90th percentile of salaries in the field in the city searched.
    :param med: the median percentile of salaries in the field in the city searched.
    :param prc10: the 10th percentile of salaries in the field in the city searched.
    :param national: the national median salary in the field.
    :return: Nothing
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
        if title_id == 0:
            cursor.execute("""SELECT title_id from titles where title=(%s)""", (job_name,))
            for vals in cursor:
                title_id = vals[0]
        # adding values to location table:
        mysql_insert_query2 = """INSERT IGNORE INTO location (location_name, latitude, longitude) 
                                VALUES (%s, %s, %s)"""  # Update auto increment on location id?
        recordtuple2 = (place, lat, lon)
        cursor.execute(mysql_insert_query2, recordtuple2)
        location_id = cursor.lastrowid
        if location_id == 0:
            cursor.execute("""SELECT location_id from location where location_name=(%s)""", (place,))
            for vals in cursor:
                location_id = vals[0]
        # adding values to national_salaries table:
        mysql_insert_query3 = """INSERT IGNORE INTO national_salaries (title_id, national_median_salary) 
                                VALUES (%s, %s)"""  # Update auto increment on location id?
        recordtuple3 = (title_id, national)
        cursor.execute(mysql_insert_query3, recordtuple3)
        # adding values to national_salaries table:
        mysql_insert_query4 = """INSERT IGNORE INTO regional_salaries (title_id, location_id,
                                area_median_salary, area_ninety_salary, area_tenth_salary) 
                                VALUES (%s,%s,%s,%s,%s)"""  # Update auto increment on location id?
        recordtuple4 = (title_id, location_id, med, prc90, prc10)
        cursor.execute(mysql_insert_query4, recordtuple4)
        for line in jobs_output:
            # adding values to open_positions table:
            mysql_insert_query5 = """INSERT IGNORE INTO open_positions (title_id, location_id,
                                    job_description, company_name, date_posted) 
                                    VALUES (%s, %s, %s, %s, %s)"""  # Update auto increment on location id?
            recordtuple3 = (title_id, location_id, line[2], line[0], line[3])
            cursor.execute(mysql_insert_query5, recordtuple3)
        connection.commit()
        print("Record inserted successfully into table")
        logger.info("{} in {} results were inserted successfully into table open_positions.".format(job_name, place))
    except mysql.connector.Error as error:
        print("Failed to insert into MySQL table {}".format(error))
        error_logger.error("Failed to insert into MySQL table {}".format(error))


    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


def main():
    job_name, city, state = get_parameters()  # gets the parameters from the CLI.
    state = check_validity_location(city, state, city_to_state_dict, states_abb,
                                    states_long)  # Verifying data is suitable.
    check_validity_jobname(job_name)  # checks if the job is within the list of jobs allowed.
    place = city + ", " + state
    lat, lon = get_lat_lon(place)  # get latitude and longitude of the place being searched.
    salaries_site = monster_get_salaries(city, state, job_name)  # Getting salaries url.
    prc90, med, prc10, national = get_salaries_page_data(
        salaries_site)  # Getting salaries stats in the city and the US.
    page = monster_get_content(job_name, place)  # Using the function on the monster URL.
    jobs_output = get_jobs_page_data(page)  # creating a list of all the retrieved data
    jobs_output_api = use_adzuna_api(job_name, city)  # extracting more data from the adzuna api
    for job in jobs_output_api:
        jobs_output.append(job)  # concatenating the jobs outputs from the scraping and the api.
    # loading data to tables:
    user = input("please insert user name")
    password = input("please insert password")
    update_mysql_tables("localhost", user, password, 'mining',
                        jobs_output, job_name, place, lat, lon, prc90, med, prc10, national)


if __name__ == '__main__':
    main()
