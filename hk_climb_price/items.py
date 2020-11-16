# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import asdict, dataclass, field
from pprint import pformat
from typing import Optional, Sequence

import scrapy


@dataclass
class PackageItem:
    """
    Data model of a product item
    """

    title: str
    category: str
    tags: Sequence[str] = field(default_factory=list)
    currency_symbol: str = field(default="$")
    price: int = field(default_factory=int)
    validity: Optional[str] = field(default=None)


@dataclass
class ClimbGym:
    name: str
    link: str
    packages: Sequence[PackageItem] = field(default_factory=set)

    def __str__(self) -> str:
        return pformat(asdict(self))
