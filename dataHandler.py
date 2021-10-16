import sqlite3
# from tasksList import TasksList, Task
# from user import User


class DataHandler:
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()

    @staticmethod
    def initialize():
        a = '''
        CREATE TABLE tasks (
            title          VARCHAR,
            price          INT     DEFAULT (0),
            description    TEXT,
            creator_name   VARCHAR,
            performer_name VARCHAR,
            create_time    TIME,
            id             INT     UNIQUE
                                   NOT NULL,
            done           STRING  DEFAULT None
        );
        CREATE TABLE users (
            name     VARCHAR,
            balance  INTEGER DEFAULT (0),
            password VARCHAR
        );
        '''
        DataHandler.cur.executescript(a)

    @staticmethod
    def get_user(param_name, param_value):
        a = DataHandler.cur.execute(f'SELECT * FROM users WHERE {param_name} = "{param_value}"').fetchall()
        return a

    @staticmethod
    def get_users_list():
        try:
            a = DataHandler.cur.execute(f'SELECT * FROM users').fetchall()
            return a
        except sqlite3.OperationalError:
            DataHandler.initialize()
            a = DataHandler.cur.execute(f'SELECT * FROM users').fetchall()
            return a

    @staticmethod
    def new_user(*data):
        DataHandler.cur.execute(f'INSERT INTO users VALUES (?, ?, ?)', data)
        DataHandler.conn.commit()

    @staticmethod
    def update_user(username, name, value):
        DataHandler.cur.execute(f'''
            UPDATE users
            SET {name} = ?
            WHERE name = "{username}";
        ''', (value,))
        DataHandler.conn.commit()

    @staticmethod
    def get_task(param_name, param_value):
        a = DataHandler.cur.execute(f'SELECT * FROM tasks WHERE {param_name} = "{param_value}"').fetchall()[0]
        return a

    @staticmethod
    def get_tasks_list():
        try:
            a = DataHandler.cur.execute(f'SELECT * FROM tasks').fetchall()
            return a
        except sqlite3.OperationalError:
            DataHandler.initialize()
            a = DataHandler.cur.execute(f'SELECT * FROM tasks').fetchall()
            return a

    @staticmethod
    def new_task(*data):
        DataHandler.cur.execute(f'INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)', data)
        DataHandler.conn.commit()

    @staticmethod
    def delete_task(task_id):
        DataHandler.cur.execute(f'DELETE FROM tasks WHERE id = ?', (task_id,))
        DataHandler.conn.commit()

    @staticmethod
    def update_task(task_id, name, value):
        DataHandler.cur.execute(f'''
            UPDATE tasks
            SET {name} = ?
            WHERE id = ?;
        ''', (value, task_id))
        DataHandler.conn.commit()