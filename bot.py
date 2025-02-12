import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, Message, PhotoSize, BotCommand
)
# from redis.asyncio import Redis
from db.db import user_dict, save_user_dict
# redis = Redis(host='localhost')

BOT_TOKEN = '7784879248:AAHNzgxlev86ftaA4ddhcOQfZmdJzESKe3E'
admin_id = 1303113402
# BOT_TOKEN = '6182678315:AAEe5Y5VoBWNUWDWXqmkybbeAQ14yuoH2zU'
bot = Bot(BOT_TOKEN)


# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
# storage = RedisStorage(redis=redis)

async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(command='/showdata',
                                     description='просмотр своей анкеты'),
                          BotCommand(command='/fillform',
                                     description='заполнить анкету'),
                          BotCommand(command='/find',
                                     description='смотреть анкеты')
                          ]
    await bot.set_my_commands(main_menu_commands)


# Создаем объекты бота и диспетчера
async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)

dp = Dispatcher()




# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    fill_name = State()        # Состояние ожидания ввода имени
    fill_age = State()         # Состояние ожидания ввода возраста
    fill_gender = State()      # Состояние ожидания выбора пола
    upload_photo = State()     # Состояние ожидания загрузки фото
    fill_education = State()   # Состояние ожидания выбора образования
    fill_wish_news = State()   # Состояние ожидания выбора получать ли новости


# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform
@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    user_id = message.from_user.id
    if user_id not in user_dict:
        await bot.send_message(chat_id=admin_id, text=f'{message.from_user.full_name} присоеденился')
    await message.answer(
        text=
             'Чтобы перейти к заполнению анкеты - '
             'нажмите на /fillform'
    )


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда работает внутри машины состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text=
             'Чтобы перейти к заполнению анкеты - '
             'нажмите на /fillform'
    )



# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='Вы прервали заполнение анкеты!\n\n'
             'Чтобы снова перейти к заполнению анкеты - '
             'нажмите на /fillform'
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите ваше имя')
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMFillForm.fill_name)


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    await state.update_data(name=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите ваш возраст')
    # Устанавливаем состояние ожидания ввода возраста
    await state.set_state(FSMFillForm.fill_age)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_name))
async def warning_not_name(message: Message):
    await message.answer(
        text='То, что вы отправили не похоже на имя\n\n'
             'Пожалуйста, введите ваше имя\n\n'
             'Если вы хотите прервать заполнение анкеты - '
             'нажмите на /cancel')


# Этот хэндлер будет срабатывать, если введен корректный возраст
# и переводить в состояние выбора пола
@dp.message(StateFilter(FSMFillForm.fill_age),
            lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120)
async def process_age_sent(message: Message, state: FSMContext):
    # Cохраняем возраст в хранилище по ключу "age"
    await state.update_data(age=message.text)
    # Создаем объекты инлайн-кнопок
    male_button = InlineKeyboardButton(
        text='Парень ♂',
        callback_data='male'
    )
    female_button = InlineKeyboardButton(
        text='Девушка ♀',
        callback_data='female'
    )

    keyboard: list[list[InlineKeyboardButton]] = [
        [male_button, female_button]
    ]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(
        text='Спасибо!\n\nУкажите ваш пол',
        reply_markup=markup
    )
    # Устанавливаем состояние ожидания выбора пола
    await state.set_state(FSMFillForm.fill_gender)


# Этот хэндлер будет срабатывать, если во время ввода возраста
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_age))
async def warning_not_age(message: Message):
    await message.answer(
        text='Возраст должен быть целым числом от 4 до 120\n\n'
             'Попробуйте еще раз\n\nЕсли вы хотите прервать '
             'заполнение анкеты - нажмите на /cancel'
    )


# Этот хэндлер будет срабатывать на нажатие кнопки при
# выборе пола и переводить в состояние отправки фото
@dp.callback_query(StateFilter(FSMFillForm.fill_gender),
                   F.data.in_(['male', 'female', 'undefined_gender']))
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    if callback.data == 'male':
        await state.update_data(gender="Парень")
    if callback.data == 'female':
        await state.update_data(gender="Девушка")
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(
        text='Спасибо! А теперь загрузите, пожалуйста, ваше фото'
    )
    # Устанавливаем состояние ожидания загрузки фото
    await state.set_state(FSMFillForm.upload_photo)


# Этот хэндлер будет срабатывать, если во время выбора пола
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_gender))
async def warning_not_gender(message: Message):
    await message.answer(
        text='Пожалуйста, пользуйтесь кнопками '
             'при выборе пола\n\nЕсли вы хотите прервать '
             'заполнение анкеты - нажмите на /cancel'
    )


# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
@dp.message(StateFilter(FSMFillForm.upload_photo),
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             largest_photo: PhotoSize):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    await state.update_data(
        photo_unique_id=largest_photo.file_unique_id,
        photo_id=largest_photo.file_id
    )
    # Добавляем в "базу данных" анкету пользователя
    # по ключу id пользователя
    user_dict[message.from_user.id] = await state.get_data()
    await save_user_dict()

    # Завершаем машину состояний
    await state.clear()
    # Отправляем в чат сообщение о выходе из машины состояний
    await message.answer(
        text='Спасибо! Ваши данные сохранены!'
    )
    # Отправляем в чат сообщение с предложением посмотреть свою анкету
    await message.answer(
        text='Чтобы посмотреть данные вашей '
             'анкеты - нажмите на /showdata'
    )



# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.upload_photo))
async def warning_not_photo(message: Message):
    await message.answer(
        text='Пожалуйста, на этом шаге отправьте '
             'ваше фото\n\nЕсли вы хотите прервать '
             'заполнение анкеты - нажмите на /cancel'
    )


# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]['photo_id'],
            caption=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'Возраст: {user_dict[message.from_user.id]["age"]}\n'
                    f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
                    # f'Образование: {user_dict[message.from_user.id]["education"]}\n'
                    # f'Получать новости: {user_dict[message.from_user.id]["wish_news"]}'
        )
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(
            text='Вы еще не заполняли анкету. Чтобы приступить - '
            'отправьте нажмите на /fillform'
        )


class LikyCallbackFactory(CallbackData, prefix='id_article'):
    user_id: int


@dp.message(Command(commands='find'), StateFilter(default_state))
async def process_find_command(message: Message):
    if message.from_user.id in user_dict:
        random_user = random.choice(list(user_dict.keys()))
        while user_dict[message.from_user.id]["gender"] == user_dict[random_user]["gender"]:
            random_user = random.choice(list(user_dict.keys()))

        button = InlineKeyboardButton(text=f"❤️",
                                      callback_data=LikyCallbackFactory(user_id=random_user).pack())
        markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
        await message.answer_photo(
            photo=user_dict[random_user]['photo_id'],
            caption=f'Имя: {user_dict[random_user]["name"]}\n'
                    f'Возраст: {user_dict[random_user]["age"]}\n'
                    f'Пол: {user_dict[random_user]["gender"]}\n',
            reply_markup=markup)
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(
            text='Вы еще не заполняли анкету. Чтобы приступить - '
            'отправьте нажмите на /fillform'
        )


@dp.callback_query(LikyCallbackFactory.filter(), StateFilter(default_state))
async def liky_press(callback: CallbackQuery,
                     callback_data: LikyCallbackFactory):
    my_user_id = callback.from_user.id
    button = InlineKeyboardButton(text=f"❤️",
                                  callback_data=LikyCallbackFactory(user_id=my_user_id).pack())
    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
    if callback.from_user.username:
        await bot.send_photo(chat_id=callback_data.user_id,
                             photo=user_dict[my_user_id]['photo_id'],
                             caption=f'Тебе симпатизирует этот человек: @{callback.from_user.username}\n'
                                     f'Имя: {user_dict[my_user_id]["name"]}\n'
                                     f'Возраст: {user_dict[my_user_id]["age"]}\n'
                                     f'Пол: {user_dict[my_user_id]["gender"]}\n',
                             reply_markup=markup
                             )
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer('этот человек получит вашу анкету и сможет вам написать или лайкнуть в ответ')
    else:
        await callback.answer()
        await callback.message.answer('Добавьте имя пользователя в настройках вашего телеграмм аккаунта чтобы вам смог написать понравившийся вам человек')


# Этот хэндлер будет срабатывать на любые сообщения в состоянии "по умолчанию",
# кроме тех, для которых есть отдельные хэндлеры
@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, я Вас не понимаю, чтобы заполнить анкету нажми /fillform')


# Запускаем поллинг
if __name__ == '__main__':
    asyncio.run(main())
