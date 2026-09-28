from pathlib import Path
from datetime import date
import calendar
import re

import pandas as pd


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

LISTING_OUTPUT = OUTPUT_DIR / "CRMLSListing_Combined_Residential.csv"
SOLD_OUTPUT = OUTPUT_DIR / "CRMLSSold_Combined_Residential.csv"


# ============================================================
# Date range
# ============================================================

START_MONTH = "202401"

today = date.today()

if today.month == 1:
    latest_year = today.year - 1
    latest_month = 12
else:
    latest_year = today.year
    latest_month = today.month - 1

END_MONTH = f"{latest_year}{latest_month:02d}"


def generate_expected_months(start_month, end_month):
    """Generate YYYYMM strings from start through end month."""

    start_year = int(start_month[:4])
    start_m = int(start_month[4:])

    end_year = int(end_month[:4])
    end_m = int(end_month[4:])

    months = []

    year = start_year
    month = start_m

    while (year, month) <= (end_year, end_m):
        months.append(f"{year}{month:02d}")

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return months


EXPECTED_MONTHS = generate_expected_months(
    START_MONTH,
    END_MONTH
)


# ============================================================
# Find monthly files
# ============================================================

def get_monthly_files(prefix):
    """
    Find one file for each YYYYMM month.

    Supports:
        CRMLSListing202401.csv
        CRMLSSold202401.csv
        CRMLSSold202401_filled.csv

    If both the normal file and a suffixed version exist,
    prefer the normal YYYYMM.csv file.
    """

    pattern = re.compile(
        rf"^{re.escape(prefix)}(\d{{6}})(.*)\.csv$",
        re.IGNORECASE
    )

    files_by_month = {}

    for file in DATA_DIR.glob(f"{prefix}*.csv"):

        match = pattern.match(file.name)

        if not match:
            print(f"Skipped unrecognized file: {file.name}")
            continue

        month = match.group(1)

        if month < START_MONTH or month > END_MONTH:
            continue

        exact_name = f"{prefix}{month}.csv"

        if month not in files_by_month:
            files_by_month[month] = file

        else:
            current = files_by_month[month]

            # Prefer exact YYYYMM.csv
            if file.name == exact_name:
                files_by_month[month] = file

            elif current.name != exact_name:
                print(
                    f"WARNING: Multiple candidate files for {month}: "
                    f"{current.name}, {file.name}. "
                    f"Using {current.name}"
                )

    missing_months = [
        month
        for month in EXPECTED_MONTHS
        if month not in files_by_month
    ]

    if missing_months:
        print(
            f"\nWARNING: Missing {prefix} months:"
        )
        print(", ".join(missing_months))
    else:
        print(
            f"\nAll expected {prefix} months are present "
            f"({START_MONTH} through {END_MONTH})."
        )

    files = [
        files_by_month[month]
        for month in EXPECTED_MONTHS
        if month in files_by_month
    ]

    return files


# ============================================================
# Combine monthly files
# ============================================================

def combine_files(files, dataset_name):
    """Read and concatenate all monthly files."""

    if not files:
        raise FileNotFoundError(
            f"No {dataset_name} files found in {DATA_DIR}"
        )

    dataframes = []
    total_before_concat = 0

    print("\n" + "=" * 75)
    print(f"{dataset_name.upper()} MONTHLY FILES")
    print("=" * 75)

    for file in files:

        df = pd.read_csv(
            file,
            low_memory=False,
            encoding="utf-8-sig"
        )

        rows = len(df)
        total_before_concat += rows

        print(
            f"{file.name:<35} "
            f"{rows:>10,} rows"
        )

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True,
        sort=False
    )

    print("-" * 75)
    print(
        f"Rows before concatenation: "
        f"{total_before_concat:,}"
    )
    print(
        f"Rows after concatenation:  "
        f"{len(combined):,}"
    )

    if total_before_concat != len(combined):
        print(
            "WARNING: concatenated row count does not "
            "match the sum of monthly files."
        )

    return combined


# ============================================================
# Residential filter
# ============================================================

def filter_residential(df, dataset_name):

    if "PropertyType" not in df.columns:
        raise KeyError(
            f"PropertyType column not found in "
            f"{dataset_name} dataset."
        )

    before = len(df)

    property_type = (
        df["PropertyType"]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    residential = df[
        property_type == "residential"
    ].copy()

    after = len(residential)

    print(
        f"{dataset_name} before Residential filter: "
        f"{before:,}"
    )
    print(
        f"{dataset_name} after Residential filter:  "
        f"{after:,}"
    )

    return residential, before, after


# ============================================================
# Listings
# ============================================================

listing_files = get_monthly_files(
    "CRMLSListing"
)

listings = combine_files(
    listing_files,
    "Listings"
)

(
    listings_residential,
    listing_before_filter,
    listing_after_filter,
) = filter_residential(
    listings,
    "Listings"
)

listings_residential.to_csv(
    LISTING_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print(
    f"Saved Listings output:\n"
    f"{LISTING_OUTPUT}"
)


# ============================================================
# Sold
# ============================================================

sold_files = get_monthly_files(
    "CRMLSSold"
)

sold = combine_files(
    sold_files,
    "Sold"
)

(
    sold_residential,
    sold_before_filter,
    sold_after_filter,
) = filter_residential(
    sold,
    "Sold"
)

sold_residential.to_csv(
    SOLD_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print(
    f"Saved Sold output:\n"
    f"{SOLD_OUTPUT}"
)


# ============================================================
# Final summary
# ============================================================

print("\n" + "=" * 75)
print("WEEK 1 FINAL SUMMARY")
print("=" * 75)

print(
    f"Expected period: "
    f"{START_MONTH} through {END_MONTH}"
)

print(
    f"Listing files combined: "
    f"{len(listing_files)} / {len(EXPECTED_MONTHS)}"
)

print(
    f"Sold files combined:    "
    f"{len(sold_files)} / {len(EXPECTED_MONTHS)}"
)

print(
    f"Listings: "
    f"{listing_before_filter:,} "
    f"-> {listing_after_filter:,} "
    f"Residential rows"
)

print(
    f"Sold:     "
    f"{sold_before_filter:,} "
    f"-> {sold_after_filter:,} "
    f"Residential rows"
)

print("\nWeek 1 aggregation completed.")