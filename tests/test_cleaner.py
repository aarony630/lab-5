import pytest
import pandas as pd
from cleaner import shorten_name, categorize_item, process_amazon_csv


def test_shorten_name_strips_after_comma():
    assert shorten_name("Anker 7-Port USB 3.0 Data Hub, with 36W Power Adapter") == "Anker 7-Port USB 3.0 Data Hub"


def test_shorten_name_strips_after_open_paren():
    assert shorten_name("Logitech MK270 Wireless Keyboard (2.4 GHz, Black, USB)") == "Logitech MK270 Wireless Keyboard"


def test_shorten_name_strips_after_open_bracket():
    assert shorten_name("Hatchbox PLA Filament [1.75mm, Black, 1kg Spool]") == "Hatchbox PLA Filament"


def test_shorten_name_truncates_to_40_chars():
    assert len(shorten_name("A" * 100)) <= 40


def test_shorten_name_collapses_extra_spaces():
    assert shorten_name("Brand   Model   X") == "Brand Model X"


def test_shorten_name_already_short_unchanged():
    assert shorten_name("Short Name") == "Short Name"


def test_shorten_name_handles_none():
    assert shorten_name(None) == ""


def test_categorize_it_by_usb():
    assert categorize_item("Anker USB 3.0 Hub") == "IT"


def test_categorize_it_by_keyboard():
    assert categorize_item("Logitech MK270 Wireless Keyboard") == "IT"


def test_categorize_mksp_by_filament():
    assert categorize_item("Hatchbox PLA Filament 1.75mm") == "MKSP"


def test_categorize_mksp_by_arduino():
    assert categorize_item("Arduino Uno Rev3 Microcontroller") == "MKSP"


def test_categorize_unassigned_no_match():
    assert categorize_item("Mystery Item 9000 Pro") == "Unassigned"


def test_categorize_case_insensitive():
    assert categorize_item("HDMI CABLE 6FT") == "IT"


def _sample_df():
    return pd.DataFrame({
        "Product Name": [
            "Logitech MK270 Wireless Keyboard (Black, USB)",
            "Hatchbox PLA Filament 1.75mm, Black, 1kg",
        ],
        "ASIN": ["B00BF9HCOW", "B01EKEMDA6"],
        "Order ID": ["123-456-789", "987-654-321"],
    })


def test_process_returns_expected_columns():
    result = process_amazon_csv(_sample_df())
    assert list(result.columns) == [
        "Original Name", "Product Name", "Category",
        "Asset ID", "Product Number", "Import Date",
    ]


def test_process_asset_ids_sequential():
    result = process_amazon_csv(_sample_df())
    assert result["Asset ID"].tolist() == ["ASSET-0001", "ASSET-0002"]


def test_process_product_number_from_asin():
    result = process_amazon_csv(_sample_df())
    assert result["Product Number"].tolist() == ["B00BF9HCOW", "B01EKEMDA6"]


def test_process_names_are_shortened():
    result = process_amazon_csv(_sample_df())
    assert result["Product Name"].iloc[0] == "Logitech MK270 Wireless Keyboard"
    assert result["Product Name"].iloc[1] == "Hatchbox PLA Filament 1.75mm"


def test_process_raises_on_missing_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        process_amazon_csv(pd.DataFrame({"Wrong": ["test"]}))


def test_process_preserves_original_name():
    result = process_amazon_csv(_sample_df())
    assert "Logitech MK270 Wireless Keyboard (Black, USB)" in result["Original Name"].values
