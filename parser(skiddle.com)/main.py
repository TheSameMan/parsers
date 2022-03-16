"""Parsing data on festivals on the skiddle.com and exporting to json"""


from time import sleep
import json
from random import randrange
import requests
from bs4 import BeautifulSoup


headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101"
                  "Firefox/97.0"
}

all_festivals = []
# infinite cycle on site with dynamic page loading
offset = 0 # pagination
while True:
    url = f"https://www.skiddle.com/festivals/search/?ajaxing=1&sort=0&" \
          f"fest_name=&from_date=&to_date=&maxprice=500&o={offset}&" \
          f"bannertitle=April"

    req = requests.get(url, headers=headers)
    sleep(randrange(1, 3))
    req_json = json.loads(req.text)

    # all festivals are shown
    if "No festivals found" in req_json['html']:
        break

    print(f"offset: {offset}, status: {req.status_code}")
    # searching for festival cards on the page
    soup = BeautifulSoup(req_json['html'], "lxml")
    festivals = soup(class_="card flex-height lvl-1 brt-5px bg-white " \
                     "relative has-details")

    festival_data = {}
    for fail_index, festival in enumerate(festivals):
        href = "https://www.skiddle.com" + festival.a['href']

        fest_req = requests.get(href, headers=headers)
        sleep(randrange(1, 3))

        try:
            # searching for the festival primary info
            fest_soup = BeautifulSoup(fest_req.text, "lxml")
            fest = fest_soup.find(class_="top-info-cont span span9 no-clear")

            festival_data['Festival Name'] = fest.h1.string
            festival_data['Date'] = fest.h3.contents[1].string.strip()
            festival_data['Location'] = fest(class_="p-13pt")[1].text.strip()

            festival_data['Link'] = "https://www.skiddle.com" + \
                                    fest(class_="p-13pt")[1].a['href']

            info_req = requests.get(festival_data['Link'], headers=headers)
            sleep(randrange(1, 3))

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

    offset += 24 # per pagination

with open("festivals.json", 'w', encoding="utf-8") as file:
    json.dump(all_festivals, file, indent=4, ensure_ascii=False)
