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
            "How often the live price refreshes automatically during market hours. "
            "Outside market hours only the USD/PLN rate keeps auto-refreshing. "
            "Lower values query Yahoo Finance more often; 60s is a reasonable default."
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
        "seconds_ago_suffix": "{s}s ago",
        "live_clock_text": "As of {time} ({ago}) · next update in {left}",
        "market_closed_refresh_caption": (
            "Price as of {time} · market closed - auto-refresh updates only the USD/PLN rate"
        ),
        "prev_value_caption": "Previous: {value} at {time}",
        "no_change_delta": "no change",
        "price_fetch_error": "Could not fetch live price: {error}",
        "manual_price_label": "Enter current price manually",
        "refresh_price_button": "Refresh price",
        "market_open": "Open",
        "market_closed": "Closed",
        "market_closed_holiday": "Closed — {holiday}",
        "market_hours_caption": (
            "Regular session: {open}-{close} (Warsaw time), Mon-Fri. "
            "NYSE holidays and early closes (13:00 ET) are accounted for."
        ),
        "chart_header": "Price chart",
        "chart_range_label": "Chart range",
        "chart_time_label": "Time",
        "chart_price_label": "Price",
        "chart_breakeven_label": "Breakeven",
        "chart_caption": "Source: {source} · interval {interval} · times in Warsaw time",
        "chart_no_data": "No trades in this range — market closed (weekend or holiday). Pick a wider range.",
        "history_fetch_error": "Could not fetch price history: {error}",
        "add_transaction_header": "Add transaction (tranche)",
        "date_label": "Date",
        "quantity_label": "Quantity",
        "price_per_share_label": "Price per share",
        "commission_label": "Commission",
        "add_button": "Add",
        "qty_price_error": "Quantity and price must be > 0.",
        "transaction_added": "Transaction added.",
        "no_transactions_info": "No transactions yet. Add your first tranche below.",
        "tranches_header": "Tranches",
        "id_col": "ID",
        "nights_held_col": "Nights held",
        "overnight_fee_col": "Overnight fee",
        "edit_tranche_title": "Edit tranche",
        "edit_button": "Edit",
        "delete_button": "Delete",
        "select_row_hint": "Select a row to edit or delete a tranche.",
        "save_button": "Save",
        "summary_header": "Position summary",
        "position_group_header": "Position",
        "costs_group_header": "Costs",
        "price_levels_group_header": "Price levels",
        "pnl_group_header": "Profit & loss",
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
        "usd_pln_rate_caption": "USD/PLN rate: {rate} ({source}), fetched at {time}",
        "pln_rate_fetch_error": "Could not fetch USD/PLN rate: {error}",
        "app_version_caption": "Version {version} ({date})",
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
            "Jak często kurs odświeża się automatycznie w godzinach sesji. Poza sesją "
            "automatycznie odświeża się tylko kurs USD/PLN. Niższe wartości częściej "
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
        "seconds_ago_suffix": "{s}s temu",
        "live_clock_text": "Stan na {time} ({ago}) · następna aktualizacja za {left}",
        "market_closed_refresh_caption": (
            "Kurs z {time} · rynek zamknięty - automatycznie odświeża się tylko kurs USD/PLN"
        ),
        "prev_value_caption": "Poprzednio: {value} o {time}",
        "no_change_delta": "bez zmian",
        "price_fetch_error": "Nie udało się pobrać kursu: {error}",
        "manual_price_label": "Wpisz aktualny kurs ręcznie",
        "refresh_price_button": "Odśwież kurs",
        "market_open": "Otwarta",
        "market_closed": "Zamknięta",
        "market_closed_holiday": "Zamknięta — {holiday}",
        "market_hours_caption": (
            "Sesja regularna: {open}-{close} (czas warszawski), pon.-pt. "
            "Uwzględnia święta NYSE i sesje skrócone (do 13:00 ET)."
        ),
        "chart_header": "Wykres kursu",
        "chart_range_label": "Zakres wykresu",
        "chart_time_label": "Czas",
        "chart_price_label": "Kurs",
        "chart_breakeven_label": "Próg rentowności",
        "chart_caption": "Źródło: {source} · interwał {interval} · czasy warszawskie",
        "chart_no_data": "Brak notowań w tym zakresie — rynek zamknięty (weekend lub święto). Wybierz szerszy zakres.",
        "history_fetch_error": "Nie udało się pobrać historii kursu: {error}",
        "add_transaction_header": "Dodaj transakcję (transza)",
        "date_label": "Data",
        "quantity_label": "Ilość",
        "price_per_share_label": "Cena za akcję",
        "commission_label": "Prowizja",
        "add_button": "Dodaj",
        "qty_price_error": "Ilość i cena muszą być > 0.",
        "transaction_added": "Transakcja dodana.",
        "no_transactions_info": "Brak transakcji. Dodaj pierwszą transzę poniżej.",
        "tranches_header": "Transze",
        "id_col": "ID",
        "nights_held_col": "Liczba nocy",
        "overnight_fee_col": "Opłata overnight",
        "edit_tranche_title": "Edytuj transzę",
        "edit_button": "Edytuj",
        "delete_button": "Usuń",
        "select_row_hint": "Zaznacz wiersz, aby edytować lub usunąć transzę.",
        "save_button": "Zapisz",
        "summary_header": "Podsumowanie pozycji",
        "position_group_header": "Pozycja",
        "costs_group_header": "Koszty",
        "price_levels_group_header": "Poziomy cenowe",
        "pnl_group_header": "Zysk / strata",
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
        "usd_pln_rate_caption": "Kurs USD/PLN: {rate} ({source}), pobrano o {time}",
        "pln_rate_fetch_error": "Nie udało się pobrać kursu USD/PLN: {error}",
        "app_version_caption": "Wersja {version} ({date})",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    template = STRINGS.get(lang, STRINGS["en"]).get(key, key)
    return template.format(**kwargs) if kwargs else template
