import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog
from PyQt5.QtWidgets import QFormLayout, QListWidgetItem
from PyQt5.QtWidgets import QWidget, QLineEdit, QInputDialog
from PyQt5.QtCore import QEvent, Qt

from maindesing import Ui_MainWindow

from dataHandler import *
from tasksList import *
from user import *

ConfigHandler = ConfigHandler()


class AskUrlDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.le = QLineEdit(self)
        self.le.move(130, 22)

    def showDialog(self):
        text, ok = QInputDialog.getText(self, 'Input Dialog',
                                        'Введите ссылку для получения файлов с кодом:')
        if ok:
            self.le.setText(str(text))


class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.lastupdate_time = datetime.datetime.now()
        self.is_login = False
        self.setupUi(self)
        self.initUI()
        self.initData()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('ААА')

        self.tasksListWidget.installEventFilter(self)
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
        self.tasksListWidget.clear()
        if not self.is_login:
            self.tasksListWidget.addItem(QListWidgetItem('Войти или зарегистрироваться'))
        self.tasksListWidget.addItem(QListWidgetItem('Создать задачу'))
        for task in TasksList.get_tasks_list():
            if task.done.strip() not in ('False', 'None'):
                if get_self_user().name not in (task.creator_name,
                                                task.performer_name):
                    continue
            self.tasksListWidget.addItem(QListWidgetItem(task.title))

    def eventFilter(self, sender, event):
        # --- Обновление отображенных данных (раз в 5 секунд)
        if (datetime.datetime.now() - self.lastupdate_time).seconds > 5:
            self.profileInfo.setText(str(get_self_user()))
            self.tasksInfo.setText(str(get_tasksInfo_text(get_self_user())))
            self.lastupdate_time = datetime.datetime.now()
        # --- Отработка эвентов
        if event.type() == 1:  # Has been clicked
            if sender is self.tasksListWidget:
                task = self.tasksListWidget.currentItem()
                if task:
                    # --- Нажатие на пользовательские кнопки
                    if task.text() == 'Создать задачу':
                        for i in reversed(range(self.verticalLayout.count())):
                            w = self.verticalLayout.itemAt(i).widget()
                            w.setParent(None)
                            w.deleteLater()
                        self.description.setText('')
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
                    elif task.text() == 'Войти или зарегистрироваться':
                        for i in reversed(range(self.verticalLayout.count())):
                            w = self.verticalLayout.itemAt(i).widget()
                            w.setParent(None)
                            w.deleteLater()
                        self.description.setText('')
                        # --- Форма для ввода данных пользователя
                        line_name = QLineEdit('Ник')
                        line_psw = QLineEdit('Пароль')
                        loginbutton = QPushButton("Отправить")
                        loginbutton.clicked.connect(self.login_user)

                        self.verticalLayout.addWidget(line_name)
                        self.verticalLayout.addWidget(line_psw)
                        self.verticalLayout.addWidget(loginbutton)
                    else:
                        task = TasksList.get_task(task.text())
                        self.show_task(task)
                        self.initData()
        return super().eventFilter(sender, event)

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
            u = User(name, password=psw)
            try:
                u.login()
            except UserNotFound:
                u.save()
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
            for i in reversed(range(self.verticalLayout.count())):
                w = self.verticalLayout.itemAt(i).widget()
                w.setParent(None)
                w.deleteLater()
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
                continue
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
            Task(title, price, desc, get_self_user().name).save()
            get_self_user().balance -= price
            self.initData()

    def show_task(self, task):
        """Вывод задания. None для опустошения вывода"""
        for i in reversed(range(self.verticalLayout.count())):
            w = self.verticalLayout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()
        if task is None:
            self.description.setText('')
            return
        self.description.setText(str(task).replace('/n', '\n\t'))
        username = get_self_user().name
        if username == task.creator_name:
            if task.performer_name == 'None':
                delbutton = QPushButton(text=f'Удалить {task.id}')
                delbutton.clicked.connect(self.delete_task)
                self.verticalLayout.addWidget(delbutton)
            else:
                if task.done.strip() not in ('False', 'None'):
                    self.description.setText(str(task).replace('/n', '\n\t')
                                             + f'\n\n\n\tСсылка для получения кода: {task.done}')
                    donebutton = QPushButton(text=f'Завершить {task.id}')
                    donebutton.clicked.connect(self.done_task)
                    self.verticalLayout.addWidget(donebutton)
                    if not task.done.startswith('Decline('):
                        declinebutton = QPushButton(text=f'Отклонить {task.id}')
                        declinebutton.clicked.connect(self.decline_task)
                        self.verticalLayout.addWidget(declinebutton)
        elif username == task.performer_name:
            if task.done.startswith('Decline('):
                self.description.setText(str(task).replace('/n', '\n\t')
                                         + f'\n\n\n\tПричина отклонения задачи: {task.done}')
            elif task.done not in ('False', 'None'):
                self.description.setText(str(task).replace('/n', '\n\t')
                                         + f'\n\n\n\tСсылка для получения кода: {task.done}')
            donebutton = QPushButton(text=f'Завершить {task.id}')
            donebutton.clicked.connect(self.done_task)
            self.verticalLayout.addWidget(donebutton)
        else:
            agreebutton = QPushButton(text=f'Взяться {task.id}')
            agreebutton.clicked.connect(self.agree_task)
            self.verticalLayout.addWidget(agreebutton)

    def delete_task(self):
        taskid = self.sender().text().replace("Удалить", '').strip()
        get_self_user().balance += Task.get_task(int(taskid)).price
        Task.delete(taskid)
        self.show_task(None)
        self.initData()

    def done_task(self):
        taskid = self.sender().text().replace("Завершить", '').strip()
        url = None
        if Task.get_task(taskid).performer_name == get_self_user().name:
            askurl = AskUrlDialog()
            askurl.showDialog()
            url = askurl.le.text()
        Task.finish(taskid, url)
        if Task.get_task(taskid).performer_name == get_self_user().name:
            self.show_task(Task.get_task(int(taskid)))
        self.initData()

    def decline_task(self):
        taskid = self.sender().text().replace("Отклонить", '').strip()
        text, ok = QInputDialog.getText(self, 'Input Dialog',
                                        'Введите причину отклонения:')
        if ok and str(text):
            task = Task.get_task(int(taskid))
            task.done = 'Decline(' + str(text) + ')'

    def agree_task(self):
        taskid = self.sender().text().replace("Взяться", '').strip()
        Task.agree(taskid)
        self.show_task(Task.get_task(int(taskid)))


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    # --- Инициализация файлов
    if 'data.db' not in os.listdir():
        SQLHandler.initialize()
    if 'config.ini' not in os.listdir():
        ConfigHandler.initialize()
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
