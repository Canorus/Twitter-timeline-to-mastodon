from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from credential import retrieve
from time import sleep
import requests
import os
import json
import re

twitter_id = 'psCanor'
twitter_pw = '48r4c4d48r4'

user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15"

options = webdriver.ChromeOptions()
options.add_argument('window-size=1920x1080') # still why?
options.add_argument('user-agent='+user_agent)
browser = webdriver.Chrome('/Users/Canor/scripts/ebay-backup/chromedriver', options=options)
browser.get('https://twitter.com/login?hide_message=true&redirect_after_login=https%3A%2F%2Ftweetdeck.twitter.com%2F%3Fvia_twitter_login%3Dtrue')
browser.implicitly_wait(5)
browser.find_element_by_name('session[username_or_email]').send_keys(twitter_id)

sleep(1)

browser.find_element_by_name('session[password]').send_keys(twitter_pw + Keys.RETURN)
home_timeline = bs(browser.page_source,'html.parser').find('div',attrs={'class':'js-chirp-container'})