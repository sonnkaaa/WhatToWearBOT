import telebot
import requests
import schedule
import time
from threading import Thread
from telebot import types

API = 'd1a4b63c8321fe1a53f477bd4bb878a9'
bot = telebot.TeleBot('7469488186:AAEP3qKloejZYPaUFrMKPe9HUMAAggVm8Ts')
users = {}

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if users[chat_id].get('frequency') == 'daily':
        markup.add('Отменить рассылку')
    else:
        markup.add('Подключить рассылку')
    markup.add('Изменить город', 'Посмотреть погоду')
    bot.send_message(chat_id, 'Выберите действие:', reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Каждое утро', 'Только по запросу')
    msg = bot.send_message(message.chat.id, 'Привет! Как часто вам отправлять прогноз погоды?', reply_markup=markup)
    bot.register_next_step_handler(msg, process_frequency_step)

def process_frequency_step(message):
    chat_id = message.chat.id
    if message.text == 'Каждое утро':
        users[chat_id] = {'frequency': 'daily'}
        msg = bot.send_message(chat_id, 'Напишите название города, чтобы я мог отправлять вам прогноз погоды каждое утро.')
        bot.register_next_step_handler(msg, save_city)
    elif message.text == 'Только по запросу':
        users[chat_id] = {'frequency': 'on_request'}
        msg = bot.send_message(chat_id, 'Напишите название города, чтобы я мог отправлять вам прогноз погоды по запросу.')
        bot.register_next_step_handler(msg, save_city)
    else:
        bot.send_message(chat_id, 'Пожалуйста, выберите один из вариантов: "Каждое утро" или "Только по запросу".')

@bot.message_handler(commands=['change_city'])
def change_city(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Напишите название нового города.')
    bot.register_next_step_handler(msg, save_city)

@bot.message_handler(commands=['show_weather'])
def show_weather(message):
    chat_id = message.chat.id
    if chat_id in users:
        city = users[chat_id].get('city')
        if city:
            weather = get_weather(city)
            if weather:
                recommendation = get_clothing_recommendation(weather)
                weather_message = format_weather_message(city, weather, recommendation)
                bot.send_message(chat_id, weather_message)
            else:
                bot.send_message(chat_id, 'Не удалось получить данные о погоде. Пожалуйста, попробуйте позже.')
        else:
            bot.send_message(chat_id, 'Пожалуйста, укажите город командой /change_city.')
    else:
        bot.send_message(chat_id, 'Пожалуйста, начните с команды /start.')

@bot.message_handler(func=lambda message: message.text in ['Изменить город', 'Посмотреть погоду', 'Отменить рассылку', 'Подключить рассылку'])
def handle_main_menu(message):
    chat_id = message.chat.id
    if message.text == 'Изменить город':
        change_city(message)
    elif message.text == 'Посмотреть погоду':
        show_weather(message)
    elif message.text == 'Отменить рассылку':
        cancel_schedule(message)
    elif message.text == 'Подключить рассылку':
        connect_schedule(message)
    else:
        send_main_menu(chat_id)

def save_city(message):
    chat_id = message.chat.id
    city = message.text
    if chat_id in users:
        users[chat_id]['city'] = city
        bot.send_message(chat_id, f'Отлично! Я буду отправлять вам прогноз погоды для города {city}.')
    else:
        users[chat_id] = {'city': city}
        bot.send_message(chat_id, f'Город {city} сохранён.')
    send_main_menu(chat_id)

def cancel_schedule(message):
    chat_id = message.chat.id
    if chat_id in users:
        users[chat_id]['frequency'] = 'on_request'
        bot.send_message(chat_id, 'Ежедневная рассылка отменена.')
    send_main_menu(chat_id)

def connect_schedule(message):
    chat_id = message.chat.id
    if chat_id in users:
        users[chat_id]['frequency'] = 'daily'
        bot.send_message(chat_id, 'Ежедневная рассылка подключена.')
    else:
        users[chat_id] = {'frequency': 'daily'}
        bot.send_message(chat_id, 'Ежедневная рассылка подключена. Пожалуйста, укажите город командой /change_city.')
    send_main_menu(chat_id)

def get_weather(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API}&units=metric&lang=ru'
    response = requests.get(url).json()
    if response.get('cod') != 200:
        return None
    weather = {
        'temperature': response['main']['temp'],
        'feels_like': response['main']['feels_like'],
        'wind_speed': response['wind']['speed'],
        'description': response['weather'][0]['description']
    }
    return weather


def get_clothing_recommendation(weather):
    temp = weather['temperature']
    feels_like = weather['feels_like']
    wind_speed = weather['wind_speed']
    description = weather['description']

    if 'дождь' in description or 'снег' in description:
        return 'Возьмите зонтик или наденьте водонепроницаемую куртку.'
    elif feels_like < 0:
        return 'Наденьте тёплую зимнюю одежду, шапку и перчатки.'
    elif 0 <= feels_like <= 10:
        return 'Наденьте пальто и тёплый свитер.'
    elif 10 < feels_like <= 20:
        return 'Наденьте лёгкую куртку или свитер.'
    else:
        return 'Наденьте лёгкую одежду, например футболку и шорты.'

def format_weather_message(city, weather, recommendation):
    return (
        f"Прогноз погоды для {city}:\n"
        f"Температура: {weather['temperature']}°C\n"
        f"Ощущается как: {weather['feels_like']}°C\n"
        f"Скорость ветра: {weather['wind_speed']} м/с\n"
        f"Осадки: {weather['description']}\n"
        f"Рекомендации по одежде: {recommendation}"
    )

def send_weather_update():
    for chat_id, info in users.items():
        if info.get('frequency') == 'daily':
            city = info.get('city')
            if city:
                weather = get_weather(city)
                if weather:
                    recommendation = get_clothing_recommendation(weather)
                    weather_message = format_weather_message(city, weather, recommendation)
                    bot.send_message(chat_id, weather_message)

def scheduler():
    schedule.every().day.at("18:21").do(send_weather_update)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    Thread(target=scheduler).start()
    bot.polling()
