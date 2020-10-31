"""
Price Crawler for Just Climb web page
"""
import logging
import re
from typing import Dict, Sequence

from scrapy import Selector, Spider

from hk_climb_price.helpers import breakdown_price_tag, process_text
from hk_climb_price.items import ClimbGym, PackageItem


def _remove_parentheses(string: str) -> str:
    return re.sub(r"[\(\)]", "", string)


class JustclimbPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from Verm City web page
    """

    name = "vermcity"
    start_urls = ["https://www.vermcity.com/pricing-chi"]

    def _select_day_pass(self, response: Selector) -> PackageItem:
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[3]/div[4]"
            "//div[contains(@class, 'block-content')]"
        )
        day_pass = {
            "title": block.xpath("./*[1]/text()").get()
            + " "
            + block.xpath("./*[2]/text()").get().split()[0],
            "category": "day-pass",
            "tags": {
                block.xpath("./*[3]/text()").get(),
                block.xpath("./*[4]/text()").get(),
                block.xpath("./*[5]/text()").get(),
                block.xpath("./*[6]/text()").get(),
            },
            **breakdown_price_tag(block.xpath("./*[2]/text()").get().split()[1]),
        }
        return PackageItem(**day_pass)

    def _select_clip_n_climb_passes(self, response: Selector) -> Sequence[PackageItem]:
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[3]/div[2]"
            "//div[contains(@class, 'block-content')]"
        )
        section_pass_text = block.xpath("./*[2]/text()").get()
        ten_pass_text = block.xpath("./*[3]/text()").get()
        base_title = block.xpath("./*[1]/text()").get()
        tags = {block.xpath("./*[5]/text()").get()}
        items = [
            {
                "title": base_title + " " + process_text(section_pass_text),
                "category": "section-pass",
                "tags": tags,
                **breakdown_price_tag(section_pass_text.split(" ")[1]),
            },
            {
                "title": base_title + " " + ten_pass_text.split(" ")[0],
                "category": "share-pass",
                "tags": tags,
                **breakdown_price_tag(ten_pass_text.split(" ")[1]),
                "validity": _remove_parentheses(ten_pass_text.split(" ")[2]),
            },
        ]

        return [PackageItem(**item) for item in items]

    def _share_pass_price_item(self, string: str) -> Sequence[PackageItem]:
        name, validity, price_tag = string.rsplit(maxsplit=2)
        return {
            "title": name,
            "validity": _remove_parentheses(validity).replace("只限", ""),
            **breakdown_price_tag(price_tag),
        }

    def _select_share_passes(self, response: Selector) -> Sequence[PackageItem]:
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[4]/div/div[1]"
            "//div[contains(@class, 'block-content')][1]"
        )
        items = [
            self._share_pass_price_item(block.xpath("./*[6]/text()").get()),
            self._share_pass_price_item(block.xpath("./*[7]/text()").get()),
        ]
        for item in items:
            item["title"] = item["title"]
            item["category"] = "share-pass"
        return [PackageItem(**item) for item in items]

    def _membership_price_item(self, string: str) -> PackageItem:
        title, price_tag = string.split("$")
        return {
            "title": process_text(title),
            **breakdown_price_tag("$" + price_tag),
            "validity": process_text(title),
        }

    def _select_membership_passes(
        self,
        response: Selector,
    ) -> PackageItem:
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[4]/div/div[1]"
            "//div[contains(@class, 'block-content')][1]"
        )
        base_title = block.xpath("./*[1]/text()").get()
        category = "membership"
        items = [
            self._membership_price_item(block.xpath("./*[2]/text()").get()),
            self._membership_price_item(block.xpath("./*[3]/text()").get()),
            self._membership_price_item(block.xpath("./*[4]/text()").get()),
            self._membership_price_item(block.xpath("./*[5]/text()").get()),
        ]
        for item in items:
            item["title"] = base_title + " " + item["title"]
            item["category"] = "membership"
        return [PackageItem(**item) for item in items]

    def parse(self, response: Selector) -> ClimbGym:  # pylint: disable=arguments-differ
        vermcity = ClimbGym(
            name="Verm City",
            packages=[
                self._select_day_pass(response),
                *self._select_clip_n_climb_passes(response),
                *self._select_share_passes(response),
                *self._select_membership_passes(response),
            ],
        )
        yield vermcity
