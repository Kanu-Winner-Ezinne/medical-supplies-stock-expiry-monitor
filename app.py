
import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Medical Supplies Stock & Expiry Monitor",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Medical Supplies Stock & Expiry Monitor")

st.markdown(
    "Monitor inventory, track expiry dates, identify stock shortages, "
    "and estimate replenishment costs."
)

st.info(
    "Portfolio demonstration only. Confirm all stock thresholds, "
    "costs, and expiry information before making operational decisions."
)


# --------------------------------------------------
# SAMPLE DATA
# --------------------------------------------------

def get_sample_data():
    today = pd.Timestamp.today().normalize()

    return pd.DataFrame(
        {
            "Item_ID": [
                "MED001", "MED002", "MED003", "MED004",
                "MED005", "MED006", "MED007", "MED008",
                "MED009", "MED010"
            ],
            "Item_Name": [
                "Surgical Gloves",
                "Face Masks",
                "Disposable Syringes",
                "Paracetamol",
                "Medical Gauze",
                "Hand Sanitizer",
                "IV Giving Sets",
                "Examination Gloves",
                "Antiseptic Solution",
                "Bandages",
            ],
            "Category": [
                "PPE", "PPE", "Equipment", "Medicine",
                "Dressing", "PPE", "Equipment", "PPE",
                "Medicine", "Dressing"
            ],
            "Batch_Number": [
                "B001", "B002", "B003", "B004", "B005",
                "B006", "B007", "B008", "B009", "B010"
            ],
            "Supplier": [
                "Supplier A", "Supplier B", "Supplier A",
                "Supplier C", "Supplier B", "Supplier A",
                "Supplier C", "Supplier B", "Supplier C",
                "Supplier A"
            ],
            "Quantity_In_Stock": [
                120, 35, 18, 200, 45, 12, 60, 80, 25, 15
            ],
            "Minimum_Stock": [
                50, 50, 30, 100, 40, 20, 25, 40, 30, 25
            ],
            "Unit_Cost_EUR": [
                0.15, 0.08, 0.35, 0.12, 0.50,
                2.50, 1.80, 0.18, 1.20, 0.75
            ],
            "Daily_Usage": [
                8, 15, 5, 12, 4, 3, 2, 6, 2, 4
            ],
            "Expiry_Date": [
                today + pd.Timedelta(days=240),
                today + pd.Timedelta(days=18),
                today + pd.Timedelta(days=90),
                today + pd.Timedelta(days=400),
                today + pd.Timedelta(days=12),
                today + pd.Timedelta(days=150),
                today + pd.Timedelta(days=45),
                today + pd.Timedelta(days=300),
                today - pd.Timedelta(days=5),
                today + pd.Timedelta(days=60),
            ],
        }
    )


# --------------------------------------------------
# COLUMN RECOGNITION
# --------------------------------------------------

COLUMN_ALIASES = {
    "Item_ID": [
        "item_id", "medicine_id", "product_id", "sku", "id"
    ],
    "Item_Name": [
        "item_name", "medicine_name", "product_name",
        "item", "medicine", "product", "name"
    ],
    "Category": [
        "category", "item_category", "medicine_category",
        "product_category"
    ],
    "Batch_Number": [
        "batch_number", "batch_no", "batch", "lot_number",
        "lot_no"
    ],
    "Supplier": [
        "supplier", "supplier_name", "vendor", "manufacturer"
    ],
    "Quantity_In_Stock": [
        "quantity_in_stock", "quantity", "stock_quantity",
        "available_quantity", "current_stock", "qty",
        "stock_level"
    ],
    "Minimum_Stock": [
        "minimum_stock", "min_stock", "reorder_level",
        "minimum_quantity", "reorder_point", "safety_stock"
    ],
    "Unit_Cost_EUR": [
        "unit_cost_eur", "unit_cost", "purchase_price",
        "unit_price", "cost_per_unit", "cost"
    ],
    "Daily_Usage": [
        "daily_usage", "average_daily_usage", "daily_consumption",
        "usage_per_day"
    ],
    "Expiry_Date": [
        "expiry_date", "expiration_date", "expiry",
        "expiration", "expires_on"
    ],
}


def normalize_column_name(name):
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def suggest_column(target, columns):
    normalized = {
        normalize_column_name(col): col for col in columns
    }

    for alias in COLUMN_ALIASES[target]:
        if alias in normalized:
            return normalized[alias]

    return None


# --------------------------------------------------
# SIDEBAR: UPLOAD AND SETTINGS
# --------------------------------------------------

st.sidebar.header("📂 Inventory Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload your inventory file",
    type=["csv", "xlsx"],
    help="Upload a CSV or Excel file containing your inventory.",
)

if uploaded_file is None:
    raw_df = get_sample_data()
    st.caption(
        "Showing fictional sample data. Upload your own CSV or Excel "
        "file using the sidebar."
    )
else:
    try:
        file_bytes = uploaded_file.getvalue()

        if uploaded_file.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            raw_df = pd.read_excel(io.BytesIO(file_bytes))

        st.success(f"Loaded file: {uploaded_file.name}")

    except Exception as exc:
        st.error(
            "The file could not be read. Check that it is a valid "
            "CSV or Excel file."
        )
        st.caption(f"Technical details: {exc}")
        st.stop()

if raw_df.empty:
    st.warning("The uploaded file contains no records.")
    st.stop()

raw_df.columns = [str(c).strip() for c in raw_df.columns]

st.sidebar.header("⚙️ Monitoring Settings")

expiry_days = st.sidebar.number_input(
    "Expiry warning window (days)",
    min_value=1,
    max_value=365,
    value=30,
    step=1,
)

default_minimum_stock = st.sidebar.number_input(
    "Default minimum stock for missing thresholds",
    min_value=0,
    max_value=1000000,
    value=20,
    step=5,
    help=(
        "Used when your file has no minimum-stock column. "
        "You can adjust each item's threshold below."
    ),
)


# --------------------------------------------------
# COLUMN MAPPING
# --------------------------------------------------

st.subheader("1. Match your columns")

st.write(
    "We try to recognize your column names automatically. "
    "Review the selections before continuing."
)

source_columns = list(raw_df.columns)
no_column = "— Not available —"
choices = [no_column] + source_columns

mapping_fields = [
    ("Item_Name", "Item name", True),
    ("Quantity_In_Stock", "Quantity in stock", True),
    ("Expiry_Date", "Expiry date", True),
    ("Minimum_Stock", "Minimum stock threshold", False),
    ("Unit_Cost_EUR", "Unit purchase cost (€)", False),
    ("Category", "Category", False),
    ("Item_ID", "Item ID", False),
    ("Batch_Number", "Batch / lot number", False),
    ("Supplier", "Supplier", False),
    ("Daily_Usage", "Daily usage", False),
]

mapping = {}

with st.expander("Review and configure column mapping", expanded=True):
    st.caption(
        "Required: item name, quantity in stock, and expiry date. "
        "Minimum stock and unit cost can be configured separately."
    )

    for i in range(0, len(mapping_fields), 2):
        pair = mapping_fields[i:i + 2]
        cols = st.columns(2)

        for col, (target, label, required) in zip(cols, pair):
            suggested = suggest_column(target, source_columns)

            if suggested is not None:
                default_index = choices.index(suggested)
            else:
                default_index = 0

            selected = col.selectbox(
                f"{label}{' *' if required else ''}",
                options=choices,
                index=default_index,
                key=f"mapping_{target}",
            )

            mapping[target] = (
                None if selected == no_column else selected
            )


required_fields = ["Item_Name", "Quantity_In_Stock", "Expiry_Date"]

missing_required = [
    field for field in required_fields
    if mapping.get(field) is None
]

if missing_required:
    st.error(
        "Please map these required fields before continuing: "
        + ", ".join(missing_required)
    )
    st.stop()


# --------------------------------------------------
# BUILD STANDARDIZED DATAFRAME
# --------------------------------------------------

df = pd.DataFrame(index=raw_df.index)

for target, _, _ in mapping_fields:
    source = mapping.get(target)

    if source is not None:
        df[target] = raw_df[source]
    else:
        df[target] = pd.NA

df["Item_Name"] = df["Item_Name"].astype("string").str.strip()

df["Quantity_In_Stock"] = pd.to_numeric(
    df["Quantity_In_Stock"], errors="coerce"
)

df["Expiry_Date"] = pd.to_datetime(
    df["Expiry_Date"], errors="coerce"
).dt.normalize()

df["Minimum_Stock"] = pd.to_numeric(
    df["Minimum_Stock"], errors="coerce"
)

df["Unit_Cost_EUR"] = pd.to_numeric(
    df["Unit_Cost_EUR"], errors="coerce"
)

df["Daily_Usage"] = pd.to_numeric(
    df["Daily_Usage"], errors="coerce"
)

for col in ["Item_ID", "Category", "Batch_Number", "Supplier"]:
    df[col] = df[col].fillna("").astype(str).str.strip()

# Drop records without essential information.
invalid_required = (
    df["Item_Name"].isna()
    | df["Item_Name"].eq("")
    | df["Quantity_In_Stock"].isna()
    | df["Expiry_Date"].isna()
)

invalid_count = int(invalid_required.sum())

if invalid_count:
    st.warning(
        f"{invalid_count} record(s) were excluded because the item name, "
        "quantity, or expiry date was missing or invalid."
    )
    df = df.loc[~invalid_required].copy()

if df.empty:
    st.error(
        "No usable inventory records remain. Please check your column "
        "mapping and uploaded data."
    )
    st.stop()

# Fill missing minimum-stock thresholds.
missing_thresholds = (
    df["Minimum_Stock"].isna()
    | (df["Minimum_Stock"] < 0)
)

df.loc[missing_thresholds, "Minimum_Stock"] = default_minimum_stock

# Missing costs remain unknown; do not silently assume they are zero.
df["Unit_Cost_EUR"] = df["Unit_Cost_EUR"].where(
    df["Unit_Cost_EUR"] >= 0
)

df["Daily_Usage"] = df["Daily_Usage"].where(
    df["Daily_Usage"] >= 0
)

# Keep a record of whether costs were supplied.
cost_column_available = mapping["Unit_Cost_EUR"] is not None

if not cost_column_available:
    st.warning(
        "No unit-cost column was mapped. Inventory value and "
        "replenishment cost will be unavailable until costs are supplied."
    )


# --------------------------------------------------
# EDIT MINIMUM STOCK THRESHOLDS
# --------------------------------------------------

st.subheader("2. Review stock thresholds")

st.write(
    "You can edit each item's minimum stock directly here. "
    "Changes apply to this app session and do not modify your original file."
)

threshold_columns = [
    "Item_Name", "Quantity_In_Stock", "Minimum_Stock"
]

if "Item_ID" in df.columns and df["Item_ID"].ne("").any():
    threshold_columns.insert(0, "Item_ID")

edited_thresholds = st.data_editor(
    df[threshold_columns].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    disabled=[
        c for c in threshold_columns
        if c != "Minimum_Stock"
    ],
    column_config={
        "Minimum_Stock": st.column_config.NumberColumn(
            "Minimum stock threshold",
            min_value=0,
            step=1,
            required=True,
        ),
        "Quantity_In_Stock": st.column_config.NumberColumn(
            "Quantity in stock",
            format="%.2f",
        ),
    },
    key="threshold_editor",
)

df = df.reset_index(drop=True)
df["Minimum_Stock"] = pd.to_numeric(
    edited_thresholds["Minimum_Stock"], errors="coerce"
).fillna(default_minimum_stock).clip(lower=0)


# --------------------------------------------------
# INVENTORY CALCULATIONS
# --------------------------------------------------

today = pd.Timestamp.today().normalize()
expiry_limit = today + pd.Timedelta(days=int(expiry_days))

df["Days_To_Expiry"] = (df["Expiry_Date"] - today).dt.days

df["Stock_Status"] = "Adequate"

df.loc[
    df["Quantity_In_Stock"] <= df["Minimum_Stock"],
    "Stock_Status"
] = "Low Stock"

df.loc[
    df["Quantity_In_Stock"] <= 0,
    "Stock_Status"
] = "Out of Stock"

df["Expiry_Status"] = "Not Expiring Soon"

df.loc[
    df["Expiry_Date"] < today,
    "Expiry_Status"
] = "Expired"

df.loc[
    (df["Expiry_Date"] >= today)
    & (df["Expiry_Date"] <= expiry_limit),
    "Expiry_Status"
] = "Expiring Soon"

df["Reorder_Quantity"] = (
    df["Minimum_Stock"] - df["Quantity_In_Stock"]
).clip(lower=0)

if cost_column_available:
    df["Inventory_Value_EUR"] = (
        df["Quantity_In_Stock"] * df["Unit_Cost_EUR"]
    )
    df["Replenishment_Cost_EUR"] = (
        df["Reorder_Quantity"] * df["Unit_Cost_EUR"]
    )
else:
    df["Inventory_Value_EUR"] = float("nan")
    df["Replenishment_Cost_EUR"] = float("nan")


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

st.subheader("3. Inventory overview")

filter_col1, filter_col2, filter_col3 = st.columns(3)

categories = sorted(
    c for c in df["Category"].dropna().unique() if c
)

if categories:
    selected_categories = filter_col1.multiselect(
        "Filter by category",
        options=categories,
        default=categories,
    )
else:
    selected_categories = []

stock_options = ["All", "Out of Stock", "Low Stock", "Adequate"]

selected_stock_status = filter_col2.selectbox(
    "Filter by stock status",
    stock_options,
)

expiry_options = [
    "All", "Expired", "Expiring Soon", "Not Expiring Soon"
]

selected_expiry_status = filter_col3.selectbox(
    "Filter by expiry status",
    expiry_options,
)

filtered_df = df.copy()

if categories:
    filtered_df = filtered_df[
        filtered_df["Category"].isin(selected_categories)
    ]

if selected_stock_status != "All":
    filtered_df = filtered_df[
        filtered_df["Stock_Status"] == selected_stock_status
    ]

if selected_expiry_status != "All":
    filtered_df = filtered_df[
        filtered_df["Expiry_Status"] == selected_expiry_status
    ]


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

total_items = len(filtered_df)
total_units = filtered_df["Quantity_In_Stock"].sum()

out_of_stock_count = int(
    (filtered_df["Stock_Status"] == "Out of Stock").sum()
)

low_stock_count = int(
    (filtered_df["Stock_Status"] == "Low Stock").sum()
)

expired_count = int(
    (filtered_df["Expiry_Status"] == "Expired").sum()
)

expiring_count = int(
    (filtered_df["Expiry_Status"] == "Expiring Soon").sum()
)

k1, k2, k3 = st.columns(3)

k1.metric("Inventory items", f"{total_items:,}")
k2.metric("Total units in stock", f"{total_units:,.0f}")
k3.metric("Out-of-stock items", f"{out_of_stock_count:,}")

k4, k5, k6 = st.columns(3)

k4.metric("Low-stock items", f"{low_stock_count:,}")
k5.metric("Expired items", f"{expired_count:,}")
k6.metric(f"Expiring in {expiry_days} days", f"{expiring_count:,}")

if cost_column_available:
    total_value = filtered_df["Inventory_Value_EUR"].sum(
        min_count=1
    )
    replenishment_cost = filtered_df[
        "Replenishment_Cost_EUR"
    ].sum(min_count=1)

    k7, k8 = st.columns(2)

    k7.metric(
        "Estimated inventory value",
        "Unavailable" if pd.isna(total_value)
        else f"€{total_value:,.2f}",
    )

    k8.metric(
        "Estimated replenishment cost",
        "Unavailable" if pd.isna(replenishment_cost)
        else f"€{replenishment_cost:,.2f}",
    )


# --------------------------------------------------
# CHARTS
# --------------------------------------------------

st.subheader("4. Inventory analytics")

chart1, chart2 = st.columns(2)

with chart1:
    stock_counts = (
        filtered_df["Stock_Status"]
        .value_counts()
        .rename_axis("Stock Status")
        .reset_index(name="Number of Items")
    )

    if not stock_counts.empty:
        fig_stock = px.bar(
            stock_counts,
            x="Stock Status",
            y="Number of Items",
            color="Stock Status",
            title="Stock Status Distribution",
            text="Number of Items",
        )
        st.plotly_chart(fig_stock, use_container_width=True)
    else:
        st.info("No stock data matches the selected filters.")

with chart2:
    expiry_counts = (
        filtered_df["Expiry_Status"]
        .value_counts()
        .rename_axis("Expiry Status")
        .reset_index(name="Number of Items")
    )

    if not expiry_counts.empty:
        fig_expiry = px.pie(
            expiry_counts,
            names="Expiry Status",
            values="Number of Items",
            title="Expiry Status Distribution",
            hole=0.4,
        )
        st.plotly_chart(fig_expiry, use_container_width=True)
    else:
        st.info("No expiry data matches the selected filters.")

if categories and not filtered_df.empty:
    category_counts = (
        filtered_df.groupby("Category", dropna=False)
        ["Quantity_In_Stock"]
        .sum()
        .reset_index()
    )

    fig_category = px.bar(
        category_counts,
        x="Category",
        y="Quantity_In_Stock",
        title="Units in Stock by Category",
        text_auto=True,
    )

    st.plotly_chart(fig_category, use_container_width=True)


# --------------------------------------------------
# ALERTS AND REORDER RECOMMENDATIONS
# --------------------------------------------------

st.subheader("5. Actionable inventory alerts")

low_stock_df = filtered_df[
    filtered_df["Stock_Status"].isin(
        ["Out of Stock", "Low Stock"]
    )
].copy()

expired_df = filtered_df[
    filtered_df["Expiry_Status"] == "Expired"
].copy()

expiring_df = filtered_df[
    filtered_df["Expiry_Status"] == "Expiring Soon"
].copy()

tab1, tab2, tab3 = st.tabs(
    ["Stock shortages", "Expired items", "Expiring soon"]
)

with tab1:
    if low_stock_df.empty:
        st.success("No stock shortages found for the selected filters.")
    else:
        reorder_columns = [
            "Item_Name", "Quantity_In_Stock", "Minimum_Stock",
            "Stock_Status", "Reorder_Quantity"
        ]

        if cost_column_available:
            reorder_columns.append("Replenishment_Cost_EUR")

        st.dataframe(
            low_stock_df[reorder_columns].sort_values(
                "Reorder_Quantity", ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    if expired_df.empty:
        st.success("No expired items found for the selected filters.")
    else:
        st.dataframe(
            expired_df[
                [
                    "Item_Name", "Batch_Number", "Expiry_Date",
                    "Days_To_Expiry", "Quantity_In_Stock"
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab3:
    if expiring_df.empty:
        st.success(
            "No items are expiring within the selected warning window."
        )
    else:
        st.dataframe(
            expiring_df[
                [
                    "Item_Name", "Batch_Number", "Expiry_Date",
                    "Days_To_Expiry", "Quantity_In_Stock"
                ]
            ].sort_values("Days_To_Expiry"),
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# FULL INVENTORY TABLE
# --------------------------------------------------

st.subheader("6. Full inventory report")

display_columns = [
    "Item_Name",
    "Category",
    "Batch_Number",
    "Supplier",
    "Quantity_In_Stock",
    "Minimum_Stock",
    "Stock_Status",
    "Expiry_Date",
    "Days_To_Expiry",
    "Expiry_Status",
    "Reorder_Quantity",
]

if cost_column_available:
    display_columns += [
        "Unit_Cost_EUR",
        "Inventory_Value_EUR",
        "Replenishment_Cost_EUR",
    ]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# DOWNLOAD REPORT
# --------------------------------------------------

st.subheader("7. Export your report")

csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="⬇️ Download inventory report (CSV)",
    data=csv_data,
    file_name="medical_supplies_inventory_report.csv",
    mime="text/csv",
)

st.caption(
    "Built as a data analytics portfolio project using Python, "
    "Pandas, Streamlit, and Plotly. This tool does not replace "
    "validated inventory management or clinical safety procedures."
)
