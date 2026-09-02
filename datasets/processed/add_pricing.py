"""
Add real-market-informed pricing to products.csv (and propagate to skus.csv).
Run this from datasets/processed/, or adjust the paths below.

Price is a per-PRODUCT (style) attribute, not per-SKU — a shoe's price
doesn't change by size or color, only by style, matching real retail.

Sourced from real Stylo Pakistan pricing (stylo.pk, shoppingbag.pk):
range observed ~PKR 999 (budget casual) to PKR 37,000+ (premium formal),
free-delivery threshold PKR 3,500-5,000 suggesting that's near a typical
order value. Category ranges below are a documented, sourced estimate —
not exact Stylo SKU-level pricing (not publicly scraped), but grounded
in real observed price points rather than invented.
"""
import pandas as pd
import numpy as np

np.random.seed(21)

PRICE_RANGES_PKR = {
    # (category): (min, typical, max) -- used to build a right-skewed
    # distribution (most styles cluster near "typical", a few premium
    # styles pull the tail up toward "max")
    "Casual": (999, 3200, 6000),
    "Formal": (3500, 8500, 22000),
    "Sports": (2000, 4200, 8500),
}

products = pd.read_csv("products.csv")
skus = pd.read_csv("skus.csv")

def sample_price(category):
    lo, typical, hi = PRICE_RANGES_PKR[category]
    # log-normal-ish: skewed toward "typical", occasional premium outlier
    val = np.random.lognormal(mean=np.log(typical), sigma=0.35)
    return int(np.clip(val, lo, hi))

products["price_pkr"] = products["category"].apply(sample_price)

print("Price summary by category:")
print(products.groupby("category")["price_pkr"].describe()[["min","mean","50%","max"]].round(0))

# propagate price onto skus (join on product_id) -- price doesn't vary by size/color
skus = skus.merge(products[["product_id", "price_pkr"]], on="product_id", how="left")

products.to_csv("products.csv", index=False)
skus.to_csv("skus.csv", index=False)
print("\nSaved products.csv and skus.csv with price_pkr added.")
