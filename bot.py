from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from credential import retrieve
from credential import chk_
from time import sleep
from logg import *
import requests
import os
import json
import re

#base = os.path.dirname(os.path.abspath(__file__))+'/'
base = os.path.join(os.path.dirname(os.path.abspath(__file__)),'')

try: # auto login from config.json
    with open(base+'config.json') as f:
        login_conf = json.load(f)
        mast_id = login_conf['mastodon']['id']
        mast_instance = login_conf['mastodon']['instance']
    acc = retrieve(mast_id, mast_instance)
except: # failed. manual login
    mast_instance = chk_(input('please input your Mastodon Instance address: '))
    mast_id = input('please input your mastodon username: ')
    acc = retrieve(mast_id, mast_instance)
head = {'Authorization': 'Bearer '+acc}
try:
    twitter_id = login_conf['twitter']['id']
    twitter_pw = login_conf['twitter']['pw']
except:
    twitter_id = input('Please input your twitter username: ')
    twitter_pw = input('Please input your twitter password: ')
# FF profile via https://stackoverflow.com/a/48459249
# String via https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent/Firefox
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15"
###
# PhantomJS was abandoned
# send_keys() didn't work

# setup options
options = webdriver.ChromeOptions()
options.add_argument('--headless') # headless mode
options.add_argument('window-size=1920x1080')
options.add_argument('user-agent='+user_agent)
#browser = webdriver.Chrome(base + 'chromedriver', options=options)
browser = webdriver.Chrome('/usr/bin/chromedriver', options=options)

# here we go
browser.get('https://twitter.com/login?hide_message=true&redirect_after_login=https%3A%2F%2Ftweetdeck.twitter.com%2F%3Fvia_twitter_login%3Dtrue')
browser.implicitly_wait(8)
# wait for page to load
browser.find_element_by_name('session[username_or_email]').send_keys(twitter_id)
# errors if not mobile agent
# firefox : selenium.common.exceptions.ElementNotInteractableException: Message: Element <input class="text-input email-input js-signin-email" name="session[username_or_email]" type="text"> is not reachable by keyboard
# chromedriver : element not interactable
# input pw after 1 sec
sleep(1)
browser.find_element_by_name('session[password]').send_keys(twitter_pw + Keys.RETURN)

# <button type="submit" class="submit EdgeButton EdgeButton--primary EdgeButtom--medium">로그인</button>
sleep(10)

logger.info('headless mode activated')

# last read
last_read = ''
current_read = ''
try:
    with open(base+'last_read.txt') as lr:
        for line in lr:
            last_read = line  # topmost data-tweet-id from last session will be in last_read var
except:
    with open(base+'last_read.txt', 'w'):
        pass
try:
    wait_til_load = WebDriverWait(browser,30).until(EC.presence_of_element_located((By.CLASS_NAME,'js-chirp-container')))
except:
    while True:
        logger.debug('retrying sign in')
        browser.get('https://tweetdeck.twitter.com')
        sleep(300)
        if bs(browser.page_source, 'html.parser').find('div', class_='js-chirp-container'):
            logger.debug('found timeline')
            break

def upload_media(url):
    import json
    img_byte = requests.get(url).content
    files = {'file':img_byte}
    r = requests.post(mast_instance+'/api/v1/media',headers=head,files=files)
    logger.debug(r.json()['id'])
    return r.json()['id']
    
def crawl():
    home_timeline = bs(browser.page_source, 'html.parser').find('div', class_='js-chirp-container')
    if len(home_timeline.find_all('article'))>100:
        browser.get('https://tweetdeck.com')
        home_timeline = bs(browser.page_source, 'html.parser').find('div', class_='js-chirp-container')
    with open(base+'last_read.txt', 'w') as lr_w:
        try:
            lr_w.write(str(home_timeline.find('article')['data-tweet-id']))
            logger.debug('1: where am I')
        except:
            pass
    #with open(base+'/home_timeline.html', 'w') as f:
    #    f.write(str(home_timeline))
    tweets = list()
    try:
        for item in home_timeline.find_all('article'):
            with open(base + 'blacklist.txt', 'r') as f: # grab blacklist
                bl = [x.strip() for x in f.read().split('\n') if x != '']
                print('blacklist: ', bl)
            logger.debug('2: number of items: '+str(len(home_timeline.find_all('article'))))
            global current_read
            if item['data-tweet-id'] == current_read or item['data-tweet-id'] == last_read:
                logger.debug('3: break!!')
                break
            content = dict()
            # tweet text
            logger.debug('4: parsing tweet')
            try:
                try: # get linked url in case url in tweet text is abbreviated
                    for link in item.find_all('a',class_='url-ext'):
                        link.string = link['data-full-url']
                except:
                    pass
                tweet_text = str(item.find('p', class_= 'js-tweet-text').get_text()) # actual text
                logger.info('tweet text: '+tweet_text)
                for blw in bl: # continue if blacklisted word is included
                    if blw in [t.strip() for t in tweet_text.split(' ')]:
                        logger.debug([t.stip() for t in tweet_text.split(' ')])
                        logger.info('blacklisted word detected')
                        continue
            except:
                tweet_text = ''
            # user id
            try:
                user_id = str(item.find('span', class_= 'account-inline').get_text()).replace('@','@ ') #+ '(' + str(item.find('span', class_= 'username'}).get_text())+')'
                logger.info('user id: '+user_id)
                username = user_id.split('@')[0].strip() # for self retweet detection
            except:
                user_id = ''
            # link
            try:
                link = str(item.find('time').a['href'])
            except:
                link = ''
            # check retweeted_by
            try:
                rt_by = str(item.find('div', class_='nbfc').a.get_text().strip())
                logger.info('rt by: '+rt_by)
            except:
                rt_by = ''
            if username == rt_by: # if tweet is retweeted by composed
                logger.info('composer retweeted; continue')
                continue
            # quote
            try:
                quote = '\n>>>\n' + str(item.find('p', class_= 'js-quoted-tweet-text').get_text())
                for blw in bl:
                    if blw in quote:
                        continue
            except:
                quote = ''
            # image
            media = []
            image = 0
            logger.debug('5: checking media')
            try:
                if len(item.find_all('div',class_='js-media')):
                    logger.debug('media found')
                    if item.find('div', class_= 'is-video'):
                        pass # all is-video items are handled as is-gif in Tweetdeck
                        # vid_url = item.find('div', class_= 'is-video').a['href']
                        # print('important: video detected')
                        # if 'youtu' in vid_url:
                        #     print('is youtube')
                        #     pass
                        # else:
                        #     print('search video procedure initiated')
                        #     browser.execute_script("window.open('');")
                        #     browser.switch_to.window(browser.window_handles[1])
                        #     browser.get(vid_url)
                        #     browser.implicitly_wait(15)
                        #     browser.find_element_by_xpath("//div[@aria-label='이 동영상 재생']").click()
                        #     try:
                        #         browser.find_element_by_xpath("//span[@class='volume-control'").click()
                        #     except:
                        #         pass
                        #     sleep(7)
                        #     vid_bs = bs(browser.page_source, 'html.parser')
                        #     vid_url = vid_bs.find('video')['src']
                        #     u = upload_media(vid_url)
                        #     media.append(u)
                        #     browser.implicitly_wait(3)
                        #     browser.close()
                        #     browser.switch_to.window(browser.window_handles[0])
                        #     browser.implicitly_wait(3)
                        #     home_timeline = bs(browser.page_source, 'html.parser').find('div', class_= 'js-chirp-container')
                    elif item.find('div',class_='is-gif'):
                        logger.debug('gif detected')
                        gif_url = item.find('div',class_='is-gif').find('video')['src']
                        u = upload_media(gif_url)
                        media.append(u)
                    elif len(item.find_all('div', class_='media-grid-container')):
                        logger.debug('multiple images detected')
                        image_list = [i['style'] for i in item.find_all('a',class_='js-media-image-link')]
                        for i in range(len(image_list)):
                            image_ = re.search('https://.*?\.jpg', str(image_list[i])).group()
                            u = upload_media(image_)
                            media.append(u)
                        #image = 1
                    else:
                        logger.debug('single image detected')
                        image_list = list()
                        ut = item.find('a',class_='js-media-image-link')['style']
                        im = re.search('https://.*?\.jpg',str(ut)).group()
                        #image_list.append(item.find('a',class_='js-media-image-link block med-link media-item media-size-medium is-zoomable')['style'])
                        #image = 1
                        u = upload_media(im)
                        media.append(u)
                    if image:
                        for i in range(len(image_list)):
                            image_list[i] = str(image_list[i]['href']).split('image_url=')[1]
                            image_list[i] = image_list[i].split('?')[0]
                            u = upload_media(image_list[i])
                            media.append(u)
                else:
                    logger.debug('no media found')
            except:
                logger.debug('error occured')
            logger.debug('6: combining texts')
            content['status'] = user_id + '\n————————————\n' + tweet_text + quote + '\n————————————\n' +  link
            content['media_ids[]'] = media
            content['sensitive'] = '1'
            content['visibility'] = 'unlisted'
            tweets.insert(0,content)
            logger.info('------------------------------')
        if len(tweets):
            logger.debug('7: sending toot')
            for tweet in tweets:
                t = requests.post(mast_instance+'/api/v1/statuses',headers=head, data=tweet)
            logger.debug('8: save position')
            try:
                current_read = home_timeline.find('article')['data-tweet-id']
                if current_read == last_read:
                    logger.debug('no new tweet')
                else:
                    logger.debug('new position set: '+current_read)
            except:
                current_read = last_read
                logger.debug('new position not recognized; using old position')
        else:
            logger.debug('no new tweet')
    except:
        with open(base+'error.html', 'w') as fw:
            fw.write(str(home_timeline))
            logger.debug('wrote to error.html')

while True:
    crawl()
    sleep(5)
    logger.info('==============================')
# browser.quit()
