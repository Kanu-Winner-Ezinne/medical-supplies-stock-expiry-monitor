# Medical Supplies Stock and Expiry Monitor

## Project Overview

The Medical Supplies Stock and Expiry Monitor is a Python-based inventory management application developed with Streamlit. It helps users monitor medical supplies, identify low-stock items, track approaching expiry dates, and estimate inventory and replenishment costs.

The project demonstrates how data analytics can support inventory control, reduce avoidable waste, and improve stock management decisions.

## Objectives

- Monitor available stock levels for medical supplies.
- Identify items that fall below their minimum stock thresholds.
- Track expired items and supplies approaching their expiry dates.
- Calculate suggested replenishment quantities.
- Estimate inventory value and replenishment costs.
- Present inventory information through interactive dashboards and charts.
- Allow users to export inventory reports for further analysis.

## Key Features

### Data Upload and Processing

- Upload inventory data in CSV or Excel format.
- Automatically identify common inventory column names.
- Review and adjust column mappings.
- Clean and validate quantity, cost, and expiry-date fields.
- Use sample inventory data to explore the application.

### Stock Monitoring

- Configure minimum stock thresholds.
- Classify items according to their stock levels.
- Identify supplies requiring replenishment.
- Calculate suggested reorder quantities.

### Expiry Monitoring

- Identify expired medical supplies.
- Flag items approaching their expiry dates.
- Configure the number of days used for expiry warnings.
- Filter inventory by expiry status.

### Inventory Analytics

- View the number of inventory items and total units in stock.
- Monitor low-stock and out-of-stock items.
- Review expiry-related alerts.
- Estimate total inventory value and replenishment costs.
- Explore inventory distributions using interactive charts.

### Reporting

- Filter inventory by category, stock status, and expiry status.
- Review inventory records and calculated indicators.
- Download filtered inventory data as a CSV report.

## Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- OpenPyXL
- Git and GitHub
- Streamlit Community Cloud

## Project Structure

```text
medical-supplies-stock-expiry-monitor/
├── app.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### Prerequisites

Install Python 3.9 or later and ensure that Git is available if you intend to clone the repository.

### 1. Clone the Repository

```bash
git clone https://github.com/Kanu-Winner-Ezinne/medical-supplies-stock-expiry-monitor.git
```

### 2. Navigate to the Project Directory

```bash
cd medical-supplies-stock-expiry-monitor
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

## Data Requirements

The application is designed to work with medical inventory datasets containing fields such as:

| Field | Description |
|---|---|
| Item Name | Name of the medical supply |
| Quantity in Stock | Current quantity available |
| Expiry Date | Expiration date of the item |
| Minimum Stock | Minimum acceptable stock level |
| Unit Cost | Cost per unit |
| Category | Inventory category |
| Item ID | Unique item identifier |
| Batch Number | Batch identification number |
| Supplier | Supplier name |

The application can automatically recognize several common column names. Users can review the detected mappings before proceeding.

Some fields may be optional, depending on the calculations and monitoring features required.

## Business Value

Effective medical inventory management is important for maintaining supply availability, controlling costs, and reducing waste.

This application demonstrates how data cleaning, validation, threshold-based monitoring, and interactive reporting can help inventory managers identify potential stock shortages and expiry risks.

The application is intended as a portfolio and analytical demonstration rather than a replacement for a validated medical inventory management system.

## Limitations

- The quality of the analysis depends on the accuracy and completeness of the uploaded data.
- Replenishment estimates are based on configured stock thresholds rather than actual demand forecasting.
- The application does not connect to live hospital inventory systems or supplier databases.
- It does not automatically place orders or manage inventory transactions.
- Cost estimates depend on the availability and accuracy of unit-cost information.

## Potential Improvements

- Add demand forecasting using historical consumption data.
- Introduce supplier performance analysis.
- Add automated notifications for low stock and approaching expiry dates.
- Include batch-level tracking and first-expiry-first-out recommendations.
- Connect the application to a database for persistent inventory records.
- Implement user authentication and role-based access.
- Develop more advanced replenishment recommendations.

## Skills Demonstrated

This project demonstrates practical skills in:

- Python programming and data manipulation
- Data cleaning and validation
- Exploratory data analysis
- Business intelligence and dashboard development
- KPI design and inventory reporting
- Interactive data visualization
- Data-driven decision support
- Application deployment and GitHub project documentation



## License

This project is intended for educational, demonstration, and portfolio purposes. A formal open-source license can be added to the repository if redistribution and reuse permissions are required.
