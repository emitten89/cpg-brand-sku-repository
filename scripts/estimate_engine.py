"""
CPG Brand-Level Estimate Engine
================================
CPG holdcos report at SEGMENT level, never at brand level. This module turns
reported segment revenue into defensible brand-level estimates using a
transparent, auditable allocation chain. Every output carries the method
name and a confidence grade so a Modeled cell is never mistaken for a
Reported one.

ALLOCATION CHAIN
----------------
  Reported segment x region net sales        [Reported]
    -> country split (US vs CA)              [Modeled: country_weight]
      -> category split within country       [Modeled: category_weight]
        -> brand split within category       [Modeled: assortment_weight]

BRAND ALLOCATION WEIGHT
-----------------------
Each brand's share of its category pool is:

    w_b = (sku_count_b ^ ALPHA)
          * (avg_price_index_b ^ BETA)
          * distribution_breadth_b
          * velocity_index_b

  sku_count_b          Distinct in-market SKUs from Sheet 2 (the empirical anchor)
  avg_price_index_b    Brand avg shelf price / category avg shelf price
  distribution_breadth Share of tracked retailers carrying the brand (0-1)
  velocity_index_b     Turn-rate proxy from review-volume-per-SKU, normalized to 1.0

ALPHA < 1 because SKU count has diminishing returns — a 200-SKU brand does not
sell 10x a 20-SKU brand. BETA < 1 because premium price only partially converts
to revenue share given lower unit velocity.

Weights are normalized within category so brand estimates sum exactly to the
reported category pool. This is the key property: the model can misallocate
BETWEEN brands but can never inflate the TOTAL beyond what the filing states.
"""

from dataclasses import dataclass, field
from typing import Dict, List

ALPHA = 0.72   # SKU-count elasticity
BETA = 0.45    # price-index elasticity

# ---------------------------------------------------------------------------
# Tier 1 — Reported anchors. Sourced from filings only. Never estimated.
# ---------------------------------------------------------------------------

@dataclass
class ReportedAnchors:
    """Straight from the 10-K / earnings release. Every field is [Reported]."""
    client: str
    fiscal_year: int
    total_net_sales_mm: float
    segment_net_sales_mm: Dict[str, float]      # segment -> $mm
    region_net_sales_mm: Dict[str, float]       # region  -> $mm
    total_advertising_mm: float
    source_urls: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tier 2 — Modeled splits. Each carries an explicit rationale string.
# ---------------------------------------------------------------------------

@dataclass
class ModelAssumption:
    key: str
    value: float
    rationale: str
    confidence: str  # High | Medium | Low


def country_split(na_sales_mm: float, ca_share: float = 0.093):
    """Split a North America pool into US and Canada.

    Default 9.3% Canada is anchored on relative population (~11.5%) discounted
    for lower per-capita CPG spend and narrower assortment. Override per client
    whenever the filing or an investor deck gives a real country figure.
    """
    return {
        "USA": na_sales_mm * (1 - ca_share),
        "Canada": na_sales_mm * ca_share,
    }


def brand_weight(sku_count: int, price_index: float,
                 distribution_breadth: float, velocity_index: float) -> float:
    """Unnormalized allocation weight for one brand."""
    return (max(sku_count, 1) ** ALPHA) * (max(price_index, 0.01) ** BETA) \
        * max(distribution_breadth, 0.01) * max(velocity_index, 0.01)


def allocate_category(category_pool_mm: float, brands: Dict[str, dict]) -> Dict[str, float]:
    """Distribute a category revenue pool across its brands.

    brands: {brand_name: {sku_count, price_index, distribution_breadth, velocity_index}}
    Returns {brand_name: est_sales_mm}. Guaranteed to sum to category_pool_mm.
    """
    weights = {b: brand_weight(**p) for b, p in brands.items()}
    total = sum(weights.values()) or 1.0
    return {b: category_pool_mm * (w / total) for b, w in weights.items()}


def allocate_advertising(total_ad_mm: float, brand_sales: Dict[str, float],
                         geo_share_of_total: float,
                         priority_multipliers: Dict[str, float] | None = None
                         ) -> Dict[str, float]:
    """Allocate the reported advertising line across brands.

    Base case is proportional to sales. `priority_multipliers` lets you tilt
    toward brands the company has publicly named as investment priorities on
    an earnings call (>1.0) or explicitly deprioritized (<1.0). Renormalized
    so the geo's total ad spend still ties to the reported figure.
    """
    priority_multipliers = priority_multipliers or {}
    geo_ad_pool = total_ad_mm * geo_share_of_total
    tilted = {b: s * priority_multipliers.get(b, 1.0) for b, s in brand_sales.items()}
    total = sum(tilted.values()) or 1.0
    return {b: geo_ad_pool * (v / total) for b, v in tilted.items()}


def channel_split(category: str, geo: str) -> tuple[float, float]:
    """Return (pct_instore, pct_online) for a category/geo.

    Benchmarks are category-level ecommerce penetration, applied to the brand.
    Replace with syndicated channel data the moment the client has it.
    """
    base = {
        "Oral Care": 0.22,
        "Personal Care": 0.26,
        "Skin Care": 0.48,      # DTC- and Amazon-skewed
        "Home Care": 0.17,
        "Pet Nutrition": 0.38,  # subscription and vet-channel ecommerce
    }
    online = base.get(category, 0.22)
    if geo == "Canada":
        online *= 0.78          # Canadian ecommerce penetration lags the US
    return round(1 - online, 3), round(online, 3)


def confidence_for(has_reported_anchor: bool, sku_count: int,
                   n_sources: int) -> str:
    """Grade a modeled brand estimate."""
    if has_reported_anchor:
        return "High"
    if sku_count >= 25 and n_sources >= 3:
        return "Medium"
    return "Low"
