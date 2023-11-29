import sqlite3 as sq

db = sq.connect('tgbot')
cur = db.cursor()


async def db_start():
    cur.execute(
        'CREATE TABLE IF NOT EXISTS user ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'name VARCHAR(50), '
        'last_created_quiz DATETIME,'
        'id_user VARCHAR(50))')

    # Создаем таблицу категорий вопросов
    cur.execute(
        'CREATE TABLE IF NOT EXISTS categories ('
        'id INTEGER PRIMARY KEY, '
        'name TEXT)')

    # Создаем таблицу вопросов с внешним ключом, связанным с категорией
    cur.execute(
        'CREATE TABLE IF NOT EXISTS questions ('
        'id INTEGER PRIMARY KEY, '
        'question TEXT, '
        'category_id INTEGER, '
        'FOREIGN KEY(category_id) REFERENCES categories(id))')

    # Создаем таблицу ответов с внешним ключом, связанным с вопросом
    cur.execute(
        'CREATE TABLE IF NOT EXISTS answers ('
        'id INTEGER PRIMARY KEY, '
        'answer TEXT, '
        'question_id INTEGER, '
        'tru_or_false BOOLEAN, '
        'FOREIGN KEY(question_id) REFERENCES questions(id))')

    # Вставляем значения в таблицу категорий
    cur.execute(
        "INSERT OR IGNORE INTO categories (id, name) "
        "VALUES "
        "(1, 'география'), "
        "(2, 'математика')")

    # Вставляем значения в таблицу вопросов
    cur.execute(
        "INSERT OR IGNORE INTO questions (id, question, category_id) "
        "VALUES "
        "(1, 'самая большая страна', 1), "
        "(2, 'страна где написан этот бот', 1), "
        "(3, 'река в Минске', 1), "
        "(4, '2*2', 2), "
        "(5, '2+2', 2)")

    # Вставляем значения в таблицу ответов
    cur.execute(
        "INSERT OR IGNORE INTO answers (id, answer, question_id, tru_or_false) "
        "VALUES "
        "(1, 'Россия', 1, 1), "
        "(2, 'Беларусь', 1, 0), "
        "(3, 'нил', 3, 0), "
        "(4, 'Свислочь', 3, 1), "
        "(5, '4', 5, 1), "
        "(6, '5', 5, 0), "
        "(7, '4', 4, 1), "
        "(8, '5', 4, 0), "
        "(9, 'Беларусь', 2, 1), "
        "(10, 'LS', 2, 0)")

    db.commit()


async def cmd_start_db(user_id, first_name):
    user = cur.execute("SELECT * FROM user "
                       "WHERE id_user=?", (user_id,)).fetchone()

    # Если запрос вернул хотя бы одну строку, это означает, что совпадающая запись уже существует
    if not user:
        cur.execute(
            "INSERT INTO user (id_user, name)"
            "VALUES (?, ?)", (user_id, first_name))
        db.commit()

