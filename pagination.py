
from response import Response
from web_parser  import BBCHeadlineParser


class PaginationEngine:
    """
    Safely follows pagination links discovered by T8.
    """

    def __init__(self, max_pages=5, timeout=10):
        self.max_pages = max_pages
        self.timeout = timeout

    def crawl(self, start_url, category=None):
        """
        Crawl pages starting from start_url.

        Returns a list of headlines collected from all pages.
        """

        current_url = start_url
        all_headlines = []

        visited_urls = set()

        for page_number in range(self.max_pages):

            # Stop if this URL has already been visited.
            # This prevents infinite pagination loops.
            if current_url in visited_urls:
                break

            visited_urls.add(current_url)

            # Fetch the current page using the existing
            # project Response/request infrastructure.
            response = Response.from_openurllib(
                current_url,
                timeout=self.timeout
            )

            # web_parser parses the HTML.
            parser = BBCHeadlineParser(
                base_url=current_url,
                category=category
            )

            parser.feed(response.body)

            # Collect the headlines from this page.
            all_headlines.extend(parser.headlines)

            # web_parser tells us where the next page is.
            next_url = parser.next_url

            # No next page means pagination is finished.
            if not next_url:
                break

            # Follow the next page.
            current_url = next_url

        return all_headlines


if __name__ == "__main__":

    engine = PaginationEngine(
        max_pages=5,
        timeout=10
    )

    headlines = engine.crawl(
        "https://www.bbc.com/news/technology",
        category="technology"
    )

    print(f"Total headlines: {len(headlines)}")

    for headline in headlines[:10]:
        print(headline)

