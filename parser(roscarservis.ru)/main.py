"""Parsing the tire info on roscarservis.ru"""

import sys
import json
from time import time, sleep, strftime
from random import randrange
import requests


URL = "https://roscarservis.ru/catalog/legkovye/?sort%5Bprice%5D=asc&" \
      "sort%5Brecommends%5D=desc&form_id=catalog_filter_form&" \
      "filter_mode=params&filter_type=tires&set_filter=Y"

headers = {
    'X-Is-Ajax-Request': "X-Is-Ajax-Request",
    'X-Requested-With': "XMLHttpRequest",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101"
                  "Firefox/97.0",
}


def parse(url):
    result = []
    with requests.Session() as session:
        sys.stdout.write("Progress ")

        i = 0
        page_count = dots = 30# the progress dots count
        while True:
            if not i % (page_count // dots):
                sys.stdout.write('.')
                sys.stdout.flush()

            sleep(randrange(1))
            req = session.get(url + f"&PAGEN_1={i}", headers=headers)

            for item in req.json()['items']:
                stores = []
                try:
                    # there are three types of the stores.
                    for store_type in ['discountStores', 'fortochkiStores',
                                       'commonStores']:
                        for store in item[store_type]:
                            stores.append({
                                'name': store['STORE_NAME'],
                                'price': store['PRICE'],
                                'amount': store['AMOUNT']
                            })
                except TypeError:
                    pass
                finally:
                    item_dict = {
                        'date': strftime("%Y-%m-%d %H:%M:%S"),
                        'name': item['name'],
                        'img': item['imgSrc'],
                        'link': item['url'],
                        'stores': stores
                    }

                result.append(item_dict)

            # constant number of pages for all requests
            page_count = req.json()['pageCount']
            if i >= page_count:
                sys.stdout.write("Ok")
                break

            i += 1
        sys.stdout.write("\n")

    with open("result.json", 'w') as file:
        json.dump(result, file, indent=4)
        print("JSON saved")


if __name__ == "__main__":
    print("Parsing...")
    tic = time()
    parse(URL)
    print(f"Completed. Elapsed time: {(time() - tic):.2f}")
# Completed. Elapsed time: 1832.61
