"""
Price Crawler for Attic V web page
"""
from abc import ABC, abstractmethod
import logging
from pprint import pprint
import re
from typing import Dict, List, Tuple

from scrapy import Selector, Spider

from helpers import breakdown_price_tag

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def _remove_parentheses(string: str) -> str:
    return re.sub(r"[\(\)]", "", string)


def _process_text(string: str) -> str:
    return string.strip().replace('\xa0', '').strip("; -:")

class ParseValidityMixin:
    def _parse_validity(self, xpath: str=".//p/span/text()") -> str:
        validitiy = self.selector.xpath(xpath).get()
        return re.match(r'\* Valid for (.*) only$', validitiy)[1]


class MultiplePassParser(ParseValidityMixin, ABC):
    def __init__(self, selector: Selector):
        self.selector = selector
        self.base_title = self._parse_base_title()
        self.category = "multi-pass"

    def _parse_base_title(self) -> str:
        base_title = self.selector.xpath(".//h6/text()").get()
        return _process_text(base_title)


    @abstractmethod
    def parse(self) -> List[Dict]:
        raise NotImplementedError("Not implemented")

class AdultMultiplePassParser(MultiplePassParser):
    def parse(self) -> List[Dict]:
        currency_symbol, price = self._parse_price()
        adult_pass = {
            "title": self._parse_title(),
            "category": self.category ,
            "currency_symbol": currency_symbol,
            "price": price,
            "validity": self._parse_validity(),
        }
        return [adult_pass]

    def _parse_title(self) -> str:
        selector = self.selector.xpath(".//h6/span/span[1]/text()")
        title = _process_text(selector.get())
        return self.base_title + " - " + title

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6/span/span[2]/text()")
        price = _process_text(selector.get())
        return "$", int(price.split(" ")[1])

class StudentOver18MultiplePassParser(MultiplePassParser):
    def parse(self) -> List[Dict]:
        currency_symbol, price = self._parse_price()
        student_over_18_pass = {
            "title": self._parse_title(),
            "category": self.category ,
            "currency_symbol": currency_symbol,
            "price": price,
            "validity": self._parse_validity(),
        }
        return [student_over_18_pass]

    def _parse_title(self) -> str:
        selector = self.selector.xpath(".//h6[2]/span/span/text()")
        title = _process_text(selector.get()).split("-")[0]
        return self.base_title + " - " + title

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6[2]/span/span/text()")
        price = _process_text(selector.get()).split("-")[1]
        return "$", int(price.replace("HK$", ""))


class StudentBelow18MultiplePassParser(MultiplePassParser):
    def parse(self) -> List[Dict]:
        currency_symbol, price = self._parse_price()
        student_over_18_pass = {
            "title": self._parse_title(),
            "category": self.category ,
            "currency_symbol": currency_symbol,
            "price": price,
            "validity": self._parse_validity(),
        }
        return [student_over_18_pass]

    def _parse_title(self) -> str:
        title_1 = _process_text(self.selector.xpath(".//h6[3]/span/span/text()").get())
        title_2 = _process_text(self.selector.xpath(".//h6[3]/span[2]/span/span/text()").get())
        return self.base_title + " - " + title_1 + " " + title_2

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6[3]/span[3]/span/text()")
        price = _process_text(selector.get())
        return "$", int(price.replace("HK$", ""))

class SharePassParser(ParseValidityMixin, ABC):
    def __init__(self, selector: Selector):
        self.selector = selector
        self.category = "share-pass"

    @abstractmethod
    def parse(self) -> List[Dict]:
        raise NotImplementedError("Not implemented")

class SharedPass10Parser(SharePassParser):
    def parse(self) -> List[Dict]:
        return [
            {
                "title": self._parse_title(),
                "category": self.category,
                "currency_symbol": "$",
                "price": self._parse_price(),
                "validity": self._parse_validity(".//p[2]/span/text()"),
            }
        ]

    def _parse_title(self)-> str:
        raw_title = self.selector.xpath(".//h6/descendant-or-self::span").get()
        return _process_text(raw_title)

    def _parse_price(self) -> int:
        raw_price = self.selector.xpath(".//h6/span[2]/span/text()").get()
        price_text = _process_text(raw_price.replace("HKD", "").replace(",", ""))
        return int(price_text)

class SharedPass5Parser(SharePassParser):
    def parse(self) -> List[Dict]:
        return [
            {
                "title": self._parse_title(),
                "category": self.category,
                "currency_symbol": "$",
                "price": self._parse_price(),
                "validity": self._parse_validity(".//p[2]/span/text()"),
            }
        ]

    def _parse_title(self)-> str:
        raw_title = self.selector.xpath(".//h6/text()").get()
        return _process_text(raw_title)

    def _parse_price(self) -> int:
        raw_price = self.selector.xpath(".//h6/span[2]/span/text()").get()
        price_text = _process_text(raw_price.replace("HKD", "").replace(",", ""))
        return int(price_text)



class AtticVPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from Attic V web page
    """

    name = "atticvpricespider"
    start_urls = ["https://www.atticv.com.hk/membership"]

    def _parse_all_day_passes(self, selector: Selector) -> List[Dict]:
        context = selector.xpath(".//div[3]")
        base_title = context.xpath(".//h6/span/text()").get()
        price_text = context.xpath(".//h6/span/span/span/text()").get()
        description = context.xpath(".//p[2]/text()").get()
        adult_price_text, student_price_text = price_text.split(";")
        adult_price_tag = adult_price_text.split("-")[1].split("/")[0].strip()
        student_price_tag = student_price_text.split("-")[1].split("/")[0].strip()
        return [
            {
                "title": base_title +adult_price_text.split("-")[0],
                "category": "day-pass",
                "currency_symbol": adult_price_tag.split(" ")[0].replace('\xa0', ''),
                "price":  adult_price_tag.split(" ")[1],
                "tags": {description},
            },
            {
                "title": base_title +student_price_text.split("-")[0],
                "category": "day-pass",
                "currency_symbol": student_price_tag.split(" ")[0],
                "price":  student_price_tag.split(" ")[1],
                "tags": {description},
            },
        ]

    def _parse_multiple_passes(self, selector: Selector) -> List[Dict]:
        context = selector.xpath(".//div[3]")

        adult_passes = AdultMultiplePassParser(selector=context).parse()
        student_over_18_passes = StudentOver18MultiplePassParser(selector=context).parse()
        student_below_18_passes = StudentBelow18MultiplePassParser(selector=context).parse()

        return [*adult_passes, *student_over_18_passes, *student_below_18_passes]

    def _parse_10_share_passes(self, selector: Selector):
        context = selector.xpath(".//div[3]")

        share_pass_10 = SharedPass10Parser(selector=context).parse()
        return [*share_pass_10]

    def _parse_5_share_passes(self, selector: Selector):
        context = selector.xpath(".//div[4]")

        share_pass_5 = SharedPass5Parser(selector=context).parse()
        return [*share_pass_5]

    def _parse_extra(self, selector:Selector):
        context = selector.css("div#masterPage #cuy0inlineContent-gridContainer > div:last-child")

        raw_text = context.xpath(".//h6/span/span/text()").get()
        raw_title, raw_price = raw_text.split(":")
        return [
            {
                "title": _process_text(raw_title),
                "category": "eq-rental",
                "currency_symbol": "$",
                "price": int(raw_price.split("/")[0].replace("$", "")),
            }
        ]


    def parse(self, response):
        selector = response.css("div#masterPage #cuy0inlineContent-gridContainer .c4inlineContent > div > div")
        sections = list(selector.getall())

        data = {
            "packages": [
            *self._parse_all_day_passes(Selector(text=sections[0])),
            *self._parse_multiple_passes(Selector(text=sections[1])),
            *self._parse_10_share_passes(Selector(text=sections[2])),
            *self._parse_5_share_passes(Selector(text=sections[3])),
            *self._parse_extra(response),
        ]}
        pprint(data)
        yield data
