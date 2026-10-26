
import io
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
    "Monitor inventory, identify stock shortages, track expiry dates, "
    "and estimate replenishment costs."
)
st.info(
    "Portfolio demonstration only. Verify stock levels, costs, and expiry "
    "information before making operational decisions."
)

# --------------------------------------------------
# SAMPLE DATA
# --------------------------------------------------

def sample_data():
    today = pd.Timestamp.today().normalize()
    return pd.DataFrame({
        "Item_ID": ["M001", "M002", "M003", "M004", "M005", "M006"],
        "Item_Name": [
            "Surgical Gloves", "Face Masks", "IV Giving Sets",
            "Paracetamol", "Medical Gauze", "Antiseptic Solution"
        ],
        "Category": [
            "Protective Supply", "Protective Supply", "IV Fluid",
            "Tablet", "Surgical Supply", "Liquid"
        ],
        "Batch_Number": ["B001", "B002", "B003", "B004", "B005", "B006"],
        "Supplier": ["Supplier A", "Supplier B", "Supplier A",
                     "Supplier C", "Supplier B", "Supplier C"],
        "Quantity_In_Stock": [120, 15, 8, 200, 25, 12],
        "Minimum_Stock": [50, 40, 20, 100, 30, 20],
        "Unit_Cost_EUR": [0.15, 0.08, 1.80, 0.12, 0.50, 1.20],
        "Expiry_Date": [
            today + pd.Timedelta(days=240),
            today + pd.Timedelta(days=18),
            today + pd.Timedelta(days=10),
            today + pd.Timedelta(days=400),
            today - pd.Timedelta(days=3),
            today + pd.Timedelta(days=60),
        ],
    })


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

st.sidebar.header("📂 Inventory data")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    raw_df = sample_data()
    st.caption("Showing fictional sample data.")
else:
    try:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            raw_df = pd.read_excel(io.BytesIO(file_bytes))
        st.success(f"Loaded {len(raw_df):,} rows from {uploaded_file.name}")
    except Exception as exc:
        st.error(f"Could not read this file: {exc}")
        st.stop()

if raw_df.empty:
    st.error("The uploaded file has no rows.")
    st.stop()

raw_df.columns = [str(c).strip() for c in raw_df.columns]


# --------------------------------------------------
# AUTOMATIC COLUMN MATCHING
# --------------------------------------------------

ALIASES = {
    "Item_Name": [
        "item_name", "medicine_name", "product_name", "medicine",
        "product", "item", "name"
    ],
    "Quantity_In_Stock": [
        "quantity_in_stock", "quantity", "stock_quantity", "qty",
        "current_stock", "available_quantity", "stock_level"
    ],
    "Expiry_Date": [
        "expiry_date", "expiration_date", "expiry", "expiration",
        "expires_on"
    ],
    "Minimum_Stock": [
        "minimum_stock", "min_stock", "reorder_level",
        "minimum_quantity", "reorder_point", "safety_stock"
    ],
    "Unit_Cost_EUR": [
        "unit_cost_eur", "unit_cost", "purchase_price",
        "unit_price", "cost_per_unit", "cost"
    ],
    "Category": ["category", "item_category", "medicine_category"],
    "Item_ID": ["item_id", "medicine_id", "product_id", "sku", "id"],
    "Batch_Number": ["batch_number", "batch_no", "batch", "lot_number"],
    "Supplier": ["supplier", "supplier_name", "vendor"],
}

def normalize(value):
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")

def find_column(target):
    normalized_columns = {normalize(c): c for c in raw_df.columns}
    for alias in ALIASES[target]:
        if alias in normalized_columns:
            return normalized_columns[alias]
    return None

st.subheader("1. Match your columns")
st.write("Review the automatic matches. Required fields are marked with *.")

mapping = {}
column_options = ["— Not available —"] + list(raw_df.columns)

field_labels = {
    "Item_Name": "Item name *",
    "Quantity_In_Stock": "Quantity in stock *",
    "Expiry_Date": "Expiry date *",
    "Minimum_Stock": "Minimum stock threshold",
    "Unit_Cost_EUR": "Unit purchase cost (€)",
    "Category": "Category",
    "Item_ID": "Item ID",
    "Batch_Number": "Batch / lot number",
    "Supplier": "Supplier",
}

with st.expander("Configure column mapping", expanded=True):
    fields = list(field_labels.keys())
    for start in range(0, len(fields), 2):
        columns = st.columns(2)
        for col, field in zip(columns, fields[start:start + 2]):
            suggested = find_column(field)
            index = column_options.index(suggested) if suggested else 0
            chosen = col.selectbox(
                field_labels[field],
                column_options,
                index=index,
                key=f"map_{field}",
            )
            mapping[field] = (
                None if chosen == "— Not available —" else chosen
            )

required = ["Item_Name", "Quantity_In_Stock", "Expiry_Date"]
missing = [f for f in required if mapping[f] is None]
if missing:
    st.error("Please select a source column for each required field.")
    st.stop()


# --------------------------------------------------
# STANDARDIZE DATA
# --------------------------------------------------

df = pd.DataFrame(index=raw_df.index)

for field in field_labels:
    source = mapping[field]
    df[field] = raw_df[source] if source else pd.NA

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

for field in ["Category", "Item_ID", "Batch_Number", "Supplier"]:
    df[field] = df[field].fillna("").astype(str).str.strip()

# Report the source data quality before filtering.
st.caption(
    f"Uploaded records: {len(df):,} | "
    f"Rows missing a usable item name: "
    f"{int((df['Item_Name'].isna() | df['Item_Name'].eq('')).sum()):,} | "
    f"Rows with invalid quantity: "
    f"{int(df['Quantity_In_Stock'].isna().sum()):,} | "
    f"Rows with invalid expiry date: "
    f"{int(df['Expiry_Date'].isna().sum()):,}"
)

invalid = (
    df["Item_Name"].isna()
    | df["Item_Name"].eq("")
    | df["Quantity_In_Stock"].isna()
    | df["Expiry_Date"].isna()
)

if invalid.any():
    st.warning(
        f"{int(invalid.sum())} rows have missing or invalid required data "
        "and will be excluded. Check your column mapping if this number "
        "is unexpectedly high."
    )
    df = df.loc[~invalid].copy()

if df.empty:
    st.error(
        "No usable records remain. Check that the selected columns contain "
        "item names, numeric quantities, and valid expiry dates."
    )
    st.stop()

# Keep unknown costs as unknown rather than pretending they are zero.
has_cost_column = mapping["Unit_Cost_EUR"] is not None
df["Unit_Cost_EUR"] = df["Unit_Cost_EUR"].where(
    df["Unit_Cost_EUR"] >= 0
)

# Fill missing thresholds with a user-configurable default.
st.sidebar.header("⚙️ Monitoring settings")
warning_days = st.sidebar.number_input(
    "Expiry warning window (days)", 1, 365, 30
)
default_threshold = st.sidebar.number_input(
    "Default minimum stock", 0, 1000000, 20
)

df["Minimum_Stock"] = df["Minimum_Stock"].where(
    df["Minimum_Stock"].notna() & (df["Minimum_Stock"] >= 0),
    default_threshold,
)


# --------------------------------------------------
# EDIT THRESHOLDS
# --------------------------------------------------

st.subheader("2. Review stock thresholds")
st.write(
    "Edit minimum stock values if needed. These edits apply to the current "
    "session only; they do not alter your uploaded file."
)

editor_columns = ["Item_Name", "Quantity_In_Stock", "Minimum_Stock"]
if df["Item_ID"].ne("").any():
    editor_columns.insert(0, "Item_ID")

edited = st.data_editor(
    df[editor_columns].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in editor_columns if c != "Minimum_Stock"],
    column_config={
        "Minimum_Stock": st.column_config.NumberColumn(
            "Minimum stock",
            min_value=0,
            step=1,
        )
    },
    key="stock_threshold_editor",
)

df = df.reset_index(drop=True)
df["Minimum_Stock"] = pd.to_numeric(
    edited["Minimum_Stock"], errors="coerce"
).fillna(default_threshold).clip(lower=0)


# --------------------------------------------------
# CALCULATE STATUS
# --------------------------------------------------

today = pd.Timestamp.today().normalize()
expiry_cutoff = today + pd.Timedelta(days=int(warning_days))

df["Days_To_Expiry"] = (df["Expiry_Date"] - today).dt.days

df["Stock_Status"] = "Adequate"
df.loc[
    df["Quantity_In_Stock"] <= df["Minimum_Stock"], "Stock_Status"
] = "Low Stock"
df.loc[
    df["Quantity_In_Stock"] <= 0, "Stock_Status"
] = "Out of Stock"

df["Expiry_Status"] = "Not Expiring Soon"
df.loc[df["Expiry_Date"] < today, "Expiry_Status"] = "Expired"
df.loc[
    (df["Expiry_Date"] >= today) & (df["Expiry_Date"] <= expiry_cutoff),
    "Expiry_Status"
] = "Expiring Soon"

df["Reorder_Quantity"] = (
    df["Minimum_Stock"] - df["Quantity_In_Stock"]
).clip(lower=0)

if has_cost_column:
    df["Inventory_Value_EUR"] = (
        df["Quantity_In_Stock"] * df["Unit_Cost_EUR"]
    )
    df["Replenishment_Cost_EUR"] = (
        df["Reorder_Quantity"] * df["Unit_Cost_EUR"]
    )


# --------------------------------------------------
# FILTERS — APPLY TO THE ACTUAL DATAFRAME
# --------------------------------------------------

st.subheader("3. Inventory overview")

categories = sorted(
    x for x in df["Category"].unique() if str(x).strip()
)

c1, c2, c3 = st.columns(3)

if categories:
    selected_categories = c1.multiselect(
        "Category",
        options=categories,
        default=categories,
    )
else:
    selected_categories = []
    c1.caption("No category column mapped; showing all categories.")

stock_filter = c2.selectbox(
    "Stock status",
    ["All", "Out of Stock", "Low Stock", "Adequate"],
)
expiry_filter = c3.selectbox(
    "Expiry status",
    ["All", "Expired", "Expiring Soon", "Not Expiring Soon"],
)

# IMPORTANT: an empty category selection means show all rows,
# not zero rows. This prevents the zero-count issue.
filtered = df.copy()

if categories and selected_categories:
    filtered = filtered[filtered["Category"].isin(selected_categories)]

if stock_filter != "All":
    filtered = filtered[filtered["Stock_Status"] == stock_filter]

if expiry_filter != "All":
    filtered = filtered[filtered["Expiry_Status"] == expiry_filter]

if filtered.empty:
    st.warning(
        "No records match the selected filters. Choose more categories "
        "or set the status filters to All."
    )

# --------------------------------------------------
# METRICS
# --------------------------------------------------

m1, m2, m3 = st.columns(3)
m1.metric("Inventory items", f"{len(filtered):,}")
m2.metric("Total units in stock", f"{filtered['Quantity_In_Stock'].sum():,.0f}")
m3.metric(
    "Out-of-stock items",
    f"{int((filtered['Stock_Status'] == 'Out of Stock').sum()):,}",
)

m4, m5, m6 = st.columns(3)
m4.metric(
    "Low-stock items",
    f"{int((filtered['Stock_Status'] == 'Low Stock').sum()):,}",
)
m5.metric(
    "Expired items",
    f"{int((filtered['Expiry_Status'] == 'Expired').sum()):,}",
)
m6.metric(
    f"Expiring in {warning_days} days",
    f"{int((filtered['Expiry_Status'] == 'Expiring Soon').sum()):,}",
)

if has_cost_column:
    inventory_value = filtered["Inventory_Value_EUR"].sum(min_count=1)
    replenishment = filtered["Replenishment_Cost_EUR"].sum(min_count=1)

    m7, m8 = st.columns(2)
    m7.metric(
        "Estimated inventory value",
        "Unavailable" if pd.isna(inventory_value)
        else f"€{inventory_value:,.2f}",
    )
    m8.metric(
        "Estimated replenishment cost",
        "Unavailable" if pd.isna(replenishment)
        else f"€{replenishment:,.2f}",
    )
else:
    st.info(
        "Map a unit purchase-cost column to calculate inventory value "
        "and estimated replenishment costs. Do not use selling price "
        "as purchase cost."
    )


# --------------------------------------------------
# CHARTS
# --------------------------------------------------

st.subheader("4. Inventory analytics")

if not filtered.empty:
    left, right = st.columns(2)

    with left:
        stock_chart = (
            filtered["Stock_Status"]
            .value_counts()
            .rename_axis("Stock status")
            .reset_index(name="Items")
        )
        fig_stock = px.bar(
            stock_chart,
            x="Stock status",
            y="Items",
            color="Stock status",
            title="Stock status distribution",
            text="Items",
        )
        st.plotly_chart(fig_stock, use_container_width=True)

    with right:
        expiry_chart = (
            filtered["Expiry_Status"]
            .value_counts()
            .rename_axis("Expiry status")
            .reset_index(name="Items")
        )
        fig_expiry = px.pie(
            expiry_chart,
            names="Expiry status",
            values="Items",
            title="Expiry status distribution",
            hole=0.4,
        )
        st.plotly_chart(fig_expiry, use_container_width=True)

    if filtered["Category"].ne("").any():
        category_chart = (
            filtered.groupby("Category", as_index=False)
            ["Quantity_In_Stock"].sum()
        )
        fig_category = px.bar(
            category_chart,
            x="Category",
            y="Quantity_In_Stock",
            title="Units in stock by category",
            text_auto=True,
        )
        st.plotly_chart(fig_category, use_container_width=True)
else:
    st.info("Charts will appear when records match your filters.")


# --------------------------------------------------
# ALERTS
# --------------------------------------------------

st.subheader("5. Actionable inventory alerts")

tab_stock, tab_expired, tab_expiring = st.tabs(
    ["Stock shortages", "Expired items", "Expiring soon"]
)

with tab_stock:
    shortages = filtered[
        filtered["Stock_Status"].isin(["Out of Stock", "Low Stock"])
    ].copy()

    if shortages.empty:
        st.success("No stock shortages in the filtered inventory.")
    else:
        cols = [
            "Item_Name", "Quantity_In_Stock", "Minimum_Stock",
            "Stock_Status", "Reorder_Quantity"
        ]
        if has_cost_column:
            cols.append("Replenishment_Cost_EUR")
        st.dataframe(
            shortages[cols].sort_values("Reorder_Quantity", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tab_expired:
    expired = filtered[filtered["Expiry_Status"] == "Expired"]
    if expired.empty:
        st.success("No expired items in the filtered inventory.")
    else:
        st.dataframe(
            expired[
                ["Item_Name", "Batch_Number", "Expiry_Date",
                 "Days_To_Expiry", "Quantity_In_Stock"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab_expiring:
    expiring = filtered[filtered["Expiry_Status"] == "Expiring Soon"]
    if expiring.empty:
        st.success("No items are expiring within the warning window.")
    else:
        st.dataframe(
            expiring[
                ["Item_Name", "Batch_Number", "Expiry_Date",
                 "Days_To_Expiry", "Quantity_In_Stock"]
            ].sort_values("Days_To_Expiry"),
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# FULL REPORT AND DOWNLOAD
# --------------------------------------------------

st.subheader("6. Full inventory report")

report_columns = [
    "Item_Name", "Category", "Batch_Number", "Supplier",
    "Quantity_In_Stock", "Minimum_Stock", "Stock_Status",
    "Expiry_Date", "Days_To_Expiry", "Expiry_Status",
    "Reorder_Quantity",
]

if has_cost_column:
    report_columns += [
        "Unit_Cost_EUR", "Inventory_Value_EUR",
        "Replenishment_Cost_EUR",
    ]

st.dataframe(
    filtered[report_columns],
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "⬇️ Download filtered inventory report (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="medical_supplies_inventory_report.csv",
    mime="text/csv",
)

st.caption(
    "Built with Python, Pandas, Streamlit, and Plotly. "
    "This portfolio project is not a validated clinical inventory system."
)
