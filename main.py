import os
import telebot  # подключение бота
from telebot import types  # тип данных для кнопок
from telegram_bot_calendar import DetailedTelegramCalendar
import re  # библиотека лоя работы с регулярками
import datetime  # подключение библиотеки времени
import user_data  # подключение класса пользователей
# подключение всех файлов поисковиков
from selection import lowprice, highprice, bestdeal, search_areas
import sqlbase  # подключение файла с работой базы данных
from dotenv import load_dotenv  # подключение библиотеки окружений
import logging.config  # подключение файла конфигурации
from logger import logger_config  # импорт логгера

load_dotenv()  # подгружаем данные из env

logging.config.dictConfig(logger_config)  # подключение файла логеров
log_error = logging.getLogger('app_error')  # создание сборщика ошибок
log_info = logging.getLogger('app_info')  # создание сборщика неверных вводов


token = os.getenv('tokken')
bot = telebot.TeleBot(token)

list_commands = ['/help', '/lowprice',  '/highprice', '/bestdeal', '/history',
                 'help', 'lowprice',  'highprice', 'bestdeal', 'history']

def arrival_date(message):
    """
    Функция для обработки даты заезда от пользователя
    состоящая из функций:

    arrival_date() - формирующуя запроса на вывод календаря для
                     ввода даты

    cal() - получает данные от пользователя, формирует их в дату,
            сверяет с текущей датой и по результатам проверки
            сохраняет результат и продолжает следующий вызов
            на ввод даты выезда. Либо повторяет запрос даты если
            она не соответстует требованиям.
    """
    user = user_data.Users.get_user(message.from_user.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                              locale='ru').build()
    bot.send_message(user.id_chat,
                     'Выберите дату заеда.',
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal(call):
    user = user_data.Users.get_user(call.message.chat.id,
                                    call.message.from_user.first_name,
                                    call.message.from_user.last_name)
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text('Выберите дату заезда.',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        if result < datetime.date.today():
            log_info.info(f'{user.name} {user.surname} ввел неверную'
                          f' дату заезда: {result}')
            bot.edit_message_text('Введенная вами дата не может '
                                  'быть меньше текущей даты.'
                                  '\nПовторите выбор',
                                  call.message.chat.id,
                                  call.message.message_id)
            arrival_date(call)  # повторный запрос при неверном вводе
        else:
            # определение времени в случае успешного ввода
            user.arrival_date = result
            bot.edit_message_text(f"Дата заезда: {result}",
                                  call.message.chat.id,
                                  call.message.message_id)
            departure_date(call.message)  # переход к следующеме действию


def departure_date(message):
    """
    Функция для обработки даты выезда от пользователя
    запрос происходит последовательно после ввода даты
    заезда. Состоиз из функций:

    departure_date() - формируют запрос на вывод календаря для
                       ввода даты

    cal() - получает данные от пользователя, формирует их в дату,
            сверяет с текущей датой, расчитывает общее количество
            суток. По результатам проверки сохраняет результаты
            выезда и  общего количества дней после чего продолжает
            следующий вызов, либо повторяет запрос даты если она
            не соответстует требованиям
    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(user.id_chat,
                     'Выберите дату выезда.',
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal(call):
    user = user_data.Users.get_user(call.message.chat.id,
                                    call.message.from_user.first_name,
                                    call.message.from_user.last_name)
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text('Выберите дату выезда.',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        if result < user.arrival_date:
            log_info.info(f'{user.name} {user.surname} ввел неверную'
                          f' дату выезда: {result}')
            bot.edit_message_text('Введенная вами дата не может'
                                  ' быть меньше даты заезда.'
                                  '\nПовторите выбор',
                                  call.message.chat.id,
                                  call.message.message_id)
            log_info.info(f'{user.name} {user.surname} ввел дату'
                          f' {result} которая меньше даты заезда.')
            departure_date(call.message)
        else:
            user.departure_date = result
            bot.edit_message_text(f"Дата выезда: {result}",
                                  call.message.chat.id,
                                  call.message.message_id)
            # расчет количество проведенных суток
            user.sum_days = user.departure_date - user.arrival_date
            # запрос у пользоателя на необходимость фотографий отелей
            bot.send_message(call.message.chat.id, 'Сколько отелей вы хотите'
                                                   ' получить?\nОграничения '
                                                   'вывода от 1 до 24.')
            bot.register_next_step_handler(call.message, checking_the_input)


def checking_the_input(message):
    """
    Функция отвечает за проверку введенного количество отелей,
    при привышении лимита производит повторный запрос до момента введения
    актуальных данных, после этого создает две кнопки на запрос нужны ли
    фотографии после чего переходит к функции
    : photo_processing
    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    try:
        if 0 < int(message.text) < 25:
            user.number_of_hotels = message.text

            keyboard = types.InlineKeyboardMarkup()
            bottum1 = types.InlineKeyboardButton("Да", callback_data="да")
            bottum2 = types.InlineKeyboardButton("Нет", callback_data="нет")
            keyboard.add(bottum1, bottum2)
            bot.send_message(message.chat.id, 'Хотите ли вы получить '
                                              'фотографии?',
                             reply_markup=keyboard)
        else:
            log_info.info(f'{user.name} {user.surname} ввел неверное значение'
                          f' количество отелей: {message.text}')
            bot.send_message(message.chat.id,
                             'Вы ввели неверное значение.\nПовторите ввод.'
                             '\nСколько отелей вы хотите получить?')
            bot.register_next_step_handler(message, checking_the_input)
    except ValueError:
        log_error.error('произошла ошибка: ', exc_info=True)
        log_info.info(f'{user.name} {user.surname} ввел неверное значение'
                      f' количество отелей: {message.text}')
        bot.send_message(message.chat.id,
                         'Вы ввели неверное значение.\nПовторите ввод.'
                         '\nСколько отелей вы хотите получить?')
        bot.register_next_step_handler(message, checking_the_input)


@bot.callback_query_handler(func=lambda call: call.data in ['да', 'нет'])
def photo_processing(message):
    """
    Функция 'ловит' нажатую пользователем кнопку и на основе его выбора
    направляет на выполнене запросы:

    'да' - происходит запрос на количество необходимых фотографий
           и переход после этого в функцию
           :getting_photos
           для определения вывода данных

    'нет' - производит отпределение поиска критерий введеных
            пользователем, направляет в файл сбора информации
            и направляет данные на вывод.
            По итогу выводит полученные от поисковика отели
    """
    bot.edit_message_text(f"Вы выбрали: {message.data.lower()}",
                          message.message.chat.id,
                          message.message.message_id)
    user = user_data.Users.get_user(message.from_user.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)

    def withdrawal_of_hotels(user):  # вывод отелей без фото
        for hotels_room in user.hotel:

            bot.send_message(message.from_user.id,
                             user.hotel[hotels_room]['data'])
        sqlbase.connecting_to_database(user, 'добавление')
        initial_state_class(user)

    if message.data.lower() in ['нет', 'да']:
        if message.data.lower() == 'да':
            user.photo_hotel = message.data.lower()
            answer_photo = bot.send_message(message.from_user.id,
                                            'Сколько фотографий вы хотели'
                                            ' бы получить?'
                                            '\nЛимит по количеству: 6')
            bot.register_next_step_handler(answer_photo, getting_photos)
        elif message.data.lower() == 'нет':
            if user.selection == '/lowprice':
                bot.send_message(message.from_user.id,
                                 'Запрос выполняется, ожидайте...')
                user.hotel = lowprice.sorting_hotels(user, message)
                withdrawal_of_hotels(user)
            elif user.selection == '/highprice':
                bot.send_message(message.from_user.id,
                                 'Запрос выполняется, ожидайте...')
                user.hotel = highprice.sorting_hotels(user, message)
                withdrawal_of_hotels(user)
            elif user.selection == '/bestdeal':
                answer_prise = bot.send_message(message.from_user.id,
                                                'Введите минимальную'
                                                ' цену проживаниия.')
                bot.register_next_step_handler(answer_prise, minimum_price)

    else:
        log_info.info(f'{user.name} {user.surname} выбрал неверное '
                      f'значение: {message.data}')
        bot.send_message(message.from_user.id, 'Значение должно быть "да" '
                                               'или "нет" повторите ввод.')
        bot.register_next_step_handler(message, photo_processing)


def getting_photos(message):
    """
    Функция преднзначена для определния количество необходимых пользователю
    фотографий отеля.
    Проверяет ввод пользователя если он больше лимита (6) устанавливает
    стандартное значение равное 6, после чего определяе критерии посика
    и выводит результат
    При неверном вводе просит повтоить ввод.

    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)

    def withdrawal_of_hotels(user):  # функция вывода отелей
        for hotels_room in user.hotel:
            media = user.hotel[hotels_room].get('photo')
            bot.send_media_group(message.chat.id, media=media)
            bot.send_message(message.chat.id,
                             user.hotel[hotels_room]['data'][0])
        sqlbase.connecting_to_database(user, 'добавление')
        initial_state_class(user)

    if message.text.isdigit():
        if int(message.text) > 0:
            if int(message.text) > 6:
                bot.send_message(message.from_user.id,
                                 'Введенное значение превышает возможный '
                                 'лимит.'
                                 '\nКоличество фотографий изменено на 6.\n')
                user.number_photos = 6
            else:
                user.number_photos = int(message.text)
            if user.selection == '/lowprice':
                bot.send_message(message.from_user.id,
                                 'Запрос выполняется, ожидайте...')
                user.hotel = lowprice.sorting_hotels(user, message)
                withdrawal_of_hotels(user)
            elif user.selection == '/highprice':
                bot.send_message(message.from_user.id,
                                 'Запрос выполняется, ожидайте...')
                user.hotel = highprice.sorting_hotels(user, message)
                withdrawal_of_hotels(user)
            elif user.selection == '/bestdeal':
                bot.send_message(message.from_user.id, 'Введите минимальную'
                                                       ' цену проживаниия.')
                bot.register_next_step_handler(message, minimum_price)
        else:
            log_info.info(f'{user.name} {user.surname} ввел неверный ответ'
                          f' необходимости фотографий: {message.text}')
            bot.send_message(message.from_user.id, 'Введено не верное'
                                                   ' значение. Повторите'
                                                   ' ввод.')
            bot.register_next_step_handler(message, getting_photos)
    else:
        log_info.info(f'{user.name} {user.surname} ввел неверный ответ'
                      f' необходимости фотографий: {message.text}')
        bot.send_message(message.from_user.id, 'Введено не верное значение.'
                                               ' Повторите ввод.')
        bot.register_next_step_handler(message, getting_photos)


def minimum_price(message):
    """
    Функция проверки вводенного значения минимальной суммы стоимости отеля
    отлавливает значение не верного формата проверяет число введенное
    пользователем, при необходимости производит повтор ввода

    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    if message.text.isdigit():
        if int(message.text) <= 0:
            bot.send_message(message.from_user.id, 'Сумма не может быть'
                                                   ' отрицательной. '
                                                   'Повторите ввод.')
            bot.register_next_step_handler(message, minimum_price)
            log_info.info(f'{user.name} {user.surname} ввел неверную минимальную'
                          f' цену за проживание: {message.text}')
        else:

            user.minimum_price = int(message.text)
            bot.send_message(message.from_user.id, 'Введите максимальныю'
                                                   ' сумму проживания.')
            bot.register_next_step_handler(message, max_price)
    else:
        log_info.info(f'{user.name} {user.surname} ввел неверную минимальную'
                      f' цену за проживание: {message.text}')
        bot.send_message(message.from_user.id, 'Введено не верное'
                                               ' значение. '
                                               'Повторите ввод.')
        bot.register_next_step_handler(message, minimum_price)



def max_price(message):
    """
     Функция проверки вводенного значения максимальной суммы стоимости отеля
    отлавливает значение не верного формата проверяет число введенное
    пользователем, при необходимости производит повтор ввода
    """

    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    if message.text.isdigit():
        if int(message.text) < 0 or int(message.text) < user.minimum_price:
            bot.send_message(message.from_user.id, 'Сумма не может быть меньше'
                                                   ' 0 либо меньше минимальной'
                                                   ' суммы.\n Повторите ввод.'
                             )
            bot.register_next_step_handler(message, max_price)
        else:
            user.max_price = int(message.text)
            bot.send_message(message.from_user.id, 'Введите растояние'
                                                   ' до центра.')
            bot.register_next_step_handler(message, distance_center)
    else:
        log_info.info(f'{user.name} {user.surname} ввел неверную максимальную'
                      f' цену за проживание: {message.text}')
        bot.send_message(message.from_user.id, 'Введено не верное'
                                               ' значение. '
                                               'Повторите ввод.')
        bot.register_next_step_handler(message, max_price)


def distance_center(message):
    """
    Фунция отслеживает ввод пользователя необходимого растояния до центра
    города, проверяет правильность ввода, при необходимости запрашивает ввод
    повторно.
    Проверяет находжение отелей, при отсутствии отелей сообщает об этом,
    выводи данные о найденных отелях.
    """

    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    if message.text.isdigit():
        if int(message.text) <= 0:
            log_info.info(f'{user.name} {user.surname} ввел неверное растояние'
                          f' до центра : {message.text}')
            bot.send_message(message.from_user.id, 'Растояние не может быть'
                                                   ' меньше 0.'
                                                   '\n Повторите ввод.')
            bot.register_next_step_handler(message, distance_center)
        else:
            bot.send_message(message.from_user.id,
                             'Запрос выполняется, ожидайте...')
            user.to_the_center = int(message.text)
            user.hotel = bestdeal.sorting_hotels(user, message)

            if len(user.hotel) == 0:
                log_info.info(
                    f'По запросу {user.name} {user.surname} не'
                    f' найдено отолей.')
                bot.send_message(message.from_user.id,
                                 'К сожалению по вашим данным отелей'
                                 ' не найдено.')
            else:
                bot.send_message(message.from_user.id,
                                 f'Количество найденных по вашему'
                                 f' запросу отелей: {len(user.hotel)}.')
                for queue, hotels_room in enumerate(user.hotel):
                    if user.photo_hotel == 'да':
                        if queue > int(user.number_of_hotels)-1:
                            break
                        media = user.hotel[hotels_room].get('photo')
                        bot.send_media_group(message.chat.id, media=media)
                        bot.send_message(message.chat.id,
                                         user.hotel[hotels_room]['data'][0])
                    else:
                        if queue > int(user.number_of_hotels)-1:
                            break
                        bot.send_message(message.from_user.id,
                                         user.hotel[hotels_room]['data'])
                sqlbase.connecting_to_database(user, 'добавление')
                initial_state_class(user)
    else:
        log_info.info(f'{user.name} {user.surname} ввел неверное растояние'
                      f' до цента: {message.text}')
        bot.send_message(message.from_user.id, 'Введено не верное значение.'
                                               ' Повторите ввод.')
        bot.register_next_step_handler(message, distance_center)



# стартовая функция для запуска бота и определения его действия
@bot.message_handler(commands=['start', 'привет'])
def start_handler(message):

    bot.send_message(message.chat.id, 'Добро пожаловать {0}!\n\n'
                     'Этот бот предназначен для поиска\n'
                     'наиболее выгодных для вас отелей.\n\n'
                     'Команды для начала работы:\n\n'
                     '/help — помощь по командам бота;\n'
                     '/lowprice — самых дешёвых отелей в городе;\n'
                     '/highprice — самых дорогих отелей в городе;\n'
                     '/bestdeal — отелей, наиболее подходящих по цене '
                                      'и расположению от центра;\n'
                     '/history — истории поиска отелей.'
                     .format(message.from_user.first_name))


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def recording_selection(message):
    """
    функция запрашивает у польхователя название города для поиска
    и сохраняеи его выбор приоритетев поиска

    :user.selection - выбор пользователя основного поиска
    :checking_the_city - функция проверки правильности ввода города
    :search_areas.choosing_a_neighborhood - функция переходящая в формирование
                                            районов города
    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    user.selection = message.text  # запись выбора команды пользователя
    bot.send_message(message.chat.id, 'Введите название города для поиска'
                                      ' отелей:\nНазвание не должно содердать'
                                      ' цифры и спецсимолы.')
    bot.register_next_step_handler(message, checking_the_city)


def checking_the_city(message):
    """
    Функция проверяет правильно ли введен город при успешной проверке
    делает запрос на районы города
    :search_areas.choosing_a_neighborhood - запрос на формирование выбора
                                            районов
    """
    user = user_data.Users.get_user(message.chat.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    # паттерн на разрешонные символы
    pattern = re.compile("^[a-zA-Zа-яА-ЯёЁ]+$")
    # проврка правильности ввода
    checking_city = pattern.search(message.text) is not None
    if checking_city:
        user.city = message.text  # запись города необходимый пользователю
        search_areas.choosing_a_neighborhood(message)
    else:
        log_info.info(f'{user.name} {user.surname} ввел неверное '
                      f'название города: {message.text}')
        bot.send_message(message.chat.id, 'Ошибка ввода.\nВведите название'
                                          ' города повторно.')
        bot.register_next_step_handler(message, checking_the_city)


# функция принимающая выбор пользователя от кнопки и сохраняющая результат
@bot.callback_query_handler(func=lambda mesage: True)
def callback_inline_first(message):
    """
    Функция 'ловит' выбор района пльзователя, создает переменную с
    йд необходимого района, а так же производит создание переменной
    для определения центра района

    :user.id_district - йд выбранного района
    :user.city_center - координаты центра района
    :arrival_date - функция отвечающая за ввод даты заезда
    """
    user = user_data.Users.get_user(message.from_user.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    user.id_district = message.data  # созранение йд необходимого рйона

    # цикл для ответа бата где пользователь выбрал поиск
    for selected_city in user.city_area:
        if selected_city['destination_id'] == user.id_district:
            user.city_center = selected_city['latitude'],\
                               selected_city['longitude']
            city = selected_city['city_name']
    bot.edit_message_text(f"Вы выбрали: {city}",
                          message.message.chat.id,
                          message.message.message_id)
    # вызов функции запрашивающая дату заезда и пользователя
    arrival_date(message)


@bot.message_handler(commands=['help'])
def start_help(message):
    """
    Функция предназначена для вывода вспомогательной информации,
    а так же при прирывании цикла пользователем задействуется
    данная функция.
    """
    bot.send_message(message.chat.id, 'Список команд работы с ботом:\n\n'
                                      '/help — помощь по командам бота;\n'
                                      '/lowprice — самых дешёвых отелей'
                                      ' в городе;\n'
                                      '/highprice — самых дорогих отелей '
                                      'в городе;\n'
                                      '/bestdeal — отелей, наиболее подходящих'
                                      ' по цене и расположению от центра;\n'
                                      '/history — истории поиска отелей.')


@bot.message_handler(commands=['history'])
def start_histori(message):
    """
    Функция предназначена для работы с историй поисков
    пользователя.
    /whole — Вывод всей истории;
    /past — Вывод последнего запроса;
    /removal — Удаление истоиии.
    """
    bot.send_message(message.chat.id, 'Команды для работы с историей:\n\n'
                                      '/whole — Вывод всей истории;\n'
                                      '/past — Вывод последнего запроса;\n'
                                      '/removal — Удаление истоиии.')


@bot.message_handler(commands=['whole', 'past', 'removal'])
def history_output(message):
    """
    Функция работает с историей поиска пользователя:
    histeri: формирует запрос к функции которая подключается к базе
             данных получает все найленную информацию и возвращает
             ее для обработки
    /whole: формирует вывод всей истории запросов
    /past: формирует только последний запрос пользователя
    /removal: сторает всю историю поиска пользователя
    """
    user = user_data.Users.get_user(message.from_user.id,
                                    message.from_user.first_name,
                                    message.from_user.last_name)
    # функция проверки прерывания цикла пользователем
    to_the_beginning(message, user)
    histeri = sqlbase.connecting_to_database(user, 'вывод')

    if message.text == '/whole':
        pass
        for hotels_room in histeri:
            bot.send_message(message.chat.id,
                             '{0}\nКоманда: {1}\nДата поиска: {2}'
                             .format(hotels_room[0][0],
                                     hotels_room[0][1],
                                     (hotels_room[0][2])))
            for i in hotels_room[1].values():
                bot.send_message(message.from_user.id, i['data'])
    elif message.text == '/past':
        bot.send_message(message.chat.id,
                         '{0}\nКоманда: {1}\nДата поиска: {2}'
                         .format(histeri[-1][0][0],
                                 histeri[-1][0][1],
                                 (histeri[-1][0][2])))
        for i in histeri[-1][1].values():
            bot.send_message(message.from_user.id, i['data'])
    elif message.text == '/removal':
        sqlbase.connecting_to_database(user, 'удаление')
        bot.send_message(message.chat.id, 'История ваших запросов'
                                          ' полность стерта.')

def to_the_beginning(message, user):
    """
    Функция предназначена для прерывания цепочки запросов от пользователя
    и переход к новому поиску
    initial_state_class(user): обнуление всех поисковых запросов
                               в классе пользователя
    start_help(message): переход к вункции предосталяющую выбор нового дейсвия
                         она же функция помощи
    breakpoint(): прерываем сессию исполнения
    """
    if message.text in list_commands:
        bot.send_message(message.chat.id, 'Запрос прерван.'
                                          '\nВыберите новое действие.')
        initial_state_class(user)
        start_help(message)
        breakpoint()


def initial_state_class(user):
    """
    Функция обнуления всех данные введенных и полученых пользователем
    (о пользователе)
    """
    user.city = None
    user.id_district = None
    user.to_the_center = None
    user.minimum_price = None
    user.max_price = None
    user.arrival_date = None
    user.departure_date = None
    user.sum_days = None
    user.photo_hotel = None
    user.number_photos = None
    user.cost_hotel = None
    user.sum_cost = None
    user.id_hotels = None
    user.selection = None
    user.number_of_hotels = None
    user.number_of_people = None
    user.hotel = None
    user.hotel_bas = None
    user.city_area = None
    user.city_center = None
    user.distance_center = None


if __name__ == '__main__':
    bot.polling()
