from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from credential import retrieve
#from fake_useragent import UserAgent
from time import sleep
import requests

mast_instance = input('please input your Mastodon Instance address: ')
if mast_instance[:8] != 'https://':
    mast_instance = 'https://'+mast_instance
mast_id = input('please input your mastodon username: ')
try:
    acc = retrieve(mast_id, mast_instance)
except:
    pass
    from credential import register
    register(mast_instance)
    # get acc
    acc = retrieve('mast_id', 'mast_instance')
print('access token is '+acc)
head = {'Authorization': 'Bearer '+acc}
twitter_id = input('Please input your twitter username: ')
twitter_pw = input('Please input your twitter password: ')
# FF profile via https://stackoverflow.com/a/48459249
# String via https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent/Firefox
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15"
###
#ua = UserAgent()
#profile = webdriver.FirefoxProfile()
#options = Options()
#options.headless = True
#profile.set_preference('general.useragent.override', user_agent)
# profile.set_preference('general.useragent.override',ua.firefox)
#browser = webdriver.Firefox(options=options, firefox_profile=profile,executable_path='/home/canor/scripts/twtimelinebot/phantomjs')
###
###
# phantomjs
# https://pythonspot.com/selenium-phantomjs/
browser = webdriver.PhantomJS(executable_path='/home/canor/scripts/twtimelinebot/phantomjs')
browser.get('https://twitter.com/login?hide_message=true&redirect_after_login=https%3A%2F%2Ftweetdeck.twitter.com%2F%3Fvia_twitter_login%3Dtrue')
# whatever here
browser.implicitly_wait(5)
browser.find_element_by_name('session[username_or_email]').send_keys(twitter_id)
# selenium.common.exceptions.ElementNotInteractableException: Message: Element <input class="text-input email-input js-signin-email" name="session[username_or_email]" type="text"> is not reachable by keyboard
# pw
sleep(1)
browser.find_element_by_name('session[password]').send_keys(twitter_pw+Keys.RETURN)
# <button type="submit" class="submit EdgeButton EdgeButton--primary EdgeButtom--medium">로그인</button>

print('headless mode activated')

# last read
last_read = ''
current_read = ''
try:
    with open('last_read.txt') as lr:
        for line in lr:
            last_read = line  # topmost data-tweet-id from last session will be in last_read var
except:
    with open('last_read.txt', 'w'):
        pass
try:
    wait_til_load = WebDriverWait(browser,30).until(EC.presence_of_element_located((By.CLASS_NAME,'js-chirp-container')))
except TimeoutException:
    pass
def upload_image(url):
    import json
    image_byte = requests.get(url).content
    files = {'file':image_byte}
    post_img = requests.post(mast_instance+'/api/v1/media',headers=head,files=files)
    return post_img.content.decode('utf-8').json()['id']

def crawl():
    home_timeline = bs(browser.page_source, 'html.parser').find('div', attrs={'class': 'js-chirp-container'})
    #print(home_timeline)
    with open('last_read.txt', 'w') as lr_w:
        try:
            lr_w.write(str(home_timeline.find('article')['data-tweet-id']))
        except:
            pass
    with open('home_timeline.html', 'w') as f:
        f.write(str(home_timeline))
    tweets = list()
    for item in home_timeline.find_all('article'):
        #print('last read: '+last_read)
        #print('current read: '+item['data-tweet-id'])
        global current_read
        if item['data-tweet-id'] == current_read or item['data-tweet-id'] == last_read:
            print('break!!')
            break
        content = dict()
        # tweet text
        try:
            tweet_text = str(item.find('p', attrs={'class': 'js-tweet-text'}).get_text())
        except:
            tweet_text = ''
        # user id
        try:
            user_id = str(item.find('span', attrs={'class': 'account-inline'}).get_text()).replace('@','@ ') #+ '(' + str(item.find('span', attrs={'class': 'username'}).get_text())+')'
        except:
            user_id = ''
        # link
        try:
            link = str(item.find('time').a['href'])
        except:
            link = ''
        # quote
        try:
            quote = '\n>>>\n' + str(item.find('p', attrs={'class': 'js-quoted-tweet-text'}).get_text())
        except:
            quote = ''
        #image
        try:
            media = list()
            image_list = item.find_all('a',attrs={'class':'reverse-image-search'})
            for i in len(image_list):
                image_list[i] = str(image_list['href']).split('image_url=')[1]
                image_list[i] = image_list[i].split('?')[0]
                media.append(upload(image_list[i]))
        except:
            print('no image')
            media=[]
        content['status'] = tweet_text + ' via' + user_id + ' ' + link + quote
        cotent['media_ids[]'] = media
        tweets.append(content)
        content['visibility'] = 'unlisted'
        t = requests.post(mast_instance+'/api/v1/statuses',headers=head, data=content)
        #print(content)
        print(t.content)
        sleep(1)
    try:
        current_read = home_timeline.find('article')['data-tweet-id']
    except:
        current_read = last_read

while True:
    crawl()
    sleep(15)
# browser.quit()
