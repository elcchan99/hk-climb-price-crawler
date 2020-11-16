"""
Price Parser for Just Climb web page
"""

from typing import Sequence

from scrapy import Selector, Spider

from hk_climb_price.helpers import breakdown_price_tag
from hk_climb_price.parser import BasePassParser
from hk_climb_price.items import ClimbGym, PackageItem


class JustclimbDayPassParser(BasePassParser):
    """
    Day pass info parser
    """

    category = "day-pass"

    def parse(self) -> Sequence[PackageItem]:
        self.base_title = self._parse_base_title()
        return [
            self._parse_adult_item(),
            self._parse_student_item(),
            self._parse_other_item(),
        ]

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='day-pass']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='day-pass']/following-sibling::div[1]")

    def _parse_base_title(self) -> str:
        return self._title_selector.css("h4::text").get()

    def _parse_items(self) -> Sequence[PackageItem]:
        return [
            self._parse_adult_item(),
            self._parse_student_item(),
            self._parse_other_item(),
        ]

    def _parse_tags(self) -> Sequence[str]:
        shoppage_selector = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        )

        tags = [
            shoppage_selector.xpath("./p[1]/text()").get(),
            *shoppage_selector.xpath("./p[3]/text()").getall(),
        ]
        return [tag.strip() for tag in tags]

    def _parse_price_tag(self, index: int) -> str:
        xpath = f".//div[contains(@class, 'shoppage-title')]/*[{index+1}]/text()"
        return self._detail_selector.xpath(xpath).get()

    def _parse_adult_item(self) -> PackageItem:
        return PackageItem(
            title=self.base_title + " Adult",
            category=self.category,
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=1)),
            validity="一日",
        )

    def _parse_student_item(self) -> PackageItem:
        return PackageItem(
            title=self.base_title + " Student",
            category=self.category,
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=2).split()[1]),
            validity="一日",
        )

    def _parse_other_item(self) -> PackageItem:
        shoppage_div_text = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        ).getall()[1]
        shoppage_div = Selector(text=shoppage_div_text)
        sep = "｜"
        title = shoppage_div.xpath(".//*[1]/span/text()").get()
        price_tag = shoppage_div.xpath(".//*[2]/span/text()").get()
        tags_str = shoppage_div.xpath(".//*[3]/span/text()").get()
        return PackageItem(
            title=title.split(sep)[0],
            category="class",
            tags=[title.split(sep)[1], *tags_str.split(sep)],
            **breakdown_price_tag(price_tag),
        )


class JustclimbSharePassParser(BasePassParser):
    """
    Share pass info parser
    """

    def parse(self) -> Sequence[PackageItem]:
        packages = [
            self.ItemParser(
                selector=item,
                base_title=self._parse_base_title(),
                category="share-pass",
            ).parse()
            for item in self._detail_selector.css("div.grve-text")
        ]
        return [package for package in packages if package.price]

    class ItemParser:
        """
        Share pass item info parser
        """

        def __init__(self, selector: Selector, base_title: str, category: str):
            self.selector = selector
            self.base_title = base_title
            self.category = category

        def parse(self) -> PackageItem:
            """Parse share pass item info

            Returns:
                PackageItem: the share pass item info
            """
            return PackageItem(
                title=self._parse_title(),
                category=self.category,
                tags=self._parse_tags(),
                validity=self._parse_validity(),
                **breakdown_price_tag(self._parse_price_tag()),
            )

        def _parse_title(self) -> str:
            return (
                self.base_title
                + " "
                + self.selector.css("div > *:nth-child(1)::text").get()
            )

        def _parse_tags(self) -> Sequence[str]:
            temp = self.selector.xpath(".//p[2]/text()").getall()
            if not temp:
                return []
            return [temp[0].strip()]

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

    def _parse_base_title(self) -> str:
        return self._title_selector.css("h4::text").get()


class JustclimbMonthPassParser(BasePassParser):
    """
    Month pass info parser
    """

    category = "month-pass"

    def parse(self) -> Sequence[PackageItem]:
        self.base_title = self._parse_base_title()
        return [
            self._parse_adult_item(),
            self._parse_student_item(),
        ]

    @property
    def _title_selector(self) -> Selector:
        return self.selector.xpath("//div[@id='monthly-pass']")

    @property
    def _detail_selector(self) -> Selector:
        return self.selector.xpath(
            "//div[@id='monthly-pass']/following-sibling::div[1]"
        )

    def _parse_base_title(self) -> str:
        return self._title_selector.css("h4::text").get()

    def _parse_tags(self) -> str:
        xpath = ".//div[contains(@class, 'shoppage-title')]/p[1]/span/text()"
        return {self._detail_selector.xpath(xpath).get()}

    def _parse_price_tag(self, index: int) -> str:
        xpath = f".//div[contains(@class, 'shoppage-title')]/*[{index+1}]/span/text()"
        return self._detail_selector.xpath(xpath).get()

    def _parse_adult_item(self) -> PackageItem:
        return PackageItem(
            title=self.base_title + " Adult",
            category=self.category,
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=1)),
            validity="一個月",
        )

    def _parse_student_item(self) -> PackageItem:
        return PackageItem(
            title=self.base_title + " Student",
            category=self.category,
            tags=self._parse_tags(),
            **breakdown_price_tag(self._parse_price_tag(index=2).split()[1]),
            validity="一個月",
        )


class JustclimbMembershipParser(BasePassParser):
    """
    Membership package info parser
    """

    def parse(self) -> Sequence[PackageItem]:
        item_selector = self._detail_selector.xpath(
            ".//div[contains(@class, 'shoppage-title')]"
        )
        item = self.ItemParser(selector=item_selector, category="membership").parse()
        # item.title = self._parse_title()
        return [item]

    class ItemParser:
        """
        Jcer package item info parser
        """

        def __init__(self, selector: Selector, category: str):
            self.selector = selector
            self.category = category

        def parse(self) -> PackageItem:
            """Parse jcer pass item info

            Returns:
                PackageItem: the jcer pass item info
            """
            return PackageItem(
                title=self._parse_title(),
                category=self.category,
                tags=self._parse_tags(),
                validity=self._parse_validity(),
                **breakdown_price_tag(self._parse_price_tag()),
            )

        def _parse_title(self) -> str:
            return self.selector.xpath("./*[2]/text()").get()

        def _parse_tags(self) -> Sequence[str]:
            tags = self.selector.xpath("./*[4]/text()").getall()
            return [tag.strip() for tag in tags]

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


class JustclimbPriceSpider(Spider):
    """
    Web spider which crawls passes, package info from JustClimb web page
    """

    name = "justclimb"
    start_urls = ["https://justclimb.hk/price/"]

    def _select_day_passes(self, response: Selector) -> Sequence[PackageItem]:
        parser = JustclimbDayPassParser(selector=response)
        return parser.parse()

    def _select_share_passes(self, response: Selector) -> Sequence[PackageItem]:
        parser = JustclimbSharePassParser(selector=response)
        return parser.parse()

    def _select_month_passes(self, response: Selector) -> Sequence[PackageItem]:
        parser = JustclimbMonthPassParser(selector=response)
        return parser.parse()

    def _select_membership_price(self, response: Selector) -> Sequence[PackageItem]:
        parser = JustclimbMembershipParser(selector=response)
        return parser.parse()

    def parse(self, response: Selector) -> ClimbGym:  # pylint: disable=arguments-differ
        justclimb = ClimbGym(
            name="Just Climb",
            link=self.start_urls[0],
            packages=[
                *self._select_day_passes(response),
                *self._select_share_passes(response),
                *self._select_month_passes(response),
                *self._select_membership_price(response),
            ],
        )
        yield justclimb
