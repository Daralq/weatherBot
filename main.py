import asyncio
import requests
import datetime
import pymorphy3  # Библиотека для склонения
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message

#токен
TG_TOKEN = "8218519059:AAEsOMpFjmYsOwcKmrkhixzIfFXFydx8m2E"
OWM_API_KEY = "2e46c50587f4626dab51eba27fb1778b"

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
morph = pymorphy3.MorphAnalyzer()

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


# Функция для склонения города в предложный падеж (в ком? в чем?)
def get_city_prepositional(city_name):
    words = city_name.split()
    inflected_words = []

    for word in words:
        parsed = morph.parse(word)[0]
        #склонение
        inflected = parsed.inflect({'loct'})
        if inflected:
            inflected_words.append(inflected.word.capitalize())
        else:
            inflected_words.append(word.capitalize())

    return " ".join(inflected_words)


@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("Привет! Напиши название города, и я скажу погоду.")


@dp.message()
async def get_weather(message: Message):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={OWM_API_KEY}&units=metric&lang=ru"
        r = requests.get(url)
        data = r.json()

        if data.get("cod") != 200:
            await message.reply("❌ Город не найден.")
            return

        #API
        city_raw = data["name"]

        # Склоняем название города
        city_in_case = get_city_prepositional(city_raw)

        temp = data["main"]["temp"]
        temp_whole = round(temp)  # До целого
        temp_decimal = round(temp, 1)  # До десятых

        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        weather_main = data["weather"][0]["main"]
        wd = code_to_smile.get(weather_main, "🏙")

        await message.reply(
            f"📍 Погода в {city_in_case}:\n" 
            f"🌡 Температура: {temp_decimal}°C\n"
            f"☁️ На улице: {wd}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} м/с"
        )

    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠️ Ошибка при получении данных.")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
