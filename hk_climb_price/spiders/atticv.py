"""
Price Crawler for Attic V web page
"""
from abc import ABC, abstractmethod
import re
from typing import Sequence, Tuple

from scrapy import Selector, Spider

from hk_climb_price.helpers import breakdown_price_tag, process_text
from hk_climb_price.items import ClimbGym, PackageItem


class ParseValidityMixin:
    def _parse_validity(self, xpath: str = ".//p/span/text()") -> str:
        validitiy = self.selector.xpath(xpath).get()
        return re.match(r"\* Valid for (.*) only$", validitiy)[1]


class MultiplePassParser(ParseValidityMixin, ABC):
    def __init__(self, selector: Selector):
        self.selector = selector
        self.base_title = self._parse_base_title()
        self.category = "multi-pass"

    def _parse_base_title(self) -> str:
        base_title = self.selector.xpath(".//h6/text()").get()
        return process_text(base_title)

    def _parse_tags(self) -> Sequence[str]:
        note = self.selector.xpath(".//*[6]/span/text()").get()
        return [note]

    @abstractmethod
    def parse(self) -> PackageItem:
        raise NotImplementedError("Not implemented")


class AdultMultiplePassParser(MultiplePassParser):
    def parse(self) -> PackageItem:
        currency_symbol, price = self._parse_price()
        return PackageItem(
            title=self._parse_title(),
            category=self.category,
            tags=self._parse_tags(),
            currency_symbol=currency_symbol,
            price=price,
            validity=self._parse_validity(),
        )

    def _parse_title(self) -> str:
        selector = self.selector.xpath(".//h6/span/span[1]/text()")
        title = process_text(selector.get())
        return self.base_title + " - " + title

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6/span/span[2]/text()")
        price = process_text(selector.get())
        return "$", int(price.split(" ")[1])


class StudentOver18MultiplePassParser(MultiplePassParser):
    def parse(self) -> PackageItem:
        currency_symbol, price = self._parse_price()
        return PackageItem(
            title=self._parse_title(),
            category=self.category,
            tags=self._parse_tags(),
            currency_symbol=currency_symbol,
            price=price,
            validity=self._parse_validity(),
        )

    def _parse_title(self) -> str:
        selector = self.selector.xpath(".//h6[2]/span/span/text()")
        title = process_text(selector.get()).split("-")[0]
        return self.base_title + " - " + title

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6[2]/span/span/text()")
        price = process_text(selector.get()).split("-")[1]
        return "$", int(price.replace("HK$", ""))


class StudentBelow18MultiplePassParser(MultiplePassParser):
    def parse(self) -> PackageItem:
        currency_symbol, price = self._parse_price()
        return PackageItem(
            title=self._parse_title(),
            category=self.category,
            tags=self._parse_tags(),
            currency_symbol=currency_symbol,
            price=price,
            validity=self._parse_validity(),
        )

    def _parse_title(self) -> str:
        title_1 = process_text(self.selector.xpath(".//h6[3]/span/span/text()").get())
        title_2 = process_text(
            self.selector.xpath(".//h6[3]/span[2]/span/span/text()").get()
        )
        return self.base_title + " - " + title_1 + " " + title_2

    def _parse_price(self) -> Tuple[str, int]:
        selector = self.selector.xpath(".//h6[3]/span[3]/span/text()")
        price = process_text(selector.get())
        return "$", int(price.replace("HK$", ""))


class SharePassParser(ParseValidityMixin, ABC):
    def __init__(self, selector: Selector):
        self.selector = selector
        self.category = "share-pass"

    @abstractmethod
    def parse(self) -> PackageItem:
        raise NotImplementedError("Not implemented")


class SharedPass10Parser(SharePassParser):
    def parse(self) -> PackageItem:
        return PackageItem(
            title=self._parse_title(),
            category=self.category,
            currency_symbol="$",
            price=self._parse_price(),
            validity=self._parse_validity(".//p[2]/span/text()"),
        )

    def _parse_title(self) -> str:
        raw_title = self.selector.xpath(".//h6/text()").get()
        return process_text(raw_title)

    def _parse_price(self) -> int:
        raw_price = self.selector.xpath(".//h6/span[2]/span/text()").get()
        price_text = process_text(raw_price.replace("HKD", "").replace(",", ""))
        return int(price_text)


class SharedPass5Parser(SharePassParser):
    def parse(self) -> PackageItem:
        return PackageItem(
            title=self._parse_title(),
            category=self.category,
            currency_symbol="$",
            price=self._parse_price(),
            validity=self._parse_validity(".//p[2]/span/text()"),
        )

    def _parse_title(self) -> str:
        raw_title = self.selector.xpath(".//h6/text()").get()
        return process_text(raw_title)

    def _parse_price(self) -> int:
        raw_price = self.selector.xpath(".//h6/span[2]/span/text()").get()
        price_text = process_text(raw_price.replace("HKD", "").replace(",", ""))
        return int(price_text)


class AtticVPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from Attic V web page
    """

    name = "atticv"
    start_urls = ["https://www.atticv.com.hk/membership"]

    def _parse_all_day_passes(self, selector: Selector) -> Sequence[PackageItem]:
        context = selector.xpath(".//div[3]")
        base_title = context.xpath(".//h6/span/text()").get()
        price_text = context.xpath(".//h6/span/span/span/text()").get()
        description = context.xpath(".//p[2]/text()").get()
        adult_price_text, student_price_text = price_text.split(";")
        adult_price_tag = adult_price_text.split("-")[1].split("/")[0].strip()
        student_price_tag = student_price_text.split("-")[1].split("/")[0].strip()
        return [
            PackageItem(
                title=base_title + adult_price_text.split("-")[0],
                category="day-pass",
                currency_symbol=adult_price_tag.split(" ")[0].replace("\xa0", ""),
                price=adult_price_tag.split(" ")[1],
                tags=[description],
                validity="1 day",
            ),
            PackageItem(
                title=base_title + student_price_text.split("-")[0],
                category="day-pass",
                currency_symbol=student_price_tag.split(" ")[0],
                price=student_price_tag.split(" ")[1],
                tags=[description],
                validity="1 day",
            ),
        ]

    def _parse_multiple_passes(self, selector: Selector) -> Sequence[PackageItem]:
        context = selector.xpath(".//div[3]")

        adult_pass = AdultMultiplePassParser(selector=context).parse()
        student_over_18_pass = StudentOver18MultiplePassParser(selector=context).parse()
        student_below_18_pass = StudentBelow18MultiplePassParser(
            selector=context
        ).parse()

        return [adult_pass, student_over_18_pass, student_below_18_pass]

    def _parse_10_share_pass(self, selector: Selector) -> PackageItem:
        context = selector.xpath(".//div[3]")
        return SharedPass10Parser(selector=context).parse()

    def _parse_5_share_pass(self, selector: Selector) -> PackageItem:
        context = selector.xpath(".//div[4]")
        return SharedPass5Parser(selector=context).parse()

    def _parse_extra(self, selector: Selector) -> Sequence[PackageItem]:
        context = selector.css(
            "div#masterPage #cuy0inlineContent-gridContainer > div:last-child"
        )

        raw_text = context.xpath(".//h6/span/span/text()").get()
        raw_title, raw_price = raw_text.split(":")
        return [
            PackageItem(
                title=process_text(raw_title),
                category="eq-rental",
                currency_symbol="$",
                price=int(raw_price.split("/")[0].replace("$", "")),
            )
        ]

    def parse(self, response):
        selector = response.css(
            "div#masterPage #cuy0inlineContent-gridContainer .c4inlineContent > div > div"
        )
        sections = list(selector.getall())

        packages = [
            *self._parse_all_day_passes(Selector(text=sections[0])),
            *self._parse_multiple_passes(Selector(text=sections[1])),
            self._parse_10_share_pass(Selector(text=sections[2])),
            self._parse_5_share_pass(Selector(text=sections[3])),
            *self._parse_extra(response),
        ]
        yield ClimbGym(name="Attic V", packages=packages)
