import platform
import json

from dataHandler import *


class IncorrectLoginData(Exception):
    pass


def get_self_user() -> 'User':
    try:
        if ConfigHandler.__getattr__(ConfigHandler, 'username'):
            u = User.get_user(ConfigHandler.__getattr__(ConfigHandler, 'username'))
            u.password = ConfigHandler.__getattr__(ConfigHandler, 'password')
            if u.login(with_exceptions=False):
                return u
        return 'Пожалуйста, войдите в аккаунт'
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
        self.is_exist = None
        self.name = name
        self.balance = 5
        self.password = password
        self.additions = additions
        if balance is not None:
            self.balance = int(balance)

    def save(self):
        SQLHandler.new_user(self.name, str(self.balance), self.password, str(self.additions))

    def login(self, with_exceptions=True):
        """Вход в аккаунт(сверка данных с БД)

        :raises: UserNotFound, IncorrectLoginData"""
        try:
            a = SQLHandler.get_user('name', self.name)[0]
            name, psw = a[0], a[2]
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
        data = SQLHandler.get_user('name', name)[0]
        data = (data[0], data[1], '', *data[3:])  # Удаление пароля из данных
        return User(*data)

    def __str__(self):
        return f'\tНик: {self.colored_name()}\n\tБаланс: {self.balance} зМ'

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        if key == 'is_exist':
            return
        if self.is_exist is None:
            u = [u for u in User.get_user_list(is_save=True) if u.name == self.name]  # Check user is exist
            if len(u) == 1:
                self.is_exist = True
            else:
                self.is_exist = False
        elif self.is_exist is True:
            if isinstance(value, dict):
                value = json.dumps(value)
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