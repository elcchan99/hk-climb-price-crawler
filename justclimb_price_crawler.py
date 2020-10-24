"""
Price Crawler for Just Climb web page
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pprint import pformat
from typing import Dict, Optional, Sequence, Union

from scrapy import Selector, Spider

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


@dataclass
class PackageItemModel:
    """
    Data model of a product item
    """

    title: str
    tags: Sequence[str] = field(default_factory=set)
    currency_symbol: str = field(default="$")
    price: int = field(default_factory=int)
    validity: Optional[str] = field(default=None)


@dataclass
class ClimbPassModel:
    """
    Data model of a climbing pass
    """

    title: str
    items: Sequence[PackageItemModel] = field(default_factory=set)

    def __str__(self) -> str:
        return pformat(asdict(self))


def breakdown_price_tag(price_tag: str) -> Dict[str, Union[str, int]]:
    """
    Breakdown a string price tag into currency & price amount
    """
    if not price_tag:
        return {}
    return {
        "currency_symbol": price_tag[0],
        "price": int(price_tag[1:].replace(",", "")),
    }


class BasePassCrawler(ABC):
    """
    Base class of a climb pass parser
    """

    def __init__(self, selector):
        self.selector = selector

    @abstractmethod
    def parse(self) -> ClimbPassModel:
        """
        Parse pass info from selector
        """
        raise NotImplementedError("parse() method is not implemented")


class JustclimbDayPassCrawler(BasePassCrawler):
    """
    Day pass info crawler
    """

    def parse(self) -> ClimbPassModel:
        return ClimbPassModel(
            title=self._parse_title(),
            items=self._parse_items(),
        )

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='day-pass']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='day-pass']/following-sibling::div[1]")

    def _parse_title(self) -> str:
        return self._title_selector.css("h4::text").get()

    def _parse_items(self) -> Sequence[PackageItemModel]:
        return [
            self._parse_adult_item(),
            self._parse_student_item(),
            self._parse_other_item(),
        ]

    def _parse_tags(self) -> Sequence[str]:
        shoppage_selector = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        )

        tags = {
            shoppage_selector.xpath("./p[1]/text()").get(),
            *shoppage_selector.xpath("./p[3]/text()").getall(),
        }
        return {tag.strip() for tag in tags}

    def _parse_price_tag(self, index: int) -> str:
        xpath = f".//div[contains(@class, 'shoppage-title')]/*[{index+1}]/text()"
        return self._detail_selector.xpath(xpath).get()

    def _parse_adult_item(self) -> PackageItemModel:
        return PackageItemModel(
            title="Adult",
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=1)),
        )

    def _parse_student_item(self) -> PackageItemModel:
        return PackageItemModel(
            title="Student",
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=2).split()[1]),
        )

    def _parse_other_item(self) -> PackageItemModel:
        shoppage_div_text = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        ).getall()[1]
        shoppage_div = Selector(text=shoppage_div_text)
        sep = "｜"
        title = shoppage_div.xpath(".//*[1]/span/text()").get()
        price_tag = shoppage_div.xpath(".//*[2]/span/text()").get()
        tags_str = shoppage_div.xpath(".//*[3]/span/text()").get()
        return PackageItemModel(
            title=title.split(sep)[0],
            tags={title.split(sep)[1], *tags_str.split(sep)},
            **breakdown_price_tag(price_tag),
        )


class JustclimbSharePassCrawler(BasePassCrawler):
    """
    Share pass info crawler
    """

    def parse(self) -> ClimbPassModel:
        return ClimbPassModel(
            title=self._parse_title(),
            items=self._parse_items(),
        )

    class ItemCrawler:
        """
        Share pass item info crawler
        """

        def __init__(self, selector):
            self.selector = selector

        def parse(self) -> PackageItemModel:
            """Parse share pass item info

            Returns:
                PackageItemModel: the share pass item info
            """
            return PackageItemModel(
                title=self._parse_title(),
                tags=self._parse_tags(),
                validity=self._parse_validity(),
                **breakdown_price_tag(self._parse_price_tag()),
            )

        def _parse_title(self) -> str:
            return self.selector.css("div > *:nth-child(1)::text").get()

        def _parse_tags(self) -> str:
            temp = self.selector.xpath(".//p[2]/text()").getall()
            if not temp:
                return set()
            return {temp[0].strip()}

        def _parse_validity(self) -> str:
            temp = self.selector.xpath(".//p[2]/text()").getall()
            if not temp:
                return None
            return temp[1].strip().replace("有效期", "")

        def _parse_price_tag(self) -> str:
            return self.selector.css("div > *:nth-child(2)::text").get()

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='share-climb']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='share-climb']/following-sibling::div[1]")

    def _parse_title(self) -> str:
        return self._title_selector.css("h4::text").get()

    def _parse_items(self) -> Sequence[PackageItemModel]:
        items = [
            self.ItemCrawler(selector=item).parse()
            for item in self._detail_selector.css("div.grve-text")
        ]
        return [item for item in items if item.price]


class JustclimbMonthPassCrawler(BasePassCrawler):
    """
    Month pass info crawler
    """

    def parse(self) -> ClimbPassModel:
        return ClimbPassModel(
            title=self._parse_title(),
            items=self._parse_items(),
        )

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='monthly-pass']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath(
            "//div[@id='monthly-pass']/following-sibling::div[1]"
        )

    def _parse_title(self) -> str:
        return self._title_selector.css("h4::text").get()

    def _parse_items(self) -> Sequence[PackageItemModel]:
        return [
            self._parse_adult_item(),
            self._parse_student_item(),
        ]

    def _parse_tags(self) -> str:
        xpath = ".//div[contains(@class, 'shoppage-title')]/p[1]/span/text()"
        return {self._detail_selector.xpath(xpath).get()}

    def _parse_price_tag(self, index: int) -> str:
        xpath = f".//div[contains(@class, 'shoppage-title')]/*[{index+1}]/span/text()"
        return self._detail_selector.xpath(xpath).get()

    def _parse_adult_item(self) -> PackageItemModel:
        return PackageItemModel(
            title="Adult",
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=1)),
        )

    def _parse_student_item(self) -> PackageItemModel:
        return PackageItemModel(
            title="Student",
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=2).split()[1]),
        )


class JustclimbJcerCrawler(BasePassCrawler):
    """
    Jcer package info crawler
    """

    def parse(self) -> ClimbPassModel:
        return ClimbPassModel(
            title=self._parse_title(),
            items=self._parse_items(),
        )

    class ItemCrawler:
        """
        Jcer package item info crawler
        """

        def __init__(self, selector):
            self.selector = selector

        def parse(self) -> PackageItemModel:
            """Parse jcer pass item info

            Returns:
                PackageItemModel: the jcer pass item info
            """
            return PackageItemModel(
                title=self._parse_title(),
                tags=self._parse_tags(),
                validity=self._parse_validity(),
                **breakdown_price_tag(self._parse_price_tag()),
            )

        def _parse_title(self) -> str:
            return self.selector.xpath("./*[2]/text()").get()

        def _parse_tags(self) -> Sequence[str]:
            tags = self.selector.xpath("./*[4]/text()").getall()
            return {tag.strip() for tag in tags}

        def _parse_validity(self) -> str:
            return self._parse_title().replace("合約", "")

        def _parse_price_tag(self) -> str:
            return "$" + self.selector.xpath("./*[1]/text()").get().split("$")[1]

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='just-climber']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath(
            "//div[@id='just-climber']/following-sibling::div[1]"
        )

    def _parse_title(self) -> str:
        return self._title_selector.xpath(".//h4/text()").get()

    def _parse_items(self) -> Sequence[PackageItemModel]:
        item_selector = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        )
        item = self.ItemCrawler(selector=item_selector).parse()
        item.title = self._parse_title()
        return [item]


class JustclimbPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from JustClimb web page
    """

    name = "justclimbpricespider"
    start_urls = ["https://justclimb.hk/price/"]

    def _select_day_pass_price(self, response):
        parser = JustclimbDayPassCrawler(selector=response)
        return parser.parse()

    def _select_share_pass_price(self, response):
        parser = JustclimbSharePassCrawler(selector=response)
        return parser.parse()

    def _select_month_pass_price(self, response):
        parser = JustclimbMonthPassCrawler(selector=response)
        return parser.parse()

    def _select_jcer_price(self, response):
        parser = JustclimbJcerCrawler(selector=response)
        return parser.parse()

    def parse(self, response):  # pylint: disable=arguments-differ
        day_pass_price = self._select_day_pass_price(response)
        LOGGER.info(f"DAYPASS PRICE: \n{day_pass_price}")

        share_pass_price = self._select_share_pass_price(response)
        LOGGER.info(f"SHAREPASS PRICE: \n{share_pass_price}")

        month_pass_price = self._select_month_pass_price(response)
        LOGGER.info(f"MONTHPASS PRICE \n{month_pass_price}")

        jcer_price = self._select_jcer_price(response)
        LOGGER.info(f"JCER PRICE \n{jcer_price}")
