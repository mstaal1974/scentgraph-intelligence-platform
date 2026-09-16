from aromatwin.services.maison_sync_manifest import build_sync_manifest


def test_manifest_counts_without_external_io(monkeypatch):
    import socket
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    report = build_sync_manifest(products=[1, 2], recommendations=[1], scentprint_matches=[1], bundles=[1])
    assert (report.product_count, report.recommendation_count, report.scentprint_match_count,
            report.bundle_count) == (2, 1, 1, 1)
    assert report.sync_mode == "dry_run"
