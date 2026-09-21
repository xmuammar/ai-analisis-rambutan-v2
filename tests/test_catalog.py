from app.ai.catalog import get_algorithm_catalog


def test_algorithm_catalog_reports_runtime_and_model_requirements():
    catalog = get_algorithm_catalog()
    isolation_forest = next(
        item for item in catalog if item["name"] == "Isolation Forest"
    )
    assert isolation_forest["runtime_status"] == "TERPASANG"
    assert isolation_forest["model_status"] == "SIAP DIPAKAI"
    assert any(item["name"] == "LSTM / GRU" for item in catalog)
