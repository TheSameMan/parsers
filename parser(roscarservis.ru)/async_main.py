"""Parsing the tires info on roscarservis.ru"""

import sys
import json
from time import time, sleep, strftime
from random import randrange
import asyncio
import requests
from aiohttp import ClientSession, DummyCookieJar
from fake_useragent import FakeUserAgent


URL = "https://roscarservis.ru/catalog/legkovye/?sort%5Bprice%5D=asc&" \
      "sort%5Brecommends%5D=desc&form_id=catalog_filter_form&" \
      "filter_mode=params&filter_type=tires&set_filter=Y"

agent = FakeUserAgent().google

headers = {
    'X-Is-Ajax-Request': "X-Is-Ajax-Request",
    'X-Requested-With': "XMLHttpRequest",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    'User-Agent': agent
}

counter = 0

async def get(url, session):

    global counter

    await asyncio.sleep(randrange(10))
    req = await session.get(url)
    req_json = await req.json(content_type=None)

    result = []
    for item in req_json['items']:
        stores = []
        try:
            for store_type in ['discountStores', 'fortochkiStores',
                               'commonStores']:
                for store in item[store_type]:
                    stores.append({
                        'name': store["STORE_NAME"],
                        'price': store["PRICE"],
                        'amount': store["AMOUNT"]
                    })
        except TypeError:
            pass
        finally:
            item_dict = {
                'date': strftime('%Y-%m-%d %H:%M:%S'),
                'name': item['name'],
                'img': item['imgSrc'],
                'link': item['url'],
                'stores': stores
            }

        result.append(item_dict)

    counter -= 1
    if not counter % 20:
        sys.stdout.write('.')
        sys.stdout.flush()

    return result

async def parse():
    sys.stdout.write("Progress ")

    req = requests.get(URL, headers=headers)
    sleep(1)

    page_count = json.loads(req.text)['pageCount']

    global counter
    counter = page_count

    jar = DummyCookieJar()
    async with ClientSession(cookie_jar=jar, headers=headers) as session:
        tasks = [asyncio.create_task(get(URL + f"&PAGEN_1={i}", session))
                 for i in range(page_count)]
        await asyncio.gather(*tasks)

    sys.stdout.write("Ok\n")
    return tasks

if __name__ == "__main__":
    print("Parsing...")
    tic = time()
    completed_tasks = asyncio.run(parse())

    results = []
    for task in completed_tasks:
        try:
            results.extend(task.result())
        except TypeError:
            continue

    with open("result.json", 'w') as file:
        json.dump(results, file, indent=4)
        print("JSON saved")

    print(f"Completed. Elapsed time: {(time() - tic):.2f}")
# Completed. Elapsed time: 185.34
