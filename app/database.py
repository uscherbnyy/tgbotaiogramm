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
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'name TEXT)')

    # Создаем таблицу вопросов с внешним ключом, связанным с категорией
    cur.execute(
        'CREATE TABLE IF NOT EXISTS questions ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'question TEXT, '
        'category_id INTEGER, '
        'FOREIGN KEY(category_id) REFERENCES categories(id))')

    # Создаем таблицу ответов с внешним ключом, связанным с вопросом
    cur.execute(
        'CREATE TABLE IF NOT EXISTS answers ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'answer TEXT, '
        'question_id INTEGER, '
        'tru_or_false BOOLEAN, '
        'FOREIGN KEY(question_id) REFERENCES questions(id))')

    # Создаем таблицу обновленых вопросов от пользователя
    cur.execute(
        'CREATE TABLE IF NOT EXISTS user_update_qw ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'user_id VARCHAR,'
        'category_name TEXT, '
        'question TEXT, '
        'true_answer TEXT, '
        'answer TEXT, '
        'timestamp DATETIME, '
        'FOREIGN KEY(user_id) REFERENCES user(id_user))')

    # Вставляем значения в таблицу категорий
    cur.execute(
        "INSERT OR IGNORE INTO categories (name) "
        "VALUES "
        "('география'), "
        "('математика')")

    # Вставляем значения в таблицу вопросов
    cur.execute(
        "INSERT OR IGNORE INTO questions (question, category_id) "
        "VALUES "
        "('самая большая страна', 1), "
        "('страна где написан этот бот', 1), "
        "('река в Минске', 1), "
        "('2*2', 2), "
        "('2+2', 2),"
        "('Столица Украины', 1)")

    # Вставляем значения в таблицу ответов
    cur.execute(
        "INSERT OR IGNORE INTO answers (answer, question_id, tru_or_false) "
        "VALUES "
        "('Россия', 1, 1), "
        "('Беларусь', 1, 0), "
        "('нил', 3, 0), "
        "('Свислочь', 3, 1), "
        "('4', 5, 1), "
        "('5', 5, 0), "
        "('4', 4, 1), "
        "('5', 4, 0), "
        "('Беларусь', 2, 1), "
        "('LS', 2, 0),"
        "('Киев', 6, 1),"
        "('Мариуполь', 6, 0),"
        "('Львов', 6, 0),"
        "('Одесса', 6, 0)")

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


async def user_update_qw(user_id, ques, cat, true_answer, str_answ):
    cur.execute(
        "INSERT INTO user_update_qw (user_id, category_name, question, true_answer, answer, timestamp)"
        "VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (user_id, ques, cat, true_answer, str_answ)
    )
    db.commit()
