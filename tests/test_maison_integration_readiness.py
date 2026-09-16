from aromatwin.services.maison_integration_readiness import (
    check_maison_integration_readiness as check,
)


def test_missing_profiles_blocks():
    assert check().overall_status == "blocked_missing_approved_profiles"


def test_missing_products_blocks():
    assert check(approved_profile_count=1).overall_status == "blocked_missing_products"


def test_missing_human_review_blocks():
    report = check(approved_profile_count=1, approved_product_count=1, supported_variant_count=1,
                   public_copy_count=1, recommendation_count=1, scentprint_contract_count=1,
                   bundle_count=1, launch_stage_approved=True)
    assert report.overall_status == "blocked_review_required"
