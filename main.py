import sys
import os

import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog
from PyQt5.QtWidgets import QFormLayout, QListWidgetItem
from PyQt5.QtWidgets import QWidget, QLineEdit, QInputDialog
from PyQt5.QtCore import QEvent, Qt
from PyQt5 import uic
from maindesing import Ui_MainWindow

from tasksList import *
from user import *


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


class PreDialog(QDialog):
    def __init__(self, parent=None):
        super(PreDialog, self).__init__(parent)
        self.parent = parent

        self.setWindowTitle('Task create')
        self.setModal(True)
        self.line_title = QLineEdit()
        self.line_price = QLineEdit()
        self.line_description = QLineEdit()
        self.connect = QPushButton("Create")

        self.form = QFormLayout()
        self.form.setSpacing(20)

        self.form.addRow("&Название:", self.line_title)
        self.form.addRow("&Цена:", self.line_price)
        self.form.addRow("&Описание:", self.line_description)
        self.form.addRow(self.connect)

        self.setLayout(self.form)

    def create(self):
        d = PreDialog()
        d.show()


class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.initUI()
        self.initData()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('ААА')

        self.tasksListWidget.installEventFilter(self)
        self.create_form = None

    def initData(self):
        """Обновление данных в выводе задач"""
        self.tasksListWidget.clear()
        self.tasksListWidget.addItem(QListWidgetItem('Создать задачу'))
        for task in TasksList.get_tasks_list():
            if task.done.strip() != 'False':
                if get_self_user().name not in (task.creator_name,
                                                task.performer_name):
                    continue
            self.tasksListWidget.addItem(QListWidgetItem(task.title))

    def eventFilter(self, sender, event):
        # --- Обновление отображенных данных
        self.profileInfo.setText(str(get_self_user()))
        self.tasksInfo.setText(str(get_tasksInfo_text(get_self_user())))
        # --- Отработка эвентов
        if event.type() == 1:  # Has been clicked
            if sender is self.tasksListWidget:
                task = self.tasksListWidget.currentItem()
                if task:
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
                    else:
                        task = TasksList.get_task(task.text())
                        self.show_task(task)
                        self.initData()
        return super().eventFilter(sender, event)

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
                delbutton = QPushButton(text=f'Delete {task.id}')
                delbutton.clicked.connect(self.delete_task)
                self.verticalLayout.addWidget(delbutton)
            else:
                if task.done.strip() not in ('False', 'None'):
                    self.description.setText(str(task).replace('/n', '\n\t')
                                             + f'\n\n\n\tСсылка для получения кода: {task.done}')
                    donebutton = QPushButton(text=f'Done {task.id}')
                    donebutton.clicked.connect(self.done_task)
                    self.verticalLayout.addWidget(donebutton)
        elif username == task.performer_name:
            if task.done:
                self.description.setText(str(task).replace('/n', '\n\t')
                                         + f'\n\n\n\tСсылка для получения кода: {task.done}')
            donebutton = QPushButton(text=f'Done {task.id}')
            donebutton.clicked.connect(self.done_task)
            self.verticalLayout.addWidget(donebutton)
        else:
            agreebutton = QPushButton(text=f'Agree {task.id}')
            agreebutton.clicked.connect(self.agree_task)
            self.verticalLayout.addWidget(agreebutton)

    def delete_task(self):
        taskid = self.sender().text().replace("Delete", '').strip()
        get_self_user().balance += Task.get_task(int(taskid)).price
        Task.delete(taskid)
        self.show_task(None)
        self.initData()

    def done_task(self):
        taskid = self.sender().text().replace("Done", '').strip()
        url = None
        if Task.get_task(taskid).performer_name == get_self_user().name:
            askurl = AskUrlDialog()
            askurl.showDialog()
            url = askurl.le.text()
        Task.finish(taskid, url)
        if Task.get_task(taskid).performer_name == get_self_user().name:
            self.show_task(taskid)
        self.initData()

    def agree_task(self):
        taskid = self.sender().text().replace("Agree", '').strip()
        Task.agree(taskid)
        self.show_task(taskid)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    # --- Инициализация файлов
    if TasksList.filename not in os.listdir():
        open(TasksList.filename, 'w+').write('')
    if User.filename not in os.listdir():
        open(User.filename, 'w+').write('')
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
