from nasdaq_protocols.common import asn1


class Address(asn1.Asn1Sequence):
    Fields = {
        'street': str,
        'city': str,
        'state': str,
        'zipCode': str,
    }

    def has_street(self) -> bool:
        return 'street' in self

    def has_city(self) -> bool:
        return 'city' in self

    def has_state(self) -> bool:
        return 'state' in self

    def has_zipCode(self) -> bool:
        return 'zipCode' in self

    street: str
    city: str
    state: str
    zipCode: str


class CustomerInfo(asn1.Asn1Sequence):
    Fields = {
        'companyName': str,
        'billingAddress': Address,
        'contactPhone': str,
    }

    def has_companyName(self) -> bool:
        return 'companyName' in self

    def has_billingAddress(self) -> bool:
        return 'billingAddress' in self

    def has_contactPhone(self) -> bool:
        return 'contactPhone' in self

    companyName: str
    billingAddress: Address
    contactPhone: str


class Item(asn1.Asn1Sequence):
    Fields = {
        'itemCode': int,
        'color': str,
        'power': int,
    }

    def has_itemCode(self) -> bool:
        return 'itemCode' in self

    def has_color(self) -> bool:
        return 'color' in self

    def has_power(self) -> bool:
        return 'power' in self

    itemCode: int
    color: str
    power: int


class ListOfItems(asn1.Asn1SequenceOf):
    Fields = {
        'Item': Item,
    }

    def has_Item(self) -> bool:
        return 'Item' in self

    Item: list[Item]


class PurchaseOrder(asn1.Asn1Sequence):
    Fields = {
        'dateOfOrder': str,
        'customer': CustomerInfo,
        'items': ListOfItems,
    }

    def has_dateOfOrder(self) -> bool:
        return 'dateOfOrder' in self

    def has_customer(self) -> bool:
        return 'customer' in self

    def has_items(self) -> bool:
        return 'items' in self

    dateOfOrder: str
    customer: CustomerInfo
    items: ListOfItems


class PurchaseQuote(asn1.Asn1Sequence):
    Fields = {
        'quoteId': int,
        'itemName': str,
        'itemPrice': int,
        'itemQty': int,
    }

    def has_quoteId(self) -> bool:
        return 'quoteId' in self

    def has_itemName(self) -> bool:
        return 'itemName' in self

    def has_itemPrice(self) -> bool:
        return 'itemPrice' in self

    def has_itemQty(self) -> bool:
        return 'itemQty' in self

    quoteId: int
    itemName: str
    itemPrice: int
    itemQty: int


class MyCompanyAutomation(asn1.Asn1Choice):
    Fields = {
        'purchaseOrder': PurchaseOrder,
        'purchaseQuote': PurchaseQuote,
    }

    def has_purchaseOrder(self) -> bool:
        return 'purchaseOrder' in self

    def has_purchaseQuote(self) -> bool:
        return 'purchaseQuote' in self

    purchaseOrder: PurchaseOrder
    purchaseQuote: PurchaseQuote


# spec
class MyAsn1app(asn1.Asn1Spec, spec_name='MyAsn1App', spec_pkg_dir='test_asn1_spec.spec'):
    ...
