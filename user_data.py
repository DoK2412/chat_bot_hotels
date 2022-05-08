"""Файл предназначен для реализации класса пользователя"""


class Users:
    user = dict()

    def __init__(self, chat_id, name, surname):

        self.id_chat = chat_id         # id чата *
        self.name = name               # имя пользователя *
        self.surname = surname         # фамилия пользователя *
        self.city = None               # название города *
        self.id_district = None        # йд района *
        self.to_the_center = None      # растояние до центра *
        self.minimum_price = None      # минимальная сумма *
        self.max_price = None          # максимальная сумма *
        self.arrival_date = None       # дата заезда *
        self.departure_date = None     # дата выезда *
        self.sum_days = None           # сумма проведенных дней
        self.photo_hotel = None        # нужно ли фото отеля *
        self.number_photos = None      # количество фото *
        self.cost_hotel = None         # стоимость гостинници (за сутки) *
        self.sum_cost = None           # стоимость гостинници (общая)
        self.id_hotels = None          # йд гостинници *
        self.selection = None          # выбор пользователя *
        self.number_of_hotels = None   # количество выводимых отелей *
        self.number_of_people = None   # количество проживающих
        self.hotel = None              # список полученных отелей *
        self.hotel_bas = None          # отели бля базы данных *
        self.city_area = None          # район города *
        self.city_center = None        # координаты центра города *
        self.distance_center = None    # растояний до центра города *

    @classmethod
    def get_user(cls, chat_id, name, surname):
        if chat_id in cls.user.keys():
            return cls.user[chat_id]
        else:
            return cls.add_user(chat_id, name, surname)

    @classmethod
    def add_user(cls, chat_id, name, surname):
        cls.user[chat_id] = Users(chat_id, name, surname)
        return cls.user[chat_id]
