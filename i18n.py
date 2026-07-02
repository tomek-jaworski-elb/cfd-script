"""UI string translations (Polish / English)."""

STRINGS = {
    "en": {
        "page_title": "Adtran (ADTN) CFD Tracker",
        "settings_header": "Settings",
        "language_label": "Language",
        "ticker_label": "Ticker",
        "overnight_rate_label": "Overnight financing rate (annual %)",
        "overnight_rate_help": "Broker-specific annual rate applied nightly to each tranche's notional value.",
        "profit_target_label": "Target profit (%)",
        "refresh_interval_label": "Auto-refresh interval (seconds)",
        "refresh_interval_help": (
            "How often the live price refreshes automatically. Lower values query "
            "Yahoo Finance more often; 60s is a reasonable default."
        ),
        "save_settings_button": "Save settings",
        "settings_saved": "Saved.",
        "cfd_note": (
            "CFD quote from your broker includes its own spread/financing terms "
            "and will differ slightly from this exchange price. This app uses the "
            "exchange price as a proxy for cost calculations."
        ),
        "live_price_header": "Live price",
        "price_metric_label": "{ticker} price",
        "source_metric_label": "Source",
        "as_of_metric_label": "As of",
        "seconds_ago_suffix": "{s}s ago",
        "price_fetch_error": "Could not fetch live price: {error}",
        "manual_price_label": "Enter current price manually",
        "refresh_price_button": "Refresh price",
        "next_update_metric": "Next update in",
        "market_open": "Open",
        "market_closed": "Closed",
        "market_hours_caption": (
            "Regular session: {open}-{close} (Warsaw time), Mon-Fri. "
            "Exchange holidays are not accounted for."
        ),
        "add_transaction_header": "Add transaction (tranche)",
        "date_label": "Date",
        "quantity_label": "Quantity",
        "price_per_share_label": "Price per share",
        "commission_label": "Commission",
        "add_button": "Add",
        "qty_price_error": "Quantity and price must be > 0.",
        "transaction_added": "Transaction added.",
        "no_transactions_info": "No transactions yet. Add your two tranches above.",
        "tranches_header": "Tranches",
        "id_col": "ID",
        "nights_held_col": "Nights held",
        "overnight_fee_col": "Overnight fee",
        "delete_select_label": "Delete a transaction (select id)",
        "delete_button": "Delete selected transaction",
        "summary_header": "Position summary",
        "total_qty_metric": "Total quantity",
        "avg_entry_price_metric": "Avg entry price",
        "total_commission_metric": "Total commission",
        "overnight_fee_metric": "Accrued overnight fee",
        "total_invested_metric": "Total invested (incl. costs)",
        "breakeven_metric": "Breakeven price",
        "target_price_metric": "Target price (+{pct:g}%)",
        "pnl_metric": "Unrealized P/L at current price",
        "pnl_pln_metric": "Unrealized P/L in PLN",
        "usd_pln_rate_metric": "USD/PLN rate",
        "pln_rate_fetch_error": "Could not fetch USD/PLN rate: {error}",
    },
    "pl": {
        "page_title": "Adtran (ADTN) CFD Tracker",
        "settings_header": "Ustawienia",
        "language_label": "Język",
        "ticker_label": "Ticker",
        "overnight_rate_label": "Stawka overnight (roczna %)",
        "overnight_rate_help": "Roczna stawka brokera naliczana co noc od wartości nominalnej każdej transzy.",
        "profit_target_label": "Docelowy zysk (%)",
        "refresh_interval_label": "Interwał auto-odświeżania (sekundy)",
        "refresh_interval_help": (
            "Jak często kurs odświeża się automatycznie. Niższe wartości częściej "
            "odpytują Yahoo Finance; 60s to rozsądna wartość domyślna."
        ),
        "save_settings_button": "Zapisz ustawienia",
        "settings_saved": "Zapisano.",
        "cfd_note": (
            "Kurs CFD u brokera zawiera własny spread/warunki finansowania i będzie "
            "się nieco różnić od kursu giełdowego. Ta aplikacja używa kursu giełdowego "
            "jako proxy do kalkulacji kosztów."
        ),
        "live_price_header": "Kurs na żywo",
        "price_metric_label": "Kurs {ticker}",
        "source_metric_label": "Źródło",
        "as_of_metric_label": "Stan na",
        "seconds_ago_suffix": "{s}s temu",
        "price_fetch_error": "Nie udało się pobrać kursu: {error}",
        "manual_price_label": "Wpisz aktualny kurs ręcznie",
        "refresh_price_button": "Odśwież kurs",
        "next_update_metric": "Następna aktualizacja za",
        "market_open": "Otwarta",
        "market_closed": "Zamknięta",
        "market_hours_caption": (
            "Sesja regularna: {open}-{close} (czas warszawski), pon.-pt. "
            "Święta giełdowe nie są uwzględniane."
        ),
        "add_transaction_header": "Dodaj transakcję (transza)",
        "date_label": "Data",
        "quantity_label": "Ilość",
        "price_per_share_label": "Cena za akcję",
        "commission_label": "Prowizja",
        "add_button": "Dodaj",
        "qty_price_error": "Ilość i cena muszą być > 0.",
        "transaction_added": "Transakcja dodana.",
        "no_transactions_info": "Brak transakcji. Dodaj swoje dwie transze powyżej.",
        "tranches_header": "Transze",
        "id_col": "ID",
        "nights_held_col": "Liczba nocy",
        "overnight_fee_col": "Opłata overnight",
        "delete_select_label": "Usuń transakcję (wybierz id)",
        "delete_button": "Usuń wybraną transakcję",
        "summary_header": "Podsumowanie pozycji",
        "total_qty_metric": "Łączna ilość",
        "avg_entry_price_metric": "Średnia cena zakupu",
        "total_commission_metric": "Suma prowizji",
        "overnight_fee_metric": "Naliczona opłata overnight",
        "total_invested_metric": "Zainwestowano łącznie (z kosztami)",
        "breakeven_metric": "Cena progu rentowności",
        "target_price_metric": "Cena docelowa (+{pct:g}%)",
        "pnl_metric": "Niezrealizowany zysk/strata przy aktualnym kursie",
        "pnl_pln_metric": "Niezrealizowany zysk/strata w PLN",
        "usd_pln_rate_metric": "Kurs USD/PLN",
        "pln_rate_fetch_error": "Nie udało się pobrać kursu USD/PLN: {error}",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    template = STRINGS.get(lang, STRINGS["en"]).get(key, key)
    return template.format(**kwargs) if kwargs else template
