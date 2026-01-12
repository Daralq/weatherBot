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

#Память бота
user_data = {}


def main_keyboard(user_id):
    buttons = [
        [KeyboardButton(text="Москва"), KeyboardButton(text="Санкт-Петербург")],
        [KeyboardButton(text="Узнать по геолокации 📍", request_location=True)]
    ]

    #кнопка сохраненого города (при существовании_)
    if user_id in user_data and user_data[user_id]:
        city = user_data[user_id]
        buttons.insert(0, [KeyboardButton(text=f"🏠 Мой город: {city}")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_city_prepositional(city_name):
    #если название пустое или None
    if not city_name:
        return "этом месте"

    words = str(city_name).split()
    inflected_words = []

    for word in words:
        parsed = morph.parse(word)[0]
        inflected = parsed.inflect({'loct'})

        if inflected:
            inflected_words.append(inflected.word.capitalize())
        else:
            #неудача склонения
            inflected_words.append(word.capitalize())

    return " ".join(inflected_words)


@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! Я метео-бот. Напиши город или отправь геолокацию.",
        reply_markup=main_keyboard(message.from_user.id)
    )


@dp.message(F.location)
async def weather_by_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=ru"

    r = requests.get(url)
    data = r.json()

    if data.get("cod") == 200:
        city_name = data.get("name")
        if city_name:
            user_data[message.from_user.id] = city_name
            await message.answer(f"📍Ваш город сохранен: {city_name}")
            #обработка данных
            await process_weather_data(message, data)
    else:
        await message.reply("Не удалось определить город по координатам.")


@dp.message(F.text)
async def weather_by_city(message: Message):
    city = message.text
    if city.startswith("🏠 Мой город: "):
        city = city.replace("🏠 Мой город: ", "")

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    r = requests.get(url)
    data = r.json()

    if data.get("cod") == 200:
        await process_weather_data(message, data)
    else:
        await message.reply("❌ Город не найден. Попробуйте другой.")


async def process_weather_data(message: Message, data: dict):
    try:
        #получение название города
        city_raw = data.get("name", "Неизвестно")
        city_in_case = get_city_prepositional(city_raw)

        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        await message.answer(
            f"📍 Погода в {city_in_case}:\n"
            f"🌡 Температура: {round(temp)}°C\n"
            f"☁️ На улице: {weather_desc.capitalize()}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} м/с",
            reply_markup=main_keyboard(message.from_user.id)
        )
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке данных погоды.")


async def main():
    print("Бот запущен и ошибки 'None' исправлены!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
