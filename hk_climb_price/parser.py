from abc import ABC, abstractmethod
from typing import Sequence

from scrapy import Selector

from hk_climb_price.items import PackageItem


class BasePassParser(ABC):
    """
    Base class of a climb pass parser
    """

    def __init__(self, selector: Selector):
        self.selector = selector

    @abstractmethod
    def parse(self) -> Sequence[PackageItem]:
        """
        Parse pass info from selector
        """
        raise NotImplementedError("parse() method is not implemented")
