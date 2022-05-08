import re  # модуль подключения регулярных выражений
import json  # модуль json для преобоазования данных
import requests  # модуль работы парсера
# модуль работы с кнопками
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# подключение необходимах функций из main
from main import user_data, bot, log_error, initial_state_class, start_help
import os  # подключение системной библиотеки


def request_to_server(url, headers, querystring):
    """
    Функция производит запрос к серверу для получения данных об отелях
    return response: возвращает полученное значение после получения данных
                     с сервера
    return None: ничего не возвращвет в счучае ошибки со стороны сервера
    """
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=9)
        if response.status_code == requests.codes.ok:
            return response
    except Exception:
        log_error.error('произошла ошибка: ', exc_info=True)
        return None


def checking_server_response(response, message, user):
    """
    Функция прабатывает в случае нулево возврата с сервера
    прерывает работу бота, обнулает поисковые данные пользователя
    и предлагает повторить поиск.
    """
    if response == None:
        bot.send_message(message.chat.id, 'К сожалению произошла ошибка'
                                          ' запроса сервера.'
                                          '\nПовторите запрос.')
        initial_state_class(user)
        start_help(message)
        breakpoint()


def urban_area(message):
    """
    Функция-парсер, получающая от пользователя необходимый город,
    производит запрос на сервер о районах города. При успешном ответе
    с сервера производит формирование словаря {район : йд района}, после
    этого сохраняет словарб в отдельную переменную и возвращает результат
    его для продолжения работы
    :param message:
    :return:
    """

    user = user_data.Users.get_user(message.chat.id, message.from_user.first_name, message.from_user.last_name)
    querystring = {'query': 'москва', 'locale': 'ru_RU'}
    querystring['query'] = user.city

    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('key')
        }
    url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    response = request_to_server(url, headers, querystring)
    checking_server_response(response, message, user)
    pattern = r'(?<="CITY_GROUP",).+?[\]]'
    area_search = re.search(pattern, response.text)
    # проверка результата и формитрование списка районов
    if area_search:
        result = json.loads(f"{{{area_search[0]}}}")
    district_result = list()  # список для словарей района и его йд
    # цикл для прогонки полученных значений и создания словаря
    for i_result in result['entities']:
        district_result.append({'city_name': i_result['name'],
                                'destination_id': i_result['destinationId'],
                                'latitude': i_result['latitude'],
                                'longitude': i_result['longitude']})
    user.city_area = district_result  # запись результата в отдкльную переменную
    return district_result  # возврат списка для формирования кнопок


# функция для создания кнопок выбора района города
def district(message):

    # вызов функции определяющая района города
    city = urban_area(message)
    # формирование кнопок выбора
    destinations = InlineKeyboardMarkup()
    for city_id in city:
        destinations.add(InlineKeyboardButton(text=city_id['city_name'],
                                              callback_data=f'{city_id["destination_id"]}'))
    return destinations  # выозрат выбора пользователя


def choosing_a_neighborhood(message):
        bot.send_message(message.chat.id, 'Выберите район: ', reply_markup=district(message))

