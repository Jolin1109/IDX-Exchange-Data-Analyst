from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

LISTING_FILE = OUTPUT_DIR / "CRMLSListing_Combined_Residential.csv"
SOLD_FILE = OUTPUT_DIR / "CRMLSSold_Combined_Residential.csv"


# ============================================================
# Load datasets
# ============================================================

print("Loading datasets...")

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

print("\nDatasets loaded successfully.")


# ============================================================
# 1. Dataset structure
# ============================================================

def inspect_structure(df, name):

    print("\n" + "=" * 75)
    print(f"{name.upper()} DATASET STRUCTURE")
    print("=" * 75)

    print(f"Rows:    {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]:,}")

    print("\nColumn data types:")
    print(df.dtypes.value_counts())

    # Save complete data type report
    dtype_report = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values
    })

    dtype_report.to_csv(
        REPORT_DIR / f"{name.lower()}_data_types.csv",
        index=False
    )


inspect_structure(listings, "Listings")
inspect_structure(sold, "Sold")


# ============================================================
# 2. Property type validation
# ============================================================

def inspect_property_types(df, name):

    print("\n" + "=" * 75)
    print(f"{name.upper()} PROPERTY TYPES")
    print("=" * 75)

    if "PropertyType" not in df.columns:
        print("PropertyType column not found.")
        return

    counts = (
        df["PropertyType"]
        .value_counts(dropna=False)
        .reset_index()
    )

    counts.columns = ["PropertyType", "Count"]

    print(counts)

    counts.to_csv(
        REPORT_DIR / f"{name.lower()}_property_types.csv",
        index=False
    )


inspect_property_types(listings, "Listings")
inspect_property_types(sold, "Sold")


# ============================================================
# 3. Missing value analysis
# ============================================================

def missing_value_report(df, name):

    missing_count = df.isna().sum()
    missing_pct = (missing_count / len(df)) * 100

    report = pd.DataFrame({
        "column": df.columns,
        "missing_count": missing_count.values,
        "missing_percentage": missing_pct.values
    })

    report = report.sort_values(
        "missing_percentage",
        ascending=False
    )

    report["over_90_percent_missing"] = (
        report["missing_percentage"] > 90
    )

    print("\n" + "=" * 75)
    print(f"{name.upper()} MISSING VALUE REPORT")
    print("=" * 75)

    print(report.head(20).to_string(index=False))

    over_90 = report[
        report["over_90_percent_missing"]
    ]

    print(
        f"\nColumns with >90% missing values: "
        f"{len(over_90)}"
    )

    if not over_90.empty:
        print(
            over_90[
                ["column", "missing_percentage"]
            ].to_string(index=False)
        )

    report.to_csv(
        REPORT_DIR / f"{name.lower()}_missing_values.csv",
        index=False
    )

    return report


listing_missing = missing_value_report(
    listings,
    "Listings"
)

sold_missing = missing_value_report(
    sold,
    "Sold"
)


# ============================================================
# 4. Numeric distribution summary
# ============================================================

NUMERIC_FIELDS = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]


def numeric_summary(df, name):

    available_fields = [
        col
        for col in NUMERIC_FIELDS
        if col in df.columns
    ]

    print("\n" + "=" * 75)
    print(f"{name.upper()} NUMERIC SUMMARY")
    print("=" * 75)

    summaries = []

    for col in available_fields:

        numeric = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        summary = {
            "column": col,
            "count": numeric.count(),
            "min": numeric.min(),
            "p25": numeric.quantile(0.25),
            "median": numeric.median(),
            "mean": numeric.mean(),
            "p75": numeric.quantile(0.75),
            "p90": numeric.quantile(0.90),
            "p95": numeric.quantile(0.95),
            "p99": numeric.quantile(0.99),
            "max": numeric.max()
        }

        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)

    print(summary_df.to_string(index=False))

    summary_df.to_csv(
        REPORT_DIR / f"{name.lower()}_numeric_summary.csv",
        index=False
    )

    return summary_df


listing_numeric = numeric_summary(
    listings,
    "Listings"
)

sold_numeric = numeric_summary(
    sold,
    "Sold"
)


# ============================================================
# 5. Histograms and boxplots
# ============================================================

def create_plots(df, name):

    available_fields = [
        col
        for col in NUMERIC_FIELDS
        if col in df.columns
    ]

    for col in available_fields:

        numeric = pd.to_numeric(
            df[col],
            errors="coerce"
        ).dropna()

        if numeric.empty:
            continue

        # Histogram
        plt.figure(figsize=(8, 5))

        plt.hist(
            numeric,
            bins=50
        )

        plt.title(
            f"{name} - {col} Histogram"
        )

        plt.xlabel(col)
        plt.ylabel("Frequency")

        plt.tight_layout()

        plt.savefig(
            REPORT_DIR /
            f"{name.lower()}_{col}_histogram.png"
        )

        plt.close()

        # Boxplot
        plt.figure(figsize=(8, 3))

        plt.boxplot(
            numeric,
            vert=False
        )

        plt.title(
            f"{name} - {col} Boxplot"
        )

        plt.xlabel(col)

        plt.tight_layout()

        plt.savefig(
            REPORT_DIR /
            f"{name.lower()}_{col}_boxplot.png"
        )

        plt.close()


create_plots(
    listings,
    "Listings"
)

create_plots(
    sold,
    "Sold"
)


# ============================================================
# 6. Basic EDA questions
# ============================================================

print("\n" + "=" * 75)
print("BASIC EDA RESULTS")
print("=" * 75)


# ---- Sold price statistics ----

if "ClosePrice" in sold.columns:

    close_price = pd.to_numeric(
        sold["ClosePrice"],
        errors="coerce"
    )

    print(
        f"\nAverage Close Price: "
        f"${close_price.mean():,.2f}"
    )

    print(
        f"Median Close Price: "
        f"${close_price.median():,.2f}"
    )


# ---- Days on Market ----

if "DaysOnMarket" in sold.columns:

    dom = pd.to_numeric(
        sold["DaysOnMarket"],
        errors="coerce"
    )

    print(
        f"\nMedian Days on Market: "
        f"{dom.median():.1f}"
    )

    print(
        f"Average Days on Market: "
        f"{dom.mean():.1f}"
    )


# ---- Above vs below list price ----

if (
    "ClosePrice" in sold.columns
    and "ListPrice" in sold.columns
):

    close_price = pd.to_numeric(
        sold["ClosePrice"],
        errors="coerce"
    )

    list_price = pd.to_numeric(
        sold["ListPrice"],
        errors="coerce"
    )

    valid = (
        close_price.notna()
        & list_price.notna()
        & (list_price > 0)
    )

    sold_above = (
        close_price[valid]
        > list_price[valid]
    ).mean() * 100

    sold_below = (
        close_price[valid]
        < list_price[valid]
    ).mean() * 100

    sold_equal = (
        close_price[valid]
        == list_price[valid]
    ).mean() * 100

    print(
        f"\nSold above list price: "
        f"{sold_above:.2f}%"
    )

    print(
        f"Sold below list price: "
        f"{sold_below:.2f}%"
    )

    print(
        f"Sold exactly at list price: "
        f"{sold_equal:.2f}%"
    )


# ---- Date consistency ----

required_dates = [
    "ListingContractDate",
    "CloseDate"
]

if all(
    col in sold.columns
    for col in required_dates
):

    listing_date = pd.to_datetime(
        sold["ListingContractDate"],
        errors="coerce"
    )

    close_date = pd.to_datetime(
        sold["CloseDate"],
        errors="coerce"
    )

    inconsistent_dates = (
        close_date < listing_date
    ).sum()

    print(
        f"\nRecords where CloseDate occurs "
        f"before ListingContractDate: "
        f"{inconsistent_dates:,}"
    )


# ---- County median price ----

if (
    "CountyOrParish" in sold.columns
    and "ClosePrice" in sold.columns
):

    county = sold[
        ["CountyOrParish", "ClosePrice"]
    ].copy()

    county["ClosePrice"] = pd.to_numeric(
        county["ClosePrice"],
        errors="coerce"
    )

    county_summary = (
        county
        .dropna()
        .groupby("CountyOrParish")
        .agg(
            median_close_price=(
                "ClosePrice",
                "median"
            ),
            sales_count=(
                "ClosePrice",
                "count"
            )
        )
        .sort_values(
            "median_close_price",
            ascending=False
        )
    )

    print(
        "\nTop counties by median Close Price:"
    )

    print(
        county_summary
        .head(10)
        .to_string()
    )

    county_summary.to_csv(
        REPORT_DIR /
        "sold_county_price_summary.csv"
    )


# ============================================================
# Final output
# ============================================================

print("\n" + "=" * 75)
print("WEEK 2–3 VALIDATION COMPLETE")
print("=" * 75)

print(
    f"Reports saved to: "
    f"{REPORT_DIR}"
)