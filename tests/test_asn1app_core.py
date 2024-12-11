import pytest

from nasdaq_protocols.asn1_app import Asn1SoupClientSession, Asn1Spec


@pytest.mark.parametrize("params", [
    {},
    {'spec_name': 'TestAsn1Spec'},
    {'spec_pkg_dir': 'test.spec'}
])
def test__asn1app__core__invalid_spec_definition(params):
    with pytest.raises(AttributeError) as e:
       class TestAsn1Spec(Asn1Spec, **params):
            ...

    assert str(e.value) == "Missing spec_name or spec_pkg_dir"


def test__asn1app__core__valid_session_definition():
    class TestAsn1MessagePdu:
        ...

    class TestSoupAsn1Session(Asn1SoupClientSession, asn1_message=TestAsn1MessagePdu):
        ...

    assert TestSoupAsn1Session.Asn1Message == TestAsn1MessagePdu


def test__asn1app__core__invalid_session_definition__throws_error():
    with pytest.raises(AttributeError) as e:
        class TestSoupAsn1Session(Asn1SoupClientSession):
            ...

    assert str(e.value) == "Missing 'asn1_message' attribute"