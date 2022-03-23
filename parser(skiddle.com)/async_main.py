"""Asynchronous parsing data on festivals on the skiddle.com and
exporting to json"""


from time import sleep, time
from random import randrange
import json
import asyncio
import aiohttp
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


URL = "https://www.skiddle.com/festivals/search/?ajaxing=1&sort=0&" \
      "fest_name=&from_date=&to_date=&maxprice=500&o={}&" \
      "bannertitle=April" # constant template for requests

OFFSET = 24 # festivals on a page

headers = {
    'User-Agent': UserAgent()['google_chrome']
}

all_festivals = []

def festival_count(offset):
    print("Pagination counting...")
    step = 0 # pagination
    while True:
        sleep(1) # reduce the load
        req = requests.get(URL.format(step * offset), headers=headers)
        req_json = json.loads(req.text)

        # all festivals are shown
        if "No festivals found" in req_json['html']:
            print(f"Pages: {step}, Festivals found: {step * offset}")
            return step * offset

        step += 1 # per pagination

async def get_url(session, url):
    await asyncio.sleep(randrange(1, 3)) # reduce the load
    req = await session.get(url, headers=headers)
    text = await req.text()
    req_json = json.loads(text)

    soup = BeautifulSoup(req_json['html'], "lxml")
    festivals = soup(class_="card flex-height lvl-1 brt-5px bg-white " \
                     "relative has-details")

    festival_data = {}
    for festival in festivals:
        href = "https://www.skiddle.com" + festival.a['href']

        await asyncio.sleep(randrange(1, 3))
        fest_req = await session.get(href, headers=headers)
        fest_text = await fest_req.text()
        print(f"Request: {festival.a['href']}")

        try:
            fest_soup = BeautifulSoup(fest_text, "lxml")
            fest = fest_soup.find(class_="top-info-cont span span9 no-clear")

            festival_data['Festival Name'] = fest.h1.string
            festival_data['Date'] = fest.h3.contents[1].string.strip()
            festival_data['Location'] = fest(class_="p-13pt")[1].text.strip()
            festival_data['Link'] = "https://www.skiddle.com" + \
                                    fest(class_="p-13pt")[1].a['href']

            await asyncio.sleep(randrange(1, 3))
            info_req = await session.get(festival_data['Link'],
                                         headers=headers)
            info_text = await info_req.text()

            # Parsing detailed info
            info_soup = BeautifulSoup(info_text, "lxml")
            info = info_soup.find("h2",
                                  string="Venue contact details and info")
            info = info.find_next().find_all("p")

            # with processing of <a> tag
            for rec in info:
                if len(rec.contents) < 3:
                    festival_data[rec.span.string] = \
                                rec.contents[1].string.strip()
                else:
                    festival_data[rec.span.string] = \
                                rec.contents[2].text.strip()
        except AttributeError:
            pass

        all_festivals.append(festival_data)

    print("Task completed")

async def main():
    fests = festival_count(OFFSET)

    print("Start asynchronous session...")
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(get_url(session, URL.format(offset)))
                 for offset in range(0, fests, OFFSET)]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    tic = time()
    asyncio.run(main())
    print(f"Completed. Elapsed time: {(time() - tic):.2f} s")

    with open("async_festivals.json", 'w', encoding="utf-8") as file:
        json.dump(all_festivals, file, indent=4, ensure_ascii=False)
# Elapsed time: 128.79 s
