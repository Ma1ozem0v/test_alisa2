import os

from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    'москва': ['965417/06a32a848fd958306409',
               '965417/af2b4268eef414df9a17'],
    'нью-йорк': ['1652229/1822afcb0e15b6b6627d',
                 '997614/ac5324e9fd6fb0ae348b'],
    'париж': ["1652229/2bd2f38f1e51fcf4e5b9",
              '1652229/795023ff1b8cfac21447']
}

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Какой город хочешь увидеть?'
            # получаем варианты buttons из ключей нашего словаря cities
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in cities
            ]
    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    else:
        # ищем город в сообщение от пользователя
        city = get_city(req)
        # если этот город среди известных нам,
        # то показываем его (выбираем одну из двух картинок случайно)
        if city in cities:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Этот город я знаю.'
            res['response']['card']['image_id'] = random.choice(cities[city])
            res['response']['text'] = 'Я угадал!'
        # если не нашел, то отвечает пользователю
        # 'Первый раз слышу об этом городе.'
        else:
            res['response']['text'] = \
                'Первый раз слышу об этом городе. Попробуй еще разок!'


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)