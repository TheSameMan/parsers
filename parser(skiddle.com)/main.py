"""Parsing data on festivals on the skiddle.com and exporting to json"""


from time import sleep, time
import json
from random import randrange
import requests
from bs4 import BeautifulSoup


URL = "https://www.skiddle.com/festivals/search/?ajaxing=1&sort=0&" \
      "fest_name=&from_date=&to_date=&maxprice=500&o={}&" \
      "bannertitle=April"

OFFSET = 24

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101"
                  "Firefox/97.0"
}

all_festivals = []

def main():
    print("Start synchronous session...")

    # infinite cycle on site with dynamic page loading
    step = 0 # pagination
    while True:
        sleep(randrange(1, 3))
        req = requests.get(URL.format(step * OFFSET), headers=headers)
        req_json = json.loads(req.text)

        # all festivals are shown
        if "No festivals found" in req_json['html']:
            print(f"Pages: {step}, Festivals found: {step * OFFSET}")
            break

        # searching for festival cards on the page
        soup = BeautifulSoup(req_json['html'], "lxml")
        festivals = soup(class_="card flex-height lvl-1 brt-5px bg-white " \
                         "relative has-details")

        festival_data = {}
        for festival in festivals:
            href = "https://www.skiddle.com" + festival.a['href']

            sleep(randrange(1, 3))
            fest_req = requests.get(href, headers=headers)
            print(f"Request: {festival.a['href']}")

            try:
                # searching for the festival primary info
                fest_soup = BeautifulSoup(fest_req.text, "lxml")
                fest = fest_soup.find(
                                    class_="top-info-cont span span9 no-clear")

                festival_data['Festival Name'] = fest.h1.string
                festival_data['Date'] = fest.h3.contents[1].string.strip()
                festival_data['Location'] = \
                                    fest(class_="p-13pt")[1].text.strip()
                festival_data['Link'] = "https://www.skiddle.com" + \
                                        fest(class_="p-13pt")[1].a['href']

                sleep(randrange(1, 3))
                info_req = requests.get(festival_data['Link'], headers=headers)

                # Parsing detailed info
                info_soup = BeautifulSoup(info_req.text, "lxml")
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

        step += 1 # per pagination

if __name__ == "__main__":
    tic = time()
    main()
    print(f"Completed. Elapsed time: {(time() - tic):.2f} s")

    with open("sync_festivals.json", 'w', encoding="utf-8") as file:
        json.dump(all_festivals, file, indent=4, ensure_ascii=False)
# Elapsed time: 1409.71 s