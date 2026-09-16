from aromatwin.services.product_variant_builder import FORMAT_CONFIG, ProductVariantBuilder


def test_all_formats_and_deterministic_public_variants():
    product = {
        "product_id": "p1",
        "brand_name": "Fiction House",
        "fragrance_name": "Quiet Orbit",
        "product_title": "Quiet Orbit",
    }
    first = ProductVariantBuilder().build([product], public_prices={"10ml_tester": "24.00"})
    second = ProductVariantBuilder().build([product], public_prices={"10ml_tester": "24.00"})
    assert {item["product_format"] for item in first} == set(FORMAT_CONFIG)
    assert [item["sku"] for item in first] == [item["sku"] for item in second]
    assert first[0]["retail_price_public"] == "24.00"
    assert all("cost" not in key and "margin" not in key for item in first for key in item)
