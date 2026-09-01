# Client Registry

Per-client anchors and quirks learned from completed runs. Read the relevant
entry before starting a rerun — it will save an hour of rediscovery.

---

## Colgate-Palmolive (CL) — first run 2026-08-31

**Roster anchor.** The Q4 earnings release boilerplate is the best source. The
corporate `/brands` pages on both `.com` and `.ca` sit behind a cookie wall and
return empty content on fetch — do not waste cycles on them.

**Reported anchors, FY2025:** worldwide net sales $20,382M · Oral, Personal &
Home Care $15,769M · Pet Nutrition $4,613M · North America division $4,045M ·
worldwide advertising $2,703M.

Critical subtlety: the North America division figure covers Oral/Personal/Home
Care **only**. Hill's North America sits inside the Pet Nutrition segment and
must be estimated separately (US is roughly 60-65% of global Hill's).

**Reported share figures** — rare and valuable, from prepared management
remarks: US toothpaste value share 31.9% YTD Q2 2026 (33.3% FY2025); US manual
toothbrush 43.4% YTD (41.3% FY2025). Note the company states its share data
**excludes eCommerce, club and discounter channels**, so it understates true share.

**Brands that look in-portfolio but are NOT sold in US/CA.** Verify before
re-including; all were refuted with evidence in run 1:
Sorriso (Brazil), Sanex and Protex (Europe/LatAm), elmex and meridol
(marketplace imports by third-party sellers only, not company distribution),
Duraphat in Canada (DIN 02232201 cancelled pre-market 2017), Palmolive personal
care (dish only in North America), Arctic Power (Canada-only), Fleecy
(Canada-only in practice despite appearing on the US corporate roster).

**Brands in retreat** — recheck status each run: Colgate hum (replacement heads
sold out), Filorga USA (`us.filorga.com` no longer processing direct orders),
Colgate Renewal (rebranded into Optic White Renewal; US listing unavailable).

**High-yield sources found.** Colgate SmartLabel URLs encode the GTIN directly
in the path (`colgatepalmolive.com/en-us/smartlabel/<GTIN>`) — manufacturer-
authoritative barcodes for free. Colgate PDPs expose barcodes in a `data-eans`
attribute. Tom's of Maine, hello, EltaMD and PCA SKIN all serve full Shopify
`/products.json` catalogs. openFDA NDC covers the Rx and OTC monograph oral care
line. Well.ca and Voila.ca are the most accessible Canadian sources.

**Blocked sources.** Walmart (307), Amazon (503), Kroger, Walgreens, Loblaws and
Real Canadian Superstore (Akamai 403, no product sitemap), barcodelookup (403),
upcitemdb (trial rate limit — contributed nothing, skip it). Target's search API
IP-blocks partway through a sweep. Shoppers Drug Mart has a 2026 GTIN feed that
timed out; it is the single highest-value retry target for Canadian coverage.

**Run 1 output:** 58 brand rows (31 USA, 27 Canada), 24 excluded brands,
2,101 SKU rows (Oral + Personal Care only). Home Care and Pet Nutrition SKUs
are the outstanding phase 2.
