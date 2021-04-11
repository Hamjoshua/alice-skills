# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request
from .geo import get_country, get_coordinates, get_distance

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}


# Задаем параметры приложения Flask.
@app.route("/maps", methods=['POST'])
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
        response,
        ensure_ascii=False,
        indent=2
    )


# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Теперь я определять страну города и' \
                                  ' расстояние между двумя городами. Введите один/два города'
        return

    cities = get_cities(req)
    if len(cities) == 1:
        country = get_country(cities[0])
        res['response']['text'] = 'Страна этого города - %s. Можете ввести следующие города!'\
                                  % country
    elif len(cities) == 2:
        distance = get_distance(get_coordinates(cities[0]), get_coordinates(cities[1]))
        res['response']['text'] = 'Дистанция между этими городами равна %s метров.' \
                                  ' Давайте попробуем еще раз?' % distance

    else:
        res['response']['text'] = 'Я умею работать с одним или двумя городами. ' \
                                  'Вспомните самый лучшеий город на свете... Или может их два?' \
                                  ' Пишите сюда!'


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['values']['city'])
    return cities


