"""Parser for calorie table on health-diet.ru"""

import os
import re
import json
import csv
import requests
from bs4 import BeautifulSoup


# calorie table link
URL = "https://health-diet.ru/table_calorie/?utm_source=leftMenu&utm_medium=" \
        "table_calorie"

site_url = re.search(r"https:\/\/(?:[-\w]+\.)?([-\w]+)\.\w+(?:\.\w+)?", URL) \
            .group()

headers = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101"
                  "Firefox/97.0"
}

# download the main page if it's not in the directory
try:
    file = open("index.html",'x')
    # saving page for the next processing
    file.write(requests.get(URL, headers=headers).text)

except FileExistsError:
    pass

finally:
    # parse saved page
    file = open("index.html", 'r')
    soup = BeautifulSoup(file.read(), "lxml")

    file.close()

# create a json file with links on the main page or open an existing one
try:
    file = open("links.json", 'x')

    # search by links class
    group_links = soup.find_all(class_="uk-flex mzr-tc-group-item")

    links = {}
    for item in group_links:
        it = item.find('a')
        links[it["title"]] = site_url + it["href"]

    json.dump(links, file, indent=4, ensure_ascii=False)

except FileExistsError:
    pass

finally:
    file = open("links.json", 'r')
    categories = json.load(file)

    file.close()

# directory for pages and csv tables
try:
    os.mkdir("data")
except FileExistsError:
    pass

# parse all links on the main page
cleaned = {}
for title, href in categories.items():
    # remove the useless prefixes and symbols
    title = re.sub("Химический состав продукта: ", "", title)
    title = re.sub(r"[-,'()]", "", title)
    cleaned[title] = href

    current_page = f"data/{title}"
    current_table = current_page + ".csv"

    # download the current page if it's not in the directory
    try:
        file = open(current_page, 'x')
        file.write(requests.get(href, headers=headers).text)

    except FileExistsError:
        pass

    finally:
        file = open(current_page, 'r')
        soup = BeautifulSoup(file.read(), "lxml")
        file.close()

        # check content on the page
        alert = soup.find(class_="uk-alert uk-alert-danger uk-h1" \
                "uk-text-center mzr-block mzr-grid-3-column-margin-top")

        if not alert or (alert and alert.string !=
                         "Запрашиваемая страница не найдена!"):

            # save current table if it's not in the directory
            try:
                csv_file = open(current_table, 'x', encoding="utf-8")
                writer = csv.writer(csv_file, delimiter=' ')

                # find the table and columns
                table = soup.find(class_="uk-table")
                column_names = [col.string for col in
                                    table.find_all_next("th")]

                # write column names of the table
                writer.writerow(column_names)

                # find the table rows
                tr_rows = table.find("tbody").find_all("tr")

                for row in tr_rows:
                    td = row.find_all("td")
                    res = []
                    for t in td:
                        if a := t.find('a'): # extract from <a> tag
                            res.append(a.string)
                        else:
                            res.append(t.string)

                    # write table rows
                    writer.writerow(res)
                csv_file.close()
            except FileExistsError:
                pass
