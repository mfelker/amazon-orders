__copyright__ = "Copyright (c) 2024-2025 Alex Laird"
__license__ = "MIT"

import logging
import re
from typing import Optional

from bs4 import Tag

from amazonorders import util
from amazonorders.conf import AmazonOrdersConfig
from amazonorders.entity.parsable import Parsable

logger = logging.getLogger(__name__)


class Tracking(Parsable):
    """
    The carrier tracking of an Amazon :class:`~amazonorders.entity.shipment.Shipment`, parsed from the
    page its :attr:`~amazonorders.entity.shipment.Shipment.tracking_link` points to. See
    :func:`~amazonorders.orders.AmazonOrders.get_tracking`.
    """

    def __init__(self,
                 parsed: Tag,
                 config: AmazonOrdersConfig) -> None:
        super().__init__(parsed, config)

        #: The carrier name, e.g. ``UPS``, or ``Amazon`` for Amazon's own delivery network.
        self.carrier: Optional[str] = self.safe_parse(self._parse_carrier)
        #: The carrier's tracking number, e.g. ``1Z999AA10123456784`` or ``TBA000000000000``. Always a ``str``,
        #: since many (e.g. USPS) are all digits and may have leading zeros.
        self.tracking_number: Optional[str] = self.safe_parse(self._parse_tracking_number)
        #: The page's headline status, as Amazon shows it, e.g. ``Delivered January 9``, ``Ordered``, or ``We will
        #: email you as soon as this order ships.`` for a package that has not shipped yet. It tells that case apart
        #: from a page that has carrier tracking, since both leave :attr:`carrier` and :attr:`tracking_number`
        #: ``None`` when Amazon shows no carrier.
        self.status: Optional[str] = self.safe_parse(self._parse_status)

    def __repr__(self) -> str:
        return f"<Tracking: \"{self.carrier} {self.tracking_number}\">"

    def __str__(self) -> str:  # pragma: no cover
        return f"Tracking: {self.carrier} {self.tracking_number}"

    def _parse_tracking_number(self) -> Optional[str]:
        tag = util.select_one(self.parsed, self.config.selectors.FIELD_TRACKING_NUMBER_SELECTOR)
        if not tag:
            return None

        value = tag.text.strip()
        prefix = self.config.selectors.FIELD_TRACKING_NUMBER_PREFIX
        if prefix and prefix in value:
            value = value.split(prefix, 1)[1].strip()
        return value or None

    def _parse_status(self) -> Optional[str]:
        tag = util.select_one(self.parsed, self.config.selectors.FIELD_TRACKING_STATUS_SELECTOR)
        if not tag:
            return None

        # The heading nests its date in a span on its own line, so collapse the whitespace
        return " ".join(tag.get_text(" ").split()) or None

    def _parse_carrier(self) -> Optional[str]:
        value = self.simple_parse(self.config.selectors.FIELD_TRACKING_CARRIER_SELECTOR)
        if not value:
            return None

        return re.sub(self.config.selectors.FIELD_TRACKING_CARRIER_REGEX, "", str(value),
                      flags=re.IGNORECASE).strip() or None
