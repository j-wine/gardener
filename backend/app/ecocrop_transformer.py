import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .field_parser import (
    parse_list_column,
    parse_categorical_with_notes,
    get_full_category_description,
)

# Constants
NUMERIC_FIELDS = [
    "TOPMN", "TOPMX", "TMIN", "TMAX", "ROPMN", "ROPMX", "RMIN", "RMAX",
    "GMIN", "GMAX", "KTMP", "LATOPMN", "LATOPMX", "LATMN", "LATMX", "ALTMX",
    "LIOPMN", "LIOPMX", "LIMN", "LIMX", "DEP", "KTMPR"
]

LATITUDE_COLUMNS = ["LATOPMN", "LATOPMX", "LATMN", "LATMX"]

# Parsed as list (simple comma-separated)
LIST_COLUMNS = [
    "COMNAME", "CAT", "CLIZ", "SYNO", "PLAT", "LISPA", "TEXTR", "FERR", "TOXR", "DRAR",
    "HABI", "LIFO", "PHYS", "PROSY", "INTRI", "ABITOL", "ABISUS"
]

# Parsed as list + descriptor (e.g., short day (<12 hours))
CATEGORICAL_WITH_NOTES = [
    "PHOTO", "TEXT", "DRA", "SALR", "FER", "TOX", "DEPR"
]

RESOURCES_PATH = "resources"
REPORT_PATH = os.path.join(RESOURCES_PATH, "data-report")
INPUT_FILE = os.path.join(RESOURCES_PATH, "EcoCrop_DB.xlsx")

def visualize_missing_values(df, title, filename):
    na_counts = df.isna().sum()
    empty_counts = (df == "").sum()
    combined = na_counts + empty_counts
    plt.figure(figsize=(15, 7))
    sns.barplot(x=combined.index, y=combined.values, palette="viridis")
    plt.xticks(rotation=90)
    plt.title(title)
    plt.ylabel("Missing / Empty Entries")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def clean_and_prepare(df):
    # Replace weird placeholders with NaN
    df.replace(["NA", "na", "None", "none", "n/a", "-", "--"], pd.NA, inplace=True)

    # Filter out unrealistic optimal temperature values
    df = df[df["TOPMN"] <= 40]

    # KTMP default logic — must be >= 1
    df["KTMP"] = df["KTMP"].fillna(df["TMIN"] - 5)
    df["KTMP"] = df["KTMP"].apply(lambda x: max(x, 1) if pd.notna(x) else x)

    # Default missing GMIN/GMAX to 0 if empty or NA
    df["GMAX"] = df["GMAX"].replace("", 0).fillna(0)
    df["GMIN"] = df["GMIN"].replace("", 0).fillna(0)

    # Sanitize latitude: replace out-of-range values with NA
    for col in LATITUDE_COLUMNS:
        df.loc[(df[col] < -90) | (df[col] > 90), col] = pd.NA

    # Required fields — drop only if missing
    core_required = ["TOPMN", "TOPMX", "TMIN", "TMAX", "ROPMN", "ROPMX", "RMIN", "RMAX", "KTMP"]
    df = df.dropna(subset=[col for col in core_required if col in df.columns])

    return df


def parse_and_normalize(df):
    for col in LIST_COLUMNS:
        df[f"{col}_LIST"] = df[col].apply(parse_list_column)

    for col in CATEGORICAL_WITH_NOTES:
        # Clean malformed brackets (e.g., "high (>10 dS/m))")
        df[col] = df[col].astype(str).str.replace("))", ")", regex=False)
        df[f"{col}_LIST"] = df[col].apply(parse_categorical_with_notes)
        df[f"{col}_DESC"] = df[col].apply(get_full_category_description)

    return df

def standardize_nulls(df):
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = df[col].where(pd.notnull(df[col]), None)
    return df

def add_additional_features(df):
    # Drought/fire/saline tolerance & susceptibility
    df["IS_DROUGHT_TOLERANT"] = df["ABITOL_LIST"].apply(lambda x: "drought" in x if isinstance(x, list) else False)
    df["IS_DROUGHT_SUSCEPTIBLE"] = df["ABISUS_LIST"].apply(lambda x: "drought" in x if isinstance(x, list) else False)

    df["IS_FIRE_TOLERANT"] = df["ABITOL_LIST"].apply(lambda x: "fire" in x if isinstance(x, list) else False)
    df["IS_FIRE_SUSCEPTIBLE"] = df["ABISUS_LIST"].apply(lambda x: "fire" in x if isinstance(x, list) else False)

    df["IS_SALINE_TOLERANT"] = df["SALR_LIST"].apply(lambda x: "high" in x if isinstance(x, list) else False)
    df["IS_SALINE_INTOLERANT"] = df["SALR_LIST"].apply(lambda x: "low" in x if isinstance(x, list) else False)

    # Photoperiod flexibility
    df["IS_MULTIPLE_PHOTO_PERIODS"] = df["PHOTO_LIST"].apply(
        lambda x: len(set(x)) > 1 if isinstance(x, list) else False
    )

    # Soil texture tolerance
    df["SOIL_TEXTURE_FLEXIBILITY_SCORE"] = df["TEXT_LIST"].apply(
        lambda x: len(set(x)) if isinstance(x, list) else 0
    )
    df["IS_SOIL_TEXTURE_TOLERANT"] = df["SOIL_TEXTURE_FLEXIBILITY_SCORE"] >= 3

    # Temperature tolerance
    df["IS_HIGH_TEMPERATURE_TOLERANT"] = df["TMAX"].apply(lambda x: x >= 40 if pd.notna(x) else False)
    # Temperature tolerance
    df["IS_LOW_TEMPERATURE_TOLERANT"] = df["TMIN"].apply(lambda x: x <= 10 if pd.notna(x) else False)

    # Growth cycle
    df["GROWTH_CYCLE_DAYS"] = df["GMAX"] - df["GMIN"]
    df["IS_FAST_CYCLE"] = df["GROWTH_CYCLE_DAYS"] <= 90

    # Precipitation range flexibility
    df["PRECIP_RANGE_WIDTH"] = df.apply(
        lambda row: float(row["RMAX"]) - float(row["RMIN"])
        if pd.notna(row["RMAX"]) and pd.notna(row["RMIN"]) else None,
        axis=1,
    )
    df["IS_WIDE_PRECIP_TOLERANCE"] = df["PRECIP_RANGE_WIDTH"] > 1500

    # PH range
    df["PH_RANGE_WIDTH"] = df.apply(
        lambda row: float(row["PHMAX"]) - float(row["PHMIN"])
        if pd.notna(row["PHMAX"]) and pd.notna(row["PHMIN"]) else None,
        axis=1,
    )
    df["IS_PH_FLEXIBLE"] = df["PH_RANGE_WIDTH"] >= 2

    df["TEMP_RANGE_WIDTH"] = df.apply(
        lambda row: float(row["TMAX"]) - float(row["TMIN"])
        if pd.notna(row["TMAX"]) and pd.notna(row["TMIN"]) else None,
        axis=1,
    )
    df["IS_TEMP_FLEXIBLE"] = df["TEMP_RANGE_WIDTH"] >= 20

    # Climate zones
    df["CLIZ_ZONE_COUNT"] = df["CLIZ_LIST"].apply(lambda x: len(x) if isinstance(x, list) else 0)

    # Cultural familiarity
    df["HAS_MULTIPLE_COMMON_NAMES"] = df["COMNAME_LIST"].apply(
        lambda x: len(x) > 3 if isinstance(x, list) else False
    )

    # Root system depth
    df["IS_SHALLOW_ROOTED"] = df["DEPR_LIST"].apply(
        lambda x: any("shallow" in val for val in x) if isinstance(x, list) else False
    )

    # Photoperiod indicator
    df["IS_SHORT_DAY"] = df["PHOTO_LIST"].apply(
        lambda x: "short day" in x if isinstance(x, list) else False
    )

    # --- Subscores ---

    # Climate adaptability: based on temperature range, heat tolerance, and climate zones
    df["CLIMATE_ADAPT_SCORE"] = (
            (df["TEMP_RANGE_WIDTH"] / 30).clip(upper=1.0).fillna(0) +  # normalized to 0–1
            df["IS_TEMP_FLEXIBLE"].astype(int) +
            df["IS_HIGH_TEMPERATURE_TOLERANT"].astype(int) +
            df["IS_LOW_TEMPERATURE_TOLERANT"].astype(int) +
            (df["CLIZ_ZONE_COUNT"] / 7).clip(upper=1.0)  # max 7 zones
    )
    df["CLIMATE_ADAPT_SCORE"] = df["CLIMATE_ADAPT_SCORE"] / 5.0  # scale to 0–1

    # Soil adaptability: based on texture and pH
    df["SOIL_ADAPT_SCORE"] = (
            df["IS_SOIL_TEXTURE_TOLERANT"].astype(int) +
            (df["PH_RANGE_WIDTH"] / 3).clip(upper=1.0).fillna(0) +  # PH range max ~3
            df["IS_PH_FLEXIBLE"].astype(int)
    )
    df["SOIL_ADAPT_SCORE"] = df["SOIL_ADAPT_SCORE"] / 3.0  # scale to 0–1

    # Water adaptability
    df["WATER_ADAPT_SCORE"] = (
                                      df["IS_DROUGHT_TOLERANT"].astype(int) +
                                      df["IS_WIDE_PRECIP_TOLERANCE"].astype(int)
                              ) / 2.0  # scale to 0–1

    # --- Final Weighted Score ---
    df["ADAPTABILITY_SCORE"] = (
            0.4 * df["CLIMATE_ADAPT_SCORE"] +
            0.35 * df["SOIL_ADAPT_SCORE"] +
            0.25 * df["WATER_ADAPT_SCORE"]
    ).round(3)
    df["ADAPTABILITY_LABEL"] = df["ADAPTABILITY_SCORE"].apply(score_to_label)

    return df

def score_to_label(score: float) -> str:
    if pd.isna(score):
        return "Unknown"
    elif score >= 0.8:
        return "High"
    elif score >= 0.6:
        return "Moderate"
    elif score >= 0.4:
        return "Low"
    else:
        return "Very Low"

def transform_ecocrop_data():
    os.makedirs(REPORT_PATH, exist_ok=True)
    df = pd.read_excel(INPUT_FILE)

    visualize_missing_values(df, "Missing Before", os.path.join(REPORT_PATH, "missing_before.png"))

    df = clean_and_prepare(df)
    df = parse_and_normalize(df)
    df = standardize_nulls(df)

    visualize_missing_values(df, "Missing After", os.path.join(REPORT_PATH, "missing_after.png"))

    df = add_additional_features(df)
    export_rag_chunks(df)


    df.to_excel(os.path.join(RESOURCES_PATH, "Cleaned_EcoCrop_DB_Final.xlsx"), index=False)
    df.to_csv(os.path.join(RESOURCES_PATH, "cleaned_ecocrop.csv"), index=False)
    df.to_json(os.path.join(RESOURCES_PATH, "cleaned_ecocrop.json"), orient="records", indent=2)
    print("Rows before clean:", len(pd.read_excel(INPUT_FILE)))
    print("Rows after clean:", len(df))
    print("✅ Exported cleaned data to .xlsx, .csv, and .json")





DISPLAY_NAMES = {
    "COMNAME": "Common names",
    "CAT": "Use categories",
    "CLIZ": "Climate zones",
    "SYNO": "Synonyms",
    "PLAT": "Plant attributes",
    "LISPA": "Lifespan",
    "TEXTR": "Soil texture range",
    "FERR": "Fertility range",
    "TOXR": "Toxicity range",
    "DRAR": "Drainage range",
    "HABI": "Habitat",
    "LIFO": "Life form",
    "PHYS": "Physical structure",
    "PROSY": "Propagation system",
    "INTRI": "Intraspecific traits",
    "ABITOL": "Biotic tolerance",
    "ABISUS": "Biotic susceptibility",
    "PHOTO": "Photoperiod",
    "TEXT": "Soil texture",
    "DRA": "Drainage",
    "SALR": "Salinity tolerance",
    "FER": "Fertility",
    "TOX": "Toxicity",
    "DEPR": "Soil depth range",
}

def generate_rag_document(row):
    name = row["ScientificName"]
    adaptability = row["ADAPTABILITY_LABEL"]
    score = row["ADAPTABILITY_SCORE"]
    growth_days = row.get("GROWTH_CYCLE_DAYS")
    photo_desc = row.get("PHOTO_DESC", "")
    ph_range = row.get("PH_RANGE_WIDTH")
    temp_range = row.get("TEMP_RANGE_WIDTH")
    precip_range = row.get("PRECIP_RANGE_WIDTH")

    lines = [f"**{name}** — Adaptability: **{adaptability}** (score: {score})"]

    # 🌿 General Lists — from LIST_COLUMNS
    for field in LIST_COLUMNS:
        values = row.get(f"{field}_LIST", [])
        if isinstance(values, list) and values:
            label = DISPLAY_NAMES.get(field.upper(), field.replace("_", " ").capitalize())
            lines.append(f"{label}: {', '.join(values)}")

    # 📝 Descriptive Lists — from *_DESC
    for field in CATEGORICAL_WITH_NOTES:
        values = row.get(f"{field}_DESC", [])
        if isinstance(values, list) and values:
            label = DISPLAY_NAMES.get(field.upper(), field.replace("_", " ").capitalize())
            lines.append(f"{label}: {', '.join(values)}")

    # 🌍 Climate zones
    cliz_desc = row.get("CLIZ_DESC", "")
    if cliz_desc.strip():
        lines.append(f"🌍 Climate zones: {cliz_desc}")
        if row.get("CLIZ_ZONE_COUNT", 0) <= 2:
            lines.append("⚠️ Warning: Grows in very few zones — may need ideal conditions.")

    # 📊 Subscores
    lines.append(
        f"📊 Subscores — Climate: {row['CLIMATE_ADAPT_SCORE']:.2f}, "
        f"Soil: {row['SOIL_ADAPT_SCORE']:.2f}, Water: {row['WATER_ADAPT_SCORE']:.2f}"
    )

    # 🌡 Environmental data
    lines.extend([
        f"🌡️ Temperature: Optimal {row['TOPMN']}–{row['TOPMX']}°C | Absolute: {row['TMIN']}–{row['TMAX']}°C",
        f"💧 Precipitation: Optimal {row['ROPMN']}–{row['ROPMX']} mm | Absolute: {row['RMIN']}–{row['RMAX']} mm",
        f"🧪 Soil pH: Optimal {row['PHOPMN']}–{row['PHOPMX']} | Absolute: {row['PHMIN']}–{row['PHMAX']}",
        f"📈 Ranges — Temp: {temp_range}°C | pH: {ph_range} | Precip: {precip_range} mm"
    ])

    # 🔎 Traits
    traits = []
    if row["IS_DROUGHT_TOLERANT"]: traits.append("drought-tolerant")
    if row["IS_DROUGHT_SUSCEPTIBLE"]: traits.append("drought-susceptible")
    if row["IS_FIRE_TOLERANT"]: traits.append("fire-tolerant")
    if row["IS_FIRE_SUSCEPTIBLE"]: traits.append("fire-susceptible")
    if row["IS_SALINE_TOLERANT"]: traits.append("salinity-tolerant")
    if row["IS_SALINE_INTOLERANT"]: traits.append("salinity-intolerant")
    if row["IS_TEMP_FLEXIBLE"]: traits.append("temperature-flexible")
    if row["IS_LOW_TEMPERATURE_TOLERANT"]: traits.append("cold-tolerant")
    if row["IS_PH_FLEXIBLE"]: traits.append("pH-flexible")
    if row["IS_SOIL_TEXTURE_TOLERANT"]: traits.append("soil-tolerant")
    if row["IS_FAST_CYCLE"]: traits.append("fast growth cycle")
    if row["IS_SHALLOW_ROOTED"]: traits.append("shallow-rooted")
    if row["IS_MULTIPLE_PHOTO_PERIODS"]: traits.append("flexible photoperiod")
    if row["IS_SHORT_DAY"]: traits.append("short-day plant")

    if traits:
        lines.append(f"🔎 Traits: {', '.join(traits)}")

    if isinstance(growth_days, (int, float)):
        lines.append(f"🕒 Growth cycle: {int(growth_days)} days")

    if photo_desc.strip():
        lines.append(f"🌞 Photoperiod: {photo_desc}")

    return "\n".join(lines)

def export_rag_chunks(df, output_dir=os.path.join(RESOURCES_PATH,"rag_chunks")):
    Path(output_dir).mkdir(exist_ok=True)
    for _, row in df.iterrows():
        doc = generate_rag_document(row)
        Path(output_dir, f"{row['EcoPortCode']}.txt").write_text(doc)


if __name__ == "__main__":
    transform_ecocrop_data()

