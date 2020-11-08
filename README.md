# data_mining_project
# Description:
The jobhunt function scrapes data from the website "www.monster.com", a search engine for jobs located at the United States. The function retrieves up to 250 jobs (the maximum number of jobs that can appear on the site), scrapes the name of the company that posted the job, the job title, location and when was it applied. The function generates a CSV file containing the data, at the folder the project is being run. the name of the csv file includes the job name and location.

# Input parameters:
At this point, the function asks the user to provide two inputs: the job location and the job title.

# Installations required:
The jobhunt function needs the following libraries:
- pandas
- requests
- BeautifulSoup from bs4
