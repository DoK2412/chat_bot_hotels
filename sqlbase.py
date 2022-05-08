import mysql.connector  # подключение библиотеки SQL
from mysql.connector import Error  # подключение ошибок SQL
import json  # подключаем формат для обмена данных
import os  # подключение системной библиотеки


# подключаемся к базе данных
def connecting_to_database(user, action):
    """
        Функкция предназначена для обработки SQL запросов на сервер
    сохряняя, производя выботрку либо удаляя значения базы.
        Функция производит подключение к серверу с базой данных производит
    необходимое действие и закрывает базу.

    user : класс пользователя
    action : выбор действия пользователя

    add_data: функция добавляет новые данные в баззу
    select_data: функция производит выборку из базы, формирует список данных
                 и возвращает их для вывода пользователю
    delet_data: удаляет историю поиска пользователя

    """
    connection = None
    try:
        # создание курсора, подключение к базе
        connection = mysql.connector.connect(
            host='localhost',
            port='3306',
            user=os.getenv('user'),
            passwd=os.getenv('password'),
            database='user_base'
        )

        try:
            if action == 'добавление':
                name = user.name + ' ' + user.surname
                # формируем из словаря строку для записи в базу
                data_hotel = json.dumps(user.hotel_bas)
                with connection.cursor() as cursor:
                    insert_query = "INSERT INTO bot_data (id_chat, name," \
                                   " team, data_time, data) VALUES " \
                                   "(%s, %s, %s, %s, %s);"
                    info_user = (user.id_chat, name, user.selection,
                                 user.arrival_date, data_hotel)
                    cursor.execute(insert_query, info_user)
                    connection.commit()

            elif action == 'вывод':
                with connection.cursor() as cursor:
                    select_all_row = "SELECT data, name, team," \
                                     " data_time FROM bot_data " \
                                     "WHERE id_chat= {0}"\
                        .format(user.id_chat)
                    cursor.execute(select_all_row)
                    history = cursor.fetchall()
                    processed_list = list()
                    for i_history in history:
                        user_data = i_history[1], i_history[2],\
                                    i_history[3]
                        # формируем из строки словарь
                        history_output = json.loads(i_history[0])
                        processed = user_data, history_output
                        processed_list.append(processed)
                return processed_list

            elif action == 'удаление':
                with connection.cursor() as cursor:
                    update = "DELETE FROM bot_data " \
                             "WHERE id_chat = {0}".format(user.id_chat)
                    cursor.execute(update)
                    connection.commit()

        finally:
            connection.close()
    except Error as err:
        print(f'Ошибка: {err}')
    return connection
