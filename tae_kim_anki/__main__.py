import csv
import requests
from bs4 import BeautifulSoup


OUTPUT_FILENAME = "out.csv"


def write_csv_file(rows: list[list[str]]) -> None:
    with open(OUTPUT_FILENAME, "w", newline="") as csvfile:
        writer = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        for row in rows:
            writer.writerow(row)


def parse_webpage():
    web_url = "https://www.geeksforgeeks.org/"
    html = requests.get(web_url).content
    soup = BeautifulSoup(html, "html.parser")
    print(soup)


def main():
    parse_webpage()

    # write_csv_file([["a", "b", "c"], ["1", "2", "3"]])


if __name__ == "__main__":
    main()
