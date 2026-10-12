from pathlib import Path
import pandas as pd


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

LISTING_FILE = OUTPUT_DIR / "CRMLSListing_Combined_Residential.csv"
SOLD_FILE = OUTPUT_DIR / "CRMLSSold_Combined_Residential.csv"

LISTING_ENRICHED = OUTPUT_DIR / "CRMLSListing_Residential_With_Mortgage.csv"
SOLD_ENRICHED = OUTPUT_DIR / "CRMLSSold_Residential_With_Mortgage.csv"


# ============================================================
# 1. Download FRED mortgage rate data
# ============================================================

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

mortgage = pd.read_csv(
    url,
    parse_dates=["observation_date"]
)

mortgage.columns = [
    "date",
    "rate_30yr_fixed"
]

print("\nFRED mortgage data loaded.")
print(mortgage.head())


# ============================================================
# 2. Convert weekly rates to monthly averages
# ============================================================

mortgage["year_month"] = (
    mortgage["date"]
    .dt.to_period("M")
)

mortgage_monthly = (
    mortgage
    .groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .reset_index()
)

print("\nMonthly mortgage rates:")
print(mortgage_monthly.tail(12))


# ============================================================
# 3. Load MLS datasets
# ============================================================

print("\nLoading MLS datasets...")

listings = pd.read_csv(
    LISTING_FILE,
    low_memory=False,
    encoding="utf-8-sig"
)

sold = pd.read_csv(
    SOLD_FILE,
    low_memory=False,
    encoding="utf-8-sig"
)

print(f"Listings rows: {len(listings):,}")
print(f"Sold rows:     {len(sold):,}")


# ============================================================
# 4. Create year_month keys
# ============================================================

listings["ListingContractDate"] = pd.to_datetime(
    listings["ListingContractDate"],
    errors="coerce"
)

sold["CloseDate"] = pd.to_datetime(
    sold["CloseDate"],
    errors="coerce"
)

listings["year_month"] = (
    listings["ListingContractDate"]
    .dt.to_period("M")
)

sold["year_month"] = (
    sold["CloseDate"]
    .dt.to_period("M")
)


# ============================================================
# 5. Merge mortgage rates
# ============================================================

listings_with_rates = listings.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)

sold_with_rates = sold.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)


# ============================================================
# 6. Validate merge
# ============================================================

listing_null_rates = (
    listings_with_rates["rate_30yr_fixed"]
    .isna()
    .sum()
)

sold_null_rates = (
    sold_with_rates["rate_30yr_fixed"]
    .isna()
    .sum()
)

print("\n" + "=" * 70)
print("MORTGAGE MERGE VALIDATION")
print("=" * 70)

print(
    f"Listings rows before merge: "
    f"{len(listings):,}"
)

print(
    f"Listings rows after merge:  "
    f"{len(listings_with_rates):,}"
)

print(
    f"Listings with missing mortgage rate: "
    f"{listing_null_rates:,}"
)

print(
    f"\nSold rows before merge: "
    f"{len(sold):,}"
)

print(
    f"Sold rows after merge:  "
    f"{len(sold_with_rates):,}"
)

print(
    f"Sold with missing mortgage rate: "
    f"{sold_null_rates:,}"
)


# ============================================================
# 7. Preview
# ============================================================

print("\nListings preview:")

print(
    listings_with_rates[
        [
            "ListingContractDate",
            "year_month",
            "ListPrice",
            "rate_30yr_fixed"
        ]
    ]
    .head()
    .to_string(index=False)
)

print("\nSold preview:")

print(
    sold_with_rates[
        [
            "CloseDate",
            "year_month",
            "ClosePrice",
            "rate_30yr_fixed"
        ]
    ]
    .head()
    .to_string(index=False)
)


# ============================================================
# 8. Save enriched datasets
# ============================================================

listings_with_rates.to_csv(
    LISTING_ENRICHED,
    index=False,
    encoding="utf-8-sig"
)

sold_with_rates.to_csv(
    SOLD_ENRICHED,
    index=False,
    encoding="utf-8-sig"
)

print("\nSaved enriched datasets:")
print(LISTING_ENRICHED)
print(SOLD_ENRICHED)

print("\nWeek 2-3 mortgage enrichment completed.")