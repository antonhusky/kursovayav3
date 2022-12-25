import configparser as cp
import time
from datetime import datetime
import os
import requests
import tqdm
import json

config = cp.ConfigParser()
config.read('config.ini')

vk_api_url = config['VK']['url']
vk_access_token = config['VK']['access_token']

ya_api_url = config['YANDEX']['url']
ya_access_token = config['YANDEX']['access_token']

if not os.path.exists('json'):
    os.mkdir('json')

class VkUser:
    def __init__(self, input):
        if input.isdigit():
            self.user_id = input
            self.screen_name = None
        else:
            self.user_id = None
            self.screen_name = input

    def get_photos(self):
        if self.user_id:
            params = {
                'access_token': vk_access_token,
                'v': '5.92',
                'owner_id': self.user_id,
                'album_id': 'profile',
                'extended': 1,
                'photo_sizes': 0,
                'count': 5
            }
        elif self.screen_name:
            params = {
                'access_token': vk_access_token,
                'v': '5.92',
                'screen_name': self.screen_name,
                'album_id': 'profile',
                'extended': 1,
                'photo_sizes': 0,
                'count': 5
            }
        response = requests.get(vk_api_url + 'photos.get', params)
        return response.json()

    def get_photos_links(self):
        photos = self.get_photos()['response']['items']
        photos_links = []
        likes_count = []
        for photo in photos:
            likes_count.append(photo['likes']['count'])
        for photo in photos:
            if likes_count.count(photo['likes']['count']) > 1:
                photo_name = f'{photo["likes"]["count"]}_{datetime.fromtimestamp(photo["date"]).strftime("%Y-%m-%d")}'
            else:
                photo_name = photo['likes']['count']
            photo_url = photo['sizes'][-1]['url']
            photo_size = photo['sizes'][-1]['type']
            photos_links.append((photo_name, photo_url, photo_size))
        return photos_links


class YaUploader:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Authorization': f'OAuth {self.token}',
            'Content-Type': 'application/json',
        }

    def create_folder(self, folder_name):
        headers = self.get_headers()
        params = {
            'path': f'/{folder_name}'
        }
        response = requests.put(ya_api_url + 'v1/disk/resources', headers=headers, params=params)
        return response.json()

    def upload(self, folder_name, file_name, file_url):
        headers = self.get_headers()
        params = {
            'path': f'/{folder_name}/{file_name}',
            'url': file_url
        }
        response = requests.post(ya_api_url + 'v1/disk/resources/upload', headers=headers, params=params)
        return response.json()


if __name__ == '__main__':
    user_input = str(input('Введите id или screen_name пользователя: '))
    if not os.path.exists(f'json/{user_input}'):
        os.mkdir(f'json/{user_input}')
    print(f'''У пользователя {user_input} 
{VkUser(user_input).get_photos()["response"]["count"]} фотографий''')
    photos_count = int(input('Сколько фотографий загрузить? '))
    if photos_count > VkUser(user_input).get_photos()['response']['count']:
        print('Введенное число больше, чем количество фотографий пользователя')
    else:
        photos_links = VkUser(user_input).get_photos_links()
        folder_name = input('Введите название папки: ')
        if YaUploader(ya_access_token).create_folder(folder_name).get('error'):
            print('Ошибка:', YaUploader(ya_access_token).create_folder(folder_name).get('message'))
        else:
            print('Папка создана')
            if not os.path.exists(f'json/{user_input}/{folder_name}'):
                os.mkdir(f'json/{user_input}/{folder_name}')
            start_time = time.time()
            for photo in tqdm.tqdm(photos_links[:photos_count]):
                YaUploader(ya_access_token).upload(folder_name, photo[0], photo[1])
                with open(f'json/{user_input}/{folder_name}/{photo[0]}.json', 'a', encoding='utf-8') as f:
                    json.dump([{'file_name': photo[0], 'size': photo[2]}], f, ensure_ascii=False, indent=4)
