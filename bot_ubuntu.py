from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from credential import retrieve
#from fake_useragent import UserAgent
from time import sleep
import requests
import os
import json
import re

base = os.path.dirname(os.path.abspath(__file__))
try:
    with open(base+'/config.json') as f:
        mas = json.load(f)
        mast_id = mas['mastodon']['id']
        mast_instance = mas['mastodon']['instance']
    acc = retrieve(mast_id, mast_instance)
except:
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
        acc = retrieve(mast_id, mast_instance)
#print('access token is '+acc)
head = {'Authorization': 'Bearer '+acc}
try:
    with open(base+'/config.json') as f:
        twitter = json.load(f)
        twitter_id = twitter['twitter']['id']
        twitter_pw = twitter['twitter']['pw']
except:
    twitter_id = input('Please input your twitter username: ')
    twitter_pw = input('Please input your twitter password: ')
# FF profile via https://stackoverflow.com/a/48459249
# String via https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent/Firefox
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15"
###
# PhantomJS was abandoned
# send_keys() didn't work
# looks like it's going back to 2016?
###
# setup options
options = webdriver.ChromeOptions()
options.add_argument('--headless') # why?
options.add_argument('window-size=1920x1080') # still why?
options.add_argument('user-agent='+user_agent)
browser = webdriver.Chrome(base+'/chromedriver',options=options)
# here we go
browser.get('https://twitter.com/login?hide_message=true&redirect_after_login=https%3A%2F%2Ftweetdeck.twitter.com%2F%3Fvia_twitter_login%3Dtrue')
# wait for page to load
browser.implicitly_wait(5)
browser.find_element_by_name('session[username_or_email]').send_keys(twitter_id)
# errors if not mobile agent
# firefox : selenium.common.exceptions.ElementNotInteractableException: Message: Element <input class="text-input email-input js-signin-email" name="session[username_or_email]" type="text"> is not reachable by keyboard
# chromedriver : element not interactable
# input pw after 1 sec
sleep(1)
browser.find_element_by_name('session[password]').send_keys(twitter_pw+Keys.RETURN)
# <button type="submit" class="submit EdgeButton EdgeButton--primary EdgeButtom--medium">로그인</button>

print('headless mode activated')

# last read
last_read = ''
current_read = ''
try:
    with open(base+'/last_read.txt') as lr:
        for line in lr:
            last_read = line  # topmost data-tweet-id from last session will be in last_read var
except:
    with open(base+'/last_read.txt', 'w'):
        pass
try:
    wait_til_load = WebDriverWait(browser,30).until(EC.presence_of_element_located((By.CLASS_NAME,'js-chirp-container')))
except TimeoutException:
    pass

def upload_media(url):
    import json
    img_byte = requests.get(url).content
    files = {'file':img_byte}
    r = requests.post(mast_instance+'/api/v1/media',headers=head,files=files)
    #print(r.json()['id'])
    return r.json()['id']
    
def crawl():
    home_timeline = bs(browser.page_source, 'html.parser').find('div', attrs={'class': 'js-chirp-container'})
    #print(home_timeline)
    with open(base+'/last_read.txt', 'w') as lr_w:
        try:
            lr_w.write(str(home_timeline.find('article')['data-tweet-id']))
        except:
            pass
    #with open(base+'/home_timeline.html', 'w') as f:
    #    f.write(str(home_timeline))
    tweets = list()
    for item in home_timeline.find_all('article'):
        #print('last read: '+last_read)
        #print('current read: '+item['data-tweet-id'])
        global current_read
        if item['data-tweet-id'] == current_read or item['data-tweet-id'] == last_read:
            #print('break!!')
            break
        content = dict()
        # tweet text
        try:
            try:
                for link in item.find_all('a',attrs={'class':'url-ext'}):
                    link.string = link['data-full-url']
            except:
                pass
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
        # image
        try:
            media=[]
            if len(item.find_all('div',attrs={'class':'js-media'})):
                print('media found')
                if item.find('div',attrs={'class':'is-video'}):
                    print('video detected')
                    vid_url = item.find('div',attrs={'class':'is-video'}).a['href']
                    print('vid_url: '+vid_url)
                    media = []
                    browser.execute_script("window.open('"+vid_url+"');")
                    print('open new window with video url')
                    browser.implicitly_wait(5)
                    print('waiting')
                    browser.switch_to.window(browser.window_handles[1])
                    print('window switched')
                    browser.find_element_by_xpath("//div[@aria-label='이 동영상 재생']").click()
                    print('start video')
                    browser.implicitly_wait(5)
                    print('waiting')
                    vid_bs = bs(browser.page_source,'html.parser')
                    print('bsing video page')
                    vid_url = vid_bs.find('video')['src']
                    print('video src: '+vid_url)
                    u = upload_media(vid_url)
                    media.append(u)
                    browser.close()
                    print('closed browser')
                    browser.switch_to.window(browser.window_handles[0])
                    print('switched to tab 1')
                    browser.implicitly_wait(1)
                elif item.find('div',attrs={'class':'is-gif'}):
                    print('gif detected')
                    gif_url = item.find('video')['src']
                    u = upload_media(gif_url)
                    media.append(u)
                elif len(item.find_all('div',attrs={'class':'media-grid-container'})):
                    image_list = item.find_all('a',attrs={'class':'reverse-image-search'})
                else:
                    print('single image')
                    image_list = list()
                    image_list.append(item.find_all('a',attrs={'class':'reverse-image-search'})[0])
                for i in range(len(image_list)):
                    image_list[i] = str(image_list[i]['href']).split('image_url=')[1]
                    image_list[i] = image_list[i].split('?')[0]
                    u = upload_media(image_list[i])
                    media.append(u)
            else:
                print('no media found')
        except:
            print('error occured')
            media=[]
        content['status'] = tweet_text + ' via ' + user_id + ' ' + link + quote
        content['media_ids[]'] = media
        content['visibility'] = 'unlisted'
        tweets.insert(0,content)
    
    for tweet in tweets:
        t = requests.post(mast_instance+'/api/v1/statuses',headers=head, data=tweet)
        #print(content)
        sleep(1)
    try:
        current_read = home_timeline.find('article')['data-tweet-id']
    except:
        current_read = last_read

while True:
    crawl()
    sleep(5)
# browser.quit()
