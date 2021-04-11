# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
import requests
from flask import Flask, request

# Импортируем random для случайного выбора картинки города
import random

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# словарь "имя города: массив с id картинок"

cities = {
    'москва': {'img_set': ['213044/069bf0697051269a0cb2',
                           '1521359/519882f5ee15f2416760'],
               'country': 'россия'},
    'нью-йорк': {'img_set': ['937455/47a0d453b991b0d10aff',
                             '937455/6a1d6b72971931e0895c'],
                 'country': 'сша'},
    'париж': {'img_set': ['1521359/f9897122bfcf76f44051',
                          '1540737/f92af27646c777d0c841'],
              'country': "франция"}
}

# Хранилище данных о сессиях.
sessionStorage = {}


# Задаем параметры приложения Flask.
@app.route("/post", methods=['POST'])
def main():
    # Функция получает тело запроса и возвращает ответ.
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', response)

    return json.dumps(
        response
    )


# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    res['response']['buttons'] = [{'title': 'Помощь', 'hide': True}]

    # Если пользователь активировал кнопку помощи
    if req['request']['command'] == 'помощь':
        res['response'][
            'text'] = '"Угадай город" - отгадывание города по его картинке. Пользователю ' \
                      'дается фиксированный набор городов, по истечению которых игра за' \
                      'канчивается. Пользователь может сам остановить игру.'
        return

        # Если это новый пользователь, то просим его представиться

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя.'
        # Создает словарь, в который в будущем положим имя юзера
        sessionStorage[user_id] = {
            'first_name': None
        }
        sessionStorage[user_id]['cities'] = []
        sessionStorage[user_id]['current_city'] = None
        sessionStorage[user_id]['game_status'] = None
        return

    user_name = sessionStorage[user_id]['first_name']
    res['response']['text'] = 'Анон, ' if user_name is None else '%s, ' % user_name.capitalize()

    if req['request']['command'] == 'покажи город на карте':
        res['response']['text'] += 'без проблем. Сыграем еще раз?'
        return

    # Если пользователь не новый, то обрабатываем его имя
    if sessionStorage[user_id]['first_name'] is None:
        # Ищем имя юзера в его последнем сообщении
        first_name = get_first_name(req)
        # Если не нашли, то просим его вписать имя снова
        if first_name is None:
            res['response']['text'] += 'не расслышала! Повторите имя, пожалуйста.'
        # Если же нашли, то категорически его приветствуем
        else:
            res['response']['text'] = 'Рада знакомству, %s. Я - Алиса.' \
                                      ' Отгадаете город по фото?' % first_name.title()
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['buttons'].extend([{'title': "Да", 'hide': True},
                                               {'title': 'Нет', 'hide': True}])

    elif sessionStorage[user_id]['game_status'] is None:
        # Проверяем на Да/Нет
        if req['request']['command'] == 'да':
            sessionStorage[user_id]['game_status'] = True
            logging.info('City selecting...')
            for city in cities:
                if city not in sessionStorage[user_id]['cities'] and \
                        sessionStorage[user_id]['current_city'] is None:
                    sessionStorage[user_id]['current_city'] = city
            logging.info('City was selected - %s', sessionStorage[user_id]['current_city'])
            if sessionStorage[user_id]['current_city'] is None:
                res['response']['text'] += "боюсь, что города закончились." \
                                           " Приходите завтра, может, завезут ;)."
                sessionStorage[user_id]['game_status'] = False
                return
            res['response']['text'] += 'что за город?'
            res['response']['card'] = {
                'type': 'BigImage',
                'title': 'Что за город?',
                'image_id': random.choice(cities[sessionStorage[user_id]['current_city']]['img_set'])
            }
        elif req['request']['command'] == 'нет':
            sessionStorage[user_id]['game_status'] = False
            res['response']['text'] += 'заходите ко мне еще. Хорошего дня!'
        else:
            res['response']['text'] += 'не поняла ответа. Так да или нет?'

    # Если мы знакомы с юзером и он что-то написал, то обрабатываем его последнее сообщение
    elif sessionStorage[user_id]['game_status'] is True:
        # ищем город в сообщении от пользователя
        geo = get_geo(req)
        if sessionStorage[user_id]['current_city'] not in sessionStorage[user_id]['cities']:
            if geo == sessionStorage[user_id]['current_city']:
                res['response']['text'] += "верно! А в какой стране находится этот город?"
            else:
                res['response']['text'] += 'вы пытались. Это "%s"! В какой стране может' \
                                           ' нахоодится этот город?' \
                                           % sessionStorage[user_id]['current_city'].capitalize()
            sessionStorage[user_id]['cities'].append(sessionStorage[user_id]['current_city'])
        else:
            country = cities[sessionStorage[user_id]['current_city']]['country']
            if geo == country:
                res['response']['text'] += 'правильно! Сыграем еще?'
            else:
                res['response']['text'] += 'почти! Правильный ответ - %s.' \
                                           ' Сыграем еще?' % country.capitalize()
            # Поскольку игра закончилась, мы ставим ей None и даем юзеру выбор
            res['response']['buttons'] = [
                {'title': "Да", 'hide': True},
                {'title': 'Нет', 'hide': True},
                {'title': "Покажи город на карте", 'hide': True,
                 'url': f"https://yandex.ru/maps/?mode=search&text={sessionStorage[user_id]['current_city']}"}
            ]
            sessionStorage[user_id]['game_status'] = None
            sessionStorage[user_id]['current_city'] = None
    else:
        if len(cities) == len(sessionStorage[user_id]['cities']):
            res['response']['text'] += "боюсь, что города закончились." \
                                       " Приходите завтра, может, завезут ;)."
        else:
            if req['request']['command'] == 'угадай город':
                sessionStorage[user_id]['game_status'] = None
                res['response']['text'] += 'точно?'
                res['response']['buttons'] = [
                    {'title': "Да", 'hide': True},
                    {'title': 'Нет', 'hide': True}]
            else:
                res['response']['text'] += 'вы закончили игру, но вы можете ее начать' \
                                           ' с помощью команды "Угадай город"'


# Функция проверяет, точно ли юзер вписал имя
def get_first_name(req):
    # Перебор сущностей
    for entity in req['request']['nlu']['entities']:
        # Находим сущность "YANDEX.FIO"
        if entity['type'] == 'YANDEX.FIO':
            # Если сущность с ключом "first_name"
            # То возвращаем ее значение. В других случаях - None
            return entity['value'].get('first_name', None)


def get_geo(req):
    for entity in req['request']['nlu']['entities']:
        # Находим сущность "YANDEX.GEO"
        if entity['type'] == 'YANDEX.GEO':
            # Если сщуность с ключом "city"
            # То возвращаем ее значение. В других случаях - None
            geo = entity['value'].get('city', None)
            if geo is None:
                geo = entity['value'].get('country', None)
            return geo

