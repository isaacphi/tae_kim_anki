import csv
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass


OUTPUT_FILENAME = "out.csv"
START_URL = "https://guidetojapanese.org/learn/grammar/stateofbeing"
IMPORT_HEADER = """#separator:,
#html:true
#columns:japanese,english,vocab,section,chapter,link,tags
#deck:A Guide to Japanese Grammar by Tae Kim - Examples
#tags column:7
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
    tags: str = ""

    def get_vocab(self) -> str:
        vocab = ""
        for v in self.vocab:
            vocab += f"{v.kanji}: {v.explanation}<br/>"
        return vocab

    def make_row(self) -> list[str]:
        if "vocab" not in self.tags:
            return [
                self.japanese,
                self.english,
                self.get_vocab(),
                self.section,
                self.chapter,
                self.link,
                # self.tags,
            ]


def write_csv_file(rows: list[list[str]]) -> None:
    with open(OUTPUT_FILENAME, "w", newline="") as csvfile:
        csvfile.write(IMPORT_HEADER)
        writer = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        for row in rows:
            writer.writerow(row)


class IncorrectlyFormattedExampleException(Exception):
    pass


def create_example_from_section(example_section):
    """
    Example li structure
    <li><span class="popup" title="ともだち - friend">友達</span><em>じゃない</em>。<br/>
    """
    flattened_string = "".join([s for s in example_section.strings])

    split_string = flattened_string.split("\n")
    # Depending on the formatting, there will sometimes be empty strings which should be removed
    # Sometimes it is not separated by a line by instead a "–" or a "。"
    cleaned_split_string = list(filter(lambda x: x != "", split_string))
    if len(cleaned_split_string) == 1:
        cleaned_split_string = cleaned_split_string[0].split("–")
    if len(cleaned_split_string) == 1:
        cleaned_split_string = cleaned_split_string[0].split("。")

    if len(cleaned_split_string) != 2:
        raise IncorrectlyFormattedExampleException(example_section)

    jp = cleaned_split_string[0]
    en = cleaned_split_string[1]

    vocab = []
    for vocab_element in example_section.find_all("span"):
        kanji = vocab_element.string
        explanation = vocab_element.get("title")
        vocab.append(Vocab(kanji=kanji, explanation=explanation))

    return Example(japanese=jp, english=en, vocab=vocab)


def parse_webpage(web_url):
    html = requests.get(web_url).content
    page = BeautifulSoup(html, "html.parser")

    examples = []
    chapter = page.find("h1").string

    # Parse all <ol>'s
    for l in page.find_all("ol"):
        previous_title = l.previous_sibling.previous_sibling
        # if previous_title and "Vocabulary" not in previous_title:
        if previous_title:
            section_name = ""
            section = l.find_previous("h2")
            if section:
                section_name = section.string
                if not section_name:
                    section_name = "".join(list(section.strings))
            tags = ""
            if "vocabulary" in str(previous_title).lower() or (
                section_name and "vocabulary" in section_name.lower()
            ):
                tags = "tae-kim-vocabulary"

            # Create Example objects from each list item
            for example_section in l.find_all("li"):
                try:
                    example = create_example_from_section(example_section)
                    example.section = section_name
                    example.chapter = chapter
                    example.link = web_url
                    example.tags = tags
                    examples.append(example)
                except IncorrectlyFormattedExampleException as e:
                    print(f"Example could not be parsed in chapter {chapter}\n{e}")

    next_url = ""
    next_url_element = page.find("span", class_="series-nav-right").find("a")
    if next_url_element:
        next_url = next_url_element.get("href")

    return examples, next_url


def main():
    all_examples = []
    next_url = START_URL
    while next_url:
        print("Parsing", next_url)
        examples, next_url = parse_webpage(next_url)
        all_examples.extend(examples)
        print(f"Found {len(examples)} items\n")
        # next_url = False

    rows = []
    for e in all_examples:
        row = e.make_row()
        if row:
            rows.append(row)

    write_csv_file(rows)


if __name__ == "__main__":
    main()
