"""Build Sheet 1 (Brand Positioning) for Colgate-Palmolive USA/Canada.

Pure transformation of /home/user/workspace/research/brands_positioning.md plus
the two SKU inventories. All modeled numbers run through estimate_engine.
"""
import csv, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estimate_engine import (country_split, allocate_category, allocate_advertising,
                             channel_split, confidence_for)

RES = "/home/user/workspace/research"
OUT = "/home/user/workspace/cpg-repo/output"
os.makedirs(OUT, exist_ok=True)
DATE = "2026-08-31"
SEG_OPHC = "Oral, Personal and Home Care"
SEG_PET = "Pet Nutrition"

# ---------------------------------------------------------------- URLs
U = dict(
    tenk="https://investor.colgatepalmolive.com/static-files/c4a7e20c-1aa8-4bb1-bd4b-74755c99688f",
    ar25="https://investor.colgatepalmolive.com/static-files/4298e292-4aaf-4b10-8953-aad27c1065d7",
    q226="https://investor.colgatepalmolive.com/news-releases/news-release-details/colgate-announces-2nd-quarter-2026-results",
    rem226="https://investor.colgatepalmolive.com/static-files/ca92df4c-8d85-4df1-bf67-c2b76b8b36fe",
    remfy25="https://investor.colgatepalmolive.com/static-files/243eca3f-093a-45e8-966a-6929c7673653",
    call226="https://finance.yahoo.com/quote/CL/earnings/CL-Q2-2026-earnings_call-659046.html",
    reuters="https://www.reuters.com/business/retail-consumer/colgate-palmolive-reaffirms-annual-sales-forecast-weak-north-america-demand-2026-07-31/",
    slides226="https://www.investing.com/news/company-news/colgatepalmolive-q2-2026-slides-strong-results-fuel-raised-guidance-93CH-4828636",
)

# ---------------------------------------------------------------- per-brand model-input rationales
def _e(price, dist, vel, ad):
    return dict(price=price, dist=dist, vel=vel, ad=ad)

EVID = {
 "Colgate": _e(
  "Index 1.00 by definition: Colgate is the category benchmark, with mass shelf prices of $1.99-$7.99 at Target and CAD $0.98-$5.97 at Walmart Canada.",
  "1.00 - the only brand in the portfolio present at every tracked retailer (Walmart, Target, CVS, Amazon, DTC in the US; Walmart Canada, Well.ca, Amazon.ca in Canada).",
  "1.25-1.30 - highest turn in the portfolio: reported 31.9% US toothpaste and 43.4% US manual toothbrush value share, and review counts up to 2,392 on a single Canadian brand page.",
  "1.25-1.30 - management named North America oral care as the priority for stepped-up advertising and premium 2026/2027 innovation."),
 "Colgate Total": _e(
  "1.10 - therapeutic tier priced above the Colgate core line at Target ($1.99-$7.99 range top end).",
  "1.00 - full national distribution in both markets, including a CDA seal listing in Canada.",
  "1.05 - historically the largest single Colgate portfolio by SKU count (163 US SKUs) but currently rebuilding share after the reformulation issue.",
  "1.25-1.30 - Total carries the flagship national creative ('One Step Ahead') and is the named share-recovery priority."),
 "Colgate Optic White": _e(
  "1.35 - premium whitening tier; Pro Series is the most advanced (and highest-priced) formula in the line.",
  "0.95 - broad mass distribution but slightly narrower than the core line in drug/value channels.",
  "1.10 - whitening is the stated share-recovery vehicle and the second-largest Colgate portfolio by SKU count (132 US SKUs).",
  "1.30-1.35 - 'The Science of WOW' campaign with 100+ assets plus the Purple and Vitamin C launches make this the most heavily supported sub-brand."),
 "Colgate Optic White Renewal": _e(
  "1.60 - premium enamel-plus-whitening tier including 3% hydrogen peroxide pens with 35 nightly treatments.",
  "0.70 - Canada-only active line (the standalone US Renewal line is withdrawn), carried at Walmart Canada and colgate.com/en-ca.",
  "0.85 - premium price point limits turn relative to core toothpaste.",
  "1.00 - supported as a Canadian premium trade-up but not a named global priority."),
 "Colgate Max Fresh": _e(
  "0.95 - freshness workhorse priced at or just below the Colgate core line.",
  "0.90 - broad mass and drug distribution; fewer professional or premium doors.",
  "1.00 - steady mainstream turn with no adverse coverage; 66 US and 33 Canadian SKUs.",
  "0.85-0.90 - a value-tier defence line rather than a named 2026 investment priority."),
 "Colgate Sensitive": _e(
  "1.45 - sensitivity toothpaste sells at a therapeutic premium ($8.99 two-pack at Target).",
  "0.85 - present at mass and drug but with a narrower assortment than core toothpaste.",
  "1.05 - strong consumer pull: 4.66/5 from 1,570 Target reviews, the best-rated Colgate toothpaste set found.",
  "1.00 - part of the premium therapeutic slate but not a named lead campaign."),
 "Colgate Sensitive Pro-Relief": _e(
  "1.45 - CAD $6.99 at Well.ca versus CAD $0.98-$5.97 for the core Canadian Colgate range.",
  "0.85 - Well.ca, Walmart Canada and drug distribution with a CDA seal listing.",
  "1.00 - solid therapeutic turn; 33 Canadian SKUs in the portfolio.",
  "1.00 - premium therapeutic tier inside the North America innovation slate."),
 "Colgate PreviDent": _e(
  "2.20 - prescription 5000ppm product at roughly 4x the fluoride of OTC toothpaste, dispensed at Rx pricing.",
  "0.35 - dental-professional and pharmacy channels only; no open-retail listing.",
  "0.60 - low turn per door given prescription gating.",
  "0.60 - professional-channel detailing rather than consumer media."),
 "Colgate PerioGard": _e(
  "2.00 in the US (Rx chlorhexidine rinse) and 1.70 in Canada, where PerioGard/PerioGardSF is also sold as a consumer gum-health line.",
  "0.30 US / 0.55 Canada - Rx-gated in the US; the Canadian line reaches retail and pharmacy as well as dental offices.",
  "0.55-0.75 - low absolute turn but rising as the launch moves through distribution.",
  "0.70 - launched 'through the profession' in 2026, so support is detailing-led, not mass media."),
 "Colgate hum": _e(
  "3.00 - connected power brush hardware at $17.99 for replacement heads alone, far above manual oral care.",
  "0.20 - DTC and Amazon only, with replacement heads already sold out.",
  "0.40 - wind-down: availability gaps and public discontinuation chatter suppress turn.",
  "0.40 - absent from 2026 earnings materials; power emphasis has shifted to manual brushes and kids battery brushes."),
 "Ultra Brite": _e(
  "0.55 - value whitening tier; the lowest-priced toothpaste in the US portfolio.",
  "0.45 - Walmart and Amazon only, with no Canadian retail distribution.",
  "0.60 - uneven ratings (3.7-5.0) and minimal support point to slow turn.",
  "0.35 - no brand-specific 2026 activity found; a price-gap tier, not a media brand."),
 "Tom's of Maine": _e(
  "1.30 - naturals premium at $4.47-$9.96 in the US and CAD $5.97-$11.97 in Canada versus mainstream toothpaste.",
  "0.70 US / 0.45 Canada - broad US mass plus health/specialty distribution; Canada is Walmart-led and much narrower.",
  "0.85 US / 0.70 Canada - solid ratings (4.0-4.8, up to 1,921 reviews) but a specialty rather than mass turn rate.",
  "1.05 US / 0.90 Canada - 'Never Underestimate Nature' was the brand's first campaign in three years, so support is real but modest."),
 "hello": _e(
  "1.25 - $2.49-$14.23 at Target and CAD $5.97-$9.98 at Walmart Canada, above private label and mainstream value toothpaste.",
  "0.60 US / 0.40 Canada - Target/Walmart/Amazon in the US; Canada launched only in June 2025 at Shoppers, Walmart and Amazon.ca.",
  "0.90 US / 0.75 Canada - high cultural velocity for a small base; trade estimate of ~$40M sales at acquisition with 15% of sales online.",
  "1.15-1.20 - influencer- and social-led investment with a named chief aura officer and the Whipped launch as a Q1 2026 North America priority."),
 "Speed Stick": _e(
  "0.80 - value men's deodorant at $4.69-$10.25 (US) and CAD $5.99-$13.49 (Canada), below premium deodorant benchmarks.",
  "0.95 US / 0.90 Canada - near-universal mass, drug and grocery distribution in both markets.",
  "1.05-1.10 - high-turn value staple: 4.4/5 from 1,388 ratings on the core Walmart SKU.",
  "0.85-0.90 - no named 2026 campaign; personal care sits inside the general price-gap and advertising step-up."),
 "Lady Speed Stick": _e(
  "0.75 - the lowest-priced deodorant line in the portfolio, from CAD $3.77.",
  "0.80 - solid mass distribution but a narrower assortment than the men's line (19-20 SKUs per market).",
  "0.85-0.90 - steady value turn with no adverse coverage and no campaign lift.",
  "0.60 - no dedicated 2025-2026 campaign found; maintained rather than invested."),
 "Softsoap": _e(
  "0.85 - value hand-wash pricing at $2.48-$12.12 (US) and CAD $4.28-$10.28 (Canada).",
  "1.00 US / 0.90 Canada - the widest personal-care distribution in the portfolio, with 153 US SKUs.",
  "1.10-1.25 - very high replenishment turn; ratings of 4.4-4.8 across review counts up to 6,575.",
  "0.90-0.95 - supported through sustainability innovation (tablets, aluminium bottles) rather than heavy paid media."),
 "Irish Spring": _e(
  "0.90 - mainstream bar-soap and body-wash pricing at CAD $5.97-$10.48.",
  "0.95 US / 0.85 Canada - broad mass and drug distribution; the US brand site was cookie-gated but trade press confirms national scale.",
  "1.15 US / 1.30 Canada - very high turn, with individual Canadian SKUs carrying up to 4,736 reviews.",
  "1.10-1.20 - the brand bought its first Super Bowl ad (reported $6.5M per unit) behind a full relaunch, the clearest paid-media signal in personal care."),
 "Skin Bracer": _e(
  "0.70 - heritage aftershave at CAD $10.99 for 100ml, a small-basket value item.",
  "0.25-0.30 - CVS, Amazon and independent grocery only, with forum chatter about discontinuation indicating patchy shelf presence.",
  "0.50-0.55 - loyal but small base (4.8/5 from 89 CVS reviews; 4.7/5 from 804 Amazon.ca ratings).",
  "0.30 - no company marketing activity found in fetched sources."),
 "Afta": _e(
  "0.70 - legacy pre-electric shave lotion at grocery price points.",
  "0.15 - a single confirmed US grocery listing (Kroger) and no Canadian listing.",
  "0.35 - one retailer review in total, indicating negligible turn.",
  "0.25 - no marketing activity found; a harvest brand."),
 "EltaMD": _e(
  "2.60 - professional sunscreen at CAD $68-$82 per unit, roughly 3x mass sun care.",
  "0.75 US / 0.55 Canada - physician offices, DTC, Dermstore and 15 authorized online retailers in the US; Amazon.ca plus professional e-tailers in Canada.",
  "1.30-1.40 - exceptional turn for a premium brand: UV Clear alone carries 42,034 reviews and the brand claims #1 dermatologist-recommended status.",
  "1.05-1.10 - skin health is a named growth engine, with clinical-proof storytelling featured in Q2 2026 investor materials."),
 "PCA SKIN": _e(
  "2.80 - professional peels and skincare at $26.99-$161 per unit.",
  "0.55 US / 0.40 Canada - esthetician channel plus Target in the US; only 3 products on walmart.ca plus authorized professional e-tailers in Canada.",
  "0.80-1.00 - more than 1 million peels performed annually but a thin consumer review base (11 reviews on walmart.ca).",
  "0.95-1.00 - featured in Q2 2026 materials (MGF Age Renewal Cream) but supported through professional channels rather than mass media."),
 "Filorga": _e(
  "3.00 - the highest price index in the portfolio; French anti-ageing skincare acquired for $1.7B.",
  "0.15 US / 0.55 Canada - us.filorga.com has stopped processing orders and redirects to a third-party e-tailer, while Canada has DTC (65 products) plus 39 products at Walmart Canada.",
  "0.40 US / 0.85 Canada - US availability disruption suppresses turn; Canadian ratings are 4.6-4.7.",
  "0.40 US / 0.80 Canada - the earnings skin-health narrative centres on EltaMD and PCA SKIN, so Filorga support is maintenance-level, concentrated where distribution works."),
 "Palmolive": _e(
  "0.90 - value dish liquid at $0.97-$29.99 (US multipacks) and CAD $4.99-$5.79 (Canada).",
  "1.00 US / 0.90 Canada - full grocery, mass and club distribution in the US; Walmart, Well.ca and Loblaw banners in Canada.",
  "1.15-1.30 - very high replenishment turn with review counts up to 9,026 on US listings.",
  "0.95-1.00 - Dish E-Z Pump was a named Q1 2026 division launch, so support is at portfolio-average intensity."),
 "Fabuloso": _e(
  "0.95 - value multi-purpose cleaner at $3.47-$13.61.",
  "1.00 US / 0.75 Canada - CPSC recall documentation names Walmart, Dollar General, Family Dollar, Home Depot, Sam's Club and Amazon as US channels; Canada is Walmart and Loblaw banners.",
  "1.45 US / 1.15 Canada - the highest velocity index assigned: company-stated #1 US all-purpose pour cleaner with review counts to 17,498.",
  "1.15-1.25 - a 2026 360 platform ('Make Your World More Fabuloso') plus telenovela creative on Hulu makes Fabuloso the most media-active home-care brand."),
 "Suavitel": _e(
  "0.85 - value fabric conditioner at $2.97-$18.19 with 100 fl oz at $8.97.",
  "0.90 US / 0.55 Canada - broad US grocery and mass distribution; only 6 SKUs listed on walmart.ca.",
  "1.20 - consistently high ratings (4.5-4.8 US, 4.63-4.84 Canada) on a high-repurchase category.",
  "0.90-1.10 - Suavitel Complete fabric refresher spray is a named 2026 innovation, so support is above the home-care tail."),
 "Ajax": _e(
  "0.60 US / 0.70 Canada - value cleaner; the Canadian multi-purpose SKU sells at CAD $7.99 while US Axion/Ajax dish sits near $1.99.",
  "0.60 - Kroger banners and Walmart in the US; Walmart Canada and Amazon.ca in Canada.",
  "0.70 - low-visibility value brand with no ratings displayed on retailer brand pages.",
  "0.50 - no 2026 Ajax-specific innovation named; home-care innovation is concentrated on Fabuloso and Suavitel."),
 "Murphy Oil Soap": _e(
  "1.10 - specialty wood cleaner priced above general-purpose cleaners, including a 4.3L B2B pack at Uline.ca.",
  "0.55 US / 0.60 Canada - grocery plus hardware (Home Depot Canada) and B2B (Uline) distribution, but not a mass staple.",
  "0.60-0.65 - occasional-use specialty product with no ratings displayed on retailer pages.",
  "0.40-0.45 - no 2026 activity found in earnings or trade sources."),
 "Axion": _e(
  "0.55 - value dish soap at $1.99 for 21.6 fl oz in Kroger-banner grocery (the imported marketplace bar at $12.92 is treated as a pricing distortion, not a shelf price).",
  "0.10 - a handful of Kroger-banner listings plus third-party import SKUs; the narrowest distribution of any included brand.",
  "0.40 - no meaningful US sentiment base and negligible shelf presence.",
  "0.20 - no North America marketing activity; core markets are Latin America."),
 "Arctic Power": _e(
  "0.80 - value cold-water detergent at CAD $7.97-$12.97, including 88-load packs at CAD $9.29.",
  "0.80 - Walmart Canada and Canadian Tire, the two national channels for the category.",
  "1.20 - laundry detergent is a high-turn category and the brand is flagged 'Top Rated' at Canadian Tire with 4.1-5.0 Walmart ratings.",
  "0.80 - no brand-specific 2026 disclosure; Canada sits inside the North America division agenda."),
 "Fleecy": _e(
  "0.75 - value fabric softener and dryer sheets at CAD $5.97-$12.97.",
  "0.70 - Walmart Canada distribution confirmed; no US retail listing.",
  "1.00 - routine replenishment turn; no aggregate rating displayed on the brand page.",
  "0.60 - no 2026 brand-specific disclosure found."),
 "Hill's Science Diet": _e(
  "1.40 - science-led premium pet food priced above grocery brands but below therapeutic diets.",
  "0.95 US / 0.85 Canada - Chewy, Petco, PetSmart, Amazon, grocery and vet clinics in the US; PetSmart Canada (208 listings) and vets in Canada.",
  "1.10-1.20 - the largest Hill's line by volume, though Science Diet dog declined in Q2 2026.",
  "1.10-1.15 - Hill's ran 70% of US media through a data clean room and is presenting sponsor of Clear The Shelters 2026."),
 "Hill's Prescription Diet": _e(
  "1.90 - therapeutic diets at $12.49-$144.99, the highest pet price tier.",
  "0.80 US / 0.70 Canada - vet clinics plus Chewy, Petco and PetSmart Canada; prescription authorization narrows the door count.",
  "1.05-1.15 - management calls the therapeutic business the growth engine within Hill's.",
  "1.05-1.10 - the July 2026 'Try Again' campaign targets veterinary professionals across Reddit, TikTok, AI search and YouTube."),
 "Hill's Bioactive Recipe": _e(
  "1.60 - functional/bioactive positioning priced above Science Diet.",
  "0.35 - Chewy and the veterinary channel only; absent from Canadian listings.",
  "0.55 - low visibility, with no presence in Hill's 2026 launch communications.",
  "0.40 - not featured in 2026 innovation disclosures."),
 "Hill's Healthy Advantage": _e(
  "1.50 - vet-channel wellness food priced between Science Diet and therapeutic diets.",
  "0.30 - vet clinics plus a Chewy listing; the narrowest Hill's distribution.",
  "0.50 - no consumer review base surfaced in the research.",
  "0.35 - no marketing activity disclosed."),
 "Prime100": _e(
  "2.20 - fresh single-protein rolls at a premium to dry pet food.",
  "0.15 - select pet-specialty retailers in the north-east region plus DTC; salmon production is temporarily paused.",
  "0.60 - early-stage US ramp; the acquisition added just 0.3% to FY2025 reported volume.",
  "0.50 - investment is going into capability (it is the platform for Hill's US fresh entry) rather than consumer media."),
}

# ---------------------------------------------------------------- empirical SKU counts
def sku_counts():
    c = collections.Counter()
    for f in ("skus_oral_care.csv", "skus_personal_care.csv"):
        for r in csv.DictReader(open(os.path.join(RES, f), encoding="utf-8-sig")):
            c[(r["brand_name"], r["geo_market"])] += 1
            if r["brand_name"] == "Colgate":
                c[("PORTFOLIO::" + r["product_portfolio"], r["geo_market"])] += 1
    return c

SKU = sku_counts()
HUM_SKU_EST = {("Colgate hum", "USA"): 6}

# Home Care / Pet Nutrition SKU counts are not in the two SKU CSVs (they cover
# oral + personal care only). Counts below are documented shelf-assortment
# estimates read off the retailer brand pages cited in brands_positioning.md.
SKU_EST = {
    ("Palmolive", "USA"): 40, ("Palmolive", "Canada"): 12,
    ("Ajax", "USA"): 20, ("Ajax", "Canada"): 8,
    ("Fabuloso", "USA"): 45, ("Fabuloso", "Canada"): 10,
    ("Suavitel", "USA"): 30, ("Suavitel", "Canada"): 6,
    ("Murphy Oil Soap", "USA"): 10, ("Murphy Oil Soap", "Canada"): 5,
    ("Axion", "USA"): 3,
    ("Arctic Power", "Canada"): 12, ("Fleecy", "Canada"): 10,
    ("Hill's Science Diet", "USA"): 400, ("Hill's Science Diet", "Canada"): 208,
    ("Hill's Prescription Diet", "USA"): 250, ("Hill's Prescription Diet", "Canada"): 150,
    ("Hill's Bioactive Recipe", "USA"): 25,
    ("Hill's Healthy Advantage", "USA"): 20,
    ("Prime100", "USA"): 10,
    ("Afta", "USA"): 2,
}

def sku_for(brand, geo):
    # SKU_EST wins where it exists: the two SKU CSVs cover oral + personal care
    # only, so e.g. Palmolive appears there with a single stray bar-soap row
    # that would badly understate the US dish assortment.
    if (brand, geo) in SKU_EST:
        return SKU_EST[(brand, geo)]
    return SKU.get((brand, geo), 1)

# ---------------------------------------------------------------- reported anchors
WW_SALES = 20382.0
OPHC_WW = 15769.0
PET_WW = 4613.0
NA_OPHC = 4045.0
AD_WW = 2703.0
CA_SHARE = 0.093
HILLS_NA_SHARE_OF_GLOBAL = 0.689   # -> US = 62.5% of global Hill's (mid of 60-65%)

ophc = country_split(NA_OPHC, CA_SHARE)
hills_na = PET_WW * HILLS_NA_SHARE_OF_GLOBAL
pet = country_split(hills_na, CA_SHARE)

CAT_WEIGHTS = {
    "USA":    {"Oral Care": 0.47, "Personal Care": 0.20, "Skin Care": 0.08, "Home Care": 0.25},
    "Canada": {"Oral Care": 0.45, "Personal Care": 0.19, "Skin Care": 0.06, "Home Care": 0.30},
}
POOL = {}
for g in ("USA", "Canada"):
    for cat, w in CAT_WEIGHTS[g].items():
        POOL[(g, cat)] = ophc[g] * w
    POOL[(g, "Pet Nutrition")] = pet[g]

# ---------------------------------------------------------------- brand definitions
# fields: brand, geo, category, sub_category, parent, price_index, dist_breadth,
#         velocity, ad_priority, n_sources, retailers, themes, sentiment, q4,
#         innovation, assets, sources
B = []
def add(**kw):
    B.append(kw)

CG_SRC = [U["tenk"], U["rem226"], U["q226"]]

# ---------------- USA ORAL CARE -------------------------------------------
add(brand="Colgate", geo="USA", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.00, db=1.00, vel=1.30, adp=1.30, n=5,
    retailers=["Walmart", "Target", "Amazon", "CVS", "Colgate DTC"], rw=[.34, .22, .18, .16, .10],
    assets="https://www.colgate.com/en-us",
    themes="Master platform \"Healthy smiles start here\" plus the March 2026 \"Your Smile Is Your Strength\" campaign across social, YouTube and TikTok.",
    sent="Retail sentiment is solid (4.5-4.7 stars at mass), but direct-brand sentiment is weak: colgate.com holds a 1.4 Trustpilot rating on reformulation and availability complaints.",
    q4="Defend: hold US toothpaste share after the slide to 31.9% YTD via price-gap management and stepped-up advertising.",
    innov="Optic White Pro Series with ActivShine, Maximum Cavity Protection and Triple Action relaunches, PerioGard professional launch, licensed kids line.",
    src=CG_SRC + ["https://www.trustpilot.com/review/colgate.com", "https://www.morningstar.com/news/pr-newswire/20260319ny14123/in-an-age-of-pressure-colgate-reminds-a-generation-your-smile-is-your-strength-in-new-campaign"],
    reported_cat_share=31.9)

def colgate_sub(geo, brand, portfolio, sub, pi, db, vel, adp, n, retailers, rw, assets, themes, sent, q4, innov, src):
    add(brand=brand, geo=geo, cat="Oral Care", sub=sub, parent="Colgate", portfolio=portfolio,
        pi=pi, db=db, vel=vel, adp=adp, n=n, retailers=retailers, rw=rw, assets=assets,
        themes=themes, sent=sent, q4=q4, innov=innov, src=src)

colgate_sub("USA", "Colgate Total", "Colgate Total", "Toothpaste", 1.10, 1.00, 1.05, 1.30, 4,
    ["Walmart", "Target", "Amazon", "CVS"], [.35, .25, .22, .18],
    "https://www.colgate.com/en-us",
    "\"Patented preventative technology\" whole-mouth bacteria control with clinically proven claims; athlete creative \"One Step Ahead\" with Bijan Robinson.",
    "The most exposed sub-brand in the portfolio: reformulation drove taste, irritation and availability complaints on Reddit and Trustpilot.",
    "Defend: recover share lost to the reformulation and complete distribution of the relaunched Total.",
    "Relaunched Total formula alongside Maximum Cavity Protection and Triple Action in the therapeutic tier.",
    [U["rem226"], U["call226"], "https://www.reddit.com/r/hygiene/comments/1i24891/colgate_total_formula_changetastes_terrible/", "https://www.trustpilot.com/review/colgate.com"])

colgate_sub("USA", "Colgate Optic White", "Colgate Optic White", "Whitening", 1.35, 0.95, 1.10, 1.35, 4,
    ["Walmart", "Target", "Amazon", "CVS"], [.34, .26, .22, .18],
    "https://www.colgate.com/en-us",
    "\"The Science of WOW\" for Pro Series with ActivShine, built with VML across 15s/30s spots and 100+ assets.",
    "Efficacy claims are heavily substantiated (\"5X whiter\"), though some direct-brand reviewers call whitening products a waste of money.",
    "Win: scale the premium whitening ladder in North America with Pro Series and the global Optic White Purple rollout.",
    "ActivShine technology at 5% hydrogen peroxide, Optic White Purple, Optic White Vitamin C.",
    ["https://www.prnewswire.com/news-releases/colgate-optic-white-unveils-its-most-advanced-whitening-formula-the-new-optic-white-pro-series-toothpaste-302715661.html", "https://news.designrush.com/colgate-optic-white-the-science-of-wow-campaign", U["rem226"], U["call226"]])

colgate_sub("USA", "Colgate Max Fresh", "Colgate Max Fresh", "Toothpaste", 0.95, 0.90, 1.00, 0.90, 2,
    ["Walmart", "CVS", "Amazon"], [.45, .30, .25],
    "https://www.colgate.com/en-ca/colgate-max-fresh",
    "\"10X longer-lasting cool\" with Ultrafreeze technology and mini breath strips across Clean Mint, Cool Mint and Knockout.",
    "Mainstream freshness workhorse with routine mass availability and no adverse coverage found in fetched sources.",
    "Defend: value-tier freshness defence inside the North America price-gap plan.",
    "Ultrafreeze breath-strip formats; no dedicated 2026 launch disclosed.",
    ["https://www.cvs.com/shop/colgate-max-fresh-toothpaste-with-mini-breath-strips-clean-mint-prodid-275748", U["call226"]])

colgate_sub("USA", "Colgate Sensitive", "Colgate Sensitive", "Toothpaste", 1.45, 0.85, 1.05, 1.00, 2,
    ["Target", "Walmart", "Amazon"], [.40, .35, .25],
    "https://www.colgate.com/en-ca/sensitive-pro-relief",
    "Clinically framed instant and lasting sensitivity relief.",
    "Strongly positive - 4.66/5 from 1,570 Target reviews, the highest-rated Colgate toothpaste SKU set found in the research.",
    "Win: premium therapeutic tier is part of the 2026/2027 innovation slate to be scaled in North America.",
    "Premium therapeutic sensitivity formats.",
    ["https://www.target.com/p/colgate-sensitive-toothpaste-complete-protection-6oz-2pk/-/A-75563177", U["call226"]])

colgate_sub("USA", "Colgate PreviDent", "Colgate PreviDent", "Professional & Therapeutic", 2.20, 0.35, 0.60, 0.60, 2,
    ["Dental professional channel", "Pharmacy (Rx)"], [.6, .4],
    "https://www.colgate.com/en-us/prevident",
    "Clinical-evidence messaging: \"4x the fluoride\" of OTC products, with root-caries remineralization data.",
    "Professional-channel credibility rather than consumer sentiment; no consumer review base found.",
    "Win: build the professional channel as PerioGard and PreviDent move through dental distribution in 2026.",
    "Professional/Rx portfolio expansion - PreviDent line extensions.",
    ["https://www.colgate.com/en-us/prevident", "https://www.fool.com/earnings/call-transcripts/2026/01/30/colgate-palmolive-cl-q4-2025-earnings-transcript/"])

colgate_sub("USA", "Colgate PerioGard", "Colgate PerioGard", "Professional & Therapeutic", 2.00, 0.30, 0.55, 0.70, 2,
    ["Dental professional channel", "Pharmacy (Rx)"], [.65, .35],
    "https://www.colgateprofessional.com/products/mouthwash/colgate-periogard-rinse",
    "Rx chlorhexidine 0.12% rinse claiming significant reduction in gum bleeding and inflammation.",
    "Professional endorsement drives credibility; no consumer review base exists for the Rx rinse.",
    "Win: PerioGard was launched through the profession and is moving through distribution during 2026.",
    "New professional gum-health launch (PerioGard) named in earnings materials.",
    ["https://www.colgateprofessional.com/products/mouthwash/colgate-periogard-rinse", "https://www.fool.com/earnings/call-transcripts/2026/01/30/colgate-palmolive-cl-q4-2025-earnings-transcript/"])

colgate_sub("USA", "Colgate hum", "Colgate hum", "Power Toothbrushes", 3.00, 0.20, 0.40, 0.40, 2,
    ["Colgate DTC", "Amazon"], [.5, .5],
    "https://shop.colgate.com/hum-smart-toothbrush-app",
    "App-connected coaching, \"clinically proven to increase efficacy by 50%\", sonic technology to 30,000 strokes/minute.",
    "Ratings are decent (4.3/5) but replacement heads are sold out and consumers openly ask whether hum is being discontinued.",
    "Defend/harvest: no hum mention in 2026 earnings materials; power emphasis has shifted to manual-brush share and kids battery brushes.",
    "Kids AR/battery brushes rather than premium connected hardware.",
    ["https://shop.colgate.com/products/hum-adult-smart-toothbrush-replacement-brush-heads", "https://www.reddit.com/r/Teethcare/comments/1exr297/is_colgate_hum_being_discontinuedphased_out/"])

add(brand="Ultra Brite", geo="USA", cat="Oral Care", sub="Whitening", parent="",
    pi=0.55, db=0.45, vel=0.60, adp=0.35, n=2,
    retailers=["Walmart", "Amazon"], rw=[.6, .4],
    assets="https://www.colgate.com/en-us/products/toothpaste/ub-baking-soda-peroxide-whitening",
    themes="Functional value whitening - \"safely and effectively whitens and cleans teeth\" with baking soda and peroxide.",
    sent="Uneven - Walmart ratings span 3.7 to 5.0, consistent with a low-priced legacy value brand with limited support.",
    q4="Defend: relevant only as a price-gap/value tier in the US toothpaste defence.",
    innov="n.a. - no brand-specific 2026 innovation found in earnings or trade sources.",
    src=["https://www.walmart.com/c/kp/ultrabrite-toothpaste", "https://www.colgate.com/en-us/products/toothpaste/ub-baking-soda-peroxide-whitening"])

add(brand="Tom's of Maine", geo="USA", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.30, db=0.70, vel=0.85, adp=1.05, n=4,
    retailers=["Walmart", "Target", "Amazon", "Tom's DTC"], rw=[.35, .25, .25, .15],
    assets="https://www.tomsofmaine.com/",
    themes="\"Our Naturally High Standards\" master positioning plus \"Never Underestimate Nature\" for WHITEN+, built with VML.",
    sent="Broadly positive at retail (4.0-4.8 stars, review counts to 1,921), with efficacy scepticism about natural formats the theme the 2025 campaign answers.",
    q4="Win: naturals credibility plus efficacy proof in whitening and deodorant.",
    innov="WHITEN+ natural whitening toothpaste and natural deodorant efficacy upgrades.",
    src=["https://www.walmart.com/brand/tomsofmaine/10024560", "https://www.tomsofmaine.com/", "https://shots.net/news/view/toms-of-maine-says-never-underestimate-nature", "https://www.mediapost.com/publications/article/395269/toms-of-maine-spots-aim-to-prove-natural-deodoran.html?edition=133995"])

add(brand="hello", geo="USA", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.25, db=0.60, vel=0.90, adp=1.20, n=4,
    retailers=["Target", "Walmart", "Amazon"], rw=[.45, .30, .25],
    assets="https://www.hello-products.com/",
    themes="\"Everyday Yay\" platform with Gen Z \"aura\" positioning (Chandler Kinney as chief aura officer) on Instagram and TikTok.",
    sent="Culturally buoyant and trade-press-favoured as Colgate's Gen Z play, framed as beauty routine rather than hygiene chore.",
    q4="Win: scale hello Whipped Toothpaste, a named Q1 2026 North America launch.",
    innov="Whipped toothpaste texture innovation and fluoride-free/naturals formats.",
    src=["https://www.target.com/c/toothpaste-oral-care-personal/hello/-/N-5xtzsZ4uey8", "https://www.campaignlive.com/article/brushing-teeth-boost-aura-hello-products-betting/1966520", "https://www.glossy.co/beauty/glossy-pop-newsletter-inside-hellos-plan-to-make-toothpaste-part-of-gen-zs-beauty-regimen/", U["remfy25"]])

# ---------------- USA PERSONAL CARE ---------------------------------------
add(brand="Speed Stick", geo="USA", cat="Personal Care", sub="Antiperspirant & Deodorant", parent="",
    pi=0.80, db=0.95, vel=1.10, adp=0.90, n=3,
    retailers=["Walmart", "Target", "Amazon"], rw=[.45, .30, .25],
    assets="https://www.speedstick.com/en-us",
    themes="Value/performance men's deodorant positioning on the brand site; no new 2026 platform disclosed.",
    sent="Polarised - the core Walmart SKU holds 4.4/5 from 1,388 ratings while Target SKU ratings range from 1.0 to 4.2.",
    q4="Defend: personal care in North America sits inside the price-gap and advertising step-up plan.",
    innov="n.a. - no announced Speed Stick R&D found in fetched sources.",
    src=["https://www.target.com/c/deodorant-personal-care/speed-stick/-/N-5xtzpZscs3c", "https://www.walmart.com/reviews/product/34575424", "https://www.speedstick.com/en-us"])

add(brand="Lady Speed Stick", geo="USA", cat="Personal Care", sub="Antiperspirant & Deodorant", parent="",
    pi=0.75, db=0.80, vel=0.85, adp=0.60, n=2,
    retailers=["Walmart", "Target"], rw=[.6, .4],
    assets="https://www.speedstick.com/en-us",
    themes="Maintained as a value women's deodorant line; no dedicated 2025-2026 campaign found.",
    sent="Low-noise value line with routine mass availability and no adverse coverage found.",
    q4="Defend: hold shelf and price gaps in mass deodorant.",
    innov="n.a. - no innovation disclosed in fetched sources.",
    src=["https://www.colgatepalmolive.com/en-us", U["tenk"]])

add(brand="Softsoap", geo="USA", cat="Personal Care", sub="Liquid Hand Soap", parent="",
    pi=0.85, db=1.00, vel=1.25, adp=0.95, n=3,
    retailers=["Walmart", "Target", "Amazon"], rw=[.45, .28, .27],
    assets="https://www.softsoap.com/en-us",
    themes="Sustainability and plastic reduction - foaming hand soap tablets with a reusable, recyclable aluminium bottle.",
    sent="Strong and stable - Walmart ratings of 4.4-4.8 across review counts up to 6,575.",
    q4="Defend: sustainable-format refill systems and mass distribution defence.",
    innov="Tablet-based foaming hand soap and refillable aluminium packaging.",
    src=["https://www.walmart.com/brand/softsoap/10021904", "https://www.adweek.com/commerce/colgate-palmolives-softsoap-debuts-hand-soap-made-from-tablets/", "https://www.globalcosmeticsnews.com/colgate-palmolives-softsoap-looks-to-reduce-plastic-waste-with-the-launch-of-foaming-hand-soap-tablets-and-refillable-recyclable-aluminum-bottle/"])

add(brand="Irish Spring", geo="USA", cat="Personal Care", sub="Bar Soap", parent="",
    pi=0.90, db=0.95, vel=1.15, adp=1.20, n=3,
    retailers=["Walmart", "Target", "Amazon"], rw=[.45, .28, .27],
    assets="https://www.colgatepalmolive.com/en-us",
    themes="Full brand relaunch - new formulas, fragrances, logo and packaging supported by the brand's first Super Bowl ad with agency Ten6.",
    sent="Very strong, with individual SKUs carrying up to 4,736 reviews at Walmart Canada and no adverse US coverage found.",
    q4="Win: sustain the relaunched range and elevated media presence.",
    innov="Reformulated bars and body washes with new fragrance range.",
    src=["https://www.adweek.com/brand-marketing/irish-spring-first-super-bowl-ad/", "https://www.colgatepalmolive.com/en-us", "https://www.walmart.ca/fr/c/brand/irish-spring"])

add(brand="Skin Bracer", geo="USA", cat="Personal Care", sub="Shaving & Grooming", parent="",
    pi=0.70, db=0.30, vel=0.55, adp=0.30, n=2,
    retailers=["CVS", "Amazon"], rw=[.6, .4],
    assets="https://www.cvs.com/shop/skin-bracer-after-shave-original-prodid-280115",
    themes="Classic heritage aftershave usage messaging; no active campaign found.",
    sent="Loyal nostalgic base (4.8/5 at CVS) but shaving forums repeatedly ask whether it has been discontinued, indicating patchy distribution.",
    q4="Defend: maintain heritage distribution; no company activity found.",
    innov="n.a. - no innovation found in fetched sources.",
    src=["https://www.cvs.com/shop/skin-bracer-after-shave-original-prodid-280115", "https://www.badgerandblade.com/forum/threads/is-mennen-skin-bracer-discontinued.649360/"])

add(brand="Afta", geo="USA", cat="Personal Care", sub="Shaving & Grooming", parent="",
    pi=0.70, db=0.15, vel=0.35, adp=0.25, n=1,
    retailers=["Kroger"], rw=[1.0],
    assets="https://www.kroger.com/p/afta-pre-electric-by-mennen-original-scent-shave-lotion/0002220000276",
    themes="n.a. - legacy tail brand with no marketing activity found in fetched sources.",
    sent="Effectively no measurable sentiment - a single retailer review, indicating minimal distribution and support.",
    q4="Defend: harvest remaining grocery distribution.",
    innov="n.a.",
    src=["https://www.kroger.com/p/afta-pre-electric-by-mennen-original-scent-shave-lotion/0002220000276"])

# ---------------- USA SKIN CARE -------------------------------------------
add(brand="EltaMD", geo="USA", cat="Skin Care", sub="Sun Care & SPF", parent="",
    pi=2.60, db=0.75, vel=1.40, adp=1.10, n=4,
    retailers=["Dermstore", "Amazon", "EltaMD DTC", "Physician/professional channel"], rw=[.32, .28, .20, .20],
    assets="https://eltamd.com/",
    themes="\"Derm Difference\" and National Dermatologist Day advocacy, anchored on dermatologist endorsement.",
    sent="Among the strongest sentiment in the portfolio - UV Clear carries 42,034 reviews and independent reviewers rank it top of category.",
    q4="Win: clinical-proof storytelling behind UV Clear (65% blemish and 61% oil reduction at 12 weeks).",
    innov="Acne/oil-control efficacy claims for UV Clear and continued professional-channel skin-health expansion.",
    src=["https://eltamd.com/", "https://www.prnewswire.com/news-releases/eltamd-commemorates-second-annual-dermatologist-day-with-the-launch-of-derm-difference-campaign-to-empower-consumers-with-expert-insights-302400611.html", "https://www.dermstore.com/c/brands/eltamd/", U["slides226"]])

add(brand="PCA SKIN", geo="USA", cat="Skin Care", sub="Professional & Clinical", parent="",
    pi=2.80, db=0.55, vel=1.00, adp=1.00, n=3,
    retailers=["Target", "PCA SKIN DTC", "Esthetician/professional channel"], rw=[.35, .30, .35],
    assets="https://www.pcaskin.com/about",
    themes="Professional/esthetician authority and results-driven medical-grade skincare.",
    sent="Positive but thin consumer review base; credibility carried by professional endorsement, with 1M+ peels performed annually.",
    q4="Win: life-stage skin health - MGF Age Renewal Cream for estrogen-depleted skin featured in Q2 2026 materials.",
    innov="Menopause/estrogen-depleted skin (MGF Age Renewal Cream) and the professional peel portfolio.",
    src=["https://www.target.com/b/pca-skin/-/N-q643le2xlpu", "https://www.pcaskin.com/about", U["slides226"]])

add(brand="Filorga", geo="USA", cat="Skin Care", sub="Serums & Treatments", parent="",
    pi=3.00, db=0.15, vel=0.40, adp=0.40, n=2,
    retailers=["Exclusive Beauty Club (third-party e-tailer)"], rw=[1.0],
    assets="https://us.filorga.com/",
    themes="NCEF-concentrated multi-correcting skincare and antioxidant serums.",
    sent="Positive where distributed, but the US order stoppage on us.filorga.com is a live availability risk to brand perception.",
    q4="Defend: stabilise US route to market; earnings skin-health narrative centres on EltaMD and PCA SKIN, not Filorga.",
    innov="n.a. - no 2026 North America innovation disclosed.",
    src=["https://us.filorga.com/", U["slides226"]])

# ---------------- USA HOME CARE -------------------------------------------
add(brand="Palmolive", geo="USA", cat="Home Care", sub="Dish Liquid", parent="",
    pi=0.90, db=1.00, vel=1.30, adp=1.00, n=3,
    retailers=["Walmart", "Kroger", "Amazon", "Target"], rw=[.40, .24, .20, .16],
    assets="https://www.palmolive.com/en-us",
    themes="Grease-cutting efficacy - \"Removes up to 99.9% of Grease\".",
    sent="Reliable mass performer with very deep review bases (up to 9,026 reviews) and ratings of 3.8-5.0.",
    q4="Win: convenience-format dish innovation - Palmolive Dish E-Z Pump was a named Q1 2026 division launch.",
    innov="Palmolive Dish E-Z Pump dispensing format.",
    src=["https://www.walmart.com/browse/household-essentials/palmolive/1115193_1071966_7583868_1661720_1332555", "https://www.palmolive.com/en-us", U["remfy25"]])

add(brand="Fabuloso", geo="USA", cat="Home Care", sub="Surface & Multi-Purpose Cleaners", parent="",
    pi=0.95, db=1.00, vel=1.45, adp=1.25, n=4,
    retailers=["Walmart", "Dollar General", "Family Dollar", "Amazon", "Sam's Club"], rw=[.38, .18, .15, .16, .13],
    assets="https://www.fabuloso.com/en-us",
    themes="\"Make Your World More Fabuloso\" 2026 platform plus \"Dramatically Clean\" telenovela creative on Hulu targeting Hispanic households.",
    sent="The portfolio's strongest home-care sentiment (4.5-4.8 stars, up to 17,498 reviews), with a residual overhang from the 2023 recall of ~4.9M units.",
    q4="Win: push form and scent extensions, which management cites as a 2026 growth driver.",
    innov="Fabuloso 3-in-1 Clean Spray, Watermelon and Ultra Frescura liquids, Fabuloso 2X concentrate.",
    src=["https://www.walmart.com/brand/fabuloso/10017747", "https://screenmag.com/vml-and-colgate-palmolive-launch-make-your-world-more-fabuloso-for-fabuloso/", "https://www.colgatepalmolive.com/en-us/news/fabuloso-2x-leads-the-way-with-efficacy-and-sustainability", "https://www.cpsc.gov/Recalls/2023/Colgate-Palmolive-Recalls-Fabuloso-Multi-Purpose-Cleaners-Due-to-Risk-of-Exposure-to-Bacteria"])

add(brand="Suavitel", geo="USA", cat="Home Care", sub="Fabric Softener", parent="",
    pi=0.85, db=0.90, vel=1.20, adp=1.10, n=3,
    retailers=["Walmart", "Kroger", "Amazon"], rw=[.5, .27, .23],
    assets="https://www.suavitel.com/en-us",
    themes="Fragrance-led fabric care with historically strong appeal in Hispanic households.",
    sent="Consistently well rated - 4.5-4.8 stars in the US.",
    q4="Win: Suavitel Complete fabric refresher spray is a named 2026 innovation.",
    innov="Suavitel Complete fabric refresher spray; scent-led line extensions.",
    src=["https://www.walmart.com/brand/suavitel/10002990", U["rem226"], "https://investor.colgatepalmolive.com/news-releases/news-release-details/colgate-palmolive-introduces-new-innovation-ironing-aid-category"])

add(brand="Ajax", geo="USA", cat="Home Care", sub="Surface & Multi-Purpose Cleaners", parent="",
    pi=0.60, db=0.60, vel=0.70, adp=0.50, n=2,
    retailers=["Kroger banners", "Walmart"], rw=[.55, .45],
    assets="https://www.ajax.com/en-us/products",
    themes="Functional value cleaning across bleach-alternative and degreaser variants.",
    sent="Low-visibility value brand - no ratings displayed on retailer brand pages and no trade coverage found, indicating minimal support.",
    q4="Defend: hold value shelf space; home-care innovation is concentrated on Fabuloso and Suavitel.",
    innov="n.a. - no 2026 Ajax-specific innovation named in earnings materials.",
    src=["https://www.ajax.com/en-us/products", "https://www.foodsco.net/p/axion-foaming-action-citrus-liquid-dish-soap/0003500098900"])

add(brand="Murphy Oil Soap", geo="USA", cat="Home Care", sub="Wood & Specialty Care", parent="",
    pi=1.10, db=0.55, vel=0.65, adp=0.45, n=2,
    retailers=["Kroger", "Walmart", "Amazon"], rw=[.4, .35, .25],
    assets="https://www.colgatepalmolive.com/en-us",
    themes="Gentle wood-care efficacy - \"safely cleans finished wood\" to a natural shine without dulling residue.",
    sent="Stable specialist utility brand with grocery, hardware and B2B distribution; retailer pages show no ratings so sentiment evidence is thin.",
    q4="Defend: maintain specialty distribution; no 2026 activity found.",
    innov="n.a. - no 2026 activity found in earnings or trade sources.",
    src=["https://www.kroger.com/p/murphy-oil-soap-wood-cleaner-original/0007048101102", "https://www.colgatepalmolive.com/en-us"])

add(brand="Axion", geo="USA", cat="Home Care", sub="Dish Liquid", parent="",
    pi=0.55, db=0.10, vel=0.40, adp=0.20, n=2,
    retailers=["Kroger banners (Foods Co)"], rw=[1.0],
    assets="https://www.colgatepalmolive.com/en-us",
    themes="Grease-cutting value positioning (\"El Verdadero Arrancagrasa\") aimed at Hispanic shoppers.",
    sent="Minimal US footprint and import pricing distortions mean there is no meaningful US sentiment base.",
    q4="Defend: niche Hispanic-grocery distribution only; core markets are Latin America.",
    innov="n.a. for North America.",
    src=["https://www.foodsco.net/p/axion-foaming-action-citrus-liquid-dish-soap/0003500098900", "https://www.walmart.com/ip/AXION-Authentic-Dish-Soap-Lemon-Lime-Scent-450g-Imported-from-Colombia/14820152528"])

# ---------------- USA PET NUTRITION ---------------------------------------
add(brand="Hill's Science Diet", geo="USA", cat="Pet Nutrition", sub="Dry Dog Food", parent="Hill's Pet Nutrition",
    pi=1.40, db=0.95, vel=1.20, adp=1.15, n=4, seg=SEG_PET,
    retailers=["Chewy", "Petco", "PetSmart", "Amazon", "Veterinary clinics"], rw=[.30, .20, .18, .17, .15],
    assets="https://www.hillspet.com/",
    themes="\"Science is the difference\" and Food, Shelter & Love; \"Because You're Only Human\" campaign and Clear The Shelters 2026 sponsorship.",
    sent="Sharply split - veterinarians endorse it while ConsumerAffairs shows 1.7/5 from 470 reviews with 72% one-star.",
    q4="Defend: reverse the Science Diet dog decline and execute the phased US fresh-food rollout through the vet channel.",
    innov="Science Diet Single Protein refrigerated dog food rolls (chicken, beef, lamb) launched into pet specialty from July 2026.",
    src=["https://www.chewy.com/brands/hills-science-diet-6899", "https://www.hillspet.com/about-us/press-releases/hills-rolls-out-science-diet-refrigerated-dog-food", "https://www.consumeraffairs.com/pets/science_diet.html", U["call226"]])

add(brand="Hill's Prescription Diet", geo="USA", cat="Pet Nutrition", sub="Therapeutic & Prescription Diets", parent="Hill's Pet Nutrition",
    pi=1.90, db=0.80, vel=1.15, adp=1.10, n=4, seg=SEG_PET,
    retailers=["Chewy", "Veterinary clinics", "Petco", "Amazon"], rw=[.33, .30, .20, .17],
    assets="https://www.hillspet.com/prescription-diet",
    themes="Clinical-outcome messaging with a 100% satisfaction guarantee; the July 2026 \"Try Again\" campaign targets veterinary professionals.",
    sent="Professionally trusted and the growth engine within Hill's, though it inherits broader consumer criticism on ingredients and price.",
    q4="Win: extend therapeutic momentum and vet-channel advocacy.",
    innov="k/d + Derm Complete for dogs and k/d + z/d Hydrolyzed for cats (June 2026); ONC Care line.",
    src=["https://www.chewy.com/brands/hills-prescription-diet-6879", "https://www.hillspet.com/prescription-diet", "https://screenmag.com/hills-pet-nutrition-and-vml-launch-veterinary-focused-try-again/", "https://www.myvetcandy.com/news/2026/6/9/hills-pet-nutrition-introduces-new-therapeutic-diets-for-pets-with-kidney-disease-and-sensitivities"])

add(brand="Hill's Bioactive Recipe", geo="USA", cat="Pet Nutrition", sub="Dry Dog Food", parent="Hill's Pet Nutrition",
    pi=1.60, db=0.35, vel=0.55, adp=0.40, n=2, seg=SEG_PET,
    retailers=["Chewy", "Veterinary clinics"], rw=[.6, .4],
    assets="https://www.chewy.com/brands/hills-6874",
    themes="Functional, bioactive-nutrition positioning within the Hill's science platform.",
    sent="Low visibility - the line is absent from Hill's 2026 launch communications, so consumer signal is minimal.",
    q4="Defend: maintain listing; not featured in 2026 innovation disclosures.",
    innov="n.a. - not featured in 2026 innovation disclosures.",
    src=["https://www.chewy.com/brands/hills-6874", "https://www.hillspet.com/about-us/press-releases/hills-pet-nutrition-unveils-prescription-diet-onc-care"])

add(brand="Hill's Healthy Advantage", geo="USA", cat="Pet Nutrition", sub="Dry Dog Food", parent="Hill's Pet Nutrition",
    pi=1.50, db=0.30, vel=0.50, adp=0.35, n=1, seg=SEG_PET,
    retailers=["Veterinary clinics", "Chewy"], rw=[.65, .35],
    assets="https://www.chewy.com/brands/hills-6874",
    themes="Vet-channel everyday wellness nutrition inside the Hill's science platform.",
    sent="Low visibility; no consumer review base surfaced in the research.",
    q4="Defend: vet-channel maintenance line.",
    innov="n.a.",
    src=["https://www.chewy.com/brands/hills-6874"])

add(brand="Prime100", geo="USA", cat="Pet Nutrition", sub="Wet Dog Food", parent="",
    pi=2.20, db=0.15, vel=0.60, adp=0.50, n=3, seg=SEG_PET,
    retailers=["Select pet specialty (north-east)", "Prime100 DTC"], rw=[.6, .4],
    assets="https://prime100.com/",
    themes="Single-protein, fresh-never-frozen, vet-and-nutritionist-designed diets, \"proudly made in the USA\".",
    sent="Early-stage US credibility built on veterinary-specialist design, but supply is constrained with salmon production paused.",
    q4="Win: act as the technology platform for Hill's US fresh entry while expanding its own pet-specialty footprint.",
    innov="SPD Fresh Rolls in five proteins; fresh-never-frozen manufacturing.",
    src=["https://prime100.com/pages/faq", "https://prime100.com/pages/where-to-buy", U["slides226"]])

# ---------------- CANADA ---------------------------------------------------
add(brand="Colgate", geo="Canada", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.00, db=1.00, vel=1.25, adp=1.25, n=3,
    retailers=["Walmart Canada", "Shoppers Drug Mart", "Amazon.ca", "Well.ca"], rw=[.40, .25, .22, .13],
    assets="https://www.colgate.com/en-ca",
    themes="Canadian site leads on Optic White Renewal enamel-nourishing whitening and Total Active Prevention cavity/gingivitis messaging.",
    sent="Positive at retail (4.5-4.7 stars on walmart.ca across up to 2,392 reviews), though the Canadian Trustpilot page carries formula and efficacy complaints.",
    q4="Defend: same North America agenda as the US, including CDA-validated Total Whitening claims in market.",
    innov="Optic White Renewal and Total relaunch claims validated by the Canadian Dental Association seal programme.",
    src=["https://www.walmart.ca/en/c/brand/colgate", "https://www.colgate.com/en-ca", "https://www.cda-adc.ca/EN/oral_health/seal/products/product_page.asp?product=301"])

colgate_sub("Canada", "Colgate Total", "Colgate Total", "Toothpaste", 1.10, 1.00, 1.05, 1.25, 3,
    ["Walmart Canada", "Shoppers Drug Mart", "Amazon.ca"], [.45, .30, .25],
    "https://www.colgate.com/en-ca/colgate-total",
    "\"Patented preventative technology\" fighting bacteria on teeth, tongue, cheeks and gums, with CDA-validated whitening claims.",
    "Carries the same reformulation overhang as the US line, with formula and efficacy complaints on the Canadian Trustpilot page.",
    "Defend: rebuild share after the reformulation and complete distribution of the relaunched Total.",
    "Relaunched Total formula with CDA-validated Total Whitening claims.",
    ["https://www.colgate.com/en-ca/colgate-total", "https://www.cda-adc.ca/EN/oral_health/seal/products/product_page.asp?product=301", "https://ca.trustpilot.com/review/colgate.com"])

colgate_sub("Canada", "Colgate Optic White", "Colgate Optic White", "Whitening", 1.35, 0.95, 1.10, 1.30, 2,
    ["Walmart Canada", "Shoppers Drug Mart", "Amazon.ca"], [.45, .30, .25],
    "https://www.colgate.com/en-ca/optic-white",
    "Premium whitening ladder - \"removes 15 years of stains in just 1 week\" across toothpaste, mouthwash, brushes and at-home treatments.",
    "Claim-led and well merchandised in Canada; no adverse Canadian coverage found beyond general direct-brand complaints.",
    "Win: scale the premium whitening ladder in North America.",
    "Optic White Pro Series with ActivShine and the Purple line rollout.",
    ["https://www.colgate.com/en-ca/optic-white", U["rem226"]])

colgate_sub("Canada", "Colgate Optic White Renewal", "Colgate Renewal", "Whitening", 1.60, 0.70, 0.85, 1.00, 2,
    ["Walmart Canada", "colgate.com/en-ca"], [.65, .35],
    "https://www.colgate.com/en-ca/products/toothpaste/ow-renewal",
    "Enamel nourishment plus deep whitening; 3% hydrogen peroxide pens delivering 35 nightly treatments.",
    "Active and supported in Canada even though the standalone US Renewal line has been withdrawn, so Canadian equity is intact.",
    "Win: premium whitening trade-up in Canada.",
    "Optic White Renewal pens and enamel-nourishing whitening formats.",
    ["https://www.colgate.com/en-ca/products/toothpaste/ow-renewal", "https://www.walmart.ca/en/c/brand/colgate"])

colgate_sub("Canada", "Colgate Max Fresh", "Colgate Max Fresh", "Toothpaste", 0.95, 0.90, 1.00, 0.85, 2,
    ["Walmart Canada", "Amazon.ca"], [.6, .4],
    "https://www.colgate.com/en-ca/colgate-max-fresh",
    "\"10X longer-lasting cool\" Ultrafreeze technology with mini breath strips across Clean Mint, Cool Mint and Knockout.",
    "Mainstream freshness workhorse with routine availability and no adverse Canadian coverage found.",
    "Defend: value-tier freshness defence inside the North America price-gap plan.",
    "Ultrafreeze breath-strip formats.",
    ["https://www.colgate.com/en-ca/colgate-max-fresh", "https://www.amazon.ca/Colgate-MaxFresh-Toothpaste-Breath-Strips/dp/B07KF6C2M9"])

colgate_sub("Canada", "Colgate Sensitive Pro-Relief", "Colgate Sensitive Pro-Relief", "Toothpaste", 1.45, 0.85, 1.00, 1.00, 3,
    ["Well.ca", "Walmart Canada", "Shoppers Drug Mart"], [.35, .40, .25],
    "https://www.colgate.com/en-ca/sensitive-pro-relief",
    "Clinically framed instant and lasting sensitivity relief with a Canadian Dental Association seal listing.",
    "Well regarded and CDA-validated; sold at CAD $6.99 through Well.ca and mass retail.",
    "Win: premium therapeutic tier within the 2026/2027 North America innovation slate.",
    "Pro-Relief sensitivity technology line extensions.",
    ["https://well.ca/products/colgate-sensitive-pro-relief_131500.html", "https://www.cda-adc.ca/EN/oral_health/seal/products/product_page.asp?product=234", "https://www.colgate.com/en-ca/sensitive-pro-relief"])

colgate_sub("Canada", "Colgate PreviDent", "Colgate PreviDent", "Professional & Therapeutic", 2.20, 0.35, 0.60, 0.60, 2,
    ["Dental professional channel", "Pharmacy (Rx)"], [.6, .4],
    "https://www.colgateprofessional.ca/en-ca/products/products-list/colgate-prevident-5000-plus-rx-only",
    "Clinical evidence messaging - root-caries remineralization of 38% at 3 months and 57% at 6 months.",
    "Professional-channel credibility; Rx-gated with no consumer review base.",
    "Win: build the professional channel through dental distribution in 2026.",
    "PreviDent 5000 Plus and 5000 Sensitive Rx line.",
    ["https://www.colgateprofessional.ca/en-ca/products/products-list/colgate-prevident-5000-plus-rx-only", "https://www.colgate.com/en-ca/products/prescription-only-products/colgate-prevident-plus"])

colgate_sub("Canada", "Colgate PerioGard", "Colgate PerioGard", "Professional & Therapeutic", 1.70, 0.55, 0.75, 0.70, 2,
    ["Walmart Canada", "Pharmacy", "Dental professional channel"], [.4, .35, .25],
    "https://www.colgate.com/en-ca/periogard",
    "Gum-health efficacy - claims of significant reduction in gum bleeding and inflammation across PerioGard and PerioGardSF.",
    "Professional endorsement carries the brand; consumer sentiment base is thin in Canada.",
    "Win: PerioGard was launched through the profession and moves through distribution during 2026.",
    "PerioGard / PerioGardSF gum-health toothpaste and rinse.",
    ["https://www.colgate.com/en-ca/periogard", "https://www.fool.com/earnings/call-transcripts/2026/01/30/colgate-palmolive-cl-q4-2025-earnings-transcript/"])

add(brand="Tom's of Maine", geo="Canada", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.30, db=0.45, vel=0.70, adp=0.90, n=2,
    retailers=["Walmart Canada", "Well.ca"], rw=[.7, .3],
    assets="https://www.tomsofmaine.ca/en-ca",
    themes="Purpose-led naturals positioning; the Canadian site states the brand donates 10% of profits.",
    sent="Steady niche naturals presence at CAD $5.97-$11.97 on walmart.ca with no adverse coverage found.",
    q4="Win: naturals credibility and efficacy proof in whitening and deodorant.",
    innov="WHITEN+ natural whitening and natural deodorant efficacy upgrades carried over from the US line.",
    src=["https://www.walmart.ca/en/c/brand/tom-s-of-maine", "https://www.tomsofmaine.ca/en-ca"])

add(brand="hello", geo="Canada", cat="Oral Care", sub="Toothpaste", parent="",
    pi=1.25, db=0.40, vel=0.75, adp=1.15, n=2,
    retailers=["Walmart Canada", "Shoppers Drug Mart", "Amazon.ca"], rw=[.45, .35, .20],
    assets="https://www.hello-products.com/",
    themes="\"Everyday Yay\" brought to Canada with the June 2025 launch of dragon dazzle kids toothpaste and sunny daze deodorant.",
    sent="New-entrant buzz rather than an established base - launched June 4 2025 and live at Walmart Canada at CAD $5.97-$9.98.",
    q4="Win: build Canadian distribution behind the launch assortment and Whipped toothpaste.",
    innov="Whipped toothpaste texture innovation and fluoride-free/naturals formats.",
    src=["https://www.newswire.ca/news-releases/hello-r-brings-everyday-yay-to-daily-routines-across-canada-with-two-new-launches-847409254.html", "https://www.walmart.ca/en/c/brand/hello"])

add(brand="Speed Stick", geo="Canada", cat="Personal Care", sub="Antiperspirant & Deodorant", parent="",
    pi=0.80, db=0.90, vel=1.05, adp=0.85, n=2,
    retailers=["Walmart Canada", "Well.ca", "Shoppers Drug Mart"], rw=[.5, .25, .25],
    assets="https://www.colgatepalmolive.ca/en-ca/local-brands/speed-stick/products",
    themes="Value/performance men's deodorant positioning carried on Colgate's Canadian local-brand pages.",
    sent="Everyday value staple at CAD $5.99-$13.49 on Well.ca with no adverse Canadian coverage found.",
    q4="Defend: hold mass deodorant shelf and price gaps.",
    innov="n.a. - no Canadian innovation disclosed in fetched sources.",
    src=["https://well.ca/brand/speed-stick.html", "https://www.colgatepalmolive.ca/en-ca/local-brands/speed-stick/products"])

add(brand="Lady Speed Stick", geo="Canada", cat="Personal Care", sub="Antiperspirant & Deodorant", parent="",
    pi=0.75, db=0.80, vel=0.90, adp=0.60, n=1,
    retailers=["Walmart Canada"], rw=[1.0],
    assets="https://www.colgatepalmolive.ca/en-ca",
    themes="Value women's deodorant line maintained without a dedicated 2025-2026 campaign.",
    sent="Priced from CAD $3.77 with routine Walmart Canada availability and no adverse coverage found.",
    q4="Defend: value shelf maintenance.",
    innov="n.a.",
    src=["https://www.walmart.ca/en/c/brand/lady-speed-stick"])

add(brand="Softsoap", geo="Canada", cat="Personal Care", sub="Liquid Hand Soap", parent="",
    pi=0.85, db=0.90, vel=1.10, adp=0.90, n=2,
    retailers=["Walmart Canada", "Shoppers Drug Mart", "Well.ca"], rw=[.55, .25, .20],
    assets="https://www.softsoap.com/en-us",
    themes="Sustainability and plastic reduction - tablet foaming hand soap and refillable aluminium bottles.",
    sent="Stable mass performer at CAD $4.28-$10.28 with no adverse Canadian coverage found.",
    q4="Defend: sustainable-format refills and mass distribution.",
    innov="Tablet-based foaming hand soap and refillable aluminium packaging.",
    src=["https://www.walmart.ca/en/c/brand/softsoap", "https://www.colgatepalmolive.ca/en-ca"])

add(brand="Irish Spring", geo="Canada", cat="Personal Care", sub="Bar Soap", parent="",
    pi=0.90, db=0.85, vel=1.30, adp=1.10, n=2,
    retailers=["Walmart Canada", "Shoppers Drug Mart"], rw=[.65, .35],
    assets="https://www.colgatepalmolive.ca/en-ca",
    themes="Relaunched formulas, fragrances, logo and packaging carried into Canada behind the brand's first Super Bowl ad.",
    sent="Very strong in Canada - individual SKUs carry up to 4,736 reviews on walmart.ca.",
    q4="Win: sustain the relaunched range and elevated media presence.",
    innov="Reformulated bars and body washes with a new fragrance range.",
    src=["https://www.walmart.ca/fr/c/brand/irish-spring", "https://www.adweek.com/brand-marketing/irish-spring-first-super-bowl-ad/"])

add(brand="Skin Bracer", geo="Canada", cat="Personal Care", sub="Shaving & Grooming", parent="",
    pi=0.70, db=0.25, vel=0.50, adp=0.30, n=2,
    retailers=["Amazon.ca", "Independent grocery"], rw=[.6, .4],
    assets="https://www.amazon.ca/Mennen-Skin-Bracer-5-oz/dp/B003YTBOJU",
    themes="Classic heritage aftershave with no active campaign found.",
    sent="Loyal nostalgic base - 4.7/5 across 804 ratings for a multipack on Amazon.ca - but distribution is patchy.",
    q4="Defend: harvest heritage distribution.",
    innov="n.a.",
    src=["https://www.amazon.ca/Mennen-Skin-Bracer-5-oz/dp/B003YTBOJU", "https://a1grocery.ca/product/skin-bracer-original-after-shave-100ml/"])

add(brand="EltaMD", geo="Canada", cat="Skin Care", sub="Sun Care & SPF", parent="",
    pi=2.60, db=0.55, vel=1.30, adp=1.05, n=2,
    retailers=["Amazon.ca", "WeDoSkin", "Professional channel"], rw=[.5, .25, .25],
    assets="https://eltamd.com/",
    themes="Dermatologist-recommended professional sunscreen positioning carried through authorized Canadian resellers.",
    sent="Very strong - UV Clear carries 42,034 reviews and is stocked and sold directly by Amazon.ca at CAD $68-$82.",
    q4="Win: clinical-proof storytelling behind UV Clear efficacy data.",
    innov="Acne/oil-control efficacy claims for UV Clear; professional-channel expansion.",
    src=["https://www.amazon.ca/EltaMD-Broad-Spectrum-Acne-Prone-Dermatologist-Recommended-Mineral-Based/dp/B002MSN3QQ", "https://wedoskin.ca/collections/elta-md"])

add(brand="PCA SKIN", geo="Canada", cat="Skin Care", sub="Professional & Clinical", parent="",
    pi=2.80, db=0.40, vel=0.80, adp=0.95, n=3,
    retailers=["Walmart Canada", "WeDoSkin", "Dermacart"], rw=[.35, .35, .30],
    assets="https://www.pcaskin.com/about",
    themes="Professional/esthetician authority and results-driven medical-grade skincare.",
    sent="Positive but thin - 4.36/5 from 11 reviews on walmart.ca, with credibility carried by professional endorsement.",
    q4="Win: life-stage skin health via MGF Age Renewal Cream.",
    innov="Menopause/estrogen-depleted skin (MGF Age Renewal Cream) and the professional peel portfolio.",
    src=["https://www.walmart.ca/en/c/brand/pca-skin", "https://wedoskin.ca/collections/pca-skin", "https://dermacart.ca/collections/pca-skin"])

add(brand="Filorga", geo="Canada", cat="Skin Care", sub="Serums & Treatments", parent="",
    pi=3.00, db=0.55, vel=0.85, adp=0.80, n=3,
    retailers=["Walmart Canada", "Filorga DTC (ca.filorga.com)", "Amazon.ca"], rw=[.40, .35, .25],
    assets="https://ca.filorga.com/shop/",
    themes="NCEF-concentrated multi-correcting skincare and antioxidant serums with a \"Radiant & Firm Skin in 10 Days\" claim.",
    sent="Positive where distributed - 4.6-4.7 stars across 39 products on walmart.ca - and Canada is now the brand's healthy North American market.",
    q4="Win: Canada is the functioning North American route to market while the US channel is rebuilt.",
    innov="n.a. - no 2026 North America innovation disclosed.",
    src=["https://ca.filorga.com/shop/", "https://www.walmart.ca/en/c/brand/filorga", "https://www.amazon.ca/FILORGA-TIME-FILLER-5XP-GEL-CREAM-Combination/dp/B08B81PYZ2"])

add(brand="Palmolive", geo="Canada", cat="Home Care", sub="Dish Liquid", parent="",
    pi=0.90, db=0.90, vel=1.15, adp=0.95, n=3,
    retailers=["Walmart Canada", "Well.ca", "Loblaw banners"], rw=[.5, .25, .25],
    assets="https://www.palmolive.com/en-ca",
    themes="Grease-cutting dish efficacy carried on the Canadian brand site.",
    sent="Reliable value staple at CAD $4.99-$5.79 with no adverse Canadian coverage found.",
    q4="Win: convenience-format dish innovation follows the US E-Z Pump launch.",
    innov="Palmolive Dish E-Z Pump dispensing format.",
    src=["https://well.ca/brand/palmolive.html", "https://www.palmolive.com/en-ca", U["remfy25"]])

add(brand="Fabuloso", geo="Canada", cat="Home Care", sub="Surface & Multi-Purpose Cleaners", parent="",
    pi=0.95, db=0.75, vel=1.15, adp=1.15, n=3,
    retailers=["Walmart Canada", "Real Canadian Superstore"], rw=[.6, .4],
    assets="https://www.fabuloso.com/en-us",
    themes="Scent-led multi-purpose cleaning; the \"Make Your World More Fabuloso\" platform runs across North America in 2026.",
    sent="Positive at retail but the 2023 Health Canada recall of the Lavender 1.65L SKU remains the notable Canadian event.",
    q4="Win: push form and scent extensions, a named 2026 growth driver.",
    innov="Fabuloso 3-in-1 Clean Spray, Watermelon and Ultra Frescura liquids.",
    src=["https://www.walmart.ca/en/c/brand/fabuloso", "https://recalls-rappels.canada.ca/en/alert-recall/fabuloso-multi-purpose-cleaner-lavender-scent-165l-recalled-due-potential-microbial", "https://screenmag.com/vml-and-colgate-palmolive-launch-make-your-world-more-fabuloso-for-fabuloso/"])

add(brand="Suavitel", geo="Canada", cat="Home Care", sub="Fabric Softener", parent="",
    pi=0.85, db=0.55, vel=1.20, adp=0.90, n=2,
    retailers=["Walmart Canada"], rw=[1.0],
    assets="https://www.walmart.ca/en/c/brand/suavitel",
    themes="Fragrance-led fabric conditioning in a compact six-SKU Canadian range.",
    sent="Consistently well rated - 4.63-4.84 across four rated SKUs on walmart.ca.",
    q4="Win: Suavitel Complete fabric refresher spray is a named 2026 innovation.",
    innov="Suavitel Complete fabric refresher spray.",
    src=["https://www.walmart.ca/en/c/brand/suavitel", U["rem226"]])

add(brand="Ajax", geo="Canada", cat="Home Care", sub="Surface & Multi-Purpose Cleaners", parent="",
    pi=0.70, db=0.60, vel=0.70, adp=0.50, n=2,
    retailers=["Walmart Canada", "Amazon.ca"], rw=[.65, .35],
    assets="https://www.walmart.ca/en/c/brand/ajax",
    themes="Functional value cleaning across multi-purpose, bleach-alternative and super-degreaser SKUs at CAD $7.99.",
    sent="Low-visibility value brand - no ratings displayed on the Walmart Canada brand page and no trade coverage found.",
    q4="Defend: hold value shelf space.",
    innov="n.a. - no 2026 Ajax-specific innovation named.",
    src=["https://www.walmart.ca/en/c/brand/ajax", "https://www.amazon.ca/Ajax-Powder-Cleanser-Bleach-Pack/dp/B0151WUFR4"])

add(brand="Murphy Oil Soap", geo="Canada", cat="Home Care", sub="Wood & Specialty Care", parent="",
    pi=1.10, db=0.60, vel=0.60, adp=0.40, n=3,
    retailers=["Home Depot Canada", "Amazon.ca", "Uline.ca", "Loblaw banners"], rw=[.35, .25, .20, .20],
    assets="https://www.homedepot.ca/product/murphy-oil-soap-liquid-original-950ml/1000753060",
    themes="Gentle wood-care efficacy - cleans to a natural shine without leaving a dulling residue.",
    sent="Stable specialist utility brand across hardware, grocery and B2B channels; retailer pages display no ratings.",
    q4="Defend: maintain specialty and B2B distribution.",
    innov="n.a. - no 2026 activity found.",
    src=["https://www.homedepot.ca/product/murphy-oil-soap-liquid-original-950ml/1000753060", "https://www.uline.ca/Product/Detail/S-25448/Floor-and-Carpet-Cleaners/Murphy-Oil-Soap-4-3-L", "https://www.amazon.ca/Murphy-Original-Formula-Liquid-Murphys/dp/B0145NIIH4"])

add(brand="Arctic Power", geo="Canada", cat="Home Care", sub="Laundry Detergent", parent="",
    pi=0.80, db=0.80, vel=1.20, adp=0.80, n=2,
    retailers=["Walmart Canada", "Canadian Tire"], rw=[.65, .35],
    assets="https://www.colgatepalmolive.ca/en-ca",
    themes="Cold-water washing performance and energy saving, merchandised around 88-load value packs.",
    sent="Well regarded in Canada - flagged \"Top Rated\" at Canadian Tire with a 49-review base and 4.1-5.0 ratings at Walmart Canada.",
    q4="Defend: Canada-only laundry franchise inside the North America division agenda.",
    innov="n.a. - no brand-specific 2026 disclosure found.",
    src=["https://www.walmart.ca/en/c/brand/arctic-power", "https://www.canadiantire.ca/en/pdp/arctic-power-cold-water-liquid-laundry-detergent-assorted-scents-88-load-3-96-l-1531554p.html"])

add(brand="Fleecy", geo="Canada", cat="Home Care", sub="Fabric Softener", parent="",
    pi=0.75, db=0.70, vel=1.00, adp=0.60, n=2,
    retailers=["Walmart Canada"], rw=[1.0],
    assets="https://www.colgatepalmolive.ca/en-ca/local-brands/fleecy/products",
    themes="Softness and static control in a value fabric-care line.",
    sent="Everyday value brand with routine Walmart Canada availability at CAD $5.97-$12.97; no adverse coverage found.",
    q4="Defend: Canada-only value fabric-care franchise.",
    innov="n.a. - no 2026 brand-specific disclosure found.",
    src=["https://www.walmart.ca/fr/c/brand/fleecy", "https://www.colgatepalmolive.ca/en-ca/local-brands/fleecy/products"])

add(brand="Hill's Science Diet", geo="Canada", cat="Pet Nutrition", sub="Dry Dog Food", parent="Hill's Pet Nutrition",
    pi=1.40, db=0.85, vel=1.10, adp=1.10, n=2, seg=SEG_PET,
    retailers=["PetSmart Canada", "Veterinary clinics", "Amazon.ca"], rw=[.45, .35, .20],
    assets="https://www.hillspet.com/",
    themes="\"Science is the difference\" science-led everyday wellness nutrition carried through pet specialty and vets.",
    sent="Vet-endorsed but exposed to the same consumer ingredient criticism as the US line.",
    q4="Defend: reverse the Science Diet dog slowdown seen globally in Q2 2026.",
    innov="Science Diet refrigerated single-protein rolls follow the US pet-specialty launch.",
    src=["https://www.petsmart.ca/featured-brands/hills-science-diet", U["call226"]])

add(brand="Hill's Prescription Diet", geo="Canada", cat="Pet Nutrition", sub="Therapeutic & Prescription Diets", parent="Hill's Pet Nutrition",
    pi=1.90, db=0.70, vel=1.05, adp=1.05, n=2, seg=SEG_PET,
    retailers=["PetSmart Canada", "Veterinary clinics"], rw=[.45, .55],
    assets="https://www.hillspet.com/prescription-diet",
    themes="Clinical-outcome messaging to vets and pet parents; 92 cat therapeutic SKUs listed at PetSmart Canada.",
    sent="Professionally trusted and the growth engine within Hill's; consumer criticism of Hill's ingredients carries across.",
    q4="Win: extend therapeutic momentum and vet-channel advocacy.",
    innov="k/d + Derm Complete for dogs and k/d + z/d Hydrolyzed for cats.",
    src=["https://www.petsmart.ca/cat/food-and-treats/veterinary-diets/hills-prescription-diet/f/brand/hill's%20science%20diet", "https://www.myvetcandy.com/news/2026/6/9/hills-pet-nutrition-introduces-new-therapeutic-diets-for-pets-with-kidney-disease-and-sensitivities"])

# ---------------------------------------------------------------- allocation
for b in B:
    b.setdefault("seg", SEG_OPHC)
    b.setdefault("parent", "")
    b.setdefault("portfolio", None)
    b["is_sub"] = b["parent"] == "Colgate"
    if b["is_sub"]:
        b["sku"] = SKU.get(("PORTFOLIO::" + b["portfolio"], b["geo"]), 1)
    else:
        b["sku"] = sku_for(b["brand"], b["geo"])

sales = {}
# 1. allocate each category pool across its top-level allocation units
for geo in ("USA", "Canada"):
    for cat in ("Oral Care", "Personal Care", "Skin Care", "Home Care", "Pet Nutrition"):
        units = [b for b in B if b["geo"] == geo and b["cat"] == cat and not b["is_sub"]]
        if not units:
            continue
        inp = {b["brand"]: dict(sku_count=b["sku"], price_index=b["pi"],
                                distribution_breadth=b["db"], velocity_index=b["vel"])
               for b in units}
        res = allocate_category(POOL[(geo, cat)], inp)
        for b in units:
            sales[(b["brand"], geo)] = res[b["brand"]]

# 2. split the Colgate master estimate across ALL its portfolios; emit only the
#    researched sub-brands (residual portfolios stay inside the master row).
for geo in ("USA", "Canada"):
    ports = {k[0][len("PORTFOLIO::"):]: v for k, v in SKU.items()
             if k[0].startswith("PORTFOLIO::") and k[1] == geo}
    subs = [b for b in B if b["geo"] == geo and b["is_sub"]]
    pmap = {b["portfolio"]: b for b in subs}
    for b in subs:
        if b["portfolio"] not in ports:
            # portfolio absent from the SKU inventory (Sheet 2 does not cover
            # power-brush hardware); documented shelf estimate instead.
            ports[b["portfolio"]] = HUM_SKU_EST.get((b["portfolio"], geo), 3)
            b["sku"] = ports[b["portfolio"]]
    inp = {}
    for p, n in ports.items():
        ref = pmap.get(p)
        inp[p] = dict(sku_count=n,
                      price_index=ref["pi"] if ref else 1.0,
                      distribution_breadth=ref["db"] if ref else 0.85,
                      velocity_index=ref["vel"] if ref else 1.0)
    res = allocate_category(sales[("Colgate", geo)], inp)
    for b in subs:
        sales[(b["brand"], geo)] = res[b["portfolio"]]

# 3. advertising — allocated over top-level units, then split inside Colgate
geo_total = {g: sum(sales[(b["brand"], g)] for b in B if b["geo"] == g and not b["is_sub"])
             for g in ("USA", "Canada")}
NA_AD_INTENSITY = 1.10
ads = {}
for geo in ("USA", "Canada"):
    units = [b for b in B if b["geo"] == geo and not b["is_sub"]]
    bs = {b["brand"]: sales[(b["brand"], geo)] for b in units}
    mult = {b["brand"]: b["adp"] for b in units}
    share = (geo_total[geo] / WW_SALES) * NA_AD_INTENSITY
    res = allocate_advertising(AD_WW, bs, share, mult)
    for b in units:
        ads[(b["brand"], geo)] = res[b["brand"]]
    subs = [b for b in B if b["geo"] == geo and b["is_sub"]]
    if subs:
        tilt = {b["brand"]: sales[(b["brand"], geo)] * b["adp"] for b in subs}
        # master ad pool shared out to sub-brands pro-rata to tilted sales, capped
        # by the master's own ad allocation (sub-brands are components).
        tot = sum(tilt.values()) or 1.0
        master_ad = ads[("Colgate", geo)]
        master_sales = sales[("Colgate", geo)]
        sub_frac = sum(sales[(s["brand"], geo)] for s in subs) / master_sales
        for b in subs:
            ads[(b["brand"], geo)] = master_ad * sub_frac * (tilt[b["brand"]] / tot)

# ---------------------------------------------------------------- rows
COLS = ["record_id", "geo_market", "reporting_segment", "category", "sub_category",
        "brand_name", "parent_brand", "est_annual_net_sales_usd_mm", "sales_estimate_method",
        "pct_sales_instore", "pct_sales_online", "top_retailers_ranked",
        "est_retailer_spend_usd_mm", "est_marketing_spend_usd_mm", "marketing_spend_pct_of_sales",
        "share_of_market_pct", "share_of_category_pct", "brand_assets_url", "marketing_themes",
        "brand_sentiment_today", "q4_focus_defend_or_win", "innovation_areas", "source_type",
        "confidence", "primary_sources", "date_collected"]

def slug(s):
    return (s.upper().replace("'", "").replace(".", "").replace("&", "AND")
            .replace(" ", "-"))

rows = []
for b in B:
    geo, brand = b["geo"], b["brand"]
    s = sales[(brand, geo)]
    ad = ads[(brand, geo)]
    instore, online = channel_split(b["cat"], geo)
    rspend = "|".join(f"{s*w:.1f}" for w in b["rw"])
    if b["is_sub"]:
        method = "sub_brand_split_within_master (component of the Colgate master row; not additive)"
    elif b["cat"] == "Pet Nutrition":
        method = "reported_segment -> hills_na_share -> country_split -> allocate_category"
    else:
        method = "reported_division -> country_split -> category_weight -> allocate_category"
    reported = b.get("reported_cat_share")
    cat_share = reported if reported else 100.0 * s / POOL[(geo, b["cat"])]
    st = "Reported" if reported else ("Mixed" if not b["is_sub"] else "Modeled")
    if b["cat"] == "Pet Nutrition":
        st = "Mixed"
    conf = confidence_for(bool(reported), b["sku"], b["n"])
    rows.append({
        "record_id": f"CL-{slug(brand)}-{'USA' if geo=='USA' else 'CA'}",
        "geo_market": geo, "reporting_segment": b["seg"], "category": b["cat"],
        "sub_category": b["sub"], "brand_name": brand, "parent_brand": b["parent"],
        "est_annual_net_sales_usd_mm": round(s, 1), "sales_estimate_method": method,
        "pct_sales_instore": round(instore * 100, 1), "pct_sales_online": round(online * 100, 1),
        "top_retailers_ranked": "|".join(b["retailers"]), "est_retailer_spend_usd_mm": rspend,
        "est_marketing_spend_usd_mm": round(ad, 1),
        "marketing_spend_pct_of_sales": round(100 * ad / s, 1) if s else 0.0,
        "share_of_market_pct": round(100 * s / geo_total[geo], 2),
        "share_of_category_pct": round(cat_share, 2),
        "brand_assets_url": b["assets"], "marketing_themes": b["themes"],
        "brand_sentiment_today": b["sent"], "q4_focus_defend_or_win": b["q4"],
        "innovation_areas": b["innov"], "source_type": st, "confidence": conf,
        "primary_sources": "|".join(b["src"]), "date_collected": DATE,
    })

rows.sort(key=lambda r: (r["geo_market"], r["category"], -r["est_annual_net_sales_usd_mm"]))
p1 = os.path.join(OUT, "sheet1_brand_positioning.csv")
with open(p1, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------- excluded
EX = [
 ("Sorriso", "USA", "Brazil-only Colgate toothpaste brand; no US retail listing found in Walmart's toothpaste-by-brand index.", "https://www.walmart.com/cp/toothpaste-by-brand/9965224"),
 ("Sorriso", "Canada", "Brazil-only brand; named in the 10-K brand list but not sold in Canada.", U["tenk"]),
 ("Colgate Duraphat", "USA", "Not marketed to US consumers; the US high-fluoride equivalent is PreviDent.", "https://www.colgate.com/en-us/prevident"),
 ("Colgate Duraphat", "Canada", "Health Canada DIN 02232201 status 'Cancelled Pre Market' since 2017-08-31.", "https://dhpp.hpfb-dgpsa.ca/dhpp/resource/51727"),
 ("Sanex", "USA", "No company distribution; Europe-managed brand with third-party import listings only.", "https://www.amazon.ca/Sanex-Zero-Skin-Shower-250Ml/dp/B00BM64L60"),
 ("Sanex", "Canada", "No company distribution; only a third-party Amazon.ca import listing found.", "https://www.amazon.ca/Sanex-Zero-Skin-Shower-250Ml/dp/B00BM64L60"),
 ("Protex", "USA", "No company distribution; the only US listing is an out-of-stock Walmart marketplace multipack.", "https://www.walmart.com/ip/Protex-Bar-Soap-Oats-for-Both-Men-and-Women-Adults-and-Children-3-12-Pack-3-7-oz/2825426583"),
 ("Protex", "Canada", "No Canadian retail listing found; brand is managed for Latin America.", "https://www.colgatepalmolive.com/en-us/guatemala/csfeed/0099176922780"),
 ("elmex", "USA", "No company distribution; Walmart marketplace import from third-party seller ChePha only.", "https://www.walmart.com/ip/Elmex-Sensitive-Professional-75ml/184462547"),
 ("elmex", "Canada", "No company distribution; Amazon.ca third-party import sellers (mfr GABA) only.", "https://www.amazon.ca/Elmex-sensitiv-professional-toothpaste-Health/dp/B0041M3L0Y"),
 ("meridol", "USA", "No company distribution; Walmart marketplace import from seller iogga Co only.", "https://www.walmart.com/ip/Meridol-Pur-Toothpaste-2-x-75ml/596602236"),
 ("meridol", "Canada", "No company distribution; German-sourced Amazon.ca import listings only.", "https://www.amazon.ca/Authentic-German-Gaba-Meridol-Toothpaste/dp/B000WHQEDS"),
 ("Palmolive (personal care)", "USA", "Palmolive personal-care (bar soap, shower gel, shampoo) is a non-US line; palmolive.com/en-us carries dish only.", "https://www.palmolive.com/en-us"),
 ("Palmolive (personal care)", "Canada", "No Canadian personal-care Palmolive listing found; Canadian brand site is dish only.", "https://www.palmolive.com/en-ca"),
 ("Arctic Power", "USA", "Canada-only laundry brand; absent from the US corporate brand roster.", "https://www.colgatepalmolive.com/en-us"),
 ("Axion", "Canada", "No Canadian retail listing confirmed; brand core markets are Latin America.", U["tenk"]),
 ("Ultra Brite", "Canada", "No Canadian retail distribution confirmed; only cross-border marketplace/eBay import listings found.", "https://www.ebay.ca/itm/115235074163"),
 ("Colgate Renewal", "USA", "Standalone US line listed as 'currently unavailable' on Amazon; equity consolidated into Optic White.", "https://www.amazon.com/Colgate-Renewal-Toothpaste-Enamel-Fortify/dp/B08P3HX4QB"),
 ("Colgate hum", "Canada", "No Canadian retail listing confirmed for the connected-brush line.", "https://shop.colgate.com/products/hum-adult-smart-toothbrush-replacement-brush-heads"),
 ("Afta", "Canada", "No Canadian retail listing found for the Mennen pre-electric shave lotion.", "https://www.kroger.com/p/afta-pre-electric-by-mennen-original-scent-shave-lotion/0002220000276"),
 ("Fleecy", "USA", "Listed on the US corporate roster but no US retail listing confirmed.", "https://www.colgatepalmolive.com/en-us"),
 ("Hill's Bioactive Recipe", "Canada", "Canadian availability not confirmed; line appears only on US Hill's/Chewy listings.", "https://www.chewy.com/brands/hills-6874"),
 ("Hill's Healthy Advantage", "Canada", "Canadian availability not confirmed; vet-channel line evidenced in the US only.", "https://www.chewy.com/brands/hills-6874"),
 ("Prime100", "Canada", "Canadian availability not confirmed; US distribution is select north-east pet specialty only.", "https://prime100.com/pages/where-to-buy"),
]
p2 = os.path.join(OUT, "sheet1_excluded_brands.csv")
with open(p2, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["brand_name", "geo_market", "exclusion_reason", "evidence_url"])
    w.writerows(EX)

# ---------------------------------------------------------------- assumptions
A = []
def a(param, scope, value, rationale, conf):
    A.append([param, scope, value, rationale, conf])

a("ca_share (country_split)", "All Colgate North America pools", CA_SHARE,
  "estimate_engine default: Canada is ~11.5% of US+Canada population, discounted for lower per-capita CPG spend and a materially narrower Canadian assortment (the Canadian roster omits Fabuloso-scale US value brands and all US-only tail brands).", "Medium")
a("North America OPHC pool", "Colgate USA + Canada (Oral, Personal and Home Care)", f"{NA_OPHC:.0f} USD mm",
  "Reported FY2025 North America division net sales from the 10-K. Note this division line covers Oral, Personal and Home Care only; Hill's North America sits inside the separate $4,613M Pet Nutrition segment.", "High")
a("USA OPHC pool", "Colgate USA", f"{ophc['USA']:.1f} USD mm", "country_split(4045, 0.093).", "Medium")
a("Canada OPHC pool", "Colgate Canada", f"{ophc['Canada']:.1f} USD mm", "country_split(4045, 0.093).", "Medium")
a("hills_na_share_of_global", "Hill's Pet Nutrition North America", HILLS_NA_SHARE_OF_GLOBAL,
  "Chosen so that Hill's USA = 62.5% of global Hill's net sales, the midpoint of the 60-65% US range used in the brief; the remaining 6.4 pts of the NA figure are Canada at the same 9.3% country split. Hill's NA pool = 4,613 x 0.689 = 3,178M.", "Low")
a("Hill's USA pool", "Hill's Pet Nutrition USA", f"{pet['USA']:.1f} USD mm", "country_split(Hill's NA 3,178M, 0.093) -> 62.5% of the reported $4,613M global Pet Nutrition segment.", "Low")
a("Hill's Canada pool", "Hill's Pet Nutrition Canada", f"{pet['Canada']:.1f} USD mm", "country_split(Hill's NA 3,178M, 0.093).", "Low")
for g in ("USA", "Canada"):
    for cat, w in CAT_WEIGHTS[g].items():
        a(f"category_weight {cat}", f"Colgate {g} OPHC", w,
          {"Oral Care": "Worldwide mix is Oral 44% / Personal 17% / Home 16% of net sales (57/22/21 within OPHC). North America is de-indexed on oral versus emerging markets, where Colgate toothpaste dominates the basket, so oral is set below the worldwide OPHC share.",
           "Personal Care": "Worldwide personal care is 22% of OPHC; the North America personal-care set (Speed Stick, Lady Speed Stick, Softsoap, Irish Spring, Mennen) is broad but value-priced, and skin health is carved out separately, so the residual is set just under the worldwide share.",
           "Skin Care": "Carve-out of the skin-health brands (EltaMD, PCA SKIN, Filorga) that Colgate reports inside Personal Care. EltaMD + PCA SKIN were ~$100M combined net sales at the 2017 acquisition and are repeatedly cited as premium growth drivers, so the implied US skin pool of ~$294M is a growth-consistent 2026 level. Canada de-indexed because Filorga is the only broadly distributed line.",
           "Home Care": "North America over-indexes on home care versus the worldwide 21% of OPHC: Fabuloso is the company-stated #1 US all-purpose pour cleaner, Palmolive dish and Suavitel are US scale franchises, and Canada adds two Canada-only laundry/fabric brands (Arctic Power, Fleecy), hence the higher Canadian weight."}[cat],
          "Low")
    a(f"category_pool {g}", f"Colgate {g}", "; ".join(f"{c}={POOL[(g,c)]:.1f}" for c in ("Oral Care", "Personal Care", "Skin Care", "Home Care", "Pet Nutrition")),
      "Category pools in USD mm after country_split and category weighting. allocate_category normalizes brand weights within each pool, so brand estimates sum exactly to the pool.", "Medium")

a("ALPHA (sku elasticity)", "All brands", 0.72, "estimate_engine default: SKU count has diminishing returns on revenue.", "Medium")
a("BETA (price elasticity)", "All brands", 0.45, "estimate_engine default: premium price only partially converts to revenue share given lower unit velocity.", "Medium")
a("NA advertising intensity uplift", "USA and Canada ad pools", NA_AD_INTENSITY,
  "Worldwide advertising was $2,703M in FY2025 and Q2 2026 hit a record 14.5% of sales with management explicitly stepping up North America spend behind price-gap management; the geo ad pool is therefore set 10% above the geo's pro-rata share of worldwide sales.", "Low")
a("Colgate sub-brand treatment", "Colgate USA and Canada sub-brands", "component rows",
  "Sub-brand rows (Total, Optic White, Max Fresh, Sensitive, PreviDent, PerioGard, hum, Optic White Renewal) are allocated inside the Colgate master estimate using empirical portfolio SKU counts from Sheet 2. They are components of the master row and are excluded from geo totals to avoid double counting; unnamed portfolios (Kids, 360, Cavity Protection and others) remain inside the master row.", "Medium")
a("Reported share override", "Colgate master USA", "31.9%",
  "US toothpaste value share 31.9% YTD as of 2Q 2026 (33.3% FY2025) is used verbatim for share_of_category_pct on the Colgate USA master row and the row is flagged Reported. US manual toothbrush share 43.4% YTD is recorded here as the second reported anchor.", "High")
a("Skin Care channel split", "All skin-care rows", "48% online (x0.78 in Canada)",
  "estimate_engine channel_split benchmark for DTC/Amazon-skewed skin care; consistent with EltaMD selling through 15 authorized online retailers plus DTC and with Filorga Canada being DTC-plus-Walmart.", "Low")
a("Pet Nutrition channel split", "All Hill's / Prime100 rows", "38% online (x0.78 in Canada)",
  "estimate_engine benchmark, corroborated by US pet food at 35.6% online in 2025 with Amazon at 42.2% of online pet sales.", "Medium")
a("Oral / Personal / Home channel splits", "All OPHC rows", "22% / 26% / 17% online",
  "estimate_engine benchmarks, corroborated by the research: US oral care online growing 8.55% CAGR with 38.62% of distribution in supermarkets, home cleaners 22-28% online, detergents 15-20% online.", "Medium")
a("sku_count source", "Oral and personal care brands", "Sheet 2 SKU inventories",
  "Empirical counts from skus_oral_care.csv and skus_personal_care.csv (distinct rows per brand x geo), including per-portfolio counts used for the Colgate sub-brand split.", "High")
a("sku_count source", "Home care and pet nutrition brands", "documented shelf estimates",
  "Home care and pet brands are not covered by the two SKU CSVs. Counts are read off the retailer brand pages cited in brands_positioning.md (e.g. Suavitel Canada = 6 SKUs on walmart.ca, Hill's Science Diet Canada = 208 PetSmart results, Hill's Prescription Diet Canada = 92 cat SKUs plus dog) and rounded assortment estimates elsewhere.", "Low")

for b in B:
    scope = f"{b['brand']} ({b['geo']})"
    a("sku_count", scope, b["sku"],
      "Assortment estimate from the retailer brand page cited in the row's primary_sources (home care and pet nutrition are not covered by the Sheet 2 SKU inventories)."
      if (b["brand"], b["geo"]) in SKU_EST else "Empirical count of distinct rows in the Sheet 2 SKU inventory.",
      "Low" if (b["brand"], b["geo"]) in SKU_EST else "High")
    e = EVID[b["brand"]]
    a("price_index", scope, b["pi"], e["price"], "Medium")
    a("distribution_breadth", scope, b["db"], e["dist"], "Medium")
    a("velocity_index", scope, b["vel"], e["vel"], "Medium")
    a("ad_priority_multiplier", scope, b["adp"], e["ad"], "Medium")

p3 = os.path.join(OUT, "sheet1_assumptions.csv")
with open(p3, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "brand_or_scope", "value", "rationale", "confidence"])
    w.writerows(A)

# ---------------------------------------------------------------- checks
print(f"sheet1_brand_positioning.csv rows: {len(rows)}")
print(f"sheet1_excluded_brands.csv rows:   {len(EX)}")
print(f"sheet1_assumptions.csv rows:       {len(A)}")
print()
for geo in ("USA", "Canada"):
    print(f"--- {geo} ---")
    tot = 0.0
    for cat in ("Oral Care", "Personal Care", "Skin Care", "Home Care", "Pet Nutrition"):
        s = sum(sales[(b['brand'], geo)] for b in B if b["geo"] == geo and b["cat"] == cat and not b["is_sub"])
        tot += s
        print(f"  {cat:<15} brands {s:9.1f}  pool {POOL[(geo,cat)]:9.1f}  delta {s-POOL[(geo,cat)]:+.4f}")
    print(f"  {'TOTAL':<15} brands {tot:9.1f}  pool {ophc[geo]+pet[geo]:9.1f}  delta {tot-(ophc[geo]+pet[geo]):+.4f}")
    subs = sum(sales[(b['brand'], geo)] for b in B if b["geo"] == geo and b["is_sub"])
    print(f"  Colgate sub-brand components {subs:.1f} of master {sales[('Colgate',geo)]:.1f} "
          f"({100*subs/sales[('Colgate',geo)]:.1f}% of master; remainder = unnamed portfolios)")
    print(f"  Advertising allocated {sum(ads[(b['brand'],geo)] for b in B if b['geo']==geo and not b['is_sub']):.1f} "
          f"of worldwide {AD_WW:.0f}")
print()
print("Written:", p1, p2, p3, sep="\n  ")
