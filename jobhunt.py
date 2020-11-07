from bs4 import BeautifulSoup
import requests
import pandas as pd


def monster_get_content(job, location):
    """
    This function gets a job title and a location, and returns a page content of the desired url in the monster website.
    The search gets up to 250 searches (the maximum amount of searches the page can display)
    """
    monster_site ='https://www.monster.com/jobs/search' # name of the site
    payload = {'q': job, 'where': location, 'page': '10'} # parameters to insert the url in the request.
    page = requests.get(monster_site, params = payload)
    return page

def get_jobs_page_data(page):
    """
    This function takes the page of the site with the specific job and place and name, and output a list of lists where
    each list contains the name of the job offer company, specific location and title.
    """
    soup = BeautifulSoup(page.text, 'html.parser')
    jobs = soup.find_all('section', class_="card-content") # Searching all the card contents of jobs
    jobs_output = []
    for job in jobs:
        if job.find('div',class_='company') != None:
            cur_results = []
            cur_results.append(job.find('div',class_='company').span.text.replace("\n","").replace("\r",""))
            cur_results.append(job.find('div',class_='location').span.text.replace("\n","").replace("\r",""))
            cur_results.append(job.div.h2.a.text.replace("\r","").replace("\n","").replace("\r",""))
            jobs_output.append(cur_results)
    return jobs_output

def export_data_to_csv(jobs_output):
    """
    This function creates a directory and places in it a csv file with the data regarding all the jobs in the query.
    """
    jobs_pd = pd.DataFrame(jobs_output, columns = ["Name","Location","Title"])
    jobs_pd.to_csv("output_data.csv")



def main():
    Job_name = input("what is the job you want to look for?")
    place = input("where do you want to find this job?")
    page = monster_get_content(Job_name, place)  # Using the function on the monster URL.
    jobs_output = get_jobs_page_data(page) # creating a list of all the retrieved data
    export_data_to_csv(jobs_output) # Exporting the data to csv file.


if __name__ == '__main__':
    main()