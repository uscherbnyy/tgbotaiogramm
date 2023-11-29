from aiogram import Bot, Dispatcher, executor, types
from app import database as db
from aiogram.types import ReplyKeyboardMarkup
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
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
    CHOICE_NUM = State()
    NUM_ANSW = State()
    TRUE_ANSW =State()
    ANSW = State()
    FINISH = State()





async def on_startup(_):
    await db.db_start()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await db.cmd_start_db(message.from_user.id, message.from_user.first_name)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('пройти викторину')
    btn2 = types.KeyboardButton('создать/обновить викторину')
    markup.add(btn1, btn2)
    await message.answer(f'добро {message.from_user.first_name}', reply_markup=markup)


# Хендлер для начала викторины выбор категории
@dp.message_handler(text='пройти викторину')
async def start_quiz(message: types.Message):
    global current_question_num
    a = db.cur.execute("SELECT name FROM categories").fetchall()  # получаем все категории
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем образ клавиатуры
    for el in a:  # делаем перебор по всем категориям и добавляем кнопку с названием категории
        button = types.KeyboardButton(text=el[0])
        keyboard.row(button)
    await message.answer(f'По какой категории хотите пройти викторину', reply_markup=keyboard)
    cat_quiz.clear()
    current_question_num = 0


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
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for answer in answers:
                keyboard.add(types.KeyboardButton(answer[1]))

            await message.answer(f"{current_question[1]}", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text in [answer[1] for answer in db.cur.execute("SELECT * FROM answers")])
async def answer_selected(message: types.Message):
    global current_question_num  # объявление глобальной переменной
    user_answer = message.text

    # Получение id категории из базы данных, где имя является тем, которую получили в сообщении
    category_id = db.cur.execute("SELECT id FROM categories WHERE name=?", (cat_quiz[0],)).fetchone()[0]

    # Получение списка вопросов для выбранной категории
    questions = db.cur.execute("SELECT * FROM questions WHERE category_id=?", (category_id,)).fetchall()

    current_question_num += 1  # увеличение текущего вопроса на 1
    if current_question_num < len(questions):
        current_question = questions[current_question_num]
        answers = db.cur.execute("SELECT * FROM answers WHERE question_id=?", (current_question[0],)).fetchall()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for answer in answers:
            keyboard.add(types.KeyboardButton(answer[1]))

        await message.answer(f"{current_question[1]}", reply_markup=keyboard)
    else:
        await message.answer("Эта викторина закончена!", reply_markup=types.ReplyKeyboardRemove())


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
        await message.answer("Вы можете создать новую викторину.")
    else:
        await message.answer("Вы уже создали викторину сегодня. через минуту.")


@dp.message_handler(text='добавить вопрос в викторину')
async def create_quiz(message: types.Message, state: FSMContext) -> None:
    a = db.cur.execute("SELECT name FROM categories").fetchall()  # получаем все категории
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем образ клавиатуры
    for el in a:  # делаем перебор по всем категориям и добавляем кнопку с названием категории
        button = types.KeyboardButton(text=el[0])
        keyboard.add(button)
    await message.answer(f'В какую категорию хотите добавить вопрос', reply_markup=keyboard)
    await state.set_state(AddQState.CATT.state)


@dp.message_handler(state=AddQState.CATT)
async def add_category(message: types.Message, state: FSMContext):
    category_name = message.text  # получаем название категории
    await state.update_data(CATEGORY=category_name)
    await message.answer(f'Вы выбрали категорию: {category_name}.\nТеперь введите ваш вопрос',
                         reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddQState.ADD_QUE.state)


@dp.message_handler(state=AddQState.ADD_QUE)
async def add_questions(message: types.Message, state: FSMContext):
    question_name = message.text    # получаем вопрос
    await state.update_data(QUESTION=question_name)
    await message.reply("Ведите кол-во ответов, ответов не может быть больше 5 и меньше 2")
    await state.set_state(AddQState.NUM_ANSW.state)


@dp.message_handler(state=AddQState.CHOICE_NUM)
async def choice_num(message: types.Message, state: FSMContext):
    num_user = message.text
    await message.answer(f"Значит {num_user}")
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
        mes = f"Почти закончили\nКатегория: {cat}\n Ваш вопрос: {ques}\n" \
              f"количество ответов:{quant_ans}\nПравильный ответ:{true_answer}\nОстальные ответы: {str_answ}"
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton('предложить вопрос на рассмотрение')
        btn2 = types.KeyboardButton('отмена')
        markup.add(btn1, btn2)
        await message.answer(mes, reply_markup=markup)
        await state.set_state(AddQState.FINISH.state)


@dp.message_handler(state=AddQState.FINISH)
async def finish(message: types.Message, state: FSMContext):
    finish = message.text    # получаем выбор
    if finish == 'предложить вопрос на рассмотрение':
        user_state_date = await state.get_data()
        cat = user_state_date['CATEGORY']
        ques = user_state_date['QUESTION']
        answ = user_state_date['ANSWER']
        mes = f"Ваш вопрос: {ques}\nв категорию: {cat}\nС ответом: {answ} передан на рассмотрение. Спасибо"
        await message.answer(mes, reply_markup=types.ReplyKeyboardRemove())
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        button = types.KeyboardButton('/start')
        markup.add(button)
        await message.reply("ты пытался", reply_markup=markup)
    await state.finish()


@dp.message_handler(state=AddQState.FINISH, text='отмена')
async def cancel_adding(message: types.Message, state: FSMContext):
    await message.reply("Добавление вопроса отменено.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)