from html.parser import HTMLParser
from urllib.parse import urljoin



# These are the BBC sections that our CLI can request.

# The CLI imports BBC_SECTIONS from this file, so we keep
# the URLs in one central place instead of duplicating them.

# web_parser's job is to take HTML and extract structured headlines.
# It does NOT make the HTTP request itself.


BBC_SECTIONS = {
    "technology": "https://www.bbc.com/news/technology",
    "business": "https://www.bbc.com/news/business",
    "science": "https://www.bbc.com/news/science-environment",
    "world": "https://www.bbc.com/news/world",
    "politics": "https://www.bbc.com/news/politics",
}


class BBCHeadlineParser(HTMLParser):
    """
    HTML parser for extracting BBC news headlines.

    HTMLParser comes from Python's standard library.

    The parser looks for BBC headline elements and extracts:

        - headline title
        - article URL
        - news category

    pagination also uses this parser to detect the next-page URL.
    """

    def __init__(self, base_url, category=None):
        super().__init__()

        # URL of the page currently being parsed.
        # This is needed when converting relative URL into complete URLs.
        self.base_url = base_url

        # Category is supplied by the caller because the HTML itself does not necessarily tell us which BBC section we are processing.
        self.category = category

    

        # Keeps track of currently open <a> elements.
        self.anchor_stack = []

        # Tells us whether we are currently inside a
        # BBC headline <h2> element.
        self.in_headline = False

        # Temporarily stores the text inside the headline.
        self.current_text = ""

        # Final collection of extracted headlines.
        self.headlines = []

     
        
        # pagination can use this value to find the next page.
        
        # web_parser only detects and stores it.
        # pagination will decide whether/how to follow it.
        self.next_url = None

    def handle_starttag(self, tag, attrs):
        """
        Called automatically whenever HTMLParser
        encounters an opening HTML tag.
        """

        # Convert the attribute list into a dictionary.
        attr_dict = dict(attrs)

      
        # Detect article links
        if tag == "a" and "href" in attr_dict:

            # Save the link so that when we encounter the headline inside this <a>, we know which article it belongs to.
            self.anchor_stack.append(
                attr_dict["href"]
            )

          
            #  pagination support
            # BBC may identify a pagination link with: aria-label="Next"
            # If we find one, convert it into an absolute URL.
            
            aria_label = attr_dict.get(
                "aria-label",
                ""
            )

            if aria_label.lower() == "next":

                self.next_url = urljoin(
                    self.base_url,
                    attr_dict["href"]
                )

      
        # Detect BBC headline elements
    
        # BBC headlines use: <h2 data-testid="card-headline">
        # When we encounter this element, start collecting the text inside it.
        elif (
            tag == "h2"
            and attr_dict.get("data-testid")
            == "card-headline"
        ):

            self.in_headline = True
            self.current_text = ""

    def handle_data(self, data):
        """
        Called whenever HTMLParser encounters text.

        If we are currently inside a headline <h2>,
        append that text to current_text.
        """

        if self.in_headline:
            self.current_text += data

    def handle_endtag(self, tag):
        """
        Called automatically whenever HTMLParser
        encounters a closing HTML tag.
        """

        # Finished reading a headline
     

        if tag == "h2" and self.in_headline:

            # We are no longer inside the headline.
            self.in_headline = False

            # Remove unnecessary whitespace from the title.
            title = self.current_text.strip()

            # We only save the headline if:
            # 1. It contains text.
            # 2. We know the article's surrounding <a> URL.
            if title and self.anchor_stack:

                # Get the URL of the surrounding article link.
                href = self.anchor_stack[-1]

                # Convert a relative URL such as: /news/articles/example into: https://www.bbc.com/news/articles/example
                absolute_url = urljoin(
                    self.base_url,
                    href
                )

                # Store the headline as a structured dictionary.
                self.headlines.append({
                    "title": title,
                    "url": absolute_url,
                    "category": self.category,
                })

 
        # Finished reading an <a> element
        # Remove the URL from the stack because we have reached the closing </a> tag.
        elif tag == "a" and self.anchor_stack:

            self.anchor_stack.pop()

# HELPER FUNCTION
# The CLI already fetches the HTML using the existing
# project request/response infrastructure.
# This function receives HTML that has already been fetched and passes it into BBCHeadlineParser.


def parse_headlines(html, category):
    """
    Parse BBC HTML and return extracted headlines.

    Parameters:
        html:
            HTML response body already fetched by the client.

        category:
            BBC section being parsed.

    Returns:
        A list of dictionaries containing:
            title
            url
            category
    """

    # Find the URL associated with this category.
    base_url = BBC_SECTIONS[category]

    # Create the T8 parser.
    parser = BBCHeadlineParser(
        base_url=base_url,
        category=category
    )

    # Feed the downloaded HTML into HTMLParser.
    parser.feed(html)

    # Return the structured headlines to the caller.
    return parser.headlines
