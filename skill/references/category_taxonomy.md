# Fixed Category Taxonomy

Use these strings verbatim. A fixed taxonomy is what makes two different
clients' repositories comparable — resist the urge to invent client-specific
categories, and map the client's own naming into this tree instead.

| Category | Sub-categories |
|---|---|
| Oral Care | Toothpaste; Manual Toothbrushes; Power Toothbrushes; Mouthwash & Rinse; Floss & Interdental; Whitening; Denture Care; Professional & Therapeutic; Kids Oral Care; Breath Freshening |
| Personal Care | Antiperspirant & Deodorant; Bar Soap; Liquid Hand Soap; Body Wash; Shaving & Grooming; Hair Care; Lotion & Body Moisturizer |
| Skin Care | Facial Cleansers; Serums & Treatments; Moisturizers; Sun Care & SPF; Professional & Clinical; Eye Care |
| Home Care | Dish Liquid; Automatic Dishwashing; Surface & Multi-Purpose Cleaners; Laundry Detergent; Fabric Softener; Bleach & Disinfectants; Wood & Specialty Care; Air Care |
| Pet Nutrition | Dry Dog Food; Wet Dog Food; Dry Cat Food; Wet Cat Food; Therapeutic & Prescription Diets; Treats & Supplements |
| Fabric & Home Fragrance | Scent Boosters; Room Sprays; Candles & Diffusers |
| Baby & Child | Baby Bath & Skin; Baby Oral Care |
| Health & Wellness | OTC Remedies; Vitamins & Supplements; First Aid |

## Mapping rules

- Assign a brand to the category where the **majority of its revenue** sits, then
  let Sheet 2 carry the true per-product category for brands that straddle.
  Tom's of Maine is an Oral Care brand in Sheet 1 but has Personal Care rows in Sheet 2.
- `reporting_segment` is the client's own reported segment verbatim, which will
  often disagree with `category`. Keep both. Colgate reports Oral, Personal and
  Home Care as one combined segment while the categories remain distinct.
- Professional and clinical lines get their own sub-category rather than being
  folded into the consumer line — they have different buyers, pricing and channels.
