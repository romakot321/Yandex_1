import sys
import os
from typing import List, Any

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog
from PyQt5.QtWidgets import QWidget, QLineEdit, QInputDialog
from PyQt5.QtCore import QEvent, Qt, QTimer, QTime

import dataHandler
from maindesing import Ui_MainWindow

from dataHandler import *
from tasksList import *
from user import *
from shop import *

ConfigHandler = ConfigHandler()


class App(QMainWindow, Ui_MainWindow):
    TIME_FOR_UPDATE: int = 10000  # ms

    def __init__(self):
        super().__init__()
        self.lastupdate_time = datetime.datetime.now()
        self.is_login = False  # Пользователь авторизован?
        self.shop_open = False  # Окно с магазином открытo?
        self.datarenew_timer = QTimer()
        self.datarenew_timer.timeout.connect(self.renewData)
        self.datarenew_timer.start(self.TIME_FOR_UPDATE)
        self.setupUi(self)
        self.initUI()
        self.initData()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('ААА')

        self.tasksListWidget.setLayout(self.tasksListLayout)
        self.tasksListWidget.setParent(None)
        self.scrollArea.setWidget(self.tasksListWidget)

        # --- Вход в аккаунт из конфига
        try:
            u = get_self_user()
            if isinstance(u, str):
                return
        except UserNotFound:
            pass
        else:
            u.password = ConfigHandler.password
            try:
                if u.login():
                    self.is_login = True
            except UserNotFound:
                pass

    def initData(self):
        """Обновление данных в выводе задач"""
        for i in reversed(range(self.tasksListLayout.count())):
            w = self.tasksListLayout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()
        # --- Функциональные кнопки
        if not self.is_login:
            self.addItem('Войти или зарегистрироваться')
        else:
            if self.shop_open:
                self.addItem('Вернуться')
                for i in Shop.items:
                    self.addItem(i.name)
            else:
                self.addItem('Выйти из аккаунта')
                self.addItem('Создать задачу')
                self.addItem('Открыть магазин')
                # --- Список задач
                for task in TasksList.get_tasks_list(sort=True):
                    if str(task.done).strip() not in ('False', 'None'):
                        if get_self_user().name not in (task.creator_name,
                                                        task.performer_name):
                            continue
                    self.addItem(task.title)

    def renewData(self):
        """Обновление отображаемых данных"""
        self.profileInfo.setText(str(get_self_user()))
        self.tasksInfo.setText(str(get_tasksInfo_text(get_self_user())))
        self.lastupdate_time = datetime.datetime.now()

    def buttonPress(self):
        # --- Отработка эвентов
        task = self.sender()
        if task and not self.shop_open:  # Обработка нажатий на задачи или функ кнопки
            # --- Нажатие на функциональные кнопки
            if task.text() == 'Создать задачу':
                self.clearOutput()
                # --- Форма для создание задачи
                line_title = QLineEdit('Название')
                line_price = QLineEdit('Цена за выполнение')
                self.description.setReadOnly(False)
                self.description.setText('Введите описание')
                createButton = QPushButton("Создать")
                createButton.clicked.connect(self.create_task)

                self.verticalLayout.addWidget(line_title)
                self.verticalLayout.addWidget(line_price)
                self.verticalLayout.addWidget(createButton)
            elif task.text() == "Выйти из аккаунта":
                self.is_login = False
                self.initData()
            elif task.text() == 'Войти или зарегистрироваться':
                self.clearOutput()
                self.description.setText('')
                # --- Форма для ввода данных пользователя
                line_name = QLineEdit('Ник')
                line_psw = QLineEdit('Пароль')
                loginbutton = QPushButton("Отправить")
                loginbutton.clicked.connect(self.login_user)

                self.verticalLayout.addWidget(line_name)
                self.verticalLayout.addWidget(line_psw)
                self.verticalLayout.addWidget(loginbutton)
            elif task.text() == 'Открыть магазин':
                self.shop_open = True
                self.clearOutput()
                self.initData()
            else:
                task = TasksList.get_task(task.text())
                self.show_task(task)
                self.initData()
        elif task and self.shop_open:  # Отработка нажатий на предметы магазина
            if task.text() == 'Вернуться':
                self.shop_open = False
                self.clearOutput()
                self.initData()
            else:
                self.clearOutput()
                i = Shop.get_shopitem(task.text())
                s = f'{i.name}\n\tЦена: {i.price} ЗМ'
                self.description.setText(s)
                # --- Форма для получения нужных аргументов
                for arg_name, field in Shop.input_fields.items():
                    if arg_name in i.need_args:
                        self.verticalLayout.addWidget(field[0](field[1]))
                button = QPushButton("Выполнить")
                self.verticalLayout.addWidget(button)
                button.clicked.connect(self.start_shopitem)

    def addItem(self, text, func=None):
        """Добавить кнопку в tasksListWidget"""
        if func is None:
            func = self.buttonPress
        b = QPushButton(text=text)
        b.clicked.connect(func)
        self.tasksListLayout.addWidget(b)

    def clearOutput(self):
        """Отчистить вывод(self.description и self.verticalLayout)"""
        for i in reversed(range(self.verticalLayout.count())):
            w = self.verticalLayout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()
        self.description.setText('')

    def start_shopitem(self):
        """Выполнение действия предмета магазина"""
        itemname = self.description.toPlainText().split('\n\t')[0]
        item = Shop.get_shopitem(itemname)
        args = []
        for i in reversed(range(self.verticalLayout.count())):
            w = self.verticalLayout.itemAt(i).widget()
            if w.text() == 'Выполнить':
                continue
            else:
                args.append(w.text())
        args = list(reversed(args))
        if not args:
            args: List[Any] = [None for _ in range(len(item.need_args))]
        # --- Преобразование названий обьектов в классы
        for i in range(len(item.need_args)):
            if item.need_args[i] == 'task':
                args[i] = Task.get_task(args[i])
                if args[i].creator_name != get_self_user().name:
                    return
            elif item.need_args[i] == 'user':
                args[i] = User.get_user(args[i])
            elif item.need_args[i] == 'selfuser':
                args[i] = get_self_user()
        item.func(*args)
        get_self_user().balance -= item.price
        self.clearOutput()
        self.description.setText('Выполнено')

    def login_user(self):
        """Получение значений из формы и попытка входа в аккаунт.
        Если акк не найден - создается."""
        if self.is_login:
            return
        name, psw = '', ''
        for i in reversed(range(self.verticalLayout.count())):
            w = self.verticalLayout.itemAt(i).widget()
            if w.text() == 'Отправить':
                continue
            else:
                if not psw:
                    psw = w.text()
                elif not name:
                    name = w.text()
        if name and psw:
            try:
                u = User.get_user(name)
                u.password = psw
                u.login()
            except UserNotFound:
                User(name, password=psw).save()
                ConfigHandler.username = name
                ConfigHandler.password = psw
                self.description.setText('Пользователь создан')
                self.is_login = True
            except IncorrectLoginData:
                self.description.setText('Неправильный логин или пароль')
            else:
                self.description.setText('Успешно')
                self.is_login = True
                ConfigHandler.username = name
                ConfigHandler.password = psw
            self.clearOutput()
            self.initData()

    def create_task(self):
        title, price, desc = '', 0, ''
        # --- Получения значений из ввода и удаление виджетов
        if self.description.toPlainText().strip() == 'Введите описание':
            return
        desc = self.description.toPlainText().replace('\n', '/n')
        self.description.setReadOnly(True)
        self.description.setText('')
        for i in reversed(range(self.verticalLayout.count())):
            w = self.verticalLayout.itemAt(i).widget()
            if w.text() == 'Создать':
                pass
            else:
                if not price:
                    if w.text().isdigit():
                        price = int(w.text())
                    elif 'Цена за выполнение' in w.text():
                        return
                    else:
                        price = None
                elif not title:
                    title = w.text()
                    if 'Название' in w.text():
                        return
            w.setParent(None)
            w.deleteLater()
        # --- Исключения
        if price is None:
            self.description.setText('Цена не является числом')
            return
        elif get_self_user().balance < price:
            self.description.setText("На вашем балансе не достаточно ЗМ")
            return
        else:
            # --- Создание задания
            try:
                Task(title, price, desc, get_self_user().name).save()
                get_self_user().balance -= price
                self.initData()
            except TaskAlreadyExist:
                self.description.setText('Задание с таким названием, созданное вами, уже существует')

    def show_task(self, task: 'Task'):
        """Вывод задания"""
        self.clearOutput()
        self.description.setText(str(task).replace('/n', '\n\t'))
        username = get_self_user().name
        if username == task.creator_name:
            if task.performer_name == 'None':
                del_button = QPushButton(text=f'Удалить {task.id}')
                del_button.clicked.connect(self.delete_task)
                agreelist_button = QPushButton(text=f'Список откликнувшихся {task.id}')
                agreelist_button.clicked.connect(self.show_agree_list_task)
                self.verticalLayout.addWidget(del_button)
                self.verticalLayout.addWidget(agreelist_button)
            else:
                if str(task.done) not in ('False', 'None'):
                    self.description.setText(str(task).replace('/n', '\n\t')
                                             + f'\n\n\n\tСсылка для получения кода: {task.done}')
                    done_button = QPushButton(text=f'Завершить {task.id}')
                    done_button.clicked.connect(self.done_task)
                    self.verticalLayout.addWidget(done_button)
                    if not task.done.startswith('Decline('):
                        decline_button = QPushButton(text=f'Отклонить {task.id}')
                        decline_button.clicked.connect(self.decline_task)
                        self.verticalLayout.addWidget(decline_button)
        elif username == task.performer_name:
            if str(task.done).startswith('Decline('):
                self.description.setText(str(task).replace('/n', '\n\t')
                                         + f'\n\n\n\tПричина отклонения задачи: {task.done}')
            elif str(task.done) not in ('False', 'None'):
                self.description.setText(str(task).replace('/n', '\n\t')
                                         + f'\n\n\n\tСсылка для получения кода: {task.done}')
            done_button = QPushButton(text=f'Завершить {task.id}')
            done_button.clicked.connect(self.done_task)
            self.verticalLayout.addWidget(done_button)
        elif task.performer_name == 'None' and username not in task.agree_list:
            agree_button = QPushButton(text=f'Взяться {task.id}')
            agree_button.clicked.connect(self.add_agree_task)
            self.verticalLayout.addWidget(agree_button)

    def delete_task(self):
        task_id = self.sender().text().replace("Удалить", '').strip()
        get_self_user().balance += Task.get_task(int(task_id)).price
        Task.delete(task_id)
        self.clearOutput()
        self.initData()

    def done_task(self):
        taskid = self.sender().text().replace("Завершить", '').strip()
        url = Task.get_task(taskid).done
        if Task.get_task(taskid).performer_name == get_self_user().name:
            text, ok = QInputDialog.getText(self, 'Input Dialog',
                                            'Введите ссылку для получения файлов с кодом:')
            if ok:
                url = text
        if Task.get_task(taskid).performer_name == get_self_user().name:
            Task.finish(taskid, url)
            self.show_task(Task.get_task(int(taskid)))
        else:
            Task.finish(taskid, url)
        self.initData()

    def decline_task(self):
        taskid = self.sender().text().replace("Отклонить", '').strip()
        text, ok = QInputDialog.getText(self, 'Input Dialog',
                                        'Введите причину отклонения:')
        if ok and str(text):
            task = Task.get_task(int(taskid))
            task.done = 'Decline(' + str(text) + ')'
            self.show_task(Task.get_task(int(taskid)))

    def show_agree_list_task(self):
        taskid = self.sender().text().replace("Список откликнувшихся", '').strip()
        for i in reversed(range(self.tasksListLayout.count())):
            w = self.tasksListLayout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()
        self.addItem("Вернуться", self.choice_agree_task)
        for nickname in Task.get_task(taskid).agree_list:
            if nickname:
                self.addItem(nickname + '\t' + taskid, self.choice_agree_task)

    def choice_agree_task(self):
        if self.sender().text() == "Вернуться":
            self.initData()
            return
        nickname, taskid = self.sender().text().split('\t')
        Task.agree(taskid, nickname)
        self.show_task(Task.get_task(int(taskid)))

    def add_agree_task(self):
        taskid = self.sender().text().replace("Взяться", '').strip()
        Task.add_agree(taskid)
        self.show_task(Task.get_task(int(taskid)))


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    # --- Инициализация файлов
    if 'data.db' not in os.listdir():
        SQLHandler.initialize()
    if 'config.ini' not in os.listdir():
        ConfigHandler.initialize()
    try:
        User.get_user('a').login(with_exceptions=False)
    except sqlite3.OperationalError as e:
        if 'no such table' in str(e):
            SQLHandler.initialize()
    except Exception as e:
        pass
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
