import requests
import json
import pprint
from tqdm import tqdm
from datetime import datetime, timezone
from time import sleep
import os


class Vk:
    url = 'https://api.vk.com/method/'

    def __init__(self, vk_token, version):
        self.params = {'access_token': vk_token,
                       'v': version}

    def get_photos_from_vk(self, user_id, offset=0):
        url_photo = 'https://api.vk.com/method/photos.get'
        photos_params = {'owner_id': user_id,
                         'album_id': 'profile',
                         'extended': 1,
                         'photo_sizes': '1',
                         'offset': offset}
        response = requests.get(url_photo, params={**self.params, **photos_params})
        photos = response.json()['response']['items']
        return photos

    def get_sorted_photos(self, user_id):
        photos = self.get_photos_from_vk(user_id)
        sorted_photos = sorted(photos, key=lambda x: (-x.get('likes', {}).get('count', 0)))
        return sorted_photos


class Yandex:
    def __init__(self, ya_token):
        self.token = ya_token

    def make_folder(self, folder_path):
        url = f'https://cloud-api.yandex.net/v1/disk/resources?path={folder_path}'
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'OAuth {self.token}'}
        response = requests.get(url=url, headers=headers)

        if response.status_code == 200:  # Если папка уже существует, возвращаем успешный статус
            print(f"Папка {folder_path} уже существует на Яндекс.Диске.")
            return True

        elif response.status_code == 404:
            response = requests.put(url=url, headers=headers)

            if response.status_code == 201:
                print("Папка успешно создана")
                return True
            else:
                print(f"Ошибка при создании папки: {response.text}")
                return False
        else:
            print(f"Ошибка при проверке/создании папки: {response.text}")
            return False

    def upload_photos(self, folder_path, num_photos, sorted_photos):
        results = []  # Список для хранения информации о каждой загруженной фотографии
        progress_bar = tqdm(total=num_photos, desc='Загрузка фото на Яндекс.Диск')

        for i, photo in enumerate(sorted_photos[:num_photos]):
            sizes = photo.get('sizes')
            if sizes:
                max_size = sizes[-1]
                max_url = max_size['url']
                likes_count = photo.get('likes', {}).get('count', 0)
                photo_date = datetime.fromtimestamp(photo.get('date'), timezone.utc).strftime('%Y-%m-%d')
                photo_id = photo.get('id')
                name = f'{likes_count}_{photo_id}_{photo_date}.jpg'
                if os.path.exists(f'{folder_path}/{name}'):
                    print(f"Файл с именем '{name}' уже существует. Пропускаем загрузку.")
                    continue
                url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
                headers = {'Content-Type': 'application/json',
                           'Authorization': f'OAuth {self.token}'}
                params_upload = {'path': f'{folder_path}/{name}', 'url': max_url}
                response = requests.post(url=url, headers=headers, params=params_upload)

                if response.status_code == 202:
                    print(f"Фотография '{name}' успешно загружена на Яндекс.Диск.")
                    results.append({'file_name': name,
                                    'size': max_size})
                    sleep(0.05)
                else:
                    print(f"Ошибка при загрузке фотографии '{name}' на Яндекс.Диск: {response.text}")
                    print(f"URL для загрузки: {url}")
                    print(f"HTTP статус: {response.status_code}")
            progress_bar.update(1)

        progress_bar.close()

        with open('photo_results.json', 'w') as f:  # Сохраняем информацию по фото в JSON-файл
            json.dump(results, f, indent=4)
        print("Результаты загрузки на Яндекс.Диск:")
        for i, photo in enumerate(sorted_photos[:num_photos]):
            print(f"Фотография {i + 1}:")
            pprint.pprint(photo.get('sizes')[-1])


if __name__ == '__main__':
    vk_token = '...'
    version = '5.131'
    user_id = input('Введите id пользователя: ')
    vk = Vk(vk_token, version)
    sorted_photos = vk.get_sorted_photos(user_id)
    #pprint.pprint(sorted_photos)

    ya_token = input('Введите токен Яндекс: ')
    yandex = Yandex(ya_token)
    folder_path = 'Загружено из vk'
    response = yandex.make_folder(folder_path)
    yandex.upload_photos(folder_path, num_photos=5, sorted_photos=sorted_photos)
