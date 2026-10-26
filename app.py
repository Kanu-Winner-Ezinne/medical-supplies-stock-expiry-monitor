
import re
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Medical Supplies Stock & Expiry Monitor",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Medical Supplies Stock & Expiry Monitor")
st.write(
    "Monitor inventory, track expiry dates, identify stock shortages, "
    "and estimate replenishment costs."
)
st.caption(
    "Portfolio demonstration. Confirm all thresholds and inventory "
    "figures before using them for operational decisions."
)


# -------------------- SAMPLE DATA --------------------

def create_sample_data():
    today = pd.Timestamp(date.today())
    return pd.DataFrame({
        "Item_ID": ["MED001", "MED002", "MED003", "MED004", "MED005"],
        "Item_Name": [
            "Surgical Gloves", "Face Masks", "Syringes",
            "Bandages", "Paracetamol"
        ],
        "Category": ["PPE", "PPE", "Equipment", "Wound Care", "Medication"],
        "Batch_Number": ["B101", "B102", "B103", "B104", "B105"],
        "Quantity_In_Stock": [40, 500, 25, 80, 15],
        "Minimum_Stock": [50, 200, 40, 50, 30],
        "Unit_Cost_EUR": [0.25, 0.10, 0.45, 0.80, 2.50],
        "Expiry_Date": [
            today + pd.Timedelta(days=15),
            today + pd.Timedelta(days=240),
            today + pd.Timedelta(days=45),
            today - pd.Timedelta(days=10),
            today + pd.Timedelta(days=20),
        ],
        "Supplier": [
            "MedSupply A", "MedSupply B", "MedSupply A",
            "CarePlus", "HealthSource"
        ],
        "Daily_Usage": [12, 30, 8, 10, 5],
    })


# -------------------- UPLOAD --------------------

st.sidebar.header("Inventory data")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"],
)

if uploaded_file is None:
    original_df = create_sample_data()
    st.info(
        "Showing fictional sample data. Upload your own CSV or Excel "
        "file using the sidebar."
    )
else:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            original_df = pd.read_csv(uploaded_file)
        else:
            original_df = pd.read_excel(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")
        st.stop()

original_df = original_df.copy()
original_df.columns = [str(c).strip() for c in original_df.columns]

if original_df.empty or len(original_df.columns) == 0:
    st.error("The uploaded file has no usable rows or columns.")
    st.stop()


# -------------------- COLUMN MAPPING --------------------

def normalize(value):
    value = str(value).strip().lower()
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return " ".join(value.split())


aliases = {
    "Item_ID": [
        "item id", "medicine id", "product id", "sku", "stock id"
    ],
    "Item_Name": [
        "item name", "medicine name", "product name", "product",
        "medicine", "item", "name"
    ],
    "Category": ["category", "item category", "product category", "type"],
    "Batch_Number": [
        "batch number", "batch no", "batch", "lot number", "lot"
    ],
    "Quantity_In_Stock": [
        "quantity in stock", "quantity", "qty", "current stock",
        "stock quantity", "available quantity", "stock on hand"
    ],
    "Minimum_Stock": [
        "minimum stock", "min stock", "minimum quantity",
        "reorder level", "reorder point", "minimum level"
    ],
    "Unit_Cost_EUR": [
        "unit cost eur", "unit cost", "purchase cost",
        "cost per unit", "unit price", "purchase price"
    ],
    "Expiry_Date": [
        "expiry date", "expiration date", "expiry",
        "expires on", "use by date"
    ],
    "Supplier": ["supplier", "supplier name", "vendor", "vendor name"],
    "Daily_Usage": [
        "daily usage", "daily consumption", "average daily usage",
        "daily demand", "units used per day"
    ],
}

normalized_columns = {}
for col in original_df.columns:
    normalized_columns.setdefault(normalize(col), col)

auto_mapping = {}
used_columns = set()

for field, field_aliases in aliases.items():
    for candidate in [field] + field_aliases:
        source = normalized_columns.get(normalize(candidate))
        if source is not None and source not in used_columns:
            auto_mapping[field] = source
            used_columns.add(source)
            break

st.subheader("1. Match your columns")
st.write(
    "We try to recognize your column names automatically. "
    "Review the selections before continuing."
)

not_mapped = "-- Not mapped --"
options = [not_mapped] + list(original_df.columns)

signature = (
    uploaded_file.name, uploaded_file.size
    if uploaded_file is not None else ("sample", 0)
)
# Use a stable signature for resetting confirmation after a new upload.
if uploaded_file is None:
    signature = ("sample", 0)
else:
    signature = (uploaded_file.name, uploaded_file.size)

if st.session_state.get("file_signature") != signature:
    st.session_state["file_signature"] = signature
    st.session_state["confirmed_mapping"] = None

with st.form("mapping_form"):
    selected = {}
    for field in aliases:
        suggested = auto_mapping.get(field, not_mapped)
        index = options.index(suggested) if suggested in options else 0
        selected[field] = st.selectbox(
            f"Column for {field}",
            options=options,
            index=index,
            key=f"column_{field}",
        )
    confirm = st.form_submit_button("Confirm mapping")

if confirm:
    required = ["Item_Name", "Quantity_In_Stock", "Expiry_Date"]
    missing = [f for f in required if selected[f] == not_mapped]
    mapped = [v for v in selected.values() if v != not_mapped]

    if missing:
        st.error("Please map these required fields: " + ", ".join(missing))
        st.session_state["confirmed_mapping"] = None
    elif len(mapped) != len(set(mapped)):
        st.error(
            "A source column has been selected more than once. "
            "Each source column can only map to one field."
        )
        st.session_state["confirmed_mapping"] = None
    else:
        st.session_state["confirmed_mapping"] = selected.copy()

mapping = st.session_state.get("confirmed_mapping")
if mapping is None:
    st.info("Confirm your column mapping to continue.")
    st.stop()

rename_map = {
    source: field for field, source in mapping.items()
    if source != not_mapped
}
df = original_df.rename(columns=rename_map).copy()


# -------------------- OPTIONAL FIELDS --------------------

if "Item_ID" not in df.columns:
    df["Item_ID"] = [f"ITEM-{i:04d}" for i in range(1, len(df) + 1)]
if "Category" not in df.columns:
    df["Category"] = "Uncategorized"
if "Batch_Number" not in df.columns:
    df["Batch_Number"] = "Not provided"
if "Supplier" not in df.columns:
    df["Supplier"] = "Unknown supplier"
if "Daily_Usage" not in df.columns:
    df["Daily_Usage"] = 0

for col in ["Quantity_In_Stock", "Unit_Cost_EUR", "Minimum_Stock", "Daily_Usage"]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.strip(),
            errors="coerce",
        )

df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"], errors="coerce")

invalid_quantity = df["Quantity_In_Stock"].isna()
if invalid_quantity.any():
    st.warning(
        f"{int(invalid_quantity.sum())} row(s) have missing or invalid "
        "quantities and will be excluded."
    )
    df = df.loc[~invalid_quantity].copy()

if df.empty:
    st.error("No rows with valid stock quantities remain.")
    st.stop()

df["Unit_Cost_EUR"] = (
    df["Unit_Cost_EUR"] if "Unit_Cost_EUR" in df.columns else pd.Series(index=df.index, dtype=float)
)
if "Unit_Cost_EUR" not in df.columns or df["Unit_Cost_EUR"].isna().all():
    st.warning(
        "No usable unit cost was mapped. Inventory valuation and reorder "
        "costs will be unavailable until you provide a unit-cost column."
    )
    df["Unit_Cost_EUR"] = 0.0
else:
    df["Unit_Cost_EUR"] = df["Unit_Cost_EUR"].fillna(0)

df["Daily_Usage"] = df["Daily_Usage"].fillna(0)
for col in ["Item_Name", "Category", "Supplier", "Batch_Number", "Item_ID"]:
    df[col] = df[col].fillna("Unknown").astype(str).str.strip()
    df[col] = df[col].replace("", "Unknown")

# -------------------- CONFIGURE MISSING MINIMUM STOCK --------------------

st.divider()
st.subheader("2. Configure minimum stock levels")

if "Minimum_Stock" not in df.columns or df["Minimum_Stock"].isna().all():
    st.info(
        "Your file does not contain usable minimum-stock levels. "
        "Set a threshold below. This value is a user-defined assumption, "
        "not a value inferred from the uploaded data."
    )
    default_minimum = st.number_input(
        "Default minimum stock per item",
        min_value=0.0,
        value=50.0,
        step=1.0,
        help="Applied to each item unless you customize its threshold below.",
    )
    df["Minimum_Stock"] = default_minimum
else:
    missing_minimum = df["Minimum_Stock"].isna()
    if missing_minimum.any():
        default_minimum = st.number_input(
            "Default minimum stock for rows with missing values",
            min_value=0.0,
            value=50.0,
            step=1.0,
        )
        df.loc[missing_minimum, "Minimum_Stock"] = default_minimum

with st.expander("Customize minimum stock by item"):
    thresholds = st.data_editor(
        df[["Item_ID", "Item_Name", "Quantity_In_Stock", "Minimum_Stock"]],
        use_container_width=True,
        hide_index=True,
        disabled=["Item_ID", "Item_Name", "Quantity_In_Stock"],
        column_config={
            "Minimum_Stock": st.column_config.NumberColumn(
                "Minimum stock threshold",
                min_value=0,
                step=1,
            )
        },
        key="threshold_editor",
    )
    df["Minimum_Stock"] = pd.to_numeric(
        thresholds["Minimum_Stock"], errors="coerce"
    ).fillna(0).values


# -------------------- METRICS --------------------

today = pd.Timestamp(date.today())
df["Days_To_Expiry"] = (df["Expiry_Date"] - today).dt.days
df["Stock_Value_EUR"] = df["Quantity_In_Stock"] * df["Unit_Cost_EUR"]
df["Suggested_Reorder"] = (
    df["Minimum_Stock"] - df["Quantity_In_Stock"]
).clip(lower=0)
df["Estimated_Reorder_Cost_EUR"] = (
    df["Suggested_Reorder"] * df["Unit_Cost_EUR"]
)

def stock_status(row):
    if row["Quantity_In_Stock"] <= 0:
        return "Out of stock"
    if row["Quantity_In_Stock"] < row["Minimum_Stock"]:
        return "Low stock"
    return "Sufficient stock"

def expiry_status(row):
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

df["Stock_Status_Calculated"] = df.apply(stock_status, axis=1)
df["Expiry_Status"] = df.apply(expiry_status, axis=1)

# -------------------- FILTERS --------------------

st.sidebar.divider()
st.sidebar.header("Filter inventory")

categories = sorted(df["Category"].unique().tolist())
suppliers = sorted(df["Supplier"].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Category", categories, default=categories
)
selected_suppliers = st.sidebar.multiselect(
    "Supplier", suppliers, default=suppliers
)

filtered = df[
    df["Category"].isin(selected_categories)
    & df["Supplier"].isin(selected_suppliers)
].copy()

if filtered.empty:
    st.warning("No items match the selected filters.")
    st.stop()

# -------------------- DASHBOARD --------------------

st.divider()
st.subheader("3. Inventory overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Inventory records", f"{len(filtered):,}")
c2.metric("Estimated stock value", f"€{filtered['Stock_Value_EUR'].sum():,.2f}")
c3.metric(
    "Low-stock items",
    int((filtered["Stock_Status_Calculated"] == "Low stock").sum()),
)
c4.metric(
    "Expired items",
    int((filtered["Expiry_Status"] == "Expired").sum()),
)

c5, c6 = st.columns(2)
c5.metric(
    "Out-of-stock items",
    int((filtered["Stock_Status_Calculated"] == "Out of stock").sum()),
)
c6.metric(
    "Expiring within 90 days",
    int(filtered["Expiry_Status"].isin([
        "Expires within 30 days", "Expires within 90 days"
    ]).sum()),
)

st.subheader("Stock status")
stock_summary = (
    filtered["Stock_Status_Calculated"]
    .value_counts()
    .rename_axis("Stock Status")
    .reset_index(name="Number of Items")
)
st.plotly_chart(
    px.bar(
        stock_summary,
        x="Stock Status",
        y="Number of Items",
        color="Stock Status",
        text="Number of Items",
    ),
    use_container_width=True,
)

st.subheader("Inventory value by category")
category_summary = (
    filtered.groupby("Category", as_index=False)["Stock_Value_EUR"]
    .sum()
    .sort_values("Stock_Value_EUR", ascending=False)
)
st.plotly_chart(
    px.bar(
        category_summary,
        x="Category",
        y="Stock_Value_EUR",
        text_auto=".2f",
    ),
    use_container_width=True,
)

st.divider()
st.subheader("Low-stock alerts")
low_stock = filtered[
    filtered["Stock_Status_Calculated"] != "Sufficient stock"
].copy()
if low_stock.empty:
    st.success("No low-stock items were found.")
else:
    st.dataframe(
        low_stock[[
            "Item_ID", "Item_Name", "Category", "Quantity_In_Stock",
            "Minimum_Stock", "Suggested_Reorder", "Supplier"
        ]],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("Expiry monitoring")
expiry_choice = st.selectbox(
    "Filter by expiry status",
    [
        "All", "Expired", "Expires within 30 days",
        "Expires within 90 days", "More than 90 days", "No expiry date"
    ],
)
expiry_view = filtered.copy() if expiry_choice == "All" else filtered[
    filtered["Expiry_Status"] == expiry_choice
]
st.dataframe(
    expiry_view[[
        "Item_Name", "Category", "Batch_Number", "Quantity_In_Stock",
        "Expiry_Date", "Days_To_Expiry", "Expiry_Status", "Supplier"
    ]].sort_values("Days_To_Expiry", na_position="last"),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.subheader("Reorder recommendations")
reorder = filtered[filtered["Suggested_Reorder"] > 0].sort_values(
    "Estimated_Reorder_Cost_EUR", ascending=False
)
if reorder.empty:
    st.success("No reorder recommendations for this selection.")
else:
    st.dataframe(
        reorder[[
            "Item_Name", "Quantity_In_Stock", "Minimum_Stock",
            "Suggested_Reorder", "Unit_Cost_EUR",
            "Estimated_Reorder_Cost_EUR", "Supplier"
        ]],
        use_container_width=True,
        hide_index=True,
    )
    st.metric(
        "Estimated reorder cost",
        f"€{reorder['Estimated_Reorder_Cost_EUR'].sum():,.2f}",
    )

st.divider()
st.subheader("Download report")
st.download_button(
    "Download filtered inventory as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="medical_inventory_report.csv",
    mime="text/csv",
)

st.caption(
    "Built with Python, Pandas, Streamlit and Plotly. "
    "Portfolio demonstration, not a validated clinical system."
)
