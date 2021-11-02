from PyQt5.QtWidgets import QLineEdit
from typing import List, Dict

# --- Функции для предметов магазина


def _task_add_priority(*args):
    """args = (task)"""
    args[0].priority += 1


def _user_set_namecolor(u):
    """args = (user)"""
    u.additions = {**u.additions, **{'color': 'red'}}


class ShopItem:
    def __init__(self, name, price, need_args: tuple, func):
        """Создание обьекта предмета магазина

        :param name:
        :param price:
        :param need_args: Аргументы, необходимые для функционала, передаются не обьекты, а названия классов
        :param func: Функция, выполняющая необходимые действия"""
        self.name = name
        self.price = price
        self.need_args = need_args
        # Есть: selfuser, user, task
        self.func = func


class Shop:
    """Обьект магазина

    :arg items: Предметы магазина
    :type items: tuple
    :arg input_fields: Поля для ввода need_args, вид - 'arg_name': (class, *args_for_class)
    :type input_fields: dict"""
    items: List[ShopItem] = (
        ShopItem('Добавить приоритет задаче',
                 1,
                 ('task',),
                 _task_add_priority),
        ShopItem('Цветной ник',
                 1,
                 ('selfuser',),
                 _user_set_namecolor)
    )
    input_fields: Dict[str, tuple] = {
        'task': (QLineEdit, 'Название СВОЕЙ задачи')
    }

    @staticmethod
    def get_shopitem(name):
        for i in Shop.items:
            if i.name == name:
                return i
        return None