# Twitter timeline to mastodon
~~Crawl Twitter timeline and send toot.~~

~~This script uses Firefox's geckodriver. May not work on Windows machine.~~ It uses Google Chrome.

~~This is just an initial commit and a lot has to be done.~~

------

~~귀찮으니~~ 한글로 작성할겁니다.(?)

~~[firefox geckodriver](https://github.com/mozilla/geckodriver) 를 이용하고, macOS에서 작성되어서 윈도우즈 기기에서는 동작하지 않을 겁니다 아마. [적당히 맞는 드라이버](https://github.com/mozilla/geckodriver/releases)와 경로를 수정하면 윈도우에서도 동작하기는 할겁니다. 아마 여기까지 오신 분이면 혼자서 충분히 할 수 있는 난이도의 작업이라고 생각합니다.~~

이 브랜치는 우분투 서버에서 동작한 코드를 커밋합니다.

아직 초기 단계이므로 예상치 못한 버그가 있을 수 있습니다.

## Requirements

- [Google Chrome (for Linux preferrably)](https://support.google.com/chrome/a/answer/9025903?hl=ko)
- [chromedriver](https://chromedriver.chromium.org/downloads) with matching version number
- Python3
- [Selenium](https://selenium-python.readthedocs.io)
- [Requests](https://requests.readthedocs.io/en/master/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

사용 전 config\_sample.json 을 config.sample 로 복사한 뒤 해당 내용에 맞게 기입한 후 bot.py 를 실행하시면 됩니다. 로그인 과정을 통해 인증 정보를 생성해야 하므로 머리가 달려있는 환경에서 진행하여 주십시오.

## Todo

- [x] 반복 크롤링
- [x] 이미지 받아오기
- [x] 동영상 링크넣기
