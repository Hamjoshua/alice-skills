# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request

# Импортируем random для случайного выбора картинки города
import random

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# словарь "имя города: массив с id картинок"

cities = {
    'москва': ['213044/069bf0697051269a0cb2', '1521359/519882f5ee15f2416760'],
    'нью-йорк': ['937455/47a0d453b991b0d10aff', '937455/6a1d6b72971931e0895c'],
    'париж': ['1521359/f9897122bfcf76f44051', '1540737/f92af27646c777d0c841']
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

    # Если это новый пользователь, то просим его представиться
    if req['session']['new']:
        sessionStorage[user_id] = {'suggests': ["Не хочу.", "Не буду.", "Отстань!"]}
        sessionStorage[user_id]['product'] = 'слоник'

        res['response']['text'] = 'Привет! Назови свое имя.'
        # Создает словарь, в который в будущем положим имя юзера
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # Если пользователь не новый, то обрабатываем его имя
    if sessionStorage[user_id]['first_name'] is None:
        # Ищем имя юзера в его последнем сообщении
        first_name = get_first_name(req)
        # Если не нашли, то просим его вписать имя снова
        if first_name is None:
            res['response']['text'] = 'Что? Не расслышала! Повтори, пожалуйста.'
        # Если же нашли, то категорически его приветствуем
        else:
            res['response']['text'] = 'Рада знакомству, %s. Я - Алиса.' \
                                      ' Какой город хочешь увидеть?' % first_name.title()
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['buttons'] = [{
                'title': city.title(),
                'hide': True
            } for city in cities]

    # Если мы знакомы с юзером и он что-то написал, то обрабатываем его последнее сообщение
    else:
        # ищем город в сообщении от пользователя
        city = get_city(req)
        # если этот город есть в нашем списке, то показываем его юзеру из двух картинок
        if city in cities:
            res['response']['card'] = {
                'type': 'BigImage',
                'title': 'Этот город я знаю.',
                'image_id': random.choice(cities[city])
            }
            res['response']['text'] = 'Я угадала!'
        else:
            res['response']['text'] = "Оу. Я никогда не слышала о таком. Попробуй еще раз!"


# Функция проверяет, точно ли юзер вписал имя
def get_first_name(req):
    # Перебор сущностей
    for entity in req['request']['nlu']['entities']:
        # Находим сущность "YANDEX.FIO"
        if entity['type'] == 'YANDEX.FIO':
            # Если сущность с ключом "first_name"
            # То возвращаем ее значение. В других случаях - None
            return entity['value'].get('first_name', None)


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        # Находим сущность "YANDEX.GEO"
        if entity['type'] == 'YANDEX.GEO':
            # Если сщуность с ключом "city"
            # То возвращаем ее значение. В других случаях - None
            return entity['value'].get('city', None)
