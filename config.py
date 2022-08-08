from json import load
from random import choice

from aiogram import types

"""Базы данных"""
codes = load(open("data/codes.json"))
comments = load(open("data/comments.json"))
suggestions = load(open("data/suggestions.json"))

"""Константы"""
diff_const = 0.7  # константа для difflib для автоматической выдачи ближайшего совпадения
diff_const_search = 0.3  # константа для difflib для поиска ближайших совпадений
suggestions_lst_length = 15  # максимальное количество предлож. кодов
comments_lst_length = 10  # максимальное количество комментов
suggestion_str_length = 35  # максимальная длина предлож. кода
comment_str_length = 50  # максимальная длина комента


"""Клавиатуры"""

markup_start = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
markup_start.add("Получить код")
markup_start.add("Предложить код")
markup_start.add("Комментарий")

comment_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
comment_markup.add("Предлож. коды не работают", "Домофон не работает")
comment_markup.add("Консъерж", "Только ключи")
comment_markup.add("Всё работает", "Назад")

suggestions_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
suggestions_markup.add("Назад")


def markup_random_adds():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    number_of_streets = 3
    for _ in range(number_of_streets):
        markup.add(choice(list(codes)))
    markup.add("Назад")
    return markup
