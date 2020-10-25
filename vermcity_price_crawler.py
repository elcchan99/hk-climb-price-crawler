"""
Price Crawler for Just Climb web page
"""
import logging
import re
from typing import Dict

from scrapy import Selector, Spider

from helpers import breakdown_price_tag

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def _remove_parentheses(string: str) -> str:
    return re.sub(r"[\(\)]", "", string)


class JustclimbPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from Verm City web page
    """

    name = "vermcitypricespider"
    start_urls = ["https://www.vermcity.com/pricing-chi"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.WARNING)

    def _select_day_pass_price(self, response: Selector):
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[3]/div[4]"
            "//div[contains(@class, 'block-content')]"
        )
        day_pass = {
            "title": block.xpath("./*[1]/text()").get(),
            "tags": {
                block.xpath("./*[3]/text()").get(),
                block.xpath("./*[4]/text()").get(),
                block.xpath("./*[5]/text()").get(),
                block.xpath("./*[6]/text()").get(),
            },
            "items": [
                {
                    "title": block.xpath("./*[2]/text()").get().split()[0],
                    **breakdown_price_tag(
                        block.xpath("./*[2]/text()").get().split()[1]
                    ),
                },
            ],
        }
        return day_pass

    def _select_clip_n_climb_price(self, response: Selector):
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[3]/div[2]"
            "//div[contains(@class, 'block-content')]"
        )
        section_pass_text = block.xpath("./*[2]/text()").get()
        ten_pass_text = block.xpath("./*[3]/text()").get()
        clip_n_climb = {
            "title": block.xpath("./*[1]/text()").get(),
            "tags": {
                block.xpath("./*[4]/text()").get(),
                block.xpath("./*[5]/text()").get(),
            },
            "items": [
                {
                    "title": section_pass_text,
                    **breakdown_price_tag(section_pass_text.split(" ")[1]),
                },
                {
                    "title": ten_pass_text.split(" ")[0],
                    **breakdown_price_tag(ten_pass_text.split(" ")[1]),
                    "validity": _remove_parentheses(ten_pass_text.split(" ")[2]),
                },
            ],
        }
        return clip_n_climb

    def _share_pass_price_item(self, string: str) -> Dict:
        name, validity, price_tag = string.rsplit(maxsplit=2)
        return {
            "title": name,
            "validity": _remove_parentheses(validity),
            **breakdown_price_tag(price_tag),
        }

    def _select_share_pass_price(self, response: Selector):
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[4]/div/div[1]"
            "//div[contains(@class, 'block-content')][1]"
        )
        share_pass = {
            "title": "通行證",
            "items": [
                self._share_pass_price_item(block.xpath("./*[6]/text()").get()),
                self._share_pass_price_item(block.xpath("./*[7]/text()").get()),
            ],
        }
        return share_pass

    def _membership_price_item(self, string: str) -> Dict:
        title, price_tag = string.split("$")
        return {
            "title": title,
            **breakdown_price_tag("$" + price_tag),
            "validity": title,
        }

    def _select_membership_price(self, response: Selector):
        block = response.xpath(
            ".//section[@class='Main-content']/div/div[4]/div/div[1]"
            "//div[contains(@class, 'block-content')][1]"
        )
        membership = {
            "title": block.xpath("./*[1]/text()").get(),
            "tags": {},
            "items": [
                self._membership_price_item(block.xpath("./*[2]/text()").get()),
                self._membership_price_item(block.xpath("./*[3]/text()").get()),
                self._membership_price_item(block.xpath("./*[4]/text()").get()),
                self._membership_price_item(block.xpath("./*[5]/text()").get()),
            ],
        }
        return membership

    def parse(self, response):  # pylint: disable=arguments-differ
        day_pass_price = self._select_day_pass_price(response)
        print(f"DAYPASS PRICE: \n{day_pass_price}")

        clip_n_climb_price = self._select_clip_n_climb_price(response)
        print(f"CLIPNCLIMB PRICE: \n{clip_n_climb_price}")

        share_pass_price = self._select_share_pass_price(response)
        print(f"SHAREPASS PRICE \n{share_pass_price}")

        membership_price = self._select_membership_price(response)
        print(f"MEMBERSHIP PRICE \n{membership_price}")

        yield {
            "day_pass": day_pass_price,
            "clip_n_climb_price": clip_n_climb_price,
            "share_pass_price": share_pass_price,
            "membership_price": membership_price,
        }
