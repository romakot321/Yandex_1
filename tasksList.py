import datetime
from PyQt5.QtWidgets import QPushButton, QTextBrowser, QVBoxLayout
from user import User, get_self_user
import platform
from dataHandler import SQLHandler


class TaskAlreadyExist(Exception):
    pass


def get_tasksInfo_text(user):
    """Получение информации о заданиях пользователя
    :return str
    """
    s = ''
    tasks_list = TasksList.get_tasks_list()
    # --- Проверка на непроверенные задачи
    notcheck_list = [t for t in tasks_list if t.creator_name == user.name and \
                     str(t.performer_name) != 'None' and str(t.done) not in ('False', 'None') and \
                     not str(t.done).startswith('Decline(')]
    if len(notcheck_list) > 0:
        s += 'У вас есть непроверенные задачи\n'
    # --- Проверка на отклоненные задачи
    decline_list = [t for t in tasks_list if t.performer_name == user.name and \
                    str(t.done).startswith('Decline(')]
    if len(decline_list) > 0:
        s += 'У вас есть отклоненные задачи\n'

    return s


class TasksList:
    @staticmethod
    def get_tasks_list(is_for_save=False, sort=False) -> list:
        """Получение списка заданий
        :param is_for_save: Список для сохранения в БД?
        :param sort: Отсортировать по приорететности?
        :return: list
        """
        a = []
        for v in SQLHandler.get_tasks_list():
            a.append(Task(*v) if not is_for_save else TaskForSave(*v))
        if sort:
            a = sorted(a, key=lambda i: i.priority)
        return a

    @staticmethod
    def get_task(data) -> 'Task':
        """Получение задания из списка по загаловку

        :param data: Загаловок или айди
        :return: class 'Task'
        """
        if isinstance(data, str) and data.isdigit():
            data = int(data)
        if isinstance(data, int):
            return Task(*SQLHandler.get_task('id', data))
        else:
            return Task(*SQLHandler.get_task('title', data))


class Task(TasksList):
    def __init__(self, title, price, description, creator_name,
                 performer_name=None, create_time=None, id=None, done=None, priority=0,
                 agree_list=None):
        """Создание задания

        :param title: Загаловок
        :param price: Вознаграждение
        :param description: Описание
        :param creator_name: Ник создателя задания
        :param performer_name: Ник исполнителя
        :param done: Примечание к выполненному заданию
        :param priority: Приорететность задачи в списке
        :param agree_list: Список откликнувшихся на задачу
        """
        self.is_exist = None
        self.id = int(id) if id is not None else len(Task.get_tasks_list(True))
        self.title = str(title)
        self.price = int(price)
        self.description = str(description)
        self.creator_name = str(creator_name)
        self.performer_name = performer_name
        self.create_time = create_time if create_time is not None else datetime.datetime.now()
        self.done = False
        self.priority = priority
        if agree_list == "['']":
            agree_list = None
        self.agree_list = agree_list.split(', ') if agree_list is not None else ''
        if done is not None:
            self.done = False if not done else done

    def save(self):
        """Сохранение задания в БД"""
        for i in TasksList.get_tasks_list():
            if i.id == self.id:
                continue
            if i.creator_name == self.creator_name and i.title == self.title:
                raise TaskAlreadyExist(f"Task with name {self.title} and created by {self.creator_name} already exist")
        SQLHandler.new_task(self.title, str(self.price), self.description, self.creator_name,
                            str(self.performer_name), str(self.create_time), str(self.id), str(self.done),
                            str(self.priority), str(self.agree_list))

    @staticmethod
    def delete(taskid):
        SQLHandler.delete_task(taskid)

    @staticmethod
    def finish(taskid, url=None):
        """Отметить задачу выполненной или завершить задачу"""
        task = Task.get_task(int(taskid))
        if get_self_user().name == task.creator_name:
            User.get_user(task.performer_name).balance += task.price
            Task.delete(int(taskid))
        else:
            task.done = url

    @staticmethod
    def add_agree(taskid):
        t = Task.get_task(int(taskid))
        t.agree_list = t.agree_list + [get_self_user().name]

    @staticmethod
    def agree(taskid, username):
        t = Task.get_task(int(taskid))
        t.performer_name = username
        t.agree_list = ''

    def __setattr__(self, key, value):
        """Изменение атрибута с занесением в БД"""
        self.__dict__[key] = value
        if key == 'is_exist':
            return
        if self.is_exist is None:
            t = [t for t in Task.get_tasks_list(is_for_save=True) if int(t.id) == self.id]
            if len(t) == 1:
                self.is_exist = True
            else:
                self.is_exist = False
        elif self.is_exist is True:
            if isinstance(value, list):
                value = ', '.join(value)
            SQLHandler.update_task(self.id, key, value)

    def __str__(self):
        s = f'''{self.title} (Создатель: {self.creator_name}, выполняет: {self.performer_name})
\n\n\t{self.description}\n\n\n\tЦена: {self.price},\n\tвремя создания: {self.create_time}'''
        return s

    def __eq__(self, other):
        return self.id == other.id and self.create_time == other.create_time


class TaskForSave(Task):
    """Используется для сохранения данных пользователя в файл"""
    def __init__(self, title, price, description, creator_name,
                 performer_name=None, createtime=None, id=None, done=None, priority=0,
                 agree_list=None):
        args = {'title': title, 'price': price, 'description': description,
                'creator_name': creator_name, 'performer_name': performer_name,
                'create_time': createtime, 'id': id, 'done': done, 'priority': priority,
                'agree_list': agree_list}
        for i, k in args.items():
            self.__dict__[i] = k

    def __setattr__(self, key, value):
        self.__dict__[key] = value
