import sqlite3
import configparser


class UserNotFound(Exception):
    pass


class ConfigHandler:
    config_filename = 'config.ini'
    config = configparser.ConfigParser()
    config.read(config_filename)

    @staticmethod
    def initialize():
        ConfigHandler.config.read(ConfigHandler.config_filename)
        ConfigHandler.config.add_section('Main')
        ConfigHandler.config.set('Main', 'username', 'b')
        ConfigHandler.config.set('Main', 'password', '')
        ConfigHandler.config.write(open(ConfigHandler.config_filename, 'w+'))

    def __getattr__(self, item):
        return ConfigHandler.config.get('Main', item)

    def __setattr__(self, key, value):
        ConfigHandler.config.set('Main', key, value)
        ConfigHandler.config.write(open(ConfigHandler.config_filename, 'w+'))


class SQLHandler:
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
        SQLHandler.cur.executescript(a)

    @staticmethod
    def get_user(param_name, param_value):
        a = SQLHandler.cur.execute(f'SELECT * FROM users WHERE {param_name} = "{param_value}"').fetchall()
        if not a:
            raise UserNotFound()
        return a

    @staticmethod
    def get_users_list():
        try:
            a = SQLHandler.cur.execute(f'SELECT * FROM users').fetchall()
            return a
        except sqlite3.OperationalError:
            SQLHandler.initialize()
            a = SQLHandler.cur.execute(f'SELECT * FROM users').fetchall()
            return a

    @staticmethod
    def new_user(*data):
        SQLHandler.cur.execute(f'INSERT INTO users VALUES (?, ?, ?)', data)
        SQLHandler.conn.commit()

    @staticmethod
    def update_user(username, name, value):
        """Обновиление данных пользователя"""
        SQLHandler.cur.execute(f'''
            UPDATE users
            SET {name} = ?
            WHERE name = "{username}";
        ''', (value,))
        SQLHandler.conn.commit()

    @staticmethod
    def get_task(param_name, param_value):
        a = SQLHandler.cur.execute(f'SELECT * FROM tasks WHERE {param_name} = "{param_value}"').fetchall()[0]
        return a

    @staticmethod
    def get_tasks_list():
        try:
            a = SQLHandler.cur.execute(f'SELECT * FROM tasks').fetchall()
            return a
        except sqlite3.OperationalError:
            SQLHandler.initialize()
            a = SQLHandler.cur.execute(f'SELECT * FROM tasks').fetchall()
            return a

    @staticmethod
    def new_task(*data):
        SQLHandler.cur.execute(f'INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)', data)
        SQLHandler.conn.commit()

    @staticmethod
    def delete_task(task_id):
        SQLHandler.cur.execute(f'DELETE FROM tasks WHERE id = ?', (task_id,))
        SQLHandler.conn.commit()

    @staticmethod
    def update_task(task_id, name, value):
        """Обновление параметра задачи"""
        SQLHandler.cur.execute(f'''
            UPDATE tasks
            SET {name} = ?
            WHERE id = ?;
        ''', (value, task_id))
        SQLHandler.conn.commit()