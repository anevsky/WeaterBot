# -*- coding: utf-8 -*-

import StringIO
import cStringIO
import json
import logging
import random
import urllib
import urllib2

from datetime import datetime
from random import randint

# html parser
import urlparse
from urllib2 import Request, urlopen, URLError
from bs4 import BeautifulSoup

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = ''

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

OPENWEATHERMAP_TOKEN = ''

# ================================
# Globals
# ================================

CACHE = {}

WEATHER_CACHE = {}

UPDATE_AFTER_TIME = 120

LIST_OF_COMMANDS = (
'\n/today - Today\'s Forecast'
'\n/tomorrow - Tomorrow\'s Forecast'
'\n/week - Weekly Forecast'
'\n/rate - Please rate me!'
'\n/settings - /celsius or /fahrenheit units system, forecast /language'
'\n/help - How can I help you?'
)

EUROPE_COUNTRY_CODES = [
'AL', 'AD', 'AM', 'AT', 'BY', 'BE', 'BA', 'BG', 'CH', 'CY', 'CZ', 'DE',
'DK', 'EE', 'ES', 'FO', 'FI', 'FR', 'GB', 'GE', 'GI', 'GR', 'HU', 'HR',
'IE', 'IS', 'IT', 'LT', 'LU', 'LV', 'MC', 'MK', 'MT', 'NO', 'NL', 'PL',
'PT', 'RO', 'RU', 'SE', 'SI', 'SK', 'SM', 'TR', 'UA', 'VA',
]

EUROZONE_COUNTRY_CODES = [
"AT", "BE", "CY", "EE", "FI", "FR", "DE", "GR", "IE", "IT", "LV", "LT",
"LU", "MT", "NL", "PT", "SK", "SI", "ES",
]

EMOJI_MAP = {
    "high voltage sign" : "\xE2\x9A\xA1".decode('utf-8'),
    "cloud" : "\xE2\x98\x81".decode('utf-8'),
    "closed umbrella" : "\xF0\x9F\x8C\x82".decode('utf-8'),
    "umbrella with rain drops" : "\xE2\x98\x94".decode('utf-8'),
    "snowflake" : "\xE2\x9D\x84".decode('utf-8'),
    "snowman without snow" : "\xE2\x9B\x84".decode('utf-8'),
    "black sun with rays" : "\xE2\x98\x80".decode('utf-8'),
    "sun behind cloud" : "\xE2\x9B\x85".decode('utf-8'),
    "sunrise" : "\xF0\x9F\x8C\x85".decode('utf-8'),
    "sunset over buildings" : "\xF0\x9F\x8C\x87".decode('utf-8'),
    "cityscape at dusk" : "\xF0\x9F\x8C\x86".decode('utf-8'),
    "sunrise over mountains" : "\xF0\x9F\x8C\x84".decode('utf-8'),
    "night with stars" : "\xF0\x9F\x8C\x83".decode('utf-8'),
    "balloon" : "\xF0\x9F\x8E\x88".decode('utf-8'),
    "water wave" : "\xF0\x9F\x8C\x8A".decode('utf-8'),
    "milky way" : "\xF0\x9F\x8C\x8C".decode('utf-8'),
    "bridge at night" : "\xF0\x9F\x8C\x89".decode('utf-8'),
    "splashing sweat symbol" : "\xF0\x9F\x92\xA6".decode('utf-8'),
    "droplet" : "\xF0\x9F\x92\xA7".decode('utf-8'),
    "ghost" : "\xF0\x9F\x91\xBB".decode('utf-8'),
    "foggy" :  "\xF0\x9F\x8C\x81".decode('utf-8'),
    "cyclone" : "\xF0\x9F\x8C\x80".decode('utf-8'),
    "wind chime" : "\xF0\x9F\x8E\x90".decode('utf-8'),
    "leaf fluttering in wind" : "\xF0\x9F\x8D\x83".decode('utf-8'),
    "alarm clock" : "\xE2\x8F\xB0".decode('utf-8'),
    "round pushpin" : "\xF0\x9F\x93\x8D".decode('utf-8'),
    "newspaper" : "\xF0\x9F\x93\xB0".decode('utf-8'),
    "bookmark" : "\xF0\x9F\x94\x96".decode('utf-8'),
    "crystal ball" : "\xF0\x9F\x94\xAE".decode('utf-8'),
    "japanese symbol for beginner" : "\xF0\x9F\x94\xB0".decode('utf-8'),
    "tractor" : "\xF0\x9F\x9A\x9C".decode('utf-8'),
    "bear face" : "\xF0\x9F\x90\xBB".decode('utf-8'),
    "wolf face" : "\xF0\x9F\x90\xBA".decode('utf-8'),
    "rabbit face" : "\xF0\x9F\x90\xB0".decode('utf-8'),
    "regional indicator symbol letter r + regional indicator symbol letter u" : "\xF0\x9F\x87\xB7\xF0\x9F\x87\xBA".decode('utf-8'),
    "earth globe europe-africa" : "\xF0\x9F\x8C\x8D".decode('utf-8'),
    "earth globe americas" : "\xF0\x9F\x8C\x8E".decode('utf-8'),
    "earth globe asia-australia" : "\xF0\x9F\x8C\x8F".decode('utf-8'),
    "european post office" : "\xF0\x9F\x8F\xA4".decode('utf-8'),
    "banknote with euro sign" : "\xF0\x9F\x92\xB6".decode('utf-8'),
    "japanese dolls" : "\xF0\x9F\x8E\x8E".decode('utf-8'),
    "White Sun With Small Cloud" : "🌤".decode('utf-8'),
    "White Sun Behind Cloud With Rain" : "🌦".decode('utf-8'),
    "Cloud With Rain" : "🌧".decode('utf-8'),
    "Cloud With Snow" : "🌨".decode('utf-8'),
    "Cloud With Lightning" : "🌩".decode('utf-8'),
    "Thunder Cloud and Rain" : "⛈".decode('utf-8'),
    "Cloud With Tornado" : "🌪".decode('utf-8'),
    "Fog" : "🌫".decode('utf-8'),
    "Wind Blowing Face" : "🌬".decode('utf-8'),
    "Snowman" : "☃".decode('utf-8'),
}

FORECAST_INCLUDE_MESSAGE = (
'Forecast include:'
+ "\n" + u"\u2109" + "/" + u"\u2103" + " - Temperature;"
+ "\n" + EMOJI_MAP["wind chime"] + " Wind speed. Unit Default: Metric: meter/sec, Imperial: miles/hour;"
+ "\n" + EMOJI_MAP["cloud"] + " Cloudiness, %;"
+ "\n" + EMOJI_MAP["droplet"] + " Humidity, %;"
+ "\n" + EMOJI_MAP["balloon"] + " Atmospheric pressure on the ground level, hPa;"
+ "\n" + EMOJI_MAP["splashing sweat symbol"] + " Rain volume for last 3 hours, mm;"
+ "\n" + EMOJI_MAP["snowflake"] + " Snow volume for last 3 hours, mm;"
)

TIME_EMOJI_MAP = {
    "03:00" : EMOJI_MAP["milky way"],
    "06:00" : EMOJI_MAP["ghost"],
    "09:00" : EMOJI_MAP["sunrise"],
    "12:00" : EMOJI_MAP["sunset over buildings"],
    "15:00" : EMOJI_MAP["cityscape at dusk"],
    "18:00" : EMOJI_MAP["sunrise over mountains"],
    "21:00" : EMOJI_MAP["bridge at night"],
    "00:00" : EMOJI_MAP["night with stars"],
}

EMOJI_WEATHER_MAP = {
    200 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["closed umbrella"], # thunderstorm with light rain
    201 : EMOJI_MAP["Thunder Cloud and Rain"] + EMOJI_MAP["umbrella with rain drops"], # thunderstorm with rain
    202 : EMOJI_MAP["Thunder Cloud and Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["Thunder Cloud and Rain"], # thunderstorm with heavy rain
    210 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["closed umbrella"], # light thunderstorm
    211 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["umbrella with rain drops"], # thunderstorm
    212 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["Cloud With Lightning"], # heavy thunderstorm
    221 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["closed umbrella"], # ragged thunderstorm
    230 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["closed umbrella"], # thunderstorm with light drizzle
    231 : EMOJI_MAP["Cloud With Lightning"] + EMOJI_MAP["umbrella with rain drops"], # thunderstorm with drizzle
    232 : EMOJI_MAP["Thunder Cloud and Rain"] + EMOJI_MAP["umbrella with rain drops"], # thunderstorm with heavy drizzle

    300 : EMOJI_MAP["White Sun Behind Cloud With Rain"] + EMOJI_MAP["closed umbrella"], # light intensity drizzle
    301 : EMOJI_MAP["cloud"] + EMOJI_MAP["closed umbrella"], # drizzle
    302 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # heavy intensity drizzle
    310 : EMOJI_MAP["cloud"] + EMOJI_MAP["closed umbrella"], # light intensity drizzle rain
    311 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["closed umbrella"] + EMOJI_MAP["umbrella with rain drops"], # drizzle rain
    312 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["umbrella with rain drops"], # heavy intensity drizzle rain
    313 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # shower rain and drizzle
    314 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["Cloud With Rain"], # heavy shower rain and drizzle
    321 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["Cloud With Rain"], # shower drizzle

    500 : EMOJI_MAP["closed umbrella"], # light rain
    501 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # moderate rain
    502 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["Cloud With Rain"], # heavy intensity rain
    503 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # very heavy rain
    504 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # extreme rain
    511 : EMOJI_MAP["snowflake"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["snowman without snow"], # freezing rain
    520 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["closed umbrella"], # light intensity shower rain
    521 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"], # shower rain
    522 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["umbrella with rain drops"], # heavy intensity shower rain
    531 : EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["Cloud With Rain"] + EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["cloud"], # ragged shower rain

    600 : EMOJI_MAP["snowflake"], # light snow
    601 : EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["snowflake"], # snow
    602 : EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["snowflake"] + EMOJI_MAP["Cloud With Snow"], # heavy snow
    611 : EMOJI_MAP["snowflake"] + EMOJI_MAP["umbrella with rain drops"], # sleet
    612 : EMOJI_MAP["snowflake"] + EMOJI_MAP["umbrella with rain drops"], # shower sleet
    615 : EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["snowflake"], # light rain and snow
    616 : EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["snowflake"], # rain and snow
    620 : EMOJI_MAP["umbrella with rain drops"] + EMOJI_MAP["snowflake"] + EMOJI_MAP["snowman without snow"], # light shower snow
    621 : EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["snowflake"] + EMOJI_MAP["Snowman"], # shower snow
    622 : EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["Cloud With Snow"] + EMOJI_MAP["snowflake"] + EMOJI_MAP["Snowman"] + EMOJI_MAP["Snowman"], # heavy shower snow

    741 : EMOJI_MAP["Fog"] + EMOJI_MAP["foggy"], # fog

    800 : EMOJI_MAP["black sun with rays"], # clear sky
    801 : EMOJI_MAP["White Sun With Small Cloud"], # few clouds
    802 : EMOJI_MAP["sun behind cloud"], # scattered clouds
    803 : EMOJI_MAP["cloud"] + EMOJI_MAP["cloud"], # broken clouds
    804 : EMOJI_MAP["cloud"] + EMOJI_MAP["cloud"] + EMOJI_MAP["cloud"], # overcast clouds
}

# ================================
# Main class
# ================================

LAST_UPDATE_TIME = datetime.now()
def updateLastRefreshTime():
    global LAST_UPDATE_TIME
    try:
        LAST_UPDATE_TIME = datetime.now()
    except Exception as e:
        logging.error("updateLastRefreshTime")
        logging.error(e)

def clearWeatherCache():
    WEATHER_CACHE.clear()
    updateLastRefreshTime()

def clearWeatherCacheIfNeeded():
    now = datetime.now()
    diff = now - LAST_UPDATE_TIME
    if (diff.total_seconds() / 60 > UPDATE_AFTER_TIME):
        clearWeatherCache()

def getForecast(chat_id):
    try:
        units = 'metric'
        if "units" in CACHE[chat_id]:
            units = CACHE[chat_id]["units"]
        else:
            CACHE[chat_id]["units"] = units

        lang = 'en'
        if "lang" in CACHE[chat_id]:
            lang = CACHE[chat_id]["lang"]
        else:
            CACHE[chat_id]["lang"] = lang

        query = ('http://api.openweathermap.org/data/2.5/forecast?'
        + 'lat=' + CACHE[chat_id]['latitude'] +
        '&lon=' + CACHE[chat_id]['longitude'] +
        '&units=' + CACHE[chat_id]['units'] +
        '&lang=' + CACHE[chat_id]['lang'] +
        '&APPID='
        )

        logging.info(query)

        contents = json.load(urllib2.urlopen(query, timeout = 5))

        return contents
    except Exception as e:
        logging.error("getForecast")
        logging.error(e)

def makeForecastInfo(chat_id):
    resultMap = {
        "status" : "Sorry, but I can not give your forecast now... Please try again a little bit later."
    }

    try:
        clearWeatherCacheIfNeeded()

        if chat_id in CACHE and 'city' in CACHE[chat_id] and 'country' in CACHE[chat_id]:
            city = CACHE[chat_id]['city']
            country = CACHE[chat_id]["country"]
            if city + ", " + country in WEATHER_CACHE:
                forecastMap = WEATHER_CACHE[city + ", " + country]
            else:
                forecastMap = getForecast(chat_id)
        else:
            forecastMap = getForecast(chat_id)

        if not forecastMap:
            return resultMap

        city = forecastMap['city']['name']
        country = forecastMap['city']['country']

        WEATHER_CACHE[city + ", " + country] = forecastMap

        day = forecastMap['list'][0]['dt_txt'].split()[0]

        resultMap["city"] = city
        resultMap["country"] = country

        CACHE[chat_id]["city"] = city
        CACHE[chat_id]["country"] = country

        if country == "BY":
            resultMap["countryEmoji"] = EMOJI_MAP["tractor"] + " " + EMOJI_MAP["rabbit face"]
        elif country == "RU":
            resultMap["countryEmoji"] = EMOJI_MAP["regional indicator symbol letter r + regional indicator symbol letter u"]
            + EMOJI_MAP["bear face"] + " " + EMOJI_MAP["wolf face"]
        elif country == "US" or country == "CA":
            resultMap["countryEmoji"] = EMOJI_MAP["earth globe americas"]
        elif country == "JP":
            resultMap["countryEmoji"] = EMOJI_MAP["japanese dolls"]
        elif country in EUROZONE_COUNTRY_CODES:
                resultMap["countryEmoji"] = EMOJI_MAP["earth globe europe-africa"] + " " + EMOJI_MAP["banknote with euro sign"]
        elif country in EUROPE_COUNTRY_CODES:
            resultMap["countryEmoji"] = EMOJI_MAP["earth globe europe-africa"]
        else:
            resultMap["countryEmoji"] = EMOJI_MAP["earth globe americas"] + EMOJI_MAP["earth globe europe-africa"] + EMOJI_MAP["earth globe asia-australia"]

        forecast = ""
        count = 0
        lastKnownDay = forecastMap['list'][0]['dt_txt'].split()[0]
        interval = range(0, len(forecastMap['list']))
        for x in interval:
            temperature = forecastMap['list'][x]['main']['temp']
            temperatureMin = forecastMap['list'][x]['main']['temp_min']
            temperatureMax = forecastMap['list'][x]['main']['temp_max']
            humidity = forecastMap['list'][x]['main']['humidity']
            pressure = forecastMap['list'][x]['main']['grnd_level']
            windSpeed = forecastMap['list'][x]['wind']['speed']
            clouds = forecastMap['list'][x]['clouds']['all']
            weatherId = forecastMap['list'][x]['weather'][0]['id']
            description = forecastMap['list'][x]['weather'][0]['description']
            time = forecastMap['list'][x]['dt_txt']

            rain = 0
            if 'rain' in forecastMap['list'][x] and '3h' in forecastMap['list'][x]['rain']:
                rain = forecastMap['list'][x]['rain']['3h']

            snow = 0
            if 'snow' in forecastMap['list'][x] and '3h' in forecastMap['list'][x]['snow']:
                snow = forecastMap['list'][x]['snow']['3h']

            day = time.split()[0]
            hour =  time.split()[1].split(':')[0] + ':' + time.split()[1].split(':')[1]

            if lastKnownDay != day:
                count += 1
                resultMap[count] = (
                EMOJI_MAP["crystal ball"] + " " + EMOJI_MAP["crystal ball"]
                + " " + lastKnownDay
                + " " + EMOJI_MAP["crystal ball"] + " " + EMOJI_MAP["crystal ball"]
                + '\n\n'
                + forecast
                )
                forecast = ""

            lastKnownDay = day

            if x > 8 and hour in ["03:00", "09:00", "15:00", "21:00"]:
                continue

            weatherInfo = description
            if weatherId in EMOJI_WEATHER_MAP:
                weatherInfo = EMOJI_WEATHER_MAP[weatherId] + " " + weatherInfo

            if CACHE[chat_id]["units"] == "imperial":
                windSpeedDescription = "miles/hour"
                temperatureDescriptor = u"\u2109"
            else:
                windSpeedDescription = "m/sec"
                temperatureDescriptor = u"\u2103"

            if int(round(temperatureMin)) == int(round(temperatureMax)):
                temperatureDegree = (
                ('+' if temperature > 0 else '')
                + str(int(round(temperature)))
                )
            else:
                temperatureDegree = (
                ('+' if temperatureMin > 0 else '')
                + str(int(round(temperatureMin)))
                + '...'
                + ('+' if temperatureMax > 0 else '')
                + str(int(round(temperatureMax)))
                )

            after = (TIME_EMOJI_MAP[hour] + " " + hour +  '\n'
                + temperatureDegree
                + temperatureDescriptor
                + ", " + weatherInfo
                + '.\n'
                + EMOJI_MAP["wind chime"] + str(windSpeed) + " " + windSpeedDescription + ", "
                + EMOJI_MAP["cloud"] + str(clouds) + "%, "
                + EMOJI_MAP["droplet"] + str(humidity) + "%, "
                + EMOJI_MAP["balloon"] + str(int(pressure)) + " hPa" + (", " if rain > 0 or snow > 0 else '.')
                + ((EMOJI_MAP["splashing sweat symbol"] + str(rain) + " mm" + (", " if snow > 0 else '.')) if rain > 0 else "")
                + ((EMOJI_MAP["snowflake"] + str(snow) + " mm.") if snow > 0 else "")
            )
            after += "\n\n"
            forecast += after

        # collect last time info
        count += 1
        resultMap[count] = forecast

        resultMap["status"] = "OK"
    except Exception as e:
        logging.error("makeForecastInfo")
        logging.error(e)

    return resultMap

class WebhookHandler(webapp2.RequestHandler):

    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        geo = message.get('location')
        if geo:
            longitude = geo['longitude']
            latitude = geo['latitude']

            CACHE[chat_id] = {'longitude' : str(longitude), 'latitude' : str(latitude)}
            text = '/today'

        if not text:
            logging.info('no text')
            return

        def chatAction():
            try:
                resp = urllib2.urlopen(BASE_URL + 'sendChatAction', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'action': "typing",
                }))
                contents = resp.read()
            except urllib2.HTTPError, error:
                logging.warn(error)

        def reply(msg=None, img=None):
            if msg:
                try:
                    chatAction()

                    keys = [
                        ['/rate \xE2\x98\x94 \xF0\x9F\x8C\x85 \xE2\x9B\x84'],
                        ['/week', '/today', '/tomorrow'],
                    ]

                    reply_markup = json.dumps({'keyboard': keys,
                        'resize_keyboard': True,
                        'one_time_keyboard': False,
                        'selective': True,
                    })

                    resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id': str(chat_id),
                        'text': msg.encode('utf-8'),
                        'disable_web_page_preview': 'false',
                        'reply_markup': reply_markup,
                    }))
                    contents = resp.read()

                    logging.info('send response:')
                    logging.info(contents)
                except urllib2.HTTPError, error:
                    logging.error("reply")
                    logging.error(error)
            elif img:
                try:
                    resp = multipart.post_multipart(BASE_URL + 'sendPhoto',
                        [('chat_id', str(chat_id)),],
                        [('photo', 'image.jpg', img),
                    ])

                    logging.info('send response:')
                    logging.info(resp)
                except urllib2.HTTPError, error:
                    contents = error.read()
                    logging.error('when send image:')
                    logging.error(contents)
            else:
                logging.error('no msg or img specified')
                resp = None

        if not chat_id in CACHE:
            reply('https://weathergirlbot.appspot.com/static/storm-2.jpg')
            reply('Please send me your Location and after that we can start...')
            return

        if text.startswith('/'):
            if text == '/start':
                setEnabled(chat_id, True)
                reply('https://weathergirlbot.appspot.com/static/storm-9.jpg')

                message = ('Hi! Nice to meet you ;)'
                +'\n\nMy name is Ororo Munroe (also known as X-Man Storm) and I can give you a wether forecast, just send me your Location ;)'
                +'\n\n'
                + FORECAST_INCLUDE_MESSAGE
                + '\n\nPlease do not forget to /rate me at https://telegram.me/storebot?start=weathergirlbot.'
                + '\n\nYou can directly ask me for the following:'
                + LIST_OF_COMMANDS
                + '\n\nThanks!'
                )

                reply(message)
            elif text == '/stop':
                setEnabled(chat_id, False)
                reply('I would miss you...')
                reply('https://weathergirlbot.appspot.com/static/storm-6.jpg')
            elif text == '/today':
                forecastInfo = makeForecastInfo(chat_id)
                if forecastInfo["status"] == "OK":
                    message = EMOJI_MAP["japanese symbol for beginner"] + " " + forecastInfo["city"] + ", " + forecastInfo["country"]
                    if "countryEmoji" in forecastInfo:
                        message += " " + forecastInfo["countryEmoji"]
                    message += "\n\n" + forecastInfo[1]
                    reply(message)
                else:
                    reply(forecastInfo["status"])
            elif text == '/tomorrow':
                forecastInfo = makeForecastInfo(chat_id)
                if forecastInfo["status"] == "OK":
                    message = EMOJI_MAP["japanese symbol for beginner"] + " " + forecastInfo["city"] + ", " + forecastInfo["country"]
                    if "countryEmoji" in forecastInfo:
                        message += " " + forecastInfo["countryEmoji"]
                    message += "\n\n" + forecastInfo[2]
                    reply(message)
                else:
                    reply(forecastInfo["status"])
            elif text == '/week':
                forecastInfo = makeForecastInfo(chat_id)
                if forecastInfo["status"] == "OK":
                    message = EMOJI_MAP["japanese symbol for beginner"] + " " + forecastInfo["city"] + ", " + forecastInfo["country"]
                    if "countryEmoji" in forecastInfo:
                        message += " " + forecastInfo["countryEmoji"]
                    message += "\n\n" + forecastInfo[1]
                    message += forecastInfo[2]
                    message += forecastInfo[3]
                    message += forecastInfo[4]
                    message += forecastInfo[5]
                    reply(message)
                else:
                    reply(forecastInfo["status"])
            elif text == '/celsius':
                CACHE[chat_id]["units"] = "metric"
                reply("OK, metric system: celsius and meters.")
            elif text == '/fahrenheit':
                CACHE[chat_id]["units"] = "imperial"
                reply("OK, imperial system: fahrenheit and miles.")
            elif text == '/help':
                reply('https://weathergirlbot.appspot.com/static/storm-8.jpg')

                message = ('I can give you a wether forecast, just send me your Location ;)'
                +'\n\n'
                + FORECAST_INCLUDE_MESSAGE
                + '\n\nYou can directly ask me for the following:'
                + LIST_OF_COMMANDS
                +'\n\nPlease do not forget to rate me at https://telegram.me/storebot?start=weathergirlbot.'
                +'\n\nThanks!'
                )

                reply(message)
            elif text == '/settings':
                reply('https://weathergirlbot.appspot.com/static/storm-1.jpg')

                message = ("Metric and imperial units are available: /celsius and /fahrenheit."
                + "\n\nYou can also choose weather forecast /language."
                )

                reply(message)
            elif text == '/rate' or text == '/rate \xE2\x98\x94 \xF0\x9F\x8C\x85 \xE2\x9B\x84'.decode('utf-8'):
                reply('https://weathergirlbot.appspot.com/static/storm-10.jpg')
                reply('Please rate me!' + '\n' + 'https://telegram.me/storebot?start=weathergirlbot')
            elif text == '/language':
                reply('https://weathergirlbot.appspot.com/static/storm-4.jpg')

                message = ("Please choose one of the following weather forecast language:"
                + "\n- English - /lang_en"
                + "\n- Russian - /lang_ru"
                + "\n- Italian - /lang_it"
                + "\n- Spanish - /lang_es"
                + "\n- Ukrainian - /lang_ua"
                + "\n- German - /lang_de,"
                + "\n- Portuguese - /lang_pt"
                + "\n- Romanian - /lang_ro"
                + "\n- Polish - /lang_pl"
                + "\n- Finnish - /lang_fi"
                + "\n- Dutch - /lang_nl"
                + "\n- French - /lang_fr"
                + "\n- Bulgarian - /lang_bg"
                + "\n- Swedish - /lang_se"
                + "\n- Chinese Traditional - /lang_zh_tw"
                + "\n- Chinese Simplified - /lang_zh_cn"
                + "\n- Turkish - /lang_tr"
                + "\n- Croatian - /lang_hr"
                + "\n- Catalan - /lang_ca"
                )
                reply(message)
            elif text.startswith('/lang_'):
                if text == '/lang_en':
                    CACHE[chat_id]["lang"] = "en"
                elif text == '/lang_ru':
                    CACHE[chat_id]["lang"] = "ru"
                elif text == '/lang_it':
                    CACHE[chat_id]["lang"] = "it"
                elif text == '/lang_es':
                    CACHE[chat_id]["lang"] = "es"
                elif text == '/lang_ua':
                    CACHE[chat_id]["lang"] = "ua"
                elif text == '/lang_de':
                    CACHE[chat_id]["lang"] = "de"
                elif text == '/lang_pt':
                    CACHE[chat_id]["lang"] = "pt"
                elif text == '/lang_ro':
                    CACHE[chat_id]["lang"] = "ro"
                elif text == '/lang_pl':
                    CACHE[chat_id]["lang"] = "pl"
                elif text == '/lang_fi':
                    CACHE[chat_id]["lang"] = "fi"
                elif text == '/lang_nl':
                    CACHE[chat_id]["lang"] = "nl"
                elif text == '/lang_fr':
                    CACHE[chat_id]["lang"] = "fr"
                elif text == '/lang_bg':
                    CACHE[chat_id]["lang"] = "bg"
                elif text == '/lang_se':
                    CACHE[chat_id]["lang"] = "se"
                elif text == '/lang_zh_tw':
                    CACHE[chat_id]["lang"] = "zh_tw"
                elif text == '/lang_zh_cn':
                    CACHE[chat_id]["lang"] = "zh_cn"
                elif text == '/lang_tr':
                    CACHE[chat_id]["lang"] = "tr"
                elif text == '/lang_hr':
                    CACHE[chat_id]["lang"] = "hr"
                elif text == '/lang_ca':
                    CACHE[chat_id]["lang"] = "ca"

                message = "Thanks! Weather forecast language was updated!"
                reply(message)
            else:
                reply('What command?' + LIST_OF_COMMANDS)
        elif 'Who are you' in text:
            reply('I am your personal agent :)')
        elif 'What can you do' in text:
            reply('Just talk to me ;)')
        else:
            # MORE
            if getEnabled(chat_id):
                reply('Oh... I have no idea what is going on.')
            else:
                logging.info('not enabled for chat_id {}'.format(chat_id))

# ================================
# Helpers
# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# ================================

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
