from telebot import *
from telebot.types import *
import sqlite3
import json
import os
import requests

TELEGRAM_TOKEN = ///
CHANNEL_ID = ////
CHANNEL_URL = ///
API_TOKEN = ///

headers = {
    'accept': 'application/json',
    'X-API-KEY': API_TOKEN,
}

bot = TeleBot(TELEGRAM_TOKEN)

if not os.path.exists("tgkinobot.db"):
    with open("tgkinobot.db", "w") as file:
        pass
db = sqlite3.connect("tgkinobot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS main (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_ids   TEXT
);""")
db.commit()

cur.execute("SELECT tg_ids FROM main")
accounts = cur.fetchone()
if accounts is None:
    cur.execute("INSERT INTO main(tg_ids) VALUES(?)", (json.dumps([]),))
    db.commit()
    accounts = []
else:
    accounts = json.loads(accounts[0])


@bot.message_handler(commands=['start', 'help'])
def start(message: Message):
    channel_members = bot.get_chat_member(CHANNEL_ID, message.from_user.id)

    if message.chat.id in accounts:
        text = f"И снова здравствуйте, {message.from_user.first_name.capitalize()}!"
    else:
        accounts.append(message.chat.id)

        cur.execute("UPDATE main SET tg_ids = ?", (json.dumps(accounts),))
        db.commit()

        text = f"Добрый день, {message.from_user.first_name.capitalize()}!"

    if channel_members.status != "left":
        bot.send_message(message.chat.id,
                         f"{text}\n\nВы находитесь в лучшем боте для просмотра сериалов прямо в Telegram!\n\nСмотрите сериалы на телефоне, планшете и компьютере. Подписывайтесь на уведомления о новых сериях. Сортируйте сериалы по названию, жанрам и интересам. Скачивайте сериалы себе на устройство и смотрите без интернета.\n\nУ нас появился бот с детскими мультсериалами\n\n<i>Используя бота, вы подтверждаете, что будете соблюдать возрастные ограничения сериалов.</i>",
                         "html", reply_markup=ReplyKeyboardRemove())
        after_start(message)
    else:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Подписаться на канал", url=CHANNEL_URL),
                   InlineKeyboardButton("Приступить к просмотру", callback_data="checksubscribe_NULL_NULL"))

        bot.send_message(message.chat.id,
                         f"{text}\n\nЧтобы приступить к просмотру сериалов в боте, необходимо подписаться на наш канал с анонсами — для этого воспользуйтесь кнопками ниже!\n\nПосле подписки на канал вернитесь обратно в @{bot.get_me().username} и нажмите кнопку «Приступить к просмотру».\n\n<i>Бот работает абсолютно бесплатно и без ограничений! Наслаждайтесь!</i>",
                         "html", reply_markup=markup)


def after_start(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Поиск", "Список сериалов и фильмов", "По жанрам")

    send_message = bot.send_message(message.chat.id,
                                    "Поздравляем! Теперь вы можете приступить к просмотру сериалов.\n\nВоспользуйтесь кнопками ниже или напишите боту название нужного сериала!",
                                    reply_markup=markup)
    bot.register_next_step_handler(send_message, main)


def main(message: Message):
    text = message.text

    if text == "Поиск":
        send_message = bot.send_message(message.chat.id, " Просто отправьте боту название сериала.")
        bot.register_next_step_handler(send_message, get_text)
    elif text == "Список сериалов и фильмов":
        params = {
            'type': 'TOP_250_BEST_FILMS',
            'page': '1',
        }

        response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films/top', params=params,
                                headers=headers)

        markup = InlineKeyboardMarkup(row_width=1)
        for film in response.json()["films"]:
            raiting = film["rating"]
            name = film["nameRu"]

            if name is None:
                name = film["nameEn"]

            if raiting:
                raiting = round(float(raiting))

                name = f"{raiting} {name}"

            markup.add(InlineKeyboardButton(name, callback_data=f"film_{film['filmId']}_tolist_1"))

        markup.add(InlineKeyboardButton("След »", callback_data="next_best_1"))

        send_message = bot.send_message(message.chat.id,
                                        "Ниже представлен список лучших сериалов и фильмов.\n\nКакой хотите посмотреть сериал?",
                                        reply_markup=markup)
        bot.register_next_step_handler(send_message, main)
    elif text == "По жанрам":
        response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films/filters', headers=headers)

        markup = InlineKeyboardMarkup(row_width=1)
        for genre in response.json()["genres"][:10 if len(response.json()["genres"]) > 10 else None]:
            name = genre["genre"].capitalize()

            markup.add(InlineKeyboardButton(name, callback_data=f"genre_{genre['id']}_{genre['genre'].capitalize()}_0"))

        markup.add(InlineKeyboardButton("След »", callback_data="next_genres_0"))

        send_message = bot.send_message(message.chat.id,
                                        "Ниже представлен список жанров.\n\nВ каком жанре хотите посмотреть сериал\фильм?",
                                        reply_markup=markup)
        bot.register_next_step_handler(send_message, main)
    else:
        send_message = bot.send_message(message.chat.id, "Нет такой кнопки")
        bot.register_next_step_handler(send_message, main)


def get_text(message: Message):
    text = message.text

    if text:
        params = {
            'order': 'RATING',
            'type': 'ALL',
            'ratingFrom': '0',
            'ratingTo': '10',
            'yearFrom': '1000',
            'yearTo': '3000',
            'keyword': text,
            'page': '1',
        }

        response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films', params=params, headers=headers)

        if response.json()["total"] != 0:
            markup = InlineKeyboardMarkup(row_width=1)
            for film in response.json()["items"]:
                raiting = film["ratingKinopoisk"]
                name = film["nameRu"]

                if name is None:
                    name = film["nameOriginal"]

                if raiting:
                    raiting = round(float(raiting))

                    name = f"{raiting} {name}"

                markup.add(InlineKeyboardButton(name, callback_data=f"film_{film['kinopoiskId']}_tolist_1"))

            send_message = bot.send_message(chat_id=message.chat.id,
                                            text=f"Ниже представлен список сериалов по запросу <b>«{text}»</b>",
                                            parse_mode="html",
                                            reply_markup=markup)
        else:
            send_message = bot.send_message(message.chat.id,
                                            "К сожалению, по вашему запросу ничего не найдено.\n\nПочему сериалы могут не находиться?\n\n1. Убедитесь, что вы ввели правильное название сериала.\n\n2. Если вы уверены в правильности названия, попробуйте найти нужный сериал с помощью кнопок ниже.\n\n3. Мы отслеживаем все поисковые запросы наших пользователей. Ваш запрос уже принят в очередь на добавление, поэтому через какое-то время нужный вам сериал появится в боте.")
        bot.register_next_step_handler(send_message, main)
    else:
        send_message = bot.send_message(message.chat.id, "Отправьте текст!")
        bot.register_next_step_handler(send_message, get_text)


@bot.callback_query_handler(func=lambda call: True)
def callback(callback: CallbackQuery):
    type, type2, param1, *params = callback.data.split("_")

    if type == "checksubscribe":
        channel_members = bot.get_chat_member(CHANNEL_ID, callback.message.chat.id)

        if channel_members.status == "left":
            bot.answer_callback_query(callback.id, "Вы не подписаны на канал!")
        else:
            bot.edit_message_text(text=callback.message.text, chat_id=callback.message.chat.id,
                                  message_id=callback.message.message_id)
            after_start(callback.message)
    elif type == "next" or type == "prev" or type == "to":
        if type2 == "best":
            param = {
                'type': 'TOP_250_BEST_FILMS',
                'page': int(param1) + 1 if type == "next" else (int(param1) - 1 if type == "prev" else int(param1)),
            }

            response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films/top', params=param,
                                    headers=headers)

            markup = InlineKeyboardMarkup(row_width=1)
            for film in response.json()["films"]:
                raiting = film["rating"]
                name = film["nameRu"]

                if name is None:
                    name = film["nameEn"]

                if raiting:
                    raiting = round(float(raiting))

                    name = f"{raiting} {name}"

                markup.add(InlineKeyboardButton(name, callback_data=f"film_{film['filmId']}_tolist_{param['page']}"))

            add_list = []
            if param["page"] > 1:
                add_list.append(InlineKeyboardButton("« Пред", callback_data=f"prev_best_{param['page']}"))
            if param["page"] < 13:
                add_list.append(InlineKeyboardButton("След »", callback_data=f"next_best_{param['page']}"))

            markup.add(*add_list, row_width=2)

            if callback.message.content_type == "text":
                if type == "to":
                    bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
                bot.edit_message_text(chat_id=callback.message.chat.id,
                                      text="Ниже представлен список лучших сериалов и фильмов.\n\nКакой хотите посмотреть сериал?",
                                      reply_markup=markup, message_id=callback.message.message_id)
            else:
                bot.delete_message(callback.message.chat.id, callback.message.message_id)
                bot.send_message(chat_id=callback.message.chat.id,
                                 text="Ниже представлен список лучших сериалов и фильмов.\n\nКакой хотите посмотреть сериал?",
                                 reply_markup=markup)
        elif type2 == "genres":
            page = int(param1) + 1 if type == "next" else (int(param1) - 1 if type == "prev" else int(param1))

            response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films/filters', headers=headers)

            markup = InlineKeyboardMarkup(row_width=1)

            for genre in response.json()["genres"][
                         page * 10:(page + 1) * 10 if len(response.json()["genres"]) > (page + 1) * 10 else None]:
                name: str = genre["genre"].capitalize()

                markup.add(InlineKeyboardButton(name,
                                                callback_data=f"genre_{genre['id']}_{genre['genre'].capitalize()}_{page}"))

            add_list = []
            if page >= 1:
                add_list.append(InlineKeyboardButton("« Пред", callback_data=f"prev_genres_{page}"))
            if len(response.json()["genres"]) > (page + 1) * 10:
                add_list.append(InlineKeyboardButton("След »", callback_data=f"next_genres_{page}"))

            markup.add(*add_list, row_width=2)

            bot.edit_message_text(chat_id=callback.message.chat.id,
                                  text="Ниже представлен список жанров.\n\nВ каком жанре хотите посмотреть сериал\фильм?",
                                  reply_markup=markup, message_id=callback.message.message_id)
        elif type2 == "gf":
            param = {
                'genres': params[0],
                'order': 'RATING',
                'type': 'ALL',
                'ratingFrom': '0',
                'ratingTo': '10',
                'yearFrom': '1000',
                'yearTo': '3000',
                'page': int(param1) + 1 if type == "next" else (int(param1) - 1 if type == "prev" else int(param1)),
            }

            response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films', params=param,
                                    headers=headers)

            markup = InlineKeyboardMarkup(row_width=1)
            for film in response.json()["items"]:
                raiting = film["ratingKinopoisk"]
                name = film["nameRu"]

                if name is None:
                    name = film["nameOriginal"]

                if raiting:
                    raiting = round(float(raiting))

                    name = f"{raiting} {name}"

                markup.add(InlineKeyboardButton(name,
                                                callback_data=f"film_{film['kinopoiskId']}_togf_to$gf${param['page']}${params[0]}${params[1]}${params[2]}"))

            add_list = []
            if param["page"] > 1:
                add_list.append(InlineKeyboardButton("« Пред",
                                                     callback_data=f"prev_gf_{param['page']}_{params[0]}_{params[1]}_{params[2]}"))
            else:
                add_list.append(InlineKeyboardButton("« К жанрам", callback_data=f"to_genres_{params[1]}"))
            if param["page"] < response.json()["totalPages"]:
                add_list.append(InlineKeyboardButton("След »",
                                                     callback_data=f"next_gf_{param['page']}_{params[0]}_{params[1]}_{params[2]}"))
            else:
                add_list.append(InlineKeyboardButton("К жанрам »", callback_data=f"to_genres_{params[1]}"))

            markup.add(*add_list, row_width=2)

            if callback.message.content_type == "text":
                if type == "to":
                    bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
                bot.edit_message_text(chat_id=callback.message.chat.id,
                                      text=f"Ниже представлен список сериалов в жанре <b>{params[2]}</b>.\n\nКакой хотите посмотреть сериал?",
                                      reply_markup=markup, message_id=callback.message.message_id, parse_mode="html")
            else:
                bot.delete_message(callback.message.chat.id, callback.message.message_id)
                bot.send_message(chat_id=callback.message.chat.id,
                                 text=f"Ниже представлен список сериалов в жанре <b>{params[2]}</b>.\n\nКакой хотите посмотреть сериал?",
                                 reply_markup=markup, parse_mode="html")

    elif type == "genre":
        param = {
            'genres': type2,
            'order': 'RATING',
            'type': 'ALL',
            'ratingFrom': '0',
            'ratingTo': '10',
            'yearFrom': '1000',
            'yearTo': '3000',
            'page': '1',
        }

        response = requests.get('https://kinopoiskapiunofficial.tech/api/v2.2/films', params=param, headers=headers)

        markup = InlineKeyboardMarkup(row_width=1)
        for film in response.json()["items"]:
            raiting = film["ratingKinopoisk"]
            name = film["nameRu"]

            if name is None:
                name = film["nameOriginal"]

            if raiting:
                raiting = round(float(raiting))

                name = f"{raiting} {name}"

            markup.add(InlineKeyboardButton(name,
                                            callback_data=f"film_{film['kinopoiskId']}_togf_to$gf$1${type2}${params[0]}${param1}"))

        markup.add(InlineKeyboardButton("« К жанрам", callback_data=f"to_genres_{params[0]}"),
                   InlineKeyboardButton("След »", callback_data=f"next_gf_1_{type2}_{params[0]}_{param1}"),
                   row_width=2)

        bot.edit_message_text(chat_id=callback.message.chat.id,
                              text=f"Ниже представлен список сериалов в жанре <b>{param1}</b>.\n\nКакой хотите посмотреть сериал?",
                              reply_markup=markup, message_id=callback.message.message_id, parse_mode="html")
    elif type == "film":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        markup = InlineKeyboardMarkup(row_width=1)
        if param1 == "tolist":
            markup.add(InlineKeyboardButton("Назад к списку сериалов", callback_data=f"to_best_{params[0]}"))
        elif param1 == "togf":
            markup.add(InlineKeyboardButton("Назад к жанру", callback_data=params[0].replace("$", "_")))

        response = requests.get(f'https://kinopoiskapiunofficial.tech/api/v2.2/films/{type2}', headers=headers)
        data = response.json()

        name = data["nameRu"]
        if name is None:
            name = data["nameOriginal"]

        photo = data["posterUrl"]
        ratingKinopoisk = data["ratingKinopoisk"]
        ratingKinopoiskVoteCount = data["ratingKinopoiskVoteCount"]
        ratingImdb = data["ratingImdb"]
        ratingImdbVoteCount = data["ratingImdbVoteCount"]
        year = data["year"]
        url = data["webUrl"]
        lenght = data["filmLength"]
        slogan = data["slogan"]
        description = data["description"]
        annotation = data["editorAnnotation"]
        age = data["ratingAgeLimits"]
        countries = [country["country"] for country in data["countries"]]
        genres = [genre["genre"] for genre in data["genres"]]
        start = data["startYear"]
        end = data["endYear"]

        slah = "\n"
        caption = f"""<b>{name}</b>

Слоган: {slogan if slogan else ''}

Описание: {description if not annotation else f'{description}{slah}{slah}Примечание: {annotation}'}

Возрастное ограничение: {age}+

Кинопоиск: {ratingKinopoisk}
Количество проголосовавших: {ratingKinopoiskVoteCount}

IMDB: {ratingImdb}
Количество проголосовавших: {ratingImdbVoteCount}

Длина: {lenght} мин

Страны: {', '.join(countries)}

Жанры: {', '.join(genres)}

{f'Год: {year}' if not start else f'Начало: {start}{slah}{slah}Конец: {end if end else ""}'}

Фильм/сериал: {url}"""

        if len(caption) > 1024:
            list_strings = caption.split("\n")
            if len(caption) <= 4096:
                bot.send_photo(chat_id=callback.message.chat.id, photo=photo, caption=f"<b>{name}</b>",
                               parse_mode="html")
                bot.send_message(chat_id=callback.message.chat.id,
                                 text="\n".join(list_strings[1:]),
                                 parse_mode="html", disable_web_page_preview=True, reply_markup=markup)
            else:
                caption = f"""<b>{name}</b>

Возрастное ограничение: {age.replace("age", "") if age else ''}+

Кинопоиск: {ratingKinopoisk}
Количество проголосовавших: {ratingKinopoiskVoteCount}

IMDB: {ratingImdb}
Количество проголосовавших: {ratingImdbVoteCount}

Длина: {lenght} мин

Страны: {', '.join(countries)}

Жанры: {', '.join(genres)}

{f'Год: {year}' if not start else f'Начало: {start}{slah}{slah}Конец: {end if end else ""}'}

Фильм/сериал: {url}"""
                bot.send_photo(chat_id=callback.message.chat.id, photo=photo,
                               caption=caption,
                               parse_mode="html", reply_markup=markup)
        else:
            bot.send_photo(chat_id=callback.message.chat.id, photo=photo,
                           caption=caption,
                           parse_mode="html", reply_markup=markup)


bot.polling()
