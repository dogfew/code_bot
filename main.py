import logging
import json
import difflib

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor, markdown

from config import (markup_start, markup_random_adds, comment_markup, suggestions_markup,
                    codes, comments, suggestions,
                    diff_const, diff_const_search,
                    suggestions_lst_length, comments_lst_length,
                    suggestion_str_length, comment_str_length)
from data.BOT_TOKEN import TOKEN

logging.basicConfig(level=logging.INFO)

API_TOKEN = TOKEN

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup):
    start = State()
    get_ads = State()
    write_comment = State()
    write_suggestion = State()


@dp.message_handler(regexp=".+")
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """Выбор опции"""
    await Form.start.set()
    await message.reply("Я вас категорически приветствую.", reply_markup=markup_start)


@dp.message_handler(state='*', commands='help')
async def get_help(message: types.Message):
    text = f"Длина комментария до {comment_str_length}, длина предлож. кода до {suggestion_str_length}"
    await message.reply(text, reply_markup=markup_start)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='Назад', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """Отмена. Возврат к началу"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await Form.start.set()
    await message.reply('Отменено.', reply_markup=markup_start)


@dp.message_handler(regexp=".+", state=Form.start)
async def process_option(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        if "коммент" in message.text.lower():
            data["comment"] = True
            data["suggest"] = False
        elif "предлож" in message.text.lower():
            data["comment"] = False
            data["suggest"] = True
        else:
            data["comment"] = False
            data["suggest"] = False

    await Form.get_ads.set()

    await bot.send_message(
        message.chat.id,
        md.text(
            md.text("Если корпусов нет, введите адрес в формате: "),
            md.text("Улица, \\(№ дома\\), \\(№ подъезда\\):"),
            md.text("Например:", md.code("11-я Парковая улица, 19, 3")),
            md.text(),
            md.text("Если корпуса есть, введите адрес в формате: "),
            md.text("Улица, \\(№ дома\\)к\\(№ корпуса\\), \\(№ подъезда\\):"),
            md.text("Например:", md.code("11-я Парковая улица, 39к1, 2")),
            md.text(),
            md.text("Или\\.\\.\\. Просто введите адрес, и будет выбрано ближайшее совпадение"),
            sep='\n'
        ),
        reply_markup=markup_random_adds(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(
    lambda message: difflib.get_close_matches(message.text, codes.keys(), cutoff=diff_const, n=1),
    state=Form.get_ads)
async def process_ads(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        found = difflib.get_close_matches(message.text, codes.keys(), cutoff=diff_const, n=1)
        if message.text in codes.keys():
            await state.update_data(ads=message.text)
        else:
            await state.update_data(ads=found[0])
        if data['comment']:
            await Form.write_comment.set()
            await message.reply("Напишите коммент", reply_markup=comment_markup)
        elif data['suggest']:
            await Form.write_suggestion.set()
            await message.reply("Предложите код", reply_markup=suggestions_markup)

        else:
            await process_info(message=message, state=state)


@dp.message_handler(state=Form.get_ads)
async def process_ads_invalid(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    for i in difflib.get_close_matches(message.text, codes.keys(), cutoff=diff_const_search):
        markup.add(i)
    markup.add("Назад")
    await message.reply("Нет такого адреса, возможно, вы имели в виду:", reply_markup=markup)


@dp.message_handler(state=Form.write_suggestion)
async def process_suggestion(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        ads = data['ads']
    suggestion = message.text
    suggestions[ads] = suggestions.get(ads, [])
    suggestions[ads].append(suggestion)
    if len(suggestions) > suggestions_lst_length:
        suggestions.pop(-1)
    if len(suggestion) <= suggestion_str_length:
        json.dump(suggestions, open("data/suggestions.json", "w+"), ensure_ascii=False)
    else:
        await message.reply("Превышен допустимый размер кода. Код не добавлен в базу")
    await process_info(message=message, state=state)


@dp.message_handler(state=Form.write_comment)
async def process_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        ads = data['ads']
    comment = markdown.escape_md(message.text)  # to prevent parse entities error
    comments[ads] = comments.get(ads, [])
    if len(comments) > comments_lst_length:
        comments.pop(-1)
    if len(comment) <= comment_str_length:
        comments[ads].append(comment)
        json.dump(comments, open("data/comments.json", "w+"), ensure_ascii=False)
    else:
        await message.reply("Превышен допустимый размер коммента. Коммент не добавлен в базу.")
    await process_info(message=message, state=state)


async def process_info(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        ads = data['ads']
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Адрес:', md.code(ads)),
                *(md.text(f'Код {i}:', md.code(x))
                  for i, x in enumerate(codes.get(ads, []))),
                *(md.text(f'Предложенный код {i}:', md.code(x))
                  for i, x in enumerate(suggestions.get(ads, []))),
                md.text("Комментарии:" + "\t".join(i for i in comments.get(ads, []))),
                sep='\n',
            ),
            reply_markup=markup_start,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    await state.finish()
    await Form.start.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
