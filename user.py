import platform
import json

from dataHandler import *


class IncorrectLoginData(Exception):
    pass


def get_self_user():
    try:
        if ConfigHandler.__getattr__(ConfigHandler, 'username'):
            u = User(ConfigHandler.__getattr__(ConfigHandler, 'username'),
                     password=ConfigHandler.__getattr__(ConfigHandler, 'password'))
            if u.login(with_exceptions=False):
                return u
            else:
                return 'Пожалуйста, войдите в аккаунт'
        return User.get_user(platform.node())
    except UserNotFound:
        return 'Пожалуйста, войдите в аккаунт'


class User:
    def __init__(self, name, balance=None, password='', additions=None):
        '''Создание юзера

        :param name: Ник
        :param balance: Баланс
        :param password: Пароль от аккаунта(нужен для входа)
        '''
        if additions is None:
            additions = {}
        else:
            additions = json.loads(additions)
        self.name = name
        self.balance = 5
        self.password = password
        self.additions = additions
        if balance is not None:
            self.balance = int(balance)

    def save(self):
        SQLHandler.new_user(self.name, str(self.balance), self.password, str(self.additions))

    def login(self, with_exceptions=True):
        """Вход в аккаунт(сверка данных с БД)"""
        try:
            name, _, psw = SQLHandler.get_user('name', self.name)[0]
        except ValueError:
            if with_exceptions:
                raise UserNotFound()
            else:
                return False
        else:
            if name == self.name and psw == self.password:
                return True
            if with_exceptions:
                raise IncorrectLoginData('Invalid username or password')
            else:
                return False

    def colored_name(self):
        if self.additions.get('color') is not None:
            return f'<span style="color: {self.additions["color"]};">' + self.name + '</span>'
        else:
            return self.name

    @staticmethod
    def get_user_list(is_save=False):
        a = []
        for v in SQLHandler.get_users_list():
            a.append(User(*v) if not is_save else UserForSave(*v))
        return a

    @staticmethod
    def get_user(name):
        data = SQLHandler.get_user('name', name)[0][:-1]
        return User(*data)

    def __str__(self):
        return f'\tНик: {self.colored_name()}\n\tБаланс: {self.balance} зМ'

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        users_list = User.get_user_list(is_save=True)
        u = [u for u in users_list if u.name == self.name]
        if len(u) == 1:
            if isinstance(value, dict):
                value = str(value)
            SQLHandler.update_user(self.name, key, value)


class UserForSave(User):
    def __init__(self, name, balance=None, password='', additions=None):
        """Используется для сохранения данных пользователя в файл"""
        if additions is None:
            additions = {}
        else:
            additions = json.loads(additions)
        args = {'name': name, 'balance': balance, 'password': password,
                'additions': additions}
        for i, k in args.items():
            self.__dict__[i] = k

    def __setattr__(self, key, value):
        self.__dict__[key] = value