# Data-Visualisation-Project-
## Engineering College Library Management System (LMS)
### Modern Data Visualization & Business Intelligence Platform

A clean, terminal-based Library Management System in Python 3.x designed for an engineering college library serving six departments (**Computer Science, Mechanical, Civil, AIML, Electronics, and E&TC**).

Built from the ground up to provide **rich, intuitive, domain-driven data visualizations** adhering directly to the Data Visualization course syllabus.

---

## 🌟 Key Highlights & Design Principles

1. **Focused on Practical Library Visualizations**:
   - **Department Breakdown**: Visual comparison of book copies across departments (CS, Mech, Civil, AIML, Electronics, E&TC).
   - **Author Analytics**: Top authors in the catalog by number of titles and student borrow frequency.
   - **Loan Status Breakdown**: Active loans vs returned books vs overdue items.
   - **Statistical Diagnostics**: Loan duration spread, fine accumulations, ECDF, and Q-Q normality checks.
   - **Borrowing Timeline & Trends**: Monthly issue trends, 3-month moving average smoothing, and seasonal decomposition.
   - **Student Demographics & Campus Geospatial Maps**: Interactive state choropleth map, campus reading room layer map, and proportional symbol cartogram.
   - **Student Profile Clustering**: 2D Principal Component Analysis (PCA) on borrowing behavior.

2. **Core LMS Operations**:
   - ➕ **Add Book**: Add new catalog titles with copy count and publisher state.
   - ➖ **Remove / Minus Book**: Reduce copy counts or safely delete unloaned titles.
   - 🔍 **Search Catalog**: Query by title, author, or department.
   - 👥 **Student Directory**: Student records across 10 Indian states and academic years 1-4.
   - 📖 **Issue Book**: Automatic 14-day due date calculation and shelf availability verification.
   - 📥 **Return Book**: Automatic overdue fine calculation (₹5/day).
   - ⚠️ **Overdue Tracker**: Immediate identification of delinquent loans.
   - 📑 **Power BI Export**: Exports data directly to `library_export.xlsx` for executive dashboarding.

3. **High Data-Ink Ratio & Minimal Visual Clutter**:
   - Avoids artificial 3D perspective distortion (Proportional Ink Principle).
   - Clean, modern color palettes (deep navy, teal, amber, slate).
   - Every visualization functions both on-demand via the CLI menu and through automated batch rendering.

---

## 🚀 Quick Setup & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python main.py
```
*(On first run, the SQLite database `library.db` is auto-initialized and seeded with 6 departments, 54 books, 90 students, and 280 transactions across 12 months).*

### 3. Generate All Visualizations in One Click
Choose **Option 12** from the main menu or run directly:
```bash
python -c "import visualizations; visualizations.generate_all_visualizations()"
```
- Static high-resolution PNGs are saved to `charts/`.
- Interactive dashboards and maps are saved to `interactive/` and open in your default browser.

---

## 📚 Complete Syllabus Mapping Matrix

Every topic and visual technique specified in the Data Visualization syllabus is mapped below:

| Syllabus Area | Course Topic / Concept | Implemented Feature & Chart Function | Output Location |
| :--- | :--- | :--- | :--- |
| **Intro to Data Viz** | Design Principles & Value of Visualization | `plot_design_principles_demo()`: Poor 3D Clutter vs Clean Horizontal Bar Chart | `charts/design_principles_comparison.png` |
| **Pre-processing & Aesthetics** | Data Cleaning & Duration Metrics | `preprocessing.py`: Active issue handling, `days_kept`, `overdue_days`, aggregations | Clean DataFrames |
| **Pre-processing & Aesthetics** | Multivariate Pairplot | `plot_borrowing_pairplot()`: Seaborn pairplot across metrics by department hue | `charts/borrowing_pairplot.png` |
| **Pre-processing & Aesthetics** | Violin Plot | `plot_duration_distributions()`: Violin plot showing duration distribution per dept | `charts/duration_distributions.png` |
| **Pre-processing & Aesthetics** | Heatmap & Continuous Scales | `plot_monthly_activity_heatmap()`: Dept x Month loan density with YlGnBu colormap | `charts/activity_heatmap.png` |
| **Pre-processing & Aesthetics** | Interactive Visualization | `plot_interactive_plotly_dashboard()`: Plotly interactive bar chart with hover tooltips | `interactive/interactive_dashboard.html` |
| **Pre-processing & Aesthetics** | Grammar of Graphics (Layering) | `plot_associations_and_pca()`: Scatter (`geom_point`) + Regression Line (`geom_smooth`) | `charts/associations_and_pca.png` |
| **Visualization Design** | Visualizing Amounts: Bar Plots | `plot_department_books()`: Total books per department (CS, Mech, Civil, AIML, etc.) | `charts/books_by_department.png` |
| **Visualization Design** | Visualizing Amounts: Dot Plots | `plot_cleveland_dot_plot()`: Cleveland dot plot comparing catalog depth | `charts/dot_books_per_dept.png` |
| **Visualization Design** | Grouped & Stacked Bars | `plot_loan_status_grouped_stacked()`: Loan status (Returned, Active, Overdue) per dept | `charts/loan_status_breakdown.png` |
| **Visualization Design** | Single Distribution: Hist + KDE | `plot_duration_distributions()`: Single histogram + KDE density of days kept | `charts/duration_distributions.png` |
| **Visualization Design** | Multiple Distributions Overlaid | `plot_duration_distributions()`: Overlaid KDE density curves across all departments | `charts/duration_distributions.png` |
| **Visualization Design** | Empirical Cumulative Distribution (ECDF) | `plot_statistical_diagnostics()`: ECDF plot of overdue fine distributions | `charts/statistical_diagnostics.png` |
| **Visualization Design** | Normal Quantile–Quantile (Q-Q) Plot | `plot_statistical_diagnostics()`: Q-Q plot comparing fine amounts to normal distribution | `charts/statistical_diagnostics.png` |
| **Visualization Design** | Highly Skewed Distributions | `plot_statistical_diagnostics()`: Raw skewed fine histogram vs log-transformed `log1p(fine)` | `charts/statistical_diagnostics.png` |
| **Advanced Design** | Vertical vs Horizontal Axis Layouts | `plot_vertical_vs_horizontal_layouts()`: Ridgeline KDE (horizontal) vs Boxplots (vertical) | `charts/vertical_vs_horizontal.png` |
| **Advanced Design** | Proportions: Case for Pie Charts | `plot_proportions_and_treemap()`: Department share pie chart of total loan volume | `charts/proportions_and_treemap.png` |
| **Advanced Design** | Proportions: 100% Stacked Bar | `plot_proportions_and_treemap()`: 100% stacked bar chart showing status proportions | `charts/proportions_and_treemap.png` |
| **Advanced Design** | Nested Proportions: Treemap | `plot_proportions_and_treemap()`: Squarify treemap of Department -> Book Titles | `charts/proportions_and_treemap.png` |
| **Advanced Design** | Associations: Scatter Plots | `plot_associations_and_pca()`: Fine amount vs overdue days scatter plot | `charts/associations_and_pca.png` |
| **Advanced Design** | Associations: Correlograms | `plot_associations_and_pca()`: Correlation matrix heatmap of quantitative metrics | `charts/associations_and_pca.png` |
| **Advanced Design** | Dimension Reduction (PCA) | `plot_associations_and_pca()`: 2D PCA projection clustering student borrowing habits | `charts/associations_and_pca.png` |
| **Advanced Design** | Paired Data: Slope Chart | `plot_paired_slope_chart()`: Expected due date (+14d) vs actual return offset | `charts/due_vs_return_slope.png` |
| **Time Series & Trends** | Individual Time Series | `plot_time_series_and_trends()`: Monthly issue volume line chart | `charts/time_series_and_trends.png` |
| **Time Series & Trends** | Multiple Time Series | `plot_time_series_and_trends()`: Multi-line chart per academic department | `charts/time_series_and_trends.png` |
| **Time Series & Trends** | Dose–Response Curve | `plot_advanced_time_series()`: Polynomial curve of fine accumulation over overdue days | `charts/advanced_time_series.png` |
| **Time Series & Trends** | Multiple Response Variables | `plot_advanced_time_series()`: Dual-axis monthly issues, returns, and revenue collected | `charts/advanced_time_series.png` |
| **Time Series & Trends** | Trend Smoothing & Regression Fit | `plot_time_series_and_trends()`: 3-month rolling average + linear regression trend line | `charts/time_series_and_trends.png` |
| **Time Series & Trends** | Detrending & Decomposition | `plot_advanced_time_series()`: `statsmodels.seasonal_decompose` (Trend, Seasonal, Resid) | `charts/advanced_time_series.png` |
| **Geospatial Data** | Projections & Choropleth Mapping | `plot_geospatial_choropleth()`: Interactive Plotly choropleth of Indian home states | `interactive/choropleth_map.html` |
| **Geospatial Data** | Multi-Layer Geospatial Mapping | `plot_folium_campus_map()`: Folium map with Student Origins & Campus Reading Rooms | `interactive/folium_map.html` |
| **Geospatial Data** | Simplified Cartogram Mapping | `plot_proportional_cartogram()`: Proportional bubble symbol map by state issues | `charts/cartogram_proportional.png` |
| **Power BI Integration** | Data Export to Excel (Multi-Sheet) | CLI Option 13 (`main.py`): Exports 4 tables to `library_export.xlsx` | `library_export.xlsx` |
| **Power BI Integration** | Business Intelligence & DAX Guide | [`POWERBI_GUIDE.md`](file:///c:/Users/Niosh%20Mate/OneDrive/3RD%20YEAR/DV/Mini%20Project/POWERBI_GUIDE.md): Power Query, DAX measures, Cards, KPIs, Slicers, RLS | `POWERBI_GUIDE.md` |

---

## 📁 Project Structure

```
.
├── main.py                     # CLI Entry Point & Core Library Operations
├── preprocessing.py            # Data Cleaning, Feature Engineering & Aggregations
├── visualizations.py           # Domain-Driven Visualization Suite
├── db_setup.py                 # SQLite Schema Setup & Realistic Data Seeding
├── library.db                  # Pre-populated SQLite Database
├── library_export.xlsx         # Multi-sheet Excel Source for Power BI
├── POWERBI_GUIDE.md            # Power BI Desktop Modeling & DAX Guide
├── requirements.txt            # Python Dependencies
├── README.md                   # Complete Documentation & Syllabus Mapping
├── charts/                     # Output Directory for High-Resolution PNG Charts
└── interactive/                # Output Directory for Interactive Plotly & Folium Maps
```

---
*Developed for Engineering College Library Management System — Data Visualization Course Project.*
