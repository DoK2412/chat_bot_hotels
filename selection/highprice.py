import json  # подключение библиотеки для обработки данных
# подключение библиотеки для формирования альбома фотографий
from telebot.types import InputMediaPhoto
import random  # стандартная библиотека рандомного выбора
import os  # подключение системной библиотеки


def sorting_hotels(user, message):
    """
    Функция предназначена для парсинга отелей по выбранному району
    формирования финального словаря доя отправки пользователю
    sorted_hotels: итоговый словарь для вывода пользователю
                   данных от большего к меньшему
    """
    # импортируем функцию для работы парсера
    from selection.search_areas import request_to_server, checking_server_response

    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": "10779356", "pageNumber": "1",
                   "pageSize": "25", "checkIn": "2022-03-26",
                   "checkOut": "2022-03-28", "adults1": "1",
                   "sortOrder": "PRICE", "locale": "ru_RU",
                   "currency": "RUB"}

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
    data_hotel = reversed(area_search['data']['body']['searchResults']
                          ['results'])

    sorted_hotels = dict()  # для вывода
    hotel_bas = dict()  # для базы

    counter = 0
    for hotel in data_hotel:
        if counter < int(user.number_of_hotels):
            id = hotel['id']  # йд гостинници
            name = hotel['name']  # название гостинници
            rating = hotel['starRating']  # рейтинг
            town = hotel.get('address', {}).get('locality', 'Город не указан')
            prise = hotel.get('ratePlan', {}).get('price', {})\
                .get('current', 'Цена не была указана')
            address = hotel.get('address', {})\
                .get('streetAddress', 'Адресс не указан администрацией отеля')
            link = 'https://www.hotels.com/ho{0}'.format(id)

            grouping_data = [f'Отель: "{name}"\nРейтинг: "{rating}"'
                             f'\nАдрес: "{town} {address}"'
                             f'\nПолная стоимость: "{prise}"'
                             f'\nСсылка на отель: {link}']

            sorted_hotels[id] = dict()
            sorted_hotels[id]['data'] = grouping_data
            hotel_bas[id] = dict()
            hotel_bas[id]['data'] = grouping_data
            if user.photo_hotel == 'да':
                grouping_photo = formation_of_photos(user, id, message)
                sorted_hotels[id]['photo'] = grouping_photo
            counter += 1
        else:
            break
    user.hotel_bas = hotel_bas
    return sorted_hotels


def formation_of_photos(user, id, message):
    """
   Функция собирает данные о фотографиях отелей, выбирает
   разные фотографии из представленных и пределет созданный
   альбом для отпревки пользователю при необходимости
    """
    # импортируем функцию для работы парсера
    from selection.search_areas import request_to_server, checking_server_response

    url_of_references = list()  # урл адреса всех фото
    grouping_photos = list()  # группировка фото в альбом

    querystring = {"id": id}

    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
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
