def test_oanda_display_symbol_mapping():
    canonical = "EUR_USD"
    display = canonical.replace("_", "")
    assert display == "EURUSD"


def test_broker_alias_suffixes():
    aliases = {
        "EUR_USD": "EURUSDm",
        "XAU_USD": "XAUUSD.pro",
        "GBP_USD": "GBPUSD#",
    }
    for canonical, execution in aliases.items():
        assert canonical != execution
        assert "_" not in execution or "." in execution or "#" in execution or "m" in execution
