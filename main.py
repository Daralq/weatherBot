import asyncio
import requests
import datetime
import pymorphy3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

#токен
TG_TOKEN = "8218519059:AAEsOMpFjmYsOwcKmrkhixzIfFXFydx8m2E"
OWM_API_KEY = "2e46c50587f4626dab51eba27fb1778b"

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
morph = pymorphy3.MorphAnalyzer()

#словарь города
user_data = {}


#клавиши
def main_keyboard(user_id):
    buttons = [
        [KeyboardButton(text="Москва"), KeyboardButton(text="Санкт-Петербург")],
        [KeyboardButton(text="Узнать по геолокации 📍", request_location=True)]
    ]

    #город на первую строку
    if user_id in user_data:
        saved_city = user_data[user_id]
        buttons.insert(0, [KeyboardButton(text=f"🏠 Мой город: {saved_city}")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите город..."
    )
    return keyboard


#словарь
code_to_smile = {
    "Clear": "Ясно \U00002600",
    "Clouds": "Облачно \U00002601",
    "Rain": "Дождь \U00002614",
    "Drizzle": "Дождь \U00002614",
    "Thunderstorm": "Гроза \U000026A1",
    "Snow": "Снег \U0001F328",
    "Mist": "Туман \U0001F32B"
}


def get_city_prepositional(city_name):
    words = city_name.split()
    inflected_words = []
    for word in words:
        parsed = morph.parse(word)[0]
        inflected = parsed.inflect({'loct'})
        if inflected:
            inflected_words.append(inflected.word.capitalize())
        else:
            inflected_words.append(word.capitalize())
    return " ".join(inflected_words)


@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! Я запомню твой город, если ты отправишь мне свою геолокацию.",
        reply_markup=main_keyboard(message.from_user.id)
    )


#Обработка гео
@dp.message(F.location)
async def weather_by_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=ru"
    #получение данных
    r = requests.get(url)
    data = r.json()
    if data.get("cod") == 200:
        city_name = data["name"]
        user_data[message.from_user.id] = city_name  # ЗАПОМИНАЕМ город
        await message.answer(f"✅ Город {city_name} сохранен! Теперь у вас появилась кнопка быстрого доступа.")

    await process_weather_data(message, url)


#Обработка текстовых сообщений
@dp.message(F.text)
async def weather_by_city(message: Message):
    text = message.text
    #мусорка
    if text.startswith("🏠 Мой город: "):
        city = text.replace("🏠 Мой город: ", "")
    else:
        city = text

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    await process_weather_data(message, url)


#функция для вывода погоды
async def process_weather_data(message: Message, url: str):
    try:
        r = requests.get(url)
        data = r.json()

        if data.get("cod") != 200:
            await message.reply("❌ Город не найден.")
            return

        city_raw = data["name"]
        city_in_case = get_city_prepositional(city_raw)

        temp = data["main"]["temp"]
        temp_whole = round(temp)
        temp_decimal = round(temp, 1)

        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        weather_main = data["weather"][0]["main"]
        wd = code_to_smile.get(weather_main, "🏙")

        await message.reply(
            f"📍 Погода в {city_in_case}:\n"
            f"🌡 Температура: {temp_decimal}°C\n"
            f"☁️ На улице: {wd}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} м/с",
            reply_markup=main_keyboard(message.from_user.id)
        )

    except Exception as e:
        await message.reply("⚠️ Ошибка при получении данных.")


async def main():
    print("Бот запущен. Теперь он умеет запоминать города!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
