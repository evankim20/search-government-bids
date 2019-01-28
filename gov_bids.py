#Imports
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import requests
import re
import time
from datetime import datetime

#Variables that are helpful:
US_states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado",
  "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois",
  "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
  "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
  "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
  "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
  "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah",
  "Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming", 
             "District of Columbia"]  #note Guam and Puerto Rico are not included

today = datetime.today()
year_today = today.year
next_year = year_today

#inititalizing selenium
options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome('chromedriver') #, options = options)

#SEARCH FILTERS 
#type in any devices you want to search for

devices = ['computer', 'ipad', 'iphone', 'phone', 'laptop', 'mobility', 'smartphone', 'tablet', 'apple','samsung',
          'managed mobility', 'telecom expense management', 'device repair']


#stores all information for all device_keys 
state_bids = dict() #key: state; value: bids 

for device_name in devices:
    #going government bids website and inserting in our filter from keys
    driver.get('https://www.governmentbids.com/government-search-advanced-en.jsa')
    driver.find_element_by_xpath('//*[@id="keywords"]').send_keys(device_name)
    #need to wait for this script to run, the "All" button does not load in time and says that there is no "All" button
    driver.implicitly_wait(20)
    #selecting the button that filters ALL STATES in search and clicks that button
    all_states_button = driver.find_element_by_link_text('All')#xpath('//*[@id="frmSearch"]/div[2]/div[1]/div[1]/div[1]/a[1]')
    all_states_button.click()

    #selects the following catagories for filters: {Computer(hardware), Computer(software), Information Technology, Telecommunications}
    hardware_button_press = driver.find_element_by_xpath('//*[@id="options-box-1-option-11"]').click()
    software_button_press = driver.find_element_by_xpath('//*[@id="options-box-1-option-12"]').click()
    it_button_press = driver.find_element_by_xpath('//*[@id="options-box-1-option-34"]').click()
    tele_button_press = driver.find_element_by_xpath('//*[@id="options-box-1-option-74"]').click()

    #executes the search
    search_button_press = driver.find_element_by_xpath('//*[@id="frmSearch"]/div[7]/a[2]').click()

    all_text = driver.find_element_by_xpath('//*[@id="contentTextLeft"]')
    all_text_list = re.sub("[^\w]", " ",  all_text.text).split()
    number_bids = []
    for n in range(len(all_text_list)):
        if all_text_list[n].isdigit() and all_text_list[n+1] == 'are' and all_text_list[n+2] == 'currently' and all_text_list[n+3] == 'open':
            num_results = int(all_text_list[n])
            break

    num_pages = (num_results//100)
    if num_results%100 != 0:
        num_pages = int(num_pages + 1)

        #IMPORTANTT UN COMMENT OUT PLEASE
    if num_pages == 0:
        continue
    
    #configures to have 100 bids per page
    view_size = Select(driver.find_element_by_xpath('//*[@id="pageResultCountdd"]'))
    view_size.select_by_visible_text('100')

    #configues the data to be shown grouped by state
    sort_by = Select(driver.find_element_by_xpath('//*[@id="sortOrderdd"]'))
    sort_by.select_by_visible_text('State/Category')

    #initializing data structures
    #seen will make sure we dont truncate a state too early given multiple pages (ie if california is on page one and page two
    #the code will not think it is in a new state because when it reaches the if statement it knows not to change states)
    seen = set()
    page = 1

    #next page stuff here
    while page <= num_pages:   
        #grabs the data from the website of all the bids avaliable given the parameters
        table = driver.find_element_by_xpath('//*[@id="resultsLeft"]/div[2]/table')
        text_from_site = table.text.split('\n')

        #going through the data from our current page
        for c in text_from_site:
            #checking to start a new col
            if any(x+' bids and contracts' == c for x in US_states) and c not in seen:
                seen.add(c)
                state = c.split(' ', 1)[0]
                if state not in state_bids:
                    state_bids[state] = set()
            elif str(year_today) in c or str(next_year) in c:
                state_bids[state].add(c[2:])

        driver.find_element_by_xpath("//*[contains(text(), 'Next')]").click()   
        time.sleep(5)
        page += 1
    

#putting into a data frame
#key value pairs
state_bids_to_df = []
for s in state_bids:
    for b in state_bids[s]:
        state_bids_to_df.append([s, b])

state_bids_df = pd.DataFrame(state_bids_to_df)

total_count = 0
for s in state_bids:
    total_count += len(state_bids[s])


state_bids_df.to_csv('state_bids.csv')
