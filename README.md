# investingdata
downloads stock data with api and saves csv files for long term and intraday trading

you need to install and have running a tor proxy in your system, look at decleration:
proxies = {
    "http": "socks5://localhost:9050",
    "https": "socks5://localhost:9050"
}

you need to install playwright and cf_clearance for python

you need to find an api link, which is unprotected by cloudflare for intraday/temporary stock data. Look at and replace with a suitable one in: download_instrument_api() sub-routine 
