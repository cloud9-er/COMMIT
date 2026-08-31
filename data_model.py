
from dataclasses import dataclass


@dataclass
class Headline:
    """
    T10: Structured representation of one news headline.
    """

    title: str
    url: str
    category: str

    @classmethod
    def from_dict(cls, data):
        """
        Convert a T8/T9 headline dictionary into
        a structured Headline object.
        """

        return cls(
            title=data["title"],
            url=data["url"],
            category=data.get("category", "unknown")
        )

    def to_dict(self):
        """
        Convert the Headline object back into
        a normal dictionary.
        """

        return {
            "title": self.title,
            "url": self.url,
            "category": self.category
        }

    def __str__(self):
        """
        Human-readable representation.
        """

        return f"[{self.category}] {self.title} - {self.url}"


def build_headlines(raw_headlines):
    """
    Convert a list of dictionaries from T8/T9
    into a list of Headline objects.
    """

    return [
        Headline.from_dict(headline)
        for headline in raw_headlines
    ]

