import argparse

from response import Response
from web_parser import BBCHeadlineParser, BBC_SECTIONS


def scrape_section(category):
    """
    Fetch and parse one BBC news section.

    T16 CLI uses the existing HTTP/Response layer to fetch
    the page, then passes the HTML to the T8 parser.
    """

    url = BBC_SECTIONS[category]

    response = Response.from_openurllib(
        url,
        timeout=10
    )

    parser = BBCHeadlineParser(
        base_url="https://www.bbc.com",
        category=category
    )

    parser.feed(response.body)

    return parser.headlines


def build_parser():
    """
    Build the command-line argument parser.

    A category is optional.

    If no category is supplied, the CLI fetches all
    available BBC sections.
    """

    parser = argparse.ArgumentParser(
        description="Latest BBC News"
    )

    parser.add_argument(
        "category",
        nargs="?",
        choices=BBC_SECTIONS.keys(),
        help="BBC section to scrape"
    )

    return parser


def main():
    """
    Main CLI entry point.

    This provides the high-level user interface.
    The user does not need to know anything about
    connections, parsing, cookies, retries, etc.
    """

    parser = build_parser()
    args = parser.parse_args()

    print()
    print("======================================")
    print("            LATEST NEWS")
    print("======================================")
    print()

    print("Fetching BBC News...")
    print()

    # -------------------------------------------------
    # Determine which categories to fetch.
    # -------------------------------------------------
    #
    # If the user specifies a category:
    #
    #     python cli.py technology
    #
    # only that category is fetched.
    #
    # If no category is specified:
    #
    #     python cli.py
    #
    # all BBC sections are fetched.
    # -------------------------------------------------

    if args.category:
        categories = [args.category]
    else:
        categories = list(BBC_SECTIONS.keys())

    all_headlines = []

    # -------------------------------------------------
    # Fetch and display each category.
    # -------------------------------------------------

    for category in categories:

        print("--------------------------------------")
        print(f"{category.upper()}")
        print("--------------------------------------")

        try:
            headlines = scrape_section(category)

        except Exception:
            print("No recent update here.")
            print()
            continue

        # -------------------------------------------------
        # No news available for this category.
        # -------------------------------------------------

        if not headlines:
            print("No recent update here.")
            print()
            continue

        # -------------------------------------------------
        # Display the headlines.
        # -------------------------------------------------

        for index, headline in enumerate(
            headlines,
            start=1
        ):

            title = headline["title"].strip()

            # Ensure every headline ends with a full stop.
            if not title.endswith("."):
                title += "."

            print(f"{index}. {title}")
            print(f"   {headline['url']}")
            print()

        # Add this category's headlines to the
        # overall collection.
        all_headlines.extend(headlines)

    # -------------------------------------------------
    # Display total number of headlines.
    # -------------------------------------------------

    print("======================================")
    print(
        f"Total headlines: {len(all_headlines)}"
    )
    print("======================================")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())