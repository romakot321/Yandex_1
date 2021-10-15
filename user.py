import platform


class UserNotFound(Exception):
    pass


def get_self_user():
    try:
        return User.get_user('OBAGEN')
    except UserNotFound:
        User(platform.node()).save()
        return User.get_user(platform.node())


class User:
    filename = 'b.txt'

    def __init__(self, name, balance=None):
        '''Создание юзера

        :param name: Ник
        '''
        self.name = name
        self.balance = 0
        if balance is not None:
            self.balance = int(balance)

    def save(self):
        with open(User.filename, 'a') as f:
            f.write('|||'.join([self.name, str(self.balance)]) + '\n')

    @staticmethod
    def get_user_list(is_save=False):
        a = []
        with open(User.filename, 'r') as f:
            for line in f:
                if line.strip() == '':
                    continue
                if is_save:
                    a.append(UserForSave(*line.split('|||')))
                else:
                    a.append(User(*line.split('|||')))
        return a

    @staticmethod
    def get_user(name):
        a = [u for u in User.get_user_list() if u.name == name]
        if len(a) == 0:
            raise UserNotFound()
        return a[0]

    @staticmethod
    def resave_users_list(users_list=None):
        with open(User.filename, 'w+') as f:
            f.write('')
        if users_list is None:
            users_list = User.get_user_list()
        for u in users_list:
            u.save()

    def __str__(self):
        return f'\tНик: {self.name}\n\tБаланс: {self.balance} зМ'

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        users_list = User.get_user_list(is_save=True)
        u = [u for u in users_list if u.name == self.name]
        if len(u) == 1:
            users_list[users_list.index(u[0])].__dict__[key] = value
            self.resave_users_list(users_list)


class UserForSave(User):
    def __init__(self, name, balance=None):
        """Используется для сохранения данных пользователя в файл"""
        args = {'name': name, 'balance': balance}
        for i, k in args.items():
            self.__dict__[i] = k

    def __setattr__(self, key, value):
        self.__dict__[key] = value