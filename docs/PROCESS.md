# CPG Brand & Product Repository Creation — Process Documentation

The end-to-end method for turning a CPG holdco name into two delivered
workbooks. Written to be run by anyone, for any client, with the same result.

**Invocation:** *"Build a new CPG Client Brand & SKU Repository for {CLIENT}
covering their portfolio of brands and products sold within the {MARKET}."*

---

## The problem this process solves

A brand and SKU repository sounds like a collection exercise. It is really a
**provenance** exercise. Anyone can produce a spreadsheet with a brand name and
a revenue figure next to it. The hard part is that in a CPG portfolio:

- Brand-level financials **do not exist publicly.** Holdcos report by segment.
- The brand roster is **contested.** Corporate sites, Wikipedia and filings
  disagree, and all three carry divested brands.
- SKU-level truth lives behind **bot mitigation** at exactly the retailers that
  matter most.

So the process is built around one principle: *a number is only as useful as the
reader's ability to tell where it came from.* Every phase exists to preserve
that traceability.

---

## Phase 1 — Discovery

**Goal:** an authoritative, defensible brand roster before a single product page
is opened.

| Step | Action | Output |
|---|---|---|
| 1.1 | Pull the latest 10-K Business section and the Q4 earnings release | Reported segment revenue, regional revenue, advertising total |
| 1.2 | Extract the brand boilerplate from the earnings release | Candidate roster (legally reviewed, excludes divested brands) |
| 1.3 | Cross-check against the corporate `/brands` page and country sites | Roster additions; note any cookie-walled pages and move on |
| 1.4 | Add Wikipedia candidates as *hypotheses only* | Expanded candidate list, unverified |
| 1.5 | Verify each candidate against a live retail listing in the target geo | Confirmed roster + rejected list with evidence |

**Deliverable:** confirmed roster, plus `sheet1_excluded_brands.csv` recording
every rejected brand with its exclusion reason and evidence URL.

The exclusion file matters more than it looks. A client reading "where is
Sanex?" needs to see that Sanex was considered and refuted, not overlooked. It
converts an apparent gap into evidence of rigour.

**Gate:** do not proceed until every brand in the roster has a URL proving it is
on sale in the target market.

---

## Phase 2 — Collection

**Goal:** exhaustive product capture at pack-size grain, with every row traceable.

One research subagent per reporting segment, run in parallel, each with
`wide-search` and `research-assistant` preloaded, each given the literal CSV
column list and its own scratch directory.

Source order, most authoritative first:

1. **Shopify catalog JSON** — `{domain}/products.json?limit=250&page=N`. Returns
   every product with its variants, pack sizes, SKUs and often barcodes. Try this
   before anything else; it is an order of magnitude faster and cleaner than
   reading rendered pages.
2. **Manufacturer barcode surfaces** — SmartLabel URLs that encode the GTIN in
   the path, `data-ean` attributes, JSON-LD `Product` blocks.
3. **Brand-owned product listings** — authoritative on the marketed line-up.
4. **Retailer PDPs** — the only place retailer-exclusive pack sizes appear.
5. **Regulatory registries** — openFDA NDC for Rx and OTC monograph products;
   Health Canada DHPP for Canadian drug status.
6. **Open barcode databases** — to *fill* a missing identifier on a product
   already confirmed to exist. Never to discover products; they carry
   discontinued items indefinitely.

**Anti-fabrication rules.** Non-negotiable, because one invented identifier
destroys trust in all 2,000 rows:

- Never generate a UPC, GTIN, ASIN, TCIN or item ID. Write `n.a.`
- Never infer pack size from an image or a category norm.
- Never carry a product forward from model knowledge. Not fetched, not included.
- Never assume Canadian availability from US availability. Verify separately.
- Record every blocked source. A disclosed gap is a finding; a silent one is a defect.

**Deliverable:** one CSV per segment plus a notes file logging sources fetched,
sources blocked, and field conventions used.

---

## Phase 3 — Cleaning and structuring

**Goal:** one clean row per real-world thing.

| Step | Rule |
|---|---|
| Merge | Concatenate segment CSVs; assert identical column order |
| Dedupe | Key is `geo_market + brand_name + product_name + pack_size`. When duplicates collide, keep the **richest** record — score by barcode present (4), retailer SKU present (2), pack size present (1) |
| Quarantine | Recompute the GS1 check digit on every barcode. Any failure is rewritten to `n.a.` and logged |
| Enrich | Derive `variant_flavor_scent` and `form_factor` conservatively from the product name; return `n.a.` rather than guessing, because a wrong variant splits one product into two |
| Key | Assign a stable `sku_record_id` |

The dedupe scoring rule is the quiet workhorse. Naive `drop_duplicates` keeps
whichever row happened to come first, frequently discarding the only copy that
carried a barcode. Scoring preserves the most useful record every time.

**Deliverable:** `sheet2_sku_catalog.csv`, deduped and keyed.

---

## Phase 4 — Estimation

**Goal:** fill the columns the client asked for that no one publishes, without
ever passing an estimate off as a fact.

The allocation chain, each step labelled with its evidence grade:

```
Reported segment x region net sales              [Reported]
  -> country split (US vs CA)                    [Modeled: country_weight]
    -> category split within country             [Modeled: category_weight]
      -> brand split within category             [Modeled: assortment_weight]
```

Brand allocation weight:

```
w_b = sku_count_b^0.72 * price_index_b^0.45 * distribution_breadth_b * velocity_index_b
```

`sku_count` comes empirically from the Phase 3 catalog — which is why collection
must precede estimation. The exponents are below 1 because both SKU count and
premium pricing have diminishing returns on revenue share.

**The safety property.** Weights normalize *within* category, so brand estimates
always sum exactly to the reported category pool. The model can misallocate
between brands; it can never inflate the total past what the filing states. Every
run must print a tie-out showing the delta is zero.

Advertising is allocated proportional to estimated sales, tilted by publicly
stated investment priorities, then renormalized to the reported advertising line.

Channel split uses category-level ecommerce penetration benchmarks, discounted
for Canada. Replace with syndicated channel data the moment the client has any.

Every parameter chosen is written to `sheet1_assumptions.csv` with an individual
rationale. A model no one can audit is a liability.

**Deliverable:** `sheet1_brand_positioning.csv` + `sheet1_assumptions.csv`.

---

## Phase 5 — Validation

`scripts/validate.py`, exits non-zero on any blocker.

| Check | Severity |
|---|---|
| Barcode format is EAN-8 / UPC-A / EAN-13 / GTIN-14 or `n.a.` | Blocker |
| Barcode passes GS1 check digit | Blocker |
| Every Sheet 2 brand joins to a Sheet 1 brand in the same geo | Blocker |
| Every row carries `product_url`, `source_type`, `confidence` | Blocker |
| No duplicates on the dedupe key | Warning |
| Brand-market pairs with fewer than 3 SKUs | Warning |

Warnings are not noise — each one should be either fixed or explicitly explained
in the delivery note. A thin brand is sometimes genuinely thin, and sometimes a
blocked retailer.

---

## Phase 6 — Build and deliver

`scripts/assemble.py` produces both workbooks.

Every workbook opens on a **README tab** that states, before the reader reaches
a single number: what the file is, which figures are reported versus modeled,
how the estimates were built, what would improve them, and what the known gaps
are. Financial cells are tinted warm for modeled and cool for reported, so the
distinction survives someone copying a single cell into a deck.

| Workbook | Tabs |
|---|---|
| Brand Positioning | README · Brand Positioning · Methodology & Assumptions · Divested & Excluded |
| SKU Repository | README · SKU Catalog · Coverage & Gaps |

The Coverage & Gaps tab reports SKU count, barcode fill rate and retailer breadth
per brand and market. It is what stops a reader treating a blocked-retailer gap
as a small assortment.

---

## Phase 7 — Document and learn

Append to `references/client_registry.md` in the skill: reported anchors, roster
quirks, brands refuted with evidence, high-yield sources discovered, sources that
blocked, and outstanding phases. The next run for that client starts from this
file and skips an hour of rediscovery.

---

## Reusability

The system is client-agnostic by construction:

- **Schemas** (`schemas/*.yaml`) are fixed and carry no client-specific fields.
- **Taxonomy** (`references/category_taxonomy.md`) is fixed, so two clients'
  repositories are directly comparable.
- **Estimate engine** takes reported anchors as input rather than hardcoding them.
- **Client specifics** live only in `references/client_registry.md`.

Adding a client means adding a registry entry. Nothing else changes.

## Known limitations

1. Brand-level financials are modeled. Syndicated POS data replaces them without
   any schema change.
2. Major retailers block automated collection; assortment from those retailers is
   under-represented and quantified in Coverage & Gaps.
3. Barcode fill rate is roughly 22% because most retailers no longer publish UPCs
   on product pages. A GS1 or licensed retailer feed would raise this sharply.
4. Sub-brand rows are allocated *inside* their master brand row and excluded from
   geo totals to prevent double-counting. Sum the master rows only.
