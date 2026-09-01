# CPG Brand & SKU Repository System

A modular, rinse-and-repeat system that turns a CPG holdco name into two
delivered workbooks:

1. **Brand & Positioning Repository** — every owned brand sold in the target
   markets, with category placement, positioning, modeled financials, current
   sentiment, forward focus and innovation areas.
2. **Product Library & In-Market SKU Repository** — every in-market product at
   pack-size grain, with barcode, retailer SKU and source URL.

## Invocation

> "Build a new CPG Client Brand & SKU Repository for **{CLIENT}** covering their
> portfolio of brands and products sold within the **{MARKET}**."

The companion Perplexity skill `cpg-brand-sku-repository` picks this up and runs
all seven phases.

## The governing principle

CPG holdcos report at **segment** level, never at brand level. Brand sales,
marketing spend, share of category, channel split and retailer spend are not
public facts — they must be modeled. So every number in these workbooks carries
a `source_type` (Reported / Derived / Modeled / Mixed) and a `confidence` grade,
and modeled financial cells are visually tinted.

A client who mistakes a modeled figure for a filed one will put it in a board
deck. Preventing that is the point of this system.

## Layout

```
schemas/     Canonical column definitions. Client-agnostic. Do not reorder.
scripts/     estimate_engine.py  Segment revenue -> brand-level estimates
             validate.py         Integrity gates; exits non-zero on blockers
             build_workbooks.py  Styling and README-tab helpers
             assemble.py         Full run entry point
docs/        PROCESS.md          The seven-phase method, end to end
output/      Delivered CSVs and workbooks
```

## Running it

```bash
python scripts/assemble.py
python scripts/validate.py output/sheet1_brand_positioning.csv \
                           output/sheet2_sku_catalog.csv
```

`validate.py` exits non-zero if any blocker fires. Never deliver on a non-zero exit.

## Why the estimates are trustworthy

Allocation weights normalize **within category**, so brand estimates always sum
exactly to the reported category pool. The model can misallocate between brands;
it can never inflate the total beyond what the filing states. Every run prints a
tie-out proving the delta is zero.

Every model parameter is written to an assumptions file with an individual
rationale — 317 of them in the first Colgate-Palmolive run.

## Why the SKU data is trustworthy

Every barcode is validated against its GS1 check digit. Any code that fails is
quarantined to `n.a.` rather than shipped. In the first run, all 470 surviving
barcodes pass, meaning no identifier in the file was invented.

Where a barcode was not exposed by an accessible source, the field reads `n.a.`
A blank is an honest gap. A plausible fabricated UPC would be far worse, because
it silently corrupts every downstream join.

## First run — Colgate-Palmolive, 2026-08-31

| | |
|---|---|
| Brand rows | 58 (31 USA, 27 Canada) |
| Brands excluded with evidence | 24 |
| SKU rows | 2,101 (Oral Care + Personal Care) |
| Verified barcodes | 470, all passing GS1 check digit |
| Model assumptions documented | 317 |
| Tie-out to reported pools | exact |

Phase 2 outstanding: Home Care and Pet Nutrition SKU sweeps.
