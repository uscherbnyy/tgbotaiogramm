from aiogram import Bot, Dispatcher, executor, types
from app import database as db
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import random
import os
import datetime


load_dotenv()
bot = Bot(os.getenv('TOKEN'))
# Хранилище состояния пользователя (хранится в ОП) использовать при тестовом проекте
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

current_question_num = 0
cat_quiz = []
count = 0


class AddQState(StatesGroup):
    # хранит в каком этапе создание вопроса
    CATT = State()
    ADD_QUE = State()
    NUM_ANSW = State()
    TRUE_ANSW = State()
    ANSW = State()
    FINISH = State()
    # состояние добавления вопроса
    START_OF_PROCESSING = State()
    PROCESSING = State()
    CONF_TO_EXIT = State()


markup_admin = ReplyKeyboardMarkup(resize_keyboard=True)
markup_admin\
    .add('пройти викторину')\
    .add('создать/обновить викторину')\
    .add('админ панель')

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel\
    .add('посмотреть добавленные вопросы')\
    .add('посмотреть добавленные викторины')\
    .add('прочие админские кнопки')

start_markup = ReplyKeyboardMarkup(resize_keyboard=True)
start_markup.add('пройти викторину').add('создать/обновить викторину')

up_markup = ReplyKeyboardMarkup(resize_keyboard=True)
up_markup.add('добавить').add('удалить').add('с меня хватит')

next_markup = ReplyKeyboardMarkup(resize_keyboard=True)
next_markup.add('дальше').add('с меня хватит')


async def on_startup(_):
    await db.db_start()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await db.cmd_start_db(message.from_user.id, message.from_user.first_name)
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы авторизированы как админ!', reply_markup=markup_admin)
    else:
        await message.answer(f'доброго, {message.from_user.first_name}', reply_markup=start_markup)


@dp.message_handler(text='админ панель')
async def cmd_start(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы авторизированны как админ!', reply_markup=admin_panel)
    else:
        await message.answer(f'Вы вошли в админ панель-\nНЕТ', reply_markup=start_markup)


@dp.message_handler(text='посмотреть добавленные вопросы')
async def chec_user_update_qw(message: types.Message, state: FSMContext):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        count_user_update_qw = db.cur.execute("SELECT COUNT(*) FROM user_update_qw").fetchone()[0]
        if count_user_update_qw == 0:
            await message.answer(f'нет добавленных вопросов')
        else:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('перейти к обработке')
            btn2 = types.KeyboardButton('ну нах')
            markup.add(btn1, btn2)
            await message.answer(f'количество добавленных вопросов {count_user_update_qw}', reply_markup=markup)
            await state.set_state(AddQState.START_OF_PROCESSING.state)
    else:
        await message.answer(f'Вы не имеете1 доступ', reply_markup=start_markup)


@dp.message_handler(state=AddQState.START_OF_PROCESSING)
async def check_user_update_qw(message: types.Message, state: FSMContext):
    mess = message.text
    if mess == 'ну нах':
        await state.finish()
        await message.answer(f'ну нет, так нет', reply_markup=admin_panel)
    else:
        user_update_qw = db.cur.execute("SELECT * FROM user_update_qw LIMIT 1").fetchone()
        if user_update_qw is not None:
            await message.answer(f'{user_update_qw}', reply_markup=up_markup)
            await state.set_state(AddQState.PROCESSING.state)
        else:
            await state.finish()
            await message.answer(f'все вопросы закончились', reply_markup=admin_panel)

@dp.message_handler(state=AddQState.PROCESSING)
async def treatment_user_update_qw(message: types.Message, state: FSMContext):
    choice = message.text
    user_id = db.cur.execute("SELECT * FROM user_update_qw LIMIT 1").fetchone()[1]
    if choice == 'удалить':
        await db.dell()
        await message.answer(f'Вопрос удален', reply_markup=next_markup)
        await state.set_state(AddQState.START_OF_PROCESSING.state)
        await bot.send_message(user_id, "Привет, Твой вопрос не прошел проверку!")
    elif choice == 'добавить':
        category_name = db.cur.execute("SELECT category_name FROM user_update_qw LIMIT 1").fetchone()[0]
        category_id = db.cur.execute("SELECT id FROM categories WHERE name=?", (category_name,)).fetchone()[0]
        question = db.cur.execute("SELECT * FROM user_update_qw LIMIT 1").fetchone()[3]
        true_answer = db.cur.execute("SELECT * FROM user_update_qw LIMIT 1").fetchone()[4]
        answer = db.cur.execute("SELECT * FROM user_update_qw LIMIT 1").fetchone()[5]
        await db.update_qw(question, category_id)
        question_id = db.cur.execute("SELECT id FROM questions WHERE question=?", (question,)).fetchone()[0]
        await db.update_true_answer(true_answer, question_id)
        await db.update_false_answer(answer, question_id)
        await message.answer(f'Вопрос вопрос добавлен', reply_markup=next_markup)
        await db.dell()
        await state.set_state(AddQState.START_OF_PROCESSING.state)
        await bot.send_message(user_id, "Привет, Твой вопрос добавлен!")
    elif choice == 'с меня хватит':
        count_user_update_qw = db.cur.execute("SELECT COUNT(*) FROM user_update_qw").fetchone()[0]
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('да').add('нет')
        await message.answer(f'Вы уверены? осталось {count_user_update_qw}', reply_markup=markup)
        await state.set_state(AddQState.CONF_TO_EXIT.state)


@dp.message_handler(state=AddQState.CONF_TO_EXIT)
async def treatment_user_update_qw(message: types.Message, state: FSMContext):
    mes = message.text
    if mes == 'да':
        await message.answer(f'Вы авторизированы как админ!', reply_markup=markup_admin)
        await state.finish()
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('перейти к обработке')
        btn2 = types.KeyboardButton('ну нах')
        markup.add(btn1, btn2)
        await message.answer(f'отлично осталось немного', reply_markup=markup)
        await state.set_state(AddQState.START_OF_PROCESSING.state)


# Хендлер для начала викторины выбор категории
@dp.message_handler(text='пройти викторину')
async def start_quiz(message: types.Message):
    global current_question_num
    global count
    a = db.cur.execute("SELECT name FROM categories").fetchall()  # получаем все категории
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем образ клавиатуры
    for el in a:  # делаем перебор по всем категориям и добавляем кнопку с названием категории
        button = types.KeyboardButton(text=el[0])
        keyboard.row(button)
    await message.answer(f'По какой категории хотите пройти викторину', reply_markup=keyboard)
    cat_quiz.clear()
    current_question_num = 0
    count = 0


@dp.message_handler(lambda msg: msg.text in [category[1] for category in db.cur.execute("SELECT * FROM categories")])
async def handle_quiz(message: types.Message):
        # Обработка выбора категории
        selected_category = message.text
        cat_quiz.append(selected_category)

        # Получение id категории из базы данных, где имя является тем, которую получили в сообщении
        category_id = db.cur.execute("SELECT id FROM categories WHERE name=?", (selected_category,)).fetchone()[0]

        # Получение вопросов для выбранной категории
        questions = db.cur.execute("SELECT * FROM questions WHERE category_id=?", (category_id,)).fetchall()

        if len(questions) == 0:
            await message.reply("В этой категории нет вопросов.")
        else:
            # Первый вопрос из выбранной категории
            current_question = questions[0]

            # Получение ответов для текущего вопроса
            answers = db.cur.execute("SELECT * FROM answers WHERE question_id=?", (current_question[0],)).fetchall()

            # Создание кнопок-ответов
            answer_list = []
            for answer in answers:
                answer_list.append(types.KeyboardButton(answer[1]))
            random.shuffle(answer_list)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*answer_list)
            await message.answer(f"{current_question[1]}", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text in [answer[1] for answer in db.cur.execute("SELECT * FROM answers")])
async def answer_selected(message: types.Message):
    global current_question_num  # объявление глобальной переменной
    global count
    user_answer = message.text
    a = [answer[1] for answer in db.cur.execute("SELECT * FROM answers WHERE tru_or_false=1")]
    if user_answer in a:
        count += 1
    # Получение id категории из базы данных, где имя является тем, которую получили в сообщении
    category_id = db.cur.execute("SELECT id FROM categories WHERE name=?", (cat_quiz[0],)).fetchone()[0]

    # Получение списка вопросов для выбранной категории
    questions = db.cur.execute("SELECT * FROM questions WHERE category_id=?", (category_id,)).fetchall()
    number_of_questions = len(questions)
    current_question_num += 1  # увеличение текущего вопроса на 1
    if current_question_num < number_of_questions:
        current_question = questions[current_question_num]
        answers = db.cur.execute("SELECT * FROM answers WHERE question_id=?", (current_question[0],)).fetchall()

        answer_list = []
        for answer in answers:
            answer_list.append(types.KeyboardButton(answer[1]))
            random.shuffle(answer_list)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*answer_list)
        await message.answer(f"{current_question[1]}", reply_markup=keyboard)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add('пройти викторину', 'создать/обновить викторину')
        await message.answer(f"Эта викторина закончена!\nВы ответили правильно на {count} вопросов"
                             f" из {number_of_questions}", reply_markup=markup)


@dp.message_handler(text='создать/обновить викторину')
async def turn_quiz(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('добавить вопрос в викторину')
    btn2 = types.KeyboardButton('создать викторину')
    markup.add(btn1, btn2)
    await message.answer(
        f'Решили создать или обновить викторину? давайте попробуем, но помните можно создать только 1 викторину и'
        f'добавить 1 вопрос в день. Следуйте инструкции, мы проверим и добавим. Выберете что хотите сделать'
        , reply_markup=markup)


@dp.message_handler(text='создать викторину')
async def create_quiz(message: types.Message):
    user_id = message.from_user.id
    last_created = db.cur.execute("SELECT last_created_quiz FROM user WHERE id_user=?", (user_id,)).fetchone()[0]
    if last_created is None or datetime.datetime.now() - datetime.datetime.strptime\
                (last_created, '%Y-%m-%d %H:%M:%S.%f') >= datetime.timedelta(minutes=1):
        db.cur.execute("UPDATE user SET last_created_quiz=? WHERE id_user=?", (datetime.datetime.now(), user_id))
        await message.answer("Вы можете создать новую викторину. Но сейчас это не реализовано:(")
    else:
        time_diff = datetime.datetime.strptime(last_created, '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(
            minutes=1) - datetime.datetime.now()
        minutes = int(time_diff.total_seconds() // 60)
        seconds = int(time_diff.total_seconds() % 60)
        limit_timer = f"{minutes} минут {seconds} секунд"
        await message.answer(f"Вы уже пытались создать викторину сегодня. Попробуй через {limit_timer}.")


@dp.message_handler(text='добавить вопрос в викторину')
async def create_quiz(message: types.Message, state: FSMContext):
    global count
    count = 0
    a = db.cur.execute("SELECT name FROM categories").fetchall()  # получаем все категории
    # создаем образ клавиатуры
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder="Выберите категорию")
    for el in a:  # делаем перебор по всем категориям и добавляем кнопку с названием категории
        button = types.KeyboardButton(text=el[0])
        keyboard.add(button)
    await message.answer(f'В какую категорию хотите добавить вопрос', reply_markup=keyboard)
    await state.set_state(AddQState.CATT.state)


@dp.message_handler(state=AddQState.CATT)
async def add_category(message: types.Message, state: FSMContext):
    catt = message.text
    a = db.cur.execute("SELECT name FROM categories").fetchall()
    if catt in [el[0] for el in a]:
        category_name = message.text  # получаем название категории
        await state.update_data(CATEGORY=category_name)
        await message.answer(f'Вы выбрали категорию: {category_name}.\nТеперь введите ваш вопрос',
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AddQState.ADD_QUE.state)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("что это значит?")
        await message.answer(f'Увы и ах, "{catt}" нет как категории', reply_markup=markup)
        await state.set_state(AddQState.FINISH.state)


@dp.message_handler(state=AddQState.ADD_QUE)
async def add_questions(message: types.Message, state: FSMContext):
    question_name = message.text    # получаем вопрос
    await state.update_data(QUESTION=question_name)
    await message.reply("Ведите кол-во ответов, ответов не может быть больше 5 и меньше 2")
    await state.set_state(AddQState.NUM_ANSW.state)


@dp.message_handler(state=AddQState.NUM_ANSW)
async def add_num_answer(message: types.Message, state: FSMContext):
    quantity_answ = message.text
    if quantity_answ.isdigit():
        int_quantity_answ = int(quantity_answ)
        if 1 < int_quantity_answ < 6:
            await state.update_data(QUANTITY_ANS=int_quantity_answ)
            await message.answer("введите правильный ответ")
            await state.set_state(AddQState.TRUE_ANSW.state)
        else:
            await message.answer("Кол-во ответов не может быть <2 и >5")
            await state.set_state(AddQState.NUM_ANSW.state)
    else:
        await message.reply("введите только число")
        await state.set_state(AddQState.NUM_ANSW.state)


@dp.message_handler(state=AddQState.TRUE_ANSW)
async def add_true_answer(message: types.Message, state: FSMContext):
    global count
    true_answer = message.text
    await state.update_data(TRUE_ANSWER=true_answer)
    await message.answer("Ведите следующий ответ")
    count += 2
    answer.clear()
    await state.set_state(AddQState.ANSW.state)

answer =[]


@dp.message_handler(state=AddQState.ANSW)
async def add_answer(message: types.Message, state: FSMContext):
    global count
    number_of_responses = await state.get_data()
    num = number_of_responses['QUANTITY_ANS']
    num = int(num)
    us_answer = message.text
    answer.append(us_answer)
    if count < num:
        count += 1
        await message.answer("Ведите следующий ответ")
        await state.set_state(AddQState.ANSW.state)
    elif count == num:
        await state.update_data(ANSWER=answer)
        count = 0
        user_state_date = await state.get_data()
        cat = user_state_date['CATEGORY']
        ques = user_state_date['QUESTION']
        quant_ans = user_state_date['QUANTITY_ANS']
        true_answer = user_state_date['TRUE_ANSWER']
        answ = user_state_date['ANSWER']
        str_answ = ", ".join(answ)
        mes = f"Проверяем:\nКатегория: {cat}\n Ваш вопрос: {ques}\n" \
              f"количество ответов:{quant_ans}\nПравильный ответ:{true_answer}\nОстальные ответы: {str_answ}"
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton('предложить вопрос на рассмотрение')
        btn2 = types.KeyboardButton('отмена')
        markup.add(btn1, btn2)
        await message.answer('Почти закончили')
        await message.answer(mes, reply_markup=markup)
        await state.set_state(AddQState.FINISH.state)


@dp.message_handler(state=AddQState.FINISH)
async def finish(message: types.Message, state: FSMContext):
    finish = message.text    # получаем выбор
    user_id = message.from_user.id
    if finish == 'предложить вопрос на рассмотрение':
        user_state_date = await state.get_data()
        cat = user_state_date['CATEGORY']
        ques = user_state_date['QUESTION']
        quant_ans = user_state_date['QUANTITY_ANS']
        true_answer = user_state_date['TRUE_ANSWER']
        answ = user_state_date['ANSWER']
        str_answ = ", ".join(answ)
        mes = f"Ваш вопрос:\n{ques}\nв категорию: {cat}\n " \
              f"с количеством ответов:{quant_ans}\nВ котором правильный ответ:\n{true_answer}\n" \
              f"а остальные ответы: {str_answ}\nпередан на рассмотрение. Спасибо"
        await message.answer(mes, reply_markup=start_markup)
        await db.user_update_qw(user_id, ques, cat, true_answer, str_answ)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        button = types.KeyboardButton('/start')
        markup.add(button)
        await message.reply("Добавление вопроса отменено.", reply_markup=markup)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)