from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    shop: str
    title: str
    image_url: str | None
    product_url: str
    price: int | None  # in `currency`; None when the shop shows no price
    currency: str
    in_stock: bool

    @property
    def price_irt(self) -> int | None:
        # Phase 0 only has toman shops; foreign currencies need /v1/rates later.
        return self.price if self.currency == "IRT" else None
