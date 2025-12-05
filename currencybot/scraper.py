import re
import aiohttp
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36"


async def fetch_html(url: str) -> str:
    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


# --- ЦБ РФ ---
CBR_URL = "https://www.cbr.ru/currency_base/daily/"


async def get_rate_ru(currency_code: str) -> tuple[str, str, str, str, str]:
    """
    currency_code: буквенный код валюты (например 'USD', 'EUR', 'JPY').
    Возвращает (курс, единиц, дата).
    """
    html = await fetch_html(CBR_URL)
    soup = BeautifulSoup(html, "lxml")

    parse_date = soup.find("div", class_="datepicker-filter").find(
        "button", class_="datepicker-filter_button"
    )
    parse = soup.find("tbody").find_all("tr")
    row_clear = []
    for row in parse:
        row = row.find_all("td")
        row_clear += [[r.get_text() for r in row]]
    for row in row_clear:
        try:
            if row[1] == currency_code:
                return (
                    row[1],  # currency_code
                    row[2],  # count
                    row[3],  # name
                    row[4],  # currency
                    parse_date.get_text(),  # date
                )
        except IndexError:
            continue


# --- НБ РБ ---
NBRB_URL = "https://www.nbrb.by/statistics/rates/ratesDaily.asp"


async def get_rate_by(currency_code: str):  # -> tuple[str, str]:
    html = await fetch_html(NBRB_URL)
    with open("by.html", "w", encoding="utf-8") as write:
        write.write(html)

    soup = BeautifulSoup(html, "lxml")

    parse_date = soup.find(id="curDate")
    parse = soup.find("tbody").find_all("tr")
    row_clear = []
    for row in parse:
        row = row.find_all("td")
        row_clear += [[r.get_text() for r in row]]
    for row in row_clear:
        try:
            row_split = row[1].split()
            if row_split[1] == currency_code:
                return (
                    row_split[1],
                    row_split[0],
                    row[0].replace("\n", ""),
                    row[2].replace("\n", ""),
                    parse_date.get_text(),
                )

        except IndexError:
            continue
