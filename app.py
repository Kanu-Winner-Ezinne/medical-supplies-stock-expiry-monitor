


import re
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


#  PAGE CONFIGURATION

st.set_page_config(
    page_title="Medical Supplies Stock & Expiry Monitor",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Medical Supplies Stock & Expiry Monitor")

st.write(
    "Monitor medical supplies, identify low-stock items, "
    "track expiry dates and estimate reorder costs."
)

st.caption(
    "Portfolio demonstration. Verify inventory data and follow "
    "your organization's approved stock and expiry procedures."
)


#  CREATE SAMPLE DATA


# Sample data is fictional and generated automatically.
# You do not need to create a separate CSV file.

def create_sample_data():
    today = pd.Timestamp(date.today())

    return pd.DataFrame({
        "Item_ID": [
            "MED001", "MED002", "MED003", "MED004",
            "MED005", "MED006", "MED007", "MED008",
            "MED009", "MED010", "MED011", "MED012"
        ],
        "Item_Name": [
            "Surgical Gloves", "Face Masks", "Syringes",
            "Bandages", "Paracetamol", "Antiseptic Solution",
            "IV Giving Sets", "Disposable Gowns", "Test Tubes",
            "Thermometers", "Saline Bags", "Alcohol Swabs"
        ],
        "Category": [
            "PPE", "PPE", "Equipment", "Wound Care",
            "Medication", "Medication", "Equipment", "PPE",
            "Laboratory", "Equipment", "Medication", "Consumables"
        ],
        "Batch_Number": [
            "B101", "B102", "B103", "B104", "B105", "B106",
            "B107", "B108", "B109", "B110", "B111", "B112"
        ],
        "Quantity_In_Stock": [
            40, 500, 25, 80, 15, 60, 12, 90, 200, 8, 100, 30
        ],
        "Minimum_Stock": [
            50, 200, 40, 50, 30, 20, 25, 40, 100, 10, 50, 50
        ],
        "Unit_Cost_EUR": [
            0.25, 0.10, 0.45, 0.80, 2.50, 3.00,
            1.75, 4.00, 0.15, 8.50, 1.20, 0.08
        ],
        "Expiry_Date": [
            today - pd.Timedelta(days=10),
            today + pd.Timedelta(days=15),
            today + pd.Timedelta(days=45),
            today + pd.Timedelta(days=120),
            today + pd.Timedelta(days=20),
            today + pd.Timedelta(days=200),
            today + pd.Timedelta(days=5),
            today + pd.Timedelta(days=80),
            today + pd.Timedelta(days=400),
            today + pd.Timedelta(days=60),
            today + pd.Timedelta(days=25),
            today + pd.Timedelta(days=300)
        ],
        "Supplier": [
            "MedSupply A", "MedSupply B", "MedSupply A",
            "CarePlus", "HealthSource", "HealthSource",
            "MedSupply B", "CarePlus", "LabSource",
            "LabSource", "HealthSource", "CarePlus"
        ],
        "Daily_Usage": [
            12, 30, 8, 10, 5, 3, 6, 7, 20, 2, 10, 15
        ]
    })


#  UPLOAD DATA OR USE SAMPLE DATA


st.sidebar.header("Upload your inventory")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    original_df = create_sample_data()
    st.info(
        "Showing fictional sample data. Upload your own file "
        "from the sidebar to analyze your inventory."
    )
else:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            original_df = pd.read_csv(uploaded_file)
        else:
            original_df = pd.read_excel(uploaded_file)
    except Exception as error:
        st.error(f"Could not read your file: {error}")
        st.stop()

original_df = original_df.copy()
original_columns = list(original_df.columns)

if original_df.empty or not original_columns:
    st.error("Your file contains no usable rows or columns.")
    st.stop()


#  AUTOMATIC COLUMN-NAME RECOGNITION


def normalize_column(column_name):
    """Standardize names for easier matching."""
    name = str(column_name).strip().lower()
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return " ".join(name.split())


# Alternative names users may have in their datasets.
column_aliases = {
    "Item_ID": [
        "item id", "product id", "sku", "stock id", "material id"
    ],
    "Item_Name": [
        "item name", "product", "product name", "item",
        "supply name", "medical supply", "name"
    ],
    "Category": [
        "category", "item category", "product category",
        "type", "supply category"
    ],
    "Batch_Number": [
        "batch number", "batch", "lot number", "lot", "batch id"
    ],
    "Quantity_In_Stock": [
        "quantity in stock", "stock quantity", "available qty",
        "available quantity", "quantity", "qty", "current stock",
        "stock on hand", "on hand", "units in stock", "stock level"
    ],
    "Minimum_Stock": [
        "minimum stock", "min stock", "minimum quantity",
        "reorder level", "reorder point", "min qty", "minimum level"
    ],
    "Unit_Cost_EUR": [
        "unit cost eur", "unit cost", "cost per unit",
        "unit price", "price per unit", "cost",
        "purchase price", "cost per item"
    ],
    "Expiry_Date": [
        "expiry date", "expiration date", "expires on",
        "expiry", "use by date", "best before", "best before date"
    ],
    "Supplier": [
        "supplier", "vendor", "supplier name", "vendor name"
    ],
    "Daily_Usage": [
        "daily usage", "average daily usage", "daily consumption",
        "units used per day", "usage per day", "daily demand"
    ]
}

normalized_columns = {}

for column in original_columns:
    normalized_name = normalize_column(column)
    if normalized_name not in normalized_columns:
        normalized_columns[normalized_name] = column


# Automatically suggest a matching source column for each field.
auto_mapping = {}
used_columns = set()

for standard_field, aliases in column_aliases.items():
    candidates = [standard_field] + aliases

    for candidate_name in candidates:
        normalized_name = normalize_column(candidate_name)

        if normalized_name in normalized_columns:
            source_column = normalized_columns[normalized_name]

            if source_column not in used_columns:
                auto_mapping[standard_field] = source_column
                used_columns.add(source_column)
                break


#  REVIEW AND CONFIRM COLUMN MAPPING


st.subheader("Match your dataset columns")

st.write(
    "Review the suggested matches. You can select a different "
    "uploaded column if a suggestion is incorrect."
)

required_fields = [
    "Item_Name",
    "Quantity_In_Stock",
    "Minimum_Stock",
    "Unit_Cost_EUR",
    "Expiry_Date"
]

options = ["-- Not mapped --"] + original_columns

# A unique file signature lets us reset the mapping if a new file
# is uploaded without resetting it on every normal rerun.
file_signature = (
    uploaded_file.name,
    uploaded_file.size
) if uploaded_file is not None else ("sample_data", 0)

if st.session_state.get("file_signature") != file_signature:
    st.session_state["file_signature"] = file_signature
    st.session_state["confirmed_mapping"] = None

with st.form("column_mapping_form"):
    selected_columns = {}

    for standard_field in column_aliases:
        suggested = auto_mapping.get(standard_field)
        default_index = options.index(suggested) if suggested in options else 0

        selected_columns[standard_field] = st.selectbox(
            f"Column for {standard_field}",
            options=options,
            index=default_index,
            key=f"mapping_{standard_field}"
        )

    submitted = st.form_submit_button(
        "Confirm mapping and analyze inventory"
    )

if submitted:
    missing_fields = [
        field for field in required_fields
        if selected_columns[field] == "-- Not mapped --"
    ]

    mapped_sources = [
        source for source in selected_columns.values()
        if source != "-- Not mapped --"
    ]

    if missing_fields:
        st.session_state["confirmed_mapping"] = None
        st.error(
            "Please map the following required fields: "
            + ", ".join(missing_fields)
        )
    elif len(mapped_sources) != len(set(mapped_sources)):
        st.session_state["confirmed_mapping"] = None
        st.error(
            "Each source column can only be assigned to one field. "
            "Please correct your selections."
        )
    else:
        st.session_state["confirmed_mapping"] = selected_columns.copy()


confirmed_mapping = st.session_state.get("confirmed_mapping")

if confirmed_mapping is None:
    st.info(
        "Review the mappings above, then click the confirmation button."
    )
    st.stop()


# Rename mapped columns to standard names for analysis.
rename_mapping = {
    source: standard_field
    for standard_field, source in confirmed_mapping.items()
    if source != "-- Not mapped --"
}

df = original_df.rename(columns=rename_mapping).copy()


#  CREATE OPTIONAL FIELDS IF THEY ARE MISSING


if "Item_ID" not in df.columns:
    df["Item_ID"] = [
        f"ITEM-{i:04d}" for i in range(1, len(df) + 1)
    ]

if "Category" not in df.columns:
    df["Category"] = "Uncategorized"

if "Batch_Number" not in df.columns:
    df["Batch_Number"] = "Not provided"

if "Supplier" not in df.columns:
    df["Supplier"] = "Unknown supplier"

if "Daily_Usage" not in df.columns:
    df["Daily_Usage"] = 0


#  CLEAN AND VALIDATE THE DATA


numeric_columns = [
    "Quantity_In_Stock",
    "Minimum_Stock",
    "Unit_Cost_EUR",
    "Daily_Usage"
]

for column in numeric_columns:
    # Also handle common numeric strings containing currency symbols
    # or thousands separators, such as "€1,200.50".
    cleaned_values = (
        df[column]
        .astype("string")
        .str.replace(",", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    df[column] = pd.to_numeric(cleaned_values, errors="coerce")

df["Expiry_Date"] = pd.to_datetime(
    df["Expiry_Date"],
    errors="coerce",
    dayfirst=False
)

invalid_numeric_rows = df[
    ["Quantity_In_Stock", "Minimum_Stock", "Unit_Cost_EUR"]
].isna().any(axis=1)

invalid_numeric_count = int(invalid_numeric_rows.sum())

# Remove records that cannot support the core stock calculations.
df = df.loc[~invalid_numeric_rows].copy()

if df.empty:
    st.error(
        "No usable records remain. Check the quantity, minimum stock "
        "and unit cost fields in your uploaded file."
    )
    st.stop()

for column in ["Item_Name", "Category", "Supplier", "Batch_Number"]:
    df[column] = (
        df[column]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )

df["Daily_Usage"] = df["Daily_Usage"].fillna(0)

negative_quantity_count = int((df["Quantity_In_Stock"] < 0).sum())
negative_cost_count = int((df["Unit_Cost_EUR"] < 0).sum())
negative_usage_count = int((df["Daily_Usage"] < 0).sum())

today = pd.Timestamp(date.today())

df["Days_To_Expiry"] = (df["Expiry_Date"] - today).dt.days


#  CALCULATE INVENTORY METRICS AND ALERTS


df["Stock_Value_EUR"] = (
    df["Quantity_In_Stock"] * df["Unit_Cost_EUR"]
)

df["Suggested_Reorder"] = (
    df["Minimum_Stock"] - df["Quantity_In_Stock"]
).clip(lower=0)

df["Estimated_Reorder_Cost_EUR"] = (
    df["Suggested_Reorder"] * df["Unit_Cost_EUR"]
)


def get_stock_status(row):
    if row["Quantity_In_Stock"] <= 0:
        return "Out of stock"
    if row["Quantity_In_Stock"] < row["Minimum_Stock"]:
        return "Low stock"
    return "Sufficient stock"


def get_expiry_status(row):
    if pd.isna(row["Expiry_Date"]):
        return "No expiry date"

    days = row["Days_To_Expiry"]

    if days < 0:
        return "Expired"
    if days <= 30:
        return "Expires within 30 days"
    if days <= 90:
        return "Expires within 90 days"
    return "More than 90 days"


df["Stock_Status"] = df.apply(get_stock_status, axis=1)
df["Expiry_Status"] = df.apply(get_expiry_status, axis=1)


# SIDEBAR FILTERS


st.sidebar.divider()
st.sidebar.header("Filter inventory")

categories = sorted(df["Category"].unique().tolist())
suppliers = sorted(df["Supplier"].unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Category",
    options=categories,
    default=categories
)

selected_suppliers = st.sidebar.multiselect(
    "Supplier",
    options=suppliers,
    default=suppliers
)

filtered_df = df[
    df["Category"].isin(selected_categories)
    & df["Supplier"].isin(selected_suppliers)
].copy()

if invalid_numeric_count:
    st.warning(
        f"{invalid_numeric_count} row(s) were excluded because "
        "essential numeric fields were missing or invalid."
    )

if negative_quantity_count:
    st.warning(
        f"{negative_quantity_count} row(s) contain negative quantities."
    )

if negative_cost_count:
    st.warning(
        f"{negative_cost_count} row(s) contain negative unit costs."
    )

if negative_usage_count:
    st.warning(
        f"{negative_usage_count} row(s) contain negative daily usage."
    )

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()



#  KEY PERFORMANCE INDICATORS


st.subheader("Inventory overview")

total_records = len(filtered_df)
total_value = filtered_df["Stock_Value_EUR"].sum()

low_stock_count = int(
    (filtered_df["Stock_Status"] == "Low stock").sum()
)

out_of_stock_count = int(
    (filtered_df["Stock_Status"] == "Out of stock").sum()
)

expired_count = int(
    (filtered_df["Expiry_Status"] == "Expired").sum()
)

expiring_soon_count = int(
    filtered_df["Expiry_Status"].isin([
        "Expires within 30 days",
        "Expires within 90 days"
    ]).sum()
)

k1, k2, k3, k4 = st.columns(4)

k1.metric("Inventory records", f"{total_records:,}")
k2.metric("Estimated stock value", f"€{total_value:,.2f}")
k3.metric("Low-stock items", f"{low_stock_count:,}")
k4.metric("Expired items", f"{expired_count:,}")

k5, k6 = st.columns(2)

k5.metric("Out-of-stock items", f"{out_of_stock_count:,}")
k6.metric("Expiring within 90 days", f"{expiring_soon_count:,}")



# STOCK STATUS CHART
st.divider()
st.subheader("Stock status")

stock_summary = (
    filtered_df["Stock_Status"]
    .value_counts()
    .rename_axis("Stock Status")
    .reset_index(name="Number of Items")
)

stock_chart = px.bar(
    stock_summary,
    x="Stock Status",
    y="Number of Items",
    color="Stock Status",
    text="Number of Items",
    title="Inventory records by stock status"
)

stock_chart.update_layout(showlegend=False)

st.plotly_chart(stock_chart, use_container_width=True)


#  INVENTORY VALUE BY CATEGORY


st.subheader("Inventory value by category")

category_summary = (
    filtered_df.groupby("Category", as_index=False)
    ["Stock_Value_EUR"]
    .sum()
    .sort_values("Stock_Value_EUR", ascending=False)
)

category_chart = px.bar(
    category_summary,
    x="Category",
    y="Stock_Value_EUR",
    text_auto=".2f",
    title="Estimated stock value by category"
)

category_chart.update_layout(
    xaxis_title="Category",
    yaxis_title="Stock value (€)"
)

st.plotly_chart(category_chart, use_container_width=True)



#  LOW-STOCK ALERTS


st.divider()
st.subheader("Low-stock alerts")

low_stock_df = filtered_df[
    filtered_df["Quantity_In_Stock"] < filtered_df["Minimum_Stock"]
].copy()

low_stock_df = low_stock_df.sort_values(
    "Suggested_Reorder",
    ascending=False
)

if low_stock_df.empty:
    st.success("No low-stock items were found.")
else:
    st.dataframe(
        low_stock_df[[
            "Item_ID",
            "Item_Name",
            "Category",
            "Quantity_In_Stock",
            "Minimum_Stock",
            "Suggested_Reorder",
            "Supplier"
        ]],
        use_container_width=True,
        hide_index=True
    )



#  EXPIRY MONITORING


st.divider()
st.subheader("Expiry monitoring")

expiry_options = [
    "All",
    "Expired",
    "Expires within 30 days",
    "Expires within 90 days",
    "More than 90 days",
    "No expiry date"
]

selected_expiry = st.selectbox(
    "Filter by expiry status",
    options=expiry_options
)

if selected_expiry == "All":
    expiry_df = filtered_df.copy()
else:
    expiry_df = filtered_df[
        filtered_df["Expiry_Status"] == selected_expiry
    ].copy()

expiry_df = expiry_df.sort_values(
    "Days_To_Expiry",
    na_position="last"
)

if expiry_df.empty:
    st.info("No items match the selected expiry status.")
else:
    st.dataframe(
        expiry_df[[
            "Item_Name",
            "Category",
            "Batch_Number",
            "Quantity_In_Stock",
            "Expiry_Date",
            "Days_To_Expiry",
            "Expiry_Status",
            "Supplier"
        ]],
        use_container_width=True,
        hide_index=True
    )



#  REORDER RECOMMENDATIONS

st.divider()
st.subheader("Reorder recommendations")

reorder_df = filtered_df[
    filtered_df["Suggested_Reorder"] > 0
].copy()

reorder_df = reorder_df.sort_values(
    "Estimated_Reorder_Cost_EUR",
    ascending=False
)

if reorder_df.empty:
    st.success("No reorder recommendations for the selected inventory.")
else:
    st.write(
        "Suggested quantities show how much is needed to reach "
        "the minimum stock level. They do not account for lead times, "
        "future demand or supplier order requirements."
    )

    st.dataframe(
        reorder_df[[
            "Item_Name",
            "Quantity_In_Stock",
            "Minimum_Stock",
            "Suggested_Reorder",
            "Unit_Cost_EUR",
            "Estimated_Reorder_Cost_EUR",
            "Supplier"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.metric(
        "Estimated reorder cost",
        f"€{reorder_df['Estimated_Reorder_Cost_EUR'].sum():,.2f}"
    )



# DOWNLOAD THE FILTERED REPORT


st.divider()
st.subheader("Download inventory report")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered inventory as CSV",
    data=csv_data,
    file_name="medical_inventory_report.csv",
    mime="text/csv"
)



# FOOTER


st.divider()

st.caption(
    "Built with Python, Pandas, Streamlit and Plotly. "
    "This is a portfolio demonstration, not a validated clinical system."
)

