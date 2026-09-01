---
name: cpg-brand-sku-repository
description: Build a two-workbook brand and SKU repository for any CPG holdco — Sheet 1 catalogs every owned brand with category, positioning, modeled financials and Q4 focus; Sheet 2 catalogs every in-market product down to pack size, UPC and retailer SKU. Use when the user asks to build a CPG client brand repository, brand and SKU catalog, product library, in-market SKU list, brand footprint, or portfolio catalog for a company such as Colgate-Palmolive, P&G, Unilever, Church & Dwight, Kenvue, Clorox, Henkel, Reckitt, or Kimberly-Clark. Trigger phrases include "build a new CPG Client Brand & SKU Repository for X", "catalog the brand footprint", "what's in market across X brands", "brand and product repository", "SKU repository".
---

# CPG Brand & Product Repository Builder

Produces two deliverables with fixed, client-agnostic schemas so output is
byte-comparable across clients and across reruns for the same client.

- **Workbook 1** — Brand & Positioning Repository (`schemas/sheet1_brand_positioning.yaml`)
- **Workbook 2** — Product Library & In-Market SKU Repository (`schemas/sheet2_sku_catalog.yaml`)

## The one rule that governs everything

CPG holdcos report at **segment** level, never at brand level. Brand sales,
marketing spend, share of category, channel split and retailer spend do not
exist as published facts. They must be **modeled** — and every modeled cell
must be labelled as such.

Never write a modeled number into a cell without setting `source_type` and
`confidence`. A client who mistakes a modeled figure for a reported one will
put it in a board deck. That is the failure mode this skill exists to prevent.

## Invocation

Minimum viable input is the client name. Everything else has a default.

> "Build a new CPG Client Brand & SKU Repository for Church & Dwight covering
> their portfolio of brands and products sold within the US Market"

Confirm only these four before starting, and only if not already stated:

| Decision | Default if unstated |
|---|---|
| Geo markets | USA + Canada |
| Estimate policy | Model all gaps, flag every cell |
| SKU depth | Phase 1 = two largest segments; phase 2 on approval |
| Syndicated data on hand | Assume none; model instead |

If the user has Circana / NIQ / Nielsen / Numerator / SPINS access, stop and
ingest it. Real share data beats every model in this skill.

## Phase 1 — Discovery

Establish the **authoritative brand roster** before any collection. Order of authority:

1. Latest 10-K "Business" section and the boilerplate brand list in the Q4
   earnings release. This is the legally-reviewed roster of brands the company
   currently markets — the single best source and the one to anchor on.
2. Corporate `/brands` page and the country-specific site (`.ca`, `.co.uk`).
   Note: many corporate sites gate content behind a cookie wall and return an
   empty fetch. Fall back to the earnings release boilerplate.
3. Wikipedia's brand list — useful for **discovering** candidates, but it mixes
   discontinued and divested brands with live ones. Never treat as authoritative;
   use it only to generate candidates to verify against a live retail listing.

A brand enters the roster only when a live retail or brand-site listing proves
it is sold in the target geo. Record the divested and discontinued brands you
rejected on a `Divested & Excluded` tab — clients ask, and it demonstrates the
roster is deliberate rather than incomplete.

## Phase 2 — Collection

Run one research subagent per segment, in parallel, with `wide-search` and
`research-assistant` preloaded and `model="claude_opus_5_0"`. Give each the
exact CSV column list from the schema and a target output path. See
`references/collection_playbook.md` for the source hierarchy, the Shopify and
retailer JSON endpoint techniques, and anti-fabrication rules.

**Give every parallel agent its own scratch directory.** Agents share one
workspace, and on the first run two of them independently created
`research/build_csv.py`, silently destroying one agent's builder. Instruct each
to write only inside `research/<segment_slug>/` and to prefix any shared-root
file with its segment name. Only the final CSV goes to the agreed path.

The highest-yield technique by far: DTC and prestige brands run on Shopify, and
`{domain}/products.json?limit=250&page=N` returns the entire catalog with
variants, pack sizes and SKUs as clean JSON. Always try this first.

## Phase 3 — Cleaning and structuring

Run `scripts/validate.py`. It enforces:

- Barcode is EAN-8, UPC-A, EAN-13 or GTIN-14 and passes GS1 check-digit validation.
  `scripts/assemble.py` quarantines any code that fails the check digit, rewriting
  it to `n.a.` — an identifier that cannot be verified is worse than an honest gap,
  because a downstream join will silently match the wrong product
- No duplicates on the dedupe key
- Every Sheet 2 `brand_name` joins to a Sheet 1 brand in the same geo
- Every row has a `product_url`, `source_type` and `confidence`

Reject fabricated identifiers aggressively. A plausible-looking invented UPC is
worse than `n.a.` because it silently corrupts every downstream join.

## Phase 4 — Estimation

Use `scripts/estimate_engine.py`. Reported segment revenue flows down through
country split, then category split, then a brand allocation weight built from
SKU count, price index, distribution breadth and velocity. Weights normalize
within category, so brand estimates always sum exactly to the reported pool —
the model can misallocate between brands but can never inflate the total past
what the filing states.

## Phase 5 — Build and deliver

Use `scripts/build_workbooks.py`. Both workbooks get a `README` tab stating
schema version, run date, sources, and the estimation methodology in plain
language. Sheet 1 gets a `Methodology & Assumptions` tab listing every model
parameter with its rationale. Modeled cells are visually distinguished from
reported cells.

## Phase 6 — Document

Append the run to the process log in the GitHub repo: client, date, roster
size, SKU count, coverage gaps, and anything about the client's digital shelf
that would speed up the next rerun.

## References

- `references/collection_playbook.md` — source hierarchy, endpoint techniques, per-retailer notes
- `references/category_taxonomy.md` — the fixed category/sub-category tree; use it verbatim so clients stay comparable
- `references/client_registry.md` — per-client roster anchors and quirks learned from past runs
