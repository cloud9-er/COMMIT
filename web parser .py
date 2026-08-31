
from response import Response
from html.parser import HTMLParser
from urllib.parse import urljoin


BBC_SECTIONS = {
    "technology": "https://www.bbc.com/news/technology",
    "business": "https://www.bbc.com/news/business",
    "science": "https://www.bbc.com/news/science-environment",
    "world": "https://www.bbc.com/news/world",
    "politics": "https://www.bbc.com/news/politics",
}


class BBCHeadlineParser(HTMLParser):
    def __init__(self, base_url, category=None):
        super().__init__()

        self.base_url = base_url
        self.category = category

        self.anchor_stack = []
        self.in_headline = False
        self.current_text = ""

        self.headlines = []

        # T9 uses this to find the next page.
        self.next_url = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)

        # Track article links.
        if tag == "a" and "href" in attr_dict:
            self.anchor_stack.append(attr_dict["href"])

            # T9 pagination support.
            # Store the URL if this anchor represents
            # the next page.
            aria_label = attr_dict.get("aria-label", "")

            if aria_label.lower() == "next":
                self.next_url = urljoin(
                    self.base_url,
                    attr_dict["href"]
                )

        # Detect BBC headline elements.
        elif (
            tag == "h2"
            and attr_dict.get("data-testid") == "card-headline"
        ):
            self.in_headline = True
            self.current_text = ""

    def handle_data(self, data):
        if self.in_headline:
            self.current_text += data

    def handle_endtag(self, tag):

        if tag == "h2" and self.in_headline:

            self.in_headline = False

            title = self.current_text.strip()

            if title and self.anchor_stack:

                href = self.anchor_stack[-1]

                absolute_url = urljoin(
                    self.base_url,
                    href
                )

                self.headlines.append({
                    "title": title,
                    "url": absolute_url,
                    "category": self.category,
                })

        elif tag == "a" and self.anchor_stack:
            self.anchor_stack.pop()


if __name__ == "__main__":

    sections = {
        "technology": "https://www.bbc.com/news/technology",
        "business": "https://www.bbc.com/news/business",
        "world": "https://www.bbc.com/news/world",
    }

    all_headlines = []

    for category, url in sections.items():

        r = Response.from_openurllib(
            url,
            timeout=10
        )

        parser = BBCHeadlineParser(
            base_url=url,
            category=category
        )

        parser.feed(r.body)

        all_headlines.extend(parser.headlines)

        print(
            f"{category}: "
            f"{len(parser.headlines)} headlines"
        )

    print(
        f"\nTotal: "
        f"{len(all_headlines)} headlines"
    )

    for h in all_headlines[:5]:
        print(h)
