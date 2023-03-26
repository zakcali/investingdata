# tradedata V0.83 by Zafer Akçalı

from time import gmtime, strftime
from playwright.sync_api import sync_playwright  # pip install pytest-playwright, playwright install
from cf_clearance import sync_cf_retry, sync_stealth  # pip install cf-clearance, pip install --upgrade cf-clearance
import datetime as dt
import csv
import json
import os
import requests

EXTENSION = '.csv'
ENCODING = 'utf-8-sig'
SEPERATOR = ','
FIELDS = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Date', 'Hour']
GMT_ZONE = 3
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * SECONDS_PER_MINUTE  # 3,6000 seconds per hour
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24
SECONDS_PER_WEEK = SECONDS_PER_DAY * 7
SECONDS_PER_MONTH = SECONDS_PER_DAY * 31
TIME_WINDOW_15M = 15 * SECONDS_PER_MINUTE * 3 * 600  # market is open for 8 hours
TIME_WINDOW_30M = 30 * SECONDS_PER_MINUTE * 3 * 600  # market is open for 8 hours
TIME_WINDOW_1H = SECONDS_PER_HOUR * 3 * 600  # market is open for 8 hours
TIME_WINDOW_2H = 2 * SECONDS_PER_HOUR * 3 * 600  # market is open for 8 hours
TIME_WINDOW_4H = 4 * SECONDS_PER_HOUR * 3 * 600  # market is open for 8 hours
TIME_WINDOW_D = SECONDS_PER_DAY * 600  # stock is open 5 days a week
TIME_WINDOW_W = SECONDS_PER_WEEK * 450
TIME_WINDOW_M = SECONDS_PER_MONTH * 500

TIME_SHIFT = GMT_ZONE * SECONDS_PER_HOUR
INSTRUMENTS_FILE = 'instruments'
SYNCHRONISING_SYMBOL = 'XU100'
MARKET_OPENING = 9.75
MARKET_CLOSING = 18

tvc_time_windows = [{'folder': '15m', 'resolution': '15', 'seconds': TIME_WINDOW_15M},
                    {'folder': '30m', 'resolution': '30', 'seconds': TIME_WINDOW_30M},
                    {'folder': '1h', 'resolution': '60', 'seconds': TIME_WINDOW_4H},
                    {'folder': '1D', 'resolution': 'D', 'seconds': TIME_WINDOW_D},
                    {'folder': '1W', 'resolution': 'W', 'seconds': TIME_WINDOW_W},
                    {'folder': '1M', 'resolution': 'M', 'seconds': TIME_WINDOW_M}]
# folder, intervals
# api_time_windows = [{'folder': '15m', 'interval': 'PT15M'}, {'folder': '1h', 'interval': 'PT1H'}, {'folder': '1D', 'interval': 'P1D'}, {'folder': '1W', 'interval': 'P1W'}, {'folder': '1M', 'interval': 'P1M'}]
api_time_windows = [{'folder': '15m', 'interval': 'PT15M'}]  # it is enough for intraday trading

folder_name = '15m'
instrument_data = ''
previous_midnight = ''
todays_ts = 0  # timestamp
market_opening_ts = 0  # timestamp
market_closing_ts = 0  # timestamp

proxies = {
    "http": "socks5://localhost:9050",
    "https": "socks5://localhost:9050"
}


def download_instruments_dict():
    input_file = open(INSTRUMENTS_FILE + EXTENSION, newline='', encoding=ENCODING)
    reader_obj = csv.DictReader(input_file, delimiter=SEPERATOR)
    instruments_dict = list(reader_obj)
    input_file.close()
    return instruments_dict


def download_instrument_tvc(page, inst_id, resolution, time_window):
    url = f"https://tvc6.investing.com/c7d22e09620934c384d0e3fea3e8ccdf/1679144285/1/1/8/history?symbol={inst_id}&resolution={resolution}&from={market_closing_ts - time_window}&to={market_closing_ts}"
    sync_stealth(page, pure=True)
    page.goto(url)
    if 'Just a moment...' in page.title():
        res = sync_cf_retry(page)
        if res is None:
            print("cf challenge fail")
            return None
        elif 'Just a moment...' in page.title():
            print("second cf challenge fail")
            return None
    downloaded_text = page.content().replace('<html><head></head><body>', '').replace('</body></html>', '')
    return json.loads(downloaded_text)  # dict


def download_instrument_api(inst_id, interval, pointscount):
    url = f"https://api.investing.com/api/financialdata/{inst_id}/historical/chart/?interval={interval}&pointscount={pointscount}"
    response = requests.get(url)
    return response.json()  # dict


def create_temp_csv(symbol, folder, data_dict, always_open):
    os.makedirs(folder + '-temp', exist_ok=True)
    csv_filename = symbol + '-' + folder + EXTENSION
    with open(os.path.join(folder + '-temp', csv_filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for item in data_dict["data"]:
            zone_time = int(item[0]) // 1000 + TIME_SHIFT  # avoid .0 for timestamp
            e = gmtime(zone_time)
            instrument_date = strftime("%Y-%m-%d", e)
            instrument_hour = strftime("%H:%M", e)
            if (folder == "30m") and (instrument_hour == "09:30") and (
                    always_open == 'N'):  # pseudo time clock is 09:30 or 10:00 in borsa istanbul
                continue
            if (folder == "1h") and (instrument_hour == "09:00") and (
                    always_open == 'N'):  # pseudo time clock is 09:30 or 10:00 in borsa istanbul
                continue
            writer.writerow([zone_time, item[1], item[2], item[3], item[4], item[5], instrument_date, instrument_hour])
        f.close()
    return


def create_base_csv(symbol, folder, data_dict, always_open):
    os.makedirs(folder, exist_ok=True)
    csv_filename = symbol + '-' + folder + EXTENSION
    output_file = open(os.path.join(folder, csv_filename), 'w', newline='', encoding='utf-8')
    writer_obj = csv.DictWriter(output_file, FIELDS, delimiter=SEPERATOR)
    writer_obj.writeheader()
    length = len(data_dict["t"])
    for i in range(length):
        zone_time = int(data_dict["t"][i]) + TIME_SHIFT
        e = gmtime(zone_time)
        instrument_date = strftime("%Y-%m-%d", e)
        instrument_hour = strftime("%H:%M", e)
        if (folder == "30m") and (instrument_hour == "09:30") and (
                always_open == 'N'):  # pseudo time clock is 09:30 or 10:00 in borsa istanbul
            continue
        if (folder == "1h") and (instrument_hour == "09:00") and (
                always_open == 'N'):  # pseudo time clock is 09:30 or 10:00 in borsa istanbul
            continue
        row_dict = {'Timestamp': zone_time,
                    'Open': data_dict["o"][i], 'High': data_dict["h"][i], 'Low': data_dict["l"][i],
                    'Close': data_dict["c"][i], 'Volume': data_dict["v"][i],
                    'Date': instrument_date,
                    'Hour': instrument_hour}  # add new row
        writer_obj.writerow(row_dict)

    output_file.close()
    return


def download_with_tvc(stocks):
    with sync_playwright() as p:
        current_browser = p.chromium.launch(headless=False, proxy={"server": "socks5://localhost:9050"})
        current_page = current_browser.new_page()
        for elem in tvc_time_windows:
            for row in stocks:
                instrument_dict = download_instrument_tvc(current_page, row["id"], elem['resolution'],
                                                          elem['seconds'])  # res, seconds
                if instrument_dict:
                    create_base_csv(row["symbol"], elem['folder'], instrument_dict,
                                    row["24h"])  # elem[1] is folder_name
        current_browser.close()
    return


def download_with_api(stocks):
    for elem in api_time_windows:
        print(elem)
        for row in stocks:
            instrument_dict = download_instrument_api(row["id"], elem['interval'], 120)  # pointscount
            if instrument_dict:
                create_temp_csv(row["symbol"], elem['folder'], instrument_dict, row["24h"])
    return


def set_todays_timestamps():
    global previous_midnight, todays_ts, market_opening_ts, market_closing_ts
    now = dt.datetime.now()
    midnight = dt.datetime(now.year, now.month, now.day)
    todays_ts = int(midnight.timestamp()) + TIME_SHIFT  # global
    previous_midnight = str(midnight)[:-3]  # global, remove seconds from the string
    market_opening_ts = todays_ts + int(SECONDS_PER_HOUR * MARKET_OPENING)  # 09:45
    market_closing_ts = todays_ts + int(SECONDS_PER_HOUR * MARKET_CLOSING)  # 18:00
    return


def starting_point():
    instruments = download_instruments_dict()
    download_with_tvc(instruments)  # for permanent database
    download_with_api(instruments)  # for intraday trading
    return


set_todays_timestamps()
# print(previous_midnight)
# print(todays_ts)
# print(market_opening_ts)
# print(market_closing_ts)
starting_point()
