                #######Бот Search_room_bot предназначет для потска отелей по параметрам пользователя#######

                                                 ####Описание работы бота###

                                                        ####/help####

        Команда отвечает за повторный вывод команд которые доступны пользовалетю, работает из любого места программы завершая сеанс
    и предоставляя пользователю произвести новый выбор.

        Функция отвечающая за работу: main.py line 545 start_help()

                                                       ####/history####

        Команда отвечает за вывод истории запросов пользователя.
        Имеет следующую структуру:
                                /whole — Вывод всей истории запросов пользователя;
                                /past — Вывод последнего запроса пользователя;
                                /removal — Удаление истории всей истории запросов пользователя.

        Функция отвечающая за работу: main.py line 563 start_histori()

        После выбора необходимого действия срабатывает функция main.py line 578 history_output()
    работающая на основе файла sqlbase.py производит запрос к функции sqlbase.py line 8 connecting_to_database()
    в которой происходит выборка из базы данных через функцию sqlbase.py line38 add_data() и возврат данных.
        После чего происходит вывод данных в соответствии c необходимости через ветвление if elif else.


                                            ####/lowprice,  /highprice,  /bestdeal####

        При получении одной из данных команд срабатывает функция  recording_selection() происходит создание (проверка)
    экземпляра класса пользователя в файле user_data.py вся последующая работа с пользовательскими данными (добавление
    пользователя в базу) проверка наличия данного пользователя в базе, а так же все что связано с запросом пользователя
    и его вводимыми данными протекает через данный файл.

        После создание пользователя происходит запрос необходимого города,переход в функцию  main.py line 487 checking_the_city()
    проходит проверка правильности ввода города, при успехе запрос посылается в файл search_areas.py функция
    search_areas.py line 63 choosing_a_neighborhood() производит формирование кнопок с районами необходимого города.

        При выборе района функция main.py line 516 callback_inline_first() получает отклик пользователя, сохраняет его
    и переходит в функции main.py line 32 arrival_date() функция  запрашивает у пользователя дату заезда реализована
    на основе библиотекки telegram_bot_calendar, после ввода даты заезда происходит запрос даты выезда через функцию
    main.py line 86 departure_date() основана идентично предыдущей за исключением ряда проверок.

        Следующим шагом срабатывает функция main.py line 150 checking_the_input(). Функция проверяет корректность ввода
    количество отелей, создает 2 кнопки необходимости фотографий (да/нет), при выборе пользователем необходимости фото
    срабатывает функция main.py line 192 photo_processing()

        photo_processing() получает ответ пользователя и на основе производит ветвление работы:
    ответ "нет": в соответствии от выбора поиска  /lowprice - вызывает файл lowprice.py производит сбор отелей без фото
                                                  /highprice - вызывает файл highprice.py производит сбор отелей без фото
    после чего вызывает функцию main.py line 214 withdrawal_of_hotels() которая выводит отели пользователю, сохраняет поиск
    в базе данных и обнуляет поисковые данные пользователя для последующей корректной работы.

    ответ "да": формирует запрос количества фотографий и запускает функцию main.py line 255 getting_photos() которая проверяет
    корректность ввода, производит замену введенного числа если оно превышает заданный лимит.

        Далее происходит проверка выбора поиска  /lowprice - вызывает файл lowprice.py производит сбор отелей с фото
                                                 /highprice - вызывает файл highprice.py производит сбор отелей с фото
    после чего вызывается функция main.py line 272  withdrawal_of_hotels() которая выводи отели с фотографиями, сохраняет
    поиск в базу данных и обнуляет поисковые данные пользователя для последующей корректной работы.

        При выборе поиска /bestdeal происходит запрос минимальной цены и вызов функции main.py line 321 minimum_price()
    функция производит проверку значения и запрашивает максимальную цену номера, после ввода максимальной суммы
    вызывается функция main.py line 355  max_price() проверяющая правильность ввода и запрашивающая расстояние до центра,
    при получении данных о расстоянии вызывается функция main.py line 389 distance_center()

        Функция distance_center() проверяет правильность ввода данных о расстоянии, создает запрос в файл bestdeal.py
    который формирует список отелей с фотографиями или без в соответствии с выбором пользователя ранее.
    По итогу происходит вывод отелей, сохранение поиска в базу данных и обнуляет поисковые данные пользователя для
    последующей корректной работы.


                                                        ####файлы####

    main.py - содержит основной код программы;
    logger.py - на основании этого файла создается 2 логера c полным описанием для их создания
        - папка loggins содержит 2 файла error.log и info.log
            - error.log в файл записываются все ошибки происходящие в программе
            - info.log в файл записываются все неверные действия пользователя;
    sqlbase.py - файл содержит подключение к базу данные, все инструкции по получению, сохранению, удалению
                 поисковых запросов пользователя;
    user_data.py - файл предназначен для работы с пользователями, проверки наличия пользователя в базе
                   либо добавлении его в базу;
    .env - содержит токен, ключ, и входные данные в базу данных;

        Папка selection:

    search_areas.py - формирует поиск районов по городам и вывод кнопок для пользователя с выбором районов
    lowprice.py - формирует ответ из ряда отелей по поиску от меньшего к большему с фото (или без) в зависимости от запроса
                  пользователя
    highprice.py - формирует ответ из ряда отелей по поиску от большего к меньшему с фото (или без) в зависимости от запроса
                   пользователя
    bestdeal.py - формирует ответ из ряда отелей по поиску  определенных параметров необходимых пользователю.


    Все данные файла .env скрыты от просмотра, при необходимости просмотра работоспомобности обращаться в профиль либо вы всегда
        можете подставить свои токены и ключи из RapidAPI.