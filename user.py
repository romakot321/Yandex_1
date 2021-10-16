import platform
from dataHandler import DataHandler


class UserNotFound(Exception):
    pass


def get_self_user():
    try:
        return User.get_user(platform.node())
    except UserNotFound:
        User(platform.node()).save()
        return User.get_user(platform.node())


class User:
    def __init__(self, name, balance=None):
        '''Создание юзера

        :param name: Ник
        '''
        self.name = name
        self.balance = 5
        if balance is not None:
            self.balance = int(balance)

    def save(self):
        DataHandler.new_user(self.name, str(self.balance), 'b')

    @staticmethod
    def get_user_list(is_save=False):
        a = []
        for v in DataHandler.get_users_list():
            v = v[:-1]
            a.append(User(name=v[0], balance=v[1]) if not is_save else UserForSave(name=v[0], balance=v[1]))
        # with open(User.filename, 'r') as f:
        #     for line in f:
        #         if line.strip() == '':
        #             continue
        #         if is_save:
        #             a.append(UserForSave(*line.split('|||')))
        #         else:
        #             a.append(User(*line.split('|||')))
        return a

    @staticmethod
    def get_user(name):
        data = DataHandler.get_user('name', name)[0][:-1]
        return User(*data)

    def __str__(self):
        return f'\tНик: {self.name}\n\tБаланс: {self.balance} зМ'

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        users_list = User.get_user_list(is_save=True)
        u = [u for u in users_list if u.name == self.name]
        if len(u) == 1:
            DataHandler.update_user(self.name, key, value)


class UserForSave(User):
    def __init__(self, name, balance=None):
        """Используется для сохранения данных пользователя в файл"""
        args = {'name': name, 'balance': balance}
        for i, k in args.items():
            self.__dict__[i] = k

    def __setattr__(self, key, value):
        self.__dict__[key] = value