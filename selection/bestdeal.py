import re  # подключение модуля для регулярок
import json  # подключение библиотеки для обработки данных
# подключение библиотеки для формирования альбома фотографий
from telebot.types import InputMediaPhoto
import random  # стандартная библиотека рандомного выбора
# библиотека для определения растояний
from geopy.distance import geodesic as GD
import os  # подключение системной библиотеки
# подключение фукции парсера
from selection.search_areas import request_to_server, checking_server_response


def sorting_hotels(user, message):
    """
    Функция предназначена для парсинга отелей по выбранному району
    формирования финального словаря доя отправки пользователю
    sorted_hotels: итоговый словарь для вывода пользователю
                   данных в зависимости от введеных данных
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": "10779356", "pageNumber": "1",
                   "pageSize": "25", "checkIn": "2022-03-26",
                   "checkOut": "2022-03-28", "adults1": "1",
                   "sortOrder": "PRICE", "locale": "ru_RU", "currency": "RUB"}

    querystring['destinationId'] = user.id_district
    querystring['checkIn'] = user.arrival_date
    querystring['checkOut'] = user.departure_date
    querystring['adults1'] = user.number_of_people

    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('key')
    }

    response = request_to_server(url, headers, querystring)
    checking_server_response(response, message, user)
    area_search = json.loads(response.text)
    data_hotel = area_search['data']['body']['searchResults']['results']

    sorted_hotels = dict()  # для вывода
    hotel_bas = dict()  # для базы
    # цикл для фильтрации и сбору данных по отелям
    for hotel in data_hotel:
        id = hotel['id']  # йд гостинници
        name = hotel['name']  # название гостинници
        rating = hotel['starRating']  # рейтинг
        town = hotel.get('address', {}).get('locality', 'Город не указан')
        prise = hotel.get('ratePlan', {}).get('price', {}).get('current', '0')
        address = hotel.get('address', {})\
            .get('streetAddress', 'Адресс не указан администрацией отеля')
        distance = hotel.get('coordinate', {})\
                        .get('lat', {}), hotel.get('coordinate', {})\
            .get('lon', {})
        prise_reconciliation = ''.join(re.findall(r'\d', prise))
        link = 'https://www.hotels.com/ho{0}'.format(id)

        distance_center = GD(user.city_center, distance).km

        if int(user.minimum_price) < int(prise_reconciliation) < int(user.max_price) and int(distance_center) < int(user.to_the_center):

            grouping_data = [f'Отель: "{name}"\nРейтинг: "{rating}"\nАдрес:'
                             f' "{town} {address}"\nПолная стоимость: "'
                             f'{prise}"\nРастояние до центра: '
                             f'"{round(distance_center, 1)}"'
                             f'\nСсылка на отель: {link}']

            sorted_hotels[id] = dict()
            sorted_hotels[id]['data'] = grouping_data
            hotel_bas[id] = dict()
            hotel_bas[id]['data'] = grouping_data
            if user.photo_hotel == 'да':
                grouping_photo = formation_of_photos(user, id, message)
                sorted_hotels[id]['photo'] = grouping_photo
    user.hotel_bas = hotel_bas
    return sorted_hotels


def formation_of_photos(user, id, message):
    """
    Функция собирает данные о фотографиях отелей, выбирает
    разные фотографии из представленных и пределет созданный
    альбом для отпревки пользователю при необходимости
    """
    url_of_references = list()  # урл адреса всех фото
    grouping_photos = list()  # группировка фото в альбом

    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'

    querystring = {"id": id}

    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('key')
    }

    response = request_to_server(url, headers, querystring)
    checking_server_response(response, message, user)
    date = json.loads(response.text)
    # цикл для отбора ссылок и качестра фото
    for i_photo_info in date.get('hotelImages'):
        url = i_photo_info.get('baseUrl').format(size='z')
        url_of_references.append(url)
    # список рандомных фотографий (количество по запросу от пользователя)
    url_of_out = random.choices(url_of_references, k=user.number_photos)
    # цикл для формирования альбома
    for i_url in url_of_out:
        grouping_photos.append(InputMediaPhoto(media=i_url))

    return grouping_photos
