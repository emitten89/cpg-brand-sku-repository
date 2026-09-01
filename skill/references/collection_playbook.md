# Collection Playbook

## Source hierarchy

Work top-down. Each tier is more authoritative than the one below it for the
question it answers.

| Question | Best source | Why |
|---|---|---|
| Which brands does the client own and still market? | Q4 earnings release boilerplate + 10-K Business section | Legally reviewed; excludes divested brands |
| What products does a brand officially offer? | Brand-owned site product listing | Authoritative on the marketed line-up |
| What pack sizes actually reach shelves? | Retailer PDPs | Only place retailer-exclusive sizes and multipacks appear |
| What is the UPC/GTIN? | Retailer PDP "specifications" block, then open barcode DBs | Brand sites rarely publish UPCs |
| What is the brand's share / spend? | Syndicated data if the client has it; otherwise model it | Never invent |

## Technique 1 — Shopify product JSON (highest yield, use first)

Most DTC, prestige and challenger CPG brands run Shopify. The catalog is
exposed as JSON with no auth:

```
https://{brand-domain}/products.json?limit=250&page=1
```

Each product returns `title`, `product_type`, `vendor`, `tags`, and a
`variants[]` array where every variant carries `title` (usually the pack size),
`sku`, `price`, and sometimes `barcode` — which is the real UPC. Page until an
empty array returns. This yields a complete, structured catalog in seconds and
is dramatically more reliable than reading rendered PDPs.

Confirmed working for: EltaMD, PCA SKIN, Tom's of Maine, hello products.
Always probe it before falling back to page-by-page fetching.

## Technique 2 — Retailer structured data

Most retailer PDPs embed `application/ld+json` Product schema containing `gtin13`,
`sku`, `name`, `brand` and `offers`. Fetch with `return_html=True` and parse the
JSON-LD rather than reading prose — far more reliable than text extraction.

Retailer notes:

- **Walmart** — item ID in the URL (`/ip/{slug}/{itemId}`). UPC in the specifications block.
- **Target** — TCIN in the URL; DPCI on the PDP. Target exposes a clean `redsky` API surface.
- **Amazon** — ASIN in the URL. UPC appears in product details for many grocery/HBA items. Heavy bot mitigation; expect partial success and rotate to other retailers rather than hammering.
- **Kroger / CVS / Walgreens** — good UPC exposure, useful for US grocery and drug-channel exclusives.
- **Loblaws / Real Canadian Superstore / Shoppers Drug Mart** — share one platform; article numbers are consistent across banners. Best Canadian source.
- **Walmart.ca / Amazon.ca** — confirm Canadian availability, which frequently differs from US assortment in both pack size and formulation.

## Technique 3 — Open barcode databases

`upcitemdb.com`, `barcodelookup.com`, `go-upc.com`. Use to **fill** a missing UPC
for a product you already confirmed exists, or to **validate** a UPC you captured.
Never use them to discover products — they carry discontinued items indefinitely.

## Anti-fabrication rules

These are non-negotiable. A repository is only worth what its worst row is worth.

1. Never generate a UPC, GTIN, ASIN, TCIN or item ID. Write `n.a.`
2. Never infer a pack size from a product image or a typical size for the category.
3. Never carry a product forward from your own knowledge of the brand. If it was
   not on a page fetched in this session, it does not go in the sheet.
4. Never list a product in Canada because it exists in the US. Canadian assortment
   is genuinely different — verify it on a Canadian retailer.
5. When a page fetch fails, record the gap. Do not silently drop the brand.

## Coverage check before delivery

For each brand, compare your captured SKU count against the count shown on the
brand's own site navigation or a retailer's brand-filtered results page. If you
captured 40 SKUs and Walmart alone shows 120 for that brand, you have a gap —
say so explicitly in the delivery notes rather than presenting the sheet as complete.
