"""
Repository validator. Run before every delivery.

Catches the failure modes that actually destroy a CPG catalog's credibility:
fabricated identifiers, orphaned brands, duplicate rows, and unsourced cells.
Exits non-zero if any BLOCKER fires.
"""
import re
import sys
import pandas as pd

# GS1 permits EAN-8, UPC-A (12), EAN-13 and GTIN-14. Canadian and imported
# items legitimately carry EAN-8/13, so all four lengths are valid.
UPC_RE = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$|^n\.a\.$", re.I)
DIGITS_RE = r"\d{8}|\d{12}|\d{13}|\d{14}"


def gs1_check_digit_ok(code: str) -> bool:
    """Validate an EAN-8 / UPC-A / EAN-13 / GTIN-14 check digit.

    A fabricated identifier almost never passes this. It is the single most
    effective automated defence against invented UPCs.
    """
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return False
    digits = [int(c) for c in code]
    body, check = digits[:-1], digits[-1]
    # Weight 3 applies to the rightmost body digit and alternates leftward.
    total = sum(d * (3 if (len(body) - i) % 2 == 1 else 1) for i, d in enumerate(body))
    return (10 - total % 10) % 10 == check


def validate(sheet1_csv: str, sheet2_csv: str):
    b = pd.read_csv(sheet1_csv, dtype=str).fillna("")
    s = pd.read_csv(sheet2_csv, dtype=str).fillna("")
    blockers, warnings = [], []

    # --- Sheet 2 identifier integrity -------------------------------------
    bad_fmt = s[~s["upc_or_gtin"].str.match(UPC_RE)]
    if len(bad_fmt):
        blockers.append(f"{len(bad_fmt)} rows with malformed upc_or_gtin")

    real = s[s["upc_or_gtin"].str.fullmatch(DIGITS_RE)]
    bad_cd = real[~real["upc_or_gtin"].apply(gs1_check_digit_ok)]
    if len(bad_cd):
        blockers.append(
            f"{len(bad_cd)} UPCs fail the GS1 check digit — likely fabricated: "
            + ", ".join(bad_cd["upc_or_gtin"].head(10))
        )

    # --- Referential integrity -------------------------------------------
    known = set(zip(b["brand_name"].str.lower(), b["geo_market"]))
    orphans = {
        (r["brand_name"], r["geo_market"])
        for _, r in s.iterrows()
        if (r["brand_name"].lower(), r["geo_market"]) not in known
    }
    if orphans:
        blockers.append(f"Sheet 2 brands with no Sheet 1 parent: {sorted(orphans)[:10]}")

    # --- Duplicates -------------------------------------------------------
    key = ["geo_market", "brand_name", "product_name", "pack_size"]
    dupes = s[s.duplicated(subset=key, keep=False)]
    if len(dupes):
        warnings.append(f"{len(dupes)} duplicate rows on {key}")

    # --- Provenance completeness -----------------------------------------
    for col in ("product_url", "source_type", "confidence"):
        n = (s[col].str.strip() == "").sum()
        if n:
            blockers.append(f"{n} Sheet 2 rows missing {col}")

    for col in ("source_type", "confidence"):
        n = (b[col].str.strip() == "").sum()
        if n:
            blockers.append(f"{n} Sheet 1 rows missing {col}")

    # --- Coverage sanity --------------------------------------------------
    for (brand, geo), grp in s.groupby(["brand_name", "geo_market"]):
        if len(grp) < 3:
            warnings.append(f"Thin coverage: {brand} / {geo} has only {len(grp)} SKUs")

    upc_fill = (real.shape[0] / max(len(s), 1)) * 100
    print(f"Sheet 1: {len(b)} brand rows | Sheet 2: {len(s)} SKU rows")
    print(f"UPC fill rate: {upc_fill:.1f}%")
    print(f"Modeled cells in Sheet 1: {(b['source_type'] == 'Modeled').sum()}")

    for w in warnings:
        print(f"  WARN    {w}")
    for x in blockers:
        print(f"  BLOCKER {x}")

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(validate(sys.argv[1], sys.argv[2]))
