import datetime
from PyQt5.QtWidgets import QPushButton, QTextBrowser, QVBoxLayout
from user import User
import platform


def get_tasksInfo_text(user):
    """Получение информации о заданиях пользователя
    :return str
    """
    s = ''
    tasks_list = TasksList.get_tasks_list()
    # --- Проверка на непроверенные задачи
    notcheck_list = [t for t in tasks_list if t.creator_name == user.name and \
                     str(t.performer_name) != 'None' and t.done not in ('False', 'None')]
    if len(notcheck_list) > 0:
        s += 'У вас есть непроверенные задачи\n'

    return s


class TasksList:
    filename = 'a.txt'

    @staticmethod
    def resave_tasks_list(tasks_list=None):
        with open(TasksList.filename, 'w+', encoding='utf-8') as f:
            f.write('')
        if tasks_list is None:
            tasks_list = TasksList.get_tasks_list()
        for t in tasks_list:
            t.save()

    @staticmethod
    def get_tasks_list(is_for_save=False):
        """Получение списка заданий
        :param is_for_save: Список для сохранения в БД?
        :return: list
        """
        a = []
        with open(TasksList.filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                if line.strip() == '':
                    continue
                a.append(Task(*line.split('|||')) if not is_for_save
                         else TaskForSave(*line.split('|||')))
        return a

    @staticmethod
    def get_task(data):
        """Получение задания из списка по загаловку

        :param data: Загаловок или айди
        :return: class Task
        """
        tasks = TasksList.get_tasks_list()
        if not tasks:
            return None
        if isinstance(data, str) and data.isdigit():
            data = int(data)
        return [t for t in tasks if t.title == data or t.id == data][0]


class Task(TasksList):
    def __init__(self, title, price, description, creator_name,
                 performer_name=None, create_time=None, id=None, done=None):
        """Создание задания

        :param title: Загаловок
        :param price: Вознаграждение
        :param description: Описание
        :param creator_name: Ник создателя задания
        :param performer_name: Ник исполнителя
        :param done: Примечание к выполненному заданию
        """
        self.id = int(id) if id is not None else len(open(TasksList.filename, 'r').readlines()) - 1
        self.title = str(title)
        self.price = int(price)
        self.description = str(description)
        self.creator_name = str(creator_name)
        self.performer_name = performer_name
        self.create_time = create_time if create_time is not None else datetime.datetime.now()
        self.done = False
        if done is not None:
            self.done = False if not done else done

    def save(self):
        """Сохранение задания в БД"""
        with open(TasksList.filename, 'a', encoding='utf-8') as f:
            f.write('|||'.join([self.title, str(self.price), self.description, self.creator_name,
                                str(self.performer_name), str(self.create_time), str(self.id), str(self.done)]) + '\n')

    @staticmethod
    def delete(taskid):
        t_list = TasksList.get_tasks_list()
        t_list.pop(int(taskid))
        TasksList.resave_tasks_list(t_list)

    @staticmethod
    def finish(taskid, url=None):
        """Отметить задачу выполненной или завершить задачу"""
        tasks_list = TasksList.get_tasks_list()
        task = Task.get_task(int(taskid))
        if User.get_user(platform.node()).name == task.creator_name:
            tasks_list.pop(int(taskid))
            User.get_user(task.performer_name).balance += task.price
        else:
            task.done = url
            tasks_list = TasksList.get_tasks_list()
            tasks_list.pop(int(taskid))
            tasks_list = [i for i in tasks_list if not i == task] + [task]  # Занесение таска в конец списка
        TasksList.resave_tasks_list(tasks_list)

    @staticmethod
    def agree(taskid):
        task = Task.get_task(int(taskid))
        task.performer_name = User.get_user(platform.node()).name

    def __setattr__(self, key, value):
        """Изменение атрибута с занесением в БД"""
        self.__dict__[key] = value
        tasks_list = Task.get_tasks_list(is_for_save=True)
        t = [t for t in tasks_list if int(t.id) == self.id]
        if len(t) == 1:
            tasks_list[tasks_list.index(t[0])].__dict__[key] = value
            self.resave_tasks_list(tasks_list)

    def __str__(self):
        s = f'''{self.title} (Создатель: {self.creator_name}, выполняет: {self.performer_name})
\n\n\t{self.description}\n\n\n\tЦена: {self.price},\n\tвремя создания: {self.create_time}'''
        return s

    def __eq__(self, other):
        return self.id == other.id and self.create_time == other.create_time


class TaskForSave(Task):
    def __init__(self, title, price, description, creator_name,
                 performer_name=None, createtime=None, id=None, done=None):
        """Используется для сохранения данных пользователя в файл"""
        args = {'title': title, 'price': price, 'description': description,
                'creator_name': creator_name, 'performer_name': performer_name,
                'create_time': createtime, 'id': id, 'done': done}
        for i, k in args.items():
            self.__dict__[i] = k

    def __setattr__(self, key, value):
        self.__dict__[key] = value
