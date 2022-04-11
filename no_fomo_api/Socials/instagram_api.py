import re
import requests
from datetime import datetime
from no_fomo_api.app_config import INSTA_LOGIN, INSTA_PASSWORD


class InstagramApi():
    def __init__(self):
        self.session = requests.Session()

    def login(self):
        link = 'https://www.instagram.com/accounts/login/'
        login_url = 'https://www.instagram.com/accounts/login/ajax/'

        time = int(datetime.now().timestamp())

        payload = {
            'username': INSTA_LOGIN,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{INSTA_PASSWORD}',
            'queryParams': {},
            'optIntoOneTap': 'false'
        }

        r = self.session.get(link)
        csrf = re.findall(r"csrf_token\":\"(.*?)\"",r.text)[0]
        self.session.post(login_url,data=payload,headers={
                "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.instagram.com/accounts/login/",
                "x-csrftoken":csrf
        })

    def get_places_info(self, lat, long):
        return self.session.get(f'https://www.instagram.com/location_search/?latitude={lat}+&longitude={long}').json()