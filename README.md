# tradedata

Downloads stock data by using two different api url, and saves csv files for intraday trading and for creating a long term base data.

There is not a web-scraping process. Every data is text based.

You need to install playwright and cf_clearance for python, to be able to download long-term base data.

I'm using it for Borsa Istanbul/Turkiye stock data. Turkiye / Istanbul city is in GMT +3 zone. Market opening time is 09:45, closing time is 18:00, 5/7 days a week. Any intraday data outside of this time window is non-sense and eliminated.

You need to install and have a running socks5 proxy in your system for cf_clearance library, look at decleration:
proxies = {
    "http": "socks5://localhost:9050",
    "https": "socks5://localhost:9050"
}

I installed tor socks5 proxy to be able to use cf_clearance library. read cf_clearance docs for further information about usage.

You need to find an api link, which is unprotected by cloudflare for intraday/temporary stock data. Look at and replace with a suitable one at line 85 in: download_instrument_api() sub-routine.

You may need to click a cloudflare confirmation box, once a day, to be able to download base data with playwright browser. If you know an unprotected api url you can share with me :) by dm
