import csv
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass


OUTPUT_FILENAME = "out.csv"
START_URL = "https://guidetojapanese.org/learn/grammar/stateofbeing"
IMPORT_HEADER = """#separator:,
#html:true
#columns:japanese,english,vocab,section,chapter,link
#deck:A Guide to Japanese Grammar by Tae Kim - Examples
"""


@dataclass
class Vocab:
    kanji: str
    explanation: str


@dataclass
class Example:
    """Corresponds to one anki card"""

    japanese: str
    english: str
    vocab: list[Vocab]
    section: str = ""
    chapter: str = ""
    link: str = ""

    def get_vocab(self) -> str:
        vocab = ""
        for v in self.vocab:
            vocab += f"{v.kanji}: {v.explanation}\n"
        return vocab

    def make_row(self) -> list[str]:
        return [
            self.japanese,
            self.english,
            self.get_vocab(),
            self.section,
            self.chapter,
            self.link,
        ]


def write_csv_file(rows: list[list[str]]) -> None:
    with open(OUTPUT_FILENAME, "w", newline="") as csvfile:
        csvfile.write(IMPORT_HEADER)
        writer = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        for row in rows:
            writer.writerow(row)


def create_example_from_section(example_section):
    """
    Example li structure
    <li><span class="popup" title="ともだち - friend">友達</span><em>じゃない</em>。<br/>
    """
    flattened_string = "".join([s for s in example_section.strings])
    [jp, en] = flattened_string.split("\n")
    vocab = []
    for vocab_element in example_section.find_all("span"):
        kanji = vocab_element.string
        explanation = vocab_element.get("title")
        vocab.append(Vocab(kanji=kanji, explanation=explanation))
    section = example_section.find_parent("h2")

    return Example(japanese=jp, english=en, vocab=vocab)


def parse_webpage(web_url):
    html = requests.get(web_url).content
    page = BeautifulSoup(html, "html.parser")

    examples = []
    chapter = page.find("h1").string

    # Find all headings for "Examples" sections
    sub_titles = page.find_all("h3")
    for sub_title in sub_titles:
        if sub_title.contents and sub_title.contents[0] == "Examples":
            section_name = sub_title.find_previous_sibling("h2").string
            # Create Example objects from each list item
            example_list = sub_title.find_next_sibling("ol")
            for example_section in example_list.find_all("li"):
                example = create_example_from_section(example_section)
                example.section = section_name
                example.chapter = chapter
                example.link = web_url
                examples.append(example)

    next_url = ""
    next_url_element = page.find("span", class_="series-nav-right").find("a")
    if next_url_element:
        next_url = next_url_element.get("href")

    return examples, next_url


def main():
    examples, next_url = parse_webpage(START_URL)

    rows = []
    for e in examples:
        rows.append(e.make_row())

    write_csv_file(rows)


if __name__ == "__main__":
    main()
