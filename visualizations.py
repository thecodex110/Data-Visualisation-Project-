import os
import webbrowser
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
import plotly.express as px
import plotly.graph_objects as go
import folium
import squarify

from preprocessing import (
    get_cleaned_transactions,
    get_department_aggregates,
    get_author_aggregates,
    get_monthly_matrix,
    get_monthly_timeseries,
    get_student_feature_matrix,
    get_state_geospatial_summary
)

CHARTS_DIR = "charts"
INTERACTIVE_DIR = "interactive"

def ensure_dirs():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    os.makedirs(INTERACTIVE_DIR, exist_ok=True)

def show_and_close():
    """Helper to display plot and close figure buffer cleanly without hanging."""
    try:
        if plt.get_backend().lower() != 'agg':
            plt.show()
    except Exception:
        pass
    finally:
        plt.close('all')

# Professional modern styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.edgecolor': '#CBD5E1',
    'grid.color': '#F1F5F9',
    'grid.linestyle': '--',
    'figure.autolayout': False
})

DEPT_PALETTE = {
    'Computer Science': '#1E3A8A',
    'AIML': '#0D9488',
    'Mechanical': '#D97706',
    'Civil': '#DC2626',
    'Electronics': '#7C3AED',
    'E&TC': '#2563EB'
}

# ==============================================================================
# SECTION 1: INVENTORY & AMOUNTS (Books by Dept, Authors, Dot Plots, Status Bars)
# ==============================================================================

def plot_department_books():
    """Visualizes book holdings across departments (CS, Mech, Civil, AIML, etc.)."""
    ensure_dirs()
    summary = get_department_aggregates().sort_values('total_copies', ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(summary['dept_name'], summary['total_copies'], color='#2563EB', width=0.55, edgecolor='#1E40AF', linewidth=1)
    
    # Value annotations on bar tips
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1, f'{int(height)} copies', 
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1E3A8A')
        
    ax.set_title("Library Collection: Total Book Copies by Department", pad=12)
    ax.set_xlabel("Academic Department")
    ax.set_ylabel("Total Copies in Inventory")
    ax.set_ylim(0, max(summary['total_copies']) + 8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=15)
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "books_by_department.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Books by Department -> {out_path}")
    show_and_close()

def plot_author_analytics():
    """Visualizes top authors by number of book titles and total student borrow count."""
    ensure_dirs()
    author_df = get_author_aggregates().head(10).sort_values('total_borrowed', ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(author_df))
    bars = ax.barh(y_pos, author_df['total_borrowed'], color='#0D9488', height=0.6, alpha=0.9)
    
    for bar, (_, row) in zip(bars, author_df.iterrows()):
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{int(w)} loans ({int(row['book_titles'])} titles)", 
                va='center', ha='left', fontsize=9, fontweight='bold', color='#134E4A')
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(author_df['author'], fontsize=9.5)
    ax.set_xlabel("Total Times Borrowed by Students")
    ax.set_title("Top 10 Most Popular Authors: Borrowing Volume & Catalog Titles", pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "author_distribution.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Author Analytics -> {out_path}")
    show_and_close()

def plot_cleveland_dot_plot():
    """Cleveland Dot Plot comparing department book holdings (cleaner than bar charts)."""
    ensure_dirs()
    summary = get_department_aggregates().sort_values('total_copies')
    
    plt.figure(figsize=(9, 5))
    plt.hlines(y=summary['dept_name'], xmin=0, xmax=summary['total_copies'], color='#94A3B8', alpha=0.8, linewidth=1.5)
    plt.scatter(summary['total_copies'], summary['dept_name'], color='#D97706', s=120, zorder=3, edgecolors='#78350F')
    
    for _, row in summary.iterrows():
        plt.text(row['total_copies'] + 1, row['dept_name'], f"{int(row['total_copies'])}", 
                 va='center', fontsize=9.5, fontweight='bold', color='#78350F')
        
    plt.title("Cleveland Dot Plot: Department Book Inventory\n(High Data-Ink Alternative to Bar Chart)", pad=10)
    plt.xlabel("Total Book Copies")
    plt.ylabel("Department")
    plt.xlim(0, max(summary['total_copies']) + 10)
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "dot_books_per_dept.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Cleveland Dot Plot -> {out_path}")
    show_and_close()

def plot_loan_status_grouped_stacked():
    """Grouped and Stacked Bar Charts of loan status (Returned, Active, Overdue) per department."""
    ensure_dirs()
    summary = get_department_aggregates()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # 1. Grouped Bar Chart
    melted = summary.melt(id_vars=['dept_name'], value_vars=['Returned', 'Active Issued', 'Overdue'], 
                          var_name='Status', value_name='Count')
    sns.barplot(x='dept_name', y='Count', hue='Status', data=melted, ax=axes[0], palette=['#10B981', '#3B82F6', '#EF4444'])
    axes[0].set_title("Grouped Bar Chart: Loan Status by Department", fontweight='bold')
    axes[0].set_xlabel("Department")
    axes[0].set_ylabel("Transaction Count")
    axes[0].tick_params(axis='x', rotation=20)
    
    # 2. Stacked Bar Chart
    summary_idx = summary.set_index('dept_name')[['Returned', 'Active Issued', 'Overdue']]
    summary_idx.plot(kind='bar', stacked=True, ax=axes[1], color=['#10B981', '#3B82F6', '#EF4444'], edgecolor='white')
    axes[1].set_title("Stacked Bar Chart: Loan Status by Department", fontweight='bold')
    axes[1].set_xlabel("Department")
    axes[1].set_ylabel("Total Transactions")
    axes[1].tick_params(axis='x', rotation=20)
    axes[1].legend(title="Status")
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "loan_status_breakdown.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Grouped & Stacked Status Breakdown -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 2: DISTRIBUTIONS & STATISTICAL ANALYSIS (Histograms, KDE, ECDF, Q-Q)
# ==============================================================================

def plot_duration_distributions():
    """Visualizing single & multiple distributions: Histogram + KDE, Overlaid KDEs, and Violin Plot."""
    ensure_dirs()
    df = get_cleaned_transactions()
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # 1. Single Distribution: Histogram + KDE
    sns.histplot(df['days_kept'], kde=True, ax=axes[0], color='#0D9488', bins=18, stat='density')
    axes[0].set_title("Single Distribution: Issue Duration (Days Kept)\n(Histogram + KDE Density)", fontweight='bold')
    axes[0].set_xlabel("Days Kept")
    axes[0].set_ylabel("Density")
    
    # 2. Overlaid Multiple Distributions across Departments
    sns.kdeplot(data=df, x='days_kept', hue='dept_name', ax=axes[1], common_norm=False, palette='tab10', linewidth=1.8)
    axes[1].set_title("Overlaid Multiple Distributions\n(KDE Across 6 Departments)", fontweight='bold')
    axes[1].set_xlabel("Days Kept")
    axes[1].set_ylabel("Density")
    
    # 3. Violin Plot across Departments
    sns.violinplot(x='dept_name', y='days_kept', hue='dept_name', data=df, ax=axes[2], 
                   palette='Spectral', inner='quartile', cut=0, legend=False)
    axes[2].set_title("Violin Plot: Duration Spread per Dept\n(Density & Quartiles)", fontweight='bold')
    axes[2].set_xlabel("Department")
    axes[2].set_ylabel("Days Kept")
    axes[2].tick_params(axis='x', rotation=25)
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "duration_distributions.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Duration Distributions -> {out_path}")
    show_and_close()

def plot_statistical_diagnostics():
    """Statistical graphics: ECDF, Normal Q-Q Plot, and Skewed vs Log Transformation."""
    ensure_dirs()
    df = get_cleaned_transactions()
    overdue_fines = df[df['effective_fine'] > 0]['effective_fine']
    log_fines = np.log1p(overdue_fines)
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # 1. ECDF Plot
    sns.ecdfplot(overdue_fines, ax=axes[0], color='#7C3AED', linewidth=2.2)
    axes[0].set_title("Empirical Cumulative Distribution Function\n(ECDF of Overdue Fines)", fontweight='bold')
    axes[0].set_xlabel("Fine Amount (₹)")
    axes[0].set_ylabel("Cumulative Proportion")
    
    # 2. Q-Q Plot
    stats.probplot(overdue_fines, dist="norm", plot=axes[1])
    axes[1].set_title("Normal Q-Q Plot\n(Assessing Fine Normality)", fontweight='bold')
    axes[1].get_lines()[0].set_markerfacecolor('#2563EB')
    axes[1].get_lines()[0].set_markersize(5)
    axes[1].get_lines()[1].set_color('#DC2626')
    
    # 3. Skewed vs Log-transformed Histogram
    axes[2].hist(overdue_fines, bins=15, alpha=0.5, color='#DC2626', label='Raw Skewed Fines (₹)', density=True)
    ax2_twin = axes[2].twiny()
    sns.kdeplot(log_fines, ax=ax2_twin, color='#0D9488', linewidth=2.2, label='log1p(Fine) KDE')
    axes[2].set_title("Handling Highly Skewed Data\n(Raw Fines vs Log-Transformed)", fontweight='bold')
    axes[2].set_xlabel("Raw Fine (₹)", color='#DC2626')
    ax2_twin.set_xlabel("log1p(Fine)", color='#0D9488')
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "statistical_diagnostics.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Statistical Diagnostics (ECDF, Q-Q, Log Transform) -> {out_path}")
    show_and_close()

def plot_vertical_vs_horizontal_layouts():
    """Distributions along Vertical vs Horizontal axis (Ridgeline KDE vs Vertical Boxplot)."""
    ensure_dirs()
    df = get_cleaned_transactions()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # Horizontal Layout (Ridgeline style)
    depts = df['dept_name'].unique()
    colors = sns.color_palette("muted", len(depts))
    for i, dept in enumerate(depts):
        dept_data = df[df['dept_name'] == dept]['days_kept']
        sns.kdeplot(dept_data, ax=axes[0], label=dept, color=colors[i], fill=True, alpha=0.35)
    axes[0].set_title("Horizontal Axis Orientation: Ridgeline / Overlapping KDE\n(Continuous Flow of Duration per Dept)", fontweight='bold')
    axes[0].set_xlabel("Days Kept")
    axes[0].set_ylabel("Density")
    axes[0].legend(title="Department", loc='upper right', fontsize=8.5)
    
    # Vertical Layout (Boxplots)
    sns.boxplot(x='dept_name', y='days_kept', hue='dept_name', data=df, ax=axes[1], palette='muted', legend=False)
    axes[1].set_title("Vertical Axis Orientation: Boxplots\n(Discrete Quartiles & Outliers Comparison)", fontweight='bold')
    axes[1].set_xlabel("Department")
    axes[1].set_ylabel("Days Kept")
    axes[1].tick_params(axis='x', rotation=20)
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "vertical_vs_horizontal.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Vertical vs Horizontal Layouts -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 3: PROPORTIONS & NESTED COMPOSITIONS (Pie, 100% Stacked, Treemap)
# ==============================================================================

def plot_proportions_and_treemap():
    """Visualizing proportions: Pie chart, 100% stacked bar, and nested Treemap."""
    ensure_dirs()
    summary = get_department_aggregates()
    df = get_cleaned_transactions()
    
    fig = plt.figure(figsize=(15, 5))
    
    # 1. Pie Chart
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.pie(summary['total_transactions'], labels=summary['dept_name'], autopct='%1.1f%%',
            startangle=140, colors=sns.color_palette("pastel"))
    ax1.set_title("Department Share of Total Loans\n(A Case for Pie Charts: Proportions of Whole)", fontweight='bold', fontsize=10.5)
    
    # 2. 100% Stacked Bar (Parts of Total)
    ax2 = fig.add_subplot(1, 3, 2)
    summary_idx = summary.set_index('dept_name')[['Returned', 'Active Issued', 'Overdue']]
    status_props = summary_idx.div(summary_idx.sum(axis=1), axis=0) * 100
    status_props.plot(kind='bar', stacked=True, ax=ax2, color=['#10B981', '#3B82F6', '#EF4444'], edgecolor='white')
    ax2.set_title("100% Stacked Bar: Proportions by Dept\n(Parts of Total Status Composition)", fontweight='bold', fontsize=10.5)
    ax2.set_xlabel("Department")
    ax2.set_ylabel("Proportion (%)")
    ax2.tick_params(axis='x', rotation=25)
    ax2.legend(title="Status", fontsize=8.5)
    
    # 3. Nested Treemap
    ax3 = fig.add_subplot(1, 3, 3)
    tree_data = df.groupby(['dept_name', 'book_title']).size().reset_index(name='count').head(16)
    labels = tree_data.apply(lambda r: f"{r['dept_name'][:4]}: {r['book_title'][:12]}.. ({r['count']})", axis=1)
    colors = sns.color_palette("Set3", len(tree_data))
    squarify.plot(sizes=tree_data['count'], label=labels, color=colors, alpha=0.85, ax=ax3)
    ax3.set_title("Nested Proportions Treemap\n(Department -> Book Title Borrow Volume)", fontweight='bold', fontsize=10.5)
    ax3.axis('off')
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "proportions_and_treemap.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Proportions & Treemap -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 4: ASSOCIATIONS & ADVANCED ANALYTICS (Scatter, Correlogram, PCA, Pairs)
# ==============================================================================

def plot_associations_and_pca():
    """Visualizing associations: Grammar of graphics scatter+regression, Correlogram, PCA 2D scatter."""
    ensure_dirs()
    df = get_cleaned_transactions()
    overdue_df = df[df['overdue_days'] > 0]
    
    fig = plt.figure(figsize=(16, 5))
    
    # 1. Grammar of Graphics: Multi-layer Scatter + Fitted Regression
    ax1 = fig.add_subplot(1, 3, 1)
    sns.scatterplot(x='overdue_days', y='effective_fine', hue='dept_name', data=overdue_df, s=65, ax=ax1, palette='tab10')
    sns.regplot(x='overdue_days', y='effective_fine', data=overdue_df, scatter=False, ax=ax1, color='red', line_kws={'linewidth': 2})
    ax1.set_title("Grammar of Graphics (Layering)\nPoints (geom_point) + Fitted Line (geom_smooth)", fontweight='bold', fontsize=10.5)
    ax1.set_xlabel("Overdue Days")
    ax1.set_ylabel("Fine Amount (₹)")
    
    # 2. Correlogram (Correlation Heatmap)
    ax2 = fig.add_subplot(1, 3, 2)
    corr_vars = df[['days_kept', 'effective_fine', 'total_copies', 'available_copies']].corr()
    sns.heatmap(corr_vars, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax2, cbar_kws={'shrink': 0.8})
    ax2.set_title("Correlogram: Matrix of Quantitative Variables\n(Linear Association Strength)", fontweight='bold', fontsize=10.5)
    
    # 3. PCA Dimension Reduction of Student Borrowing Profiles
    ax3 = fig.add_subplot(1, 3, 3)
    matrix = get_student_feature_matrix()
    dept_cols = [c for c in matrix.columns if c not in ['student_id', 'name', 'dept_id', 'home_state', 'primary_dept']]
    X = matrix[dept_cols].values
    pca = PCA(n_components=2, random_state=42)
    components = pca.fit_transform(X)
    pca_df = pd.DataFrame(components, columns=['PC1', 'PC2'])
    pca_df['Primary Dept'] = matrix['primary_dept']
    
    sns.scatterplot(x='PC1', y='PC2', hue='Primary Dept', data=pca_df, s=75, ax=ax3, palette='Set1')
    ax3.set_title(f"PCA Dimension Reduction (2D Projection)\nStudent Borrowing Profile Clusters (Exp. Var: {sum(pca.explained_variance_ratio_)*100:.1f}%)", 
                  fontweight='bold', fontsize=10.5)
    ax3.set_xlabel("PC1 (Borrowing Volume)")
    ax3.set_ylabel("PC2 (Department Focus)")
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "associations_and_pca.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Associations & PCA -> {out_path}")
    show_and_close()

def plot_borrowing_pairplot():
    """Seaborn Pairplot across library metrics colored by department."""
    ensure_dirs()
    df = get_cleaned_transactions()
    pair_df = df[['days_kept', 'effective_fine', 'total_copies', 'available_copies', 'dept_name']].copy()
    pair_df.rename(columns={'effective_fine': 'fine_amount'}, inplace=True)
    
    g = sns.pairplot(pair_df, hue='dept_name', corner=True, palette='Set2', diag_kind='kde')
    g.fig.suptitle("Multivariate Pairplot Matrix by Department", y=1.02, fontsize=12, fontweight='bold')
    
    out_path = os.path.join(CHARTS_DIR, "borrowing_pairplot.png")
    g.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Pairplot Matrix -> {out_path}")
    show_and_close()

def plot_paired_slope_chart():
    """Paired Slope Chart: Due Date (+14d) vs Actual Return Date Offset."""
    ensure_dirs()
    df = get_cleaned_transactions()
    returned_df = df[df['return_date_dt'].notnull()].sample(n=25, random_state=42).copy()
    
    plt.figure(figsize=(9, 5.5))
    for _, row in returned_df.iterrows():
        color = '#EF4444' if row['days_kept'] > 14 else '#10B981'
        plt.plot([1, 2], [14, row['days_kept']], marker='o', color=color, alpha=0.65, linewidth=1.8)
        
    plt.xticks([1, 2], ['Assigned Due Date (+14d)', 'Actual Return Date Offset'])
    plt.ylabel("Days from Issue")
    plt.title("Paired Data Slope Chart: Due Date vs Return Deviation\n(Green = On-Time, Red = Overdue Deviation)", pad=10)
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "due_vs_return_slope.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Paired Slope Chart -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 5: TIME SERIES & TREND ANALYSIS (Trends, Decomposition, Dose-Response)
# ==============================================================================

def plot_time_series_and_trends():
    """Visualizes time series: Individual monthly issues, multi-dept lines, and 3-month rolling average."""
    ensure_dirs()
    ts = get_monthly_timeseries()
    df = get_cleaned_transactions()
    monthly_dept = df.groupby(['issue_month', 'dept_name']).size().reset_index(name='issued_count')
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # 1. Total Monthly Issues
    axes[0].plot(ts['issue_month'], ts['issued_count'], marker='o', color='#1E3A8A', linewidth=2.2)
    axes[0].set_title("Individual Time Series: Monthly Book Issues", fontweight='bold')
    axes[0].set_xlabel("Month (YYYY-MM)")
    axes[0].set_ylabel("Total Issues")
    axes[0].tick_params(axis='x', rotation=45)
    
    # 2. Multiple Time Series (Per Department)
    sns.lineplot(x='issue_month', y='issued_count', hue='dept_name', data=monthly_dept, marker='o', ax=axes[1], palette='tab10')
    axes[1].set_title("Multiple Time Series: Issues by Department", fontweight='bold')
    axes[1].set_xlabel("Month (YYYY-MM)")
    axes[1].set_ylabel("Issues")
    axes[1].tick_params(axis='x', rotation=45)
    
    # 3. Trend Smoothing (3-Month Rolling Average) & Linear Fit
    x = np.arange(len(ts))
    y = ts['issued_count'].values
    slope, intercept, r_val, _, _ = stats.linregress(x, y)
    trend_line = slope * x + intercept
    
    axes[2].plot(ts['issue_month'], ts['issued_count'], label='Actual Issues', alpha=0.45, color='gray', linestyle='--')
    axes[2].plot(ts['issue_month'], ts['rolling_3m_issues'], label='3-Month Rolling Avg (Smoothing)', color='#DC2626', linewidth=2.2)
    axes[2].plot(ts['issue_month'], trend_line, label=f'Linear Trend (R²={r_val**2:.2f})', color='#2563EB', linestyle=':')
    axes[2].set_title("Trend Analysis: Smoothing & Regression Fit", fontweight='bold')
    axes[2].set_xlabel("Month (YYYY-MM)")
    axes[2].set_ylabel("Issues")
    axes[2].tick_params(axis='x', rotation=45)
    axes[2].legend(fontsize=8.5)
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "time_series_and_trends.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Time Series & Trends -> {out_path}")
    show_and_close()

def plot_advanced_time_series():
    """Dose-response curve, multi-response timeline, and seasonal decomposition."""
    ensure_dirs()
    ts = get_monthly_timeseries()
    df = get_cleaned_transactions()
    overdue_df = df[df['overdue_days'] > 0]
    
    fig = plt.figure(figsize=(16, 5))
    
    # 1. Dose-Response Curve (Fine buildup vs overdue days)
    ax1 = fig.add_subplot(1, 3, 1)
    sns.regplot(x='overdue_days', y='effective_fine', data=overdue_df, order=2, ax=ax1,
                scatter_kws={'alpha': 0.6, 'color': '#D97706'}, line_kws={'color': '#1E3A8A', 'linewidth': 2})
    ax1.set_title("Dose-Response Curve: Fine Buildup\n(Overdue Days = Dose, Fine ₹ = Response)", fontweight='bold', fontsize=10.5)
    ax1.set_xlabel("Overdue Days")
    ax1.set_ylabel("Fine Amount (₹)")
    
    # 2. Multi-Response Time Series (Issues, Returns, Fines)
    ax2 = fig.add_subplot(1, 3, 2)
    ax2.plot(ts['issue_month'], ts['issued_count'], color='#2563EB', marker='o', label='Issued Books')
    ax2.plot(ts['issue_month'], ts['returned_count'], color='#10B981', marker='s', label='Returned Books')
    ax2.set_xlabel("Month (YYYY-MM)")
    ax2.set_ylabel("Book Count")
    ax2.tick_params(axis='x', rotation=45)
    
    ax2_twin = ax2.twinx()
    ax2_twin.plot(ts['issue_month'], ts['total_fines'], color='#DC2626', marker='^', linestyle='--', label='Fines (₹)')
    ax2_twin.set_ylabel("Fines Collected (₹)", color='#DC2626')
    ax2.set_title("Multi-Response Time Series\n(Issues, Returns & Revenue over Time)", fontweight='bold', fontsize=10.5)
    
    # 3. Seasonal Decomposition (Trend, Seasonal, Residual)
    ax3 = fig.add_subplot(1, 3, 3)
    ts_decomp = ts.set_index(pd.to_datetime(ts['issue_month'] + '-01'))['issued_count']
    res = seasonal_decompose(ts_decomp, model='additive', period=3)
    ax3.plot(res.trend, color='#DC2626', label='Trend')
    ax3.plot(res.seasonal, color='#10B981', label='Seasonal')
    ax3.plot(res.resid, color='#7C3AED', label='Residual')
    ax3.set_title("Time Series Decomposition\n(Trend, Seasonal, Residual Components)", fontweight='bold', fontsize=10.5)
    ax3.tick_params(axis='x', rotation=45)
    ax3.legend(fontsize=8)
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "advanced_time_series.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Advanced Time Series & Decomposition -> {out_path}")
    show_and_close()

def plot_monthly_activity_heatmap():
    """Department x Month Heatmap with continuous colormap."""
    ensure_dirs()
    matrix = get_monthly_matrix()
    
    plt.figure(figsize=(11, 5.5))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='YlGnBu', cbar_kws={'label': 'Monthly Issue Count'}, linewidths=0.5)
    plt.title("Heatmap: Monthly Book Borrowing Intensity by Department\n(Aesthetic Mapping: X=Month, Y=Department, Color=Loan Density)", pad=10)
    plt.xlabel("Month (YYYY-MM)")
    plt.ylabel("Department")
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "activity_heatmap.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Activity Heatmap -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 6: GEOSPATIAL & DEMOGRAPHICS (Choropleth, Folium, Cartogram)
# ==============================================================================

def plot_geospatial_choropleth():
    """Interactive Plotly Choropleth of Indian states by student origin."""
    ensure_dirs()
    geo_df = get_state_geospatial_summary()
    geojson_url = "https://raw.githubusercontent.com/subhash-chandra/india-states-geojson/master/india_states.geojson"
    
    try:
        fig = px.choropleth(
            geo_df,
            geojson=geojson_url,
            featureidkey="properties.ST_NM",
            locations="home_state",
            color="student_count",
            color_continuous_scale="Blues",
            title="Geospatial Choropleth: Student Demographics Across Indian States",
            labels={'student_count': 'Total Students', 'home_state': 'State'}
        )
        fig.update_geos(fitbounds="locations", visible=False)
    except Exception as e:
        print(f"Notice: Network offline for GeoJSON ({e}). Generating scatter geo fallback...")
        fig = px.scatter_geo(
            geo_df,
            locations="home_state",
            locationmode="country names",
            size="student_count",
            color="student_count",
            hover_name="home_state",
            title="Geospatial Map: Student Demographics by Indian State",
            scope="asia"
        )
        
    fig.update_layout(template='plotly_white')
    out_html = os.path.join(INTERACTIVE_DIR, "choropleth_map.html")
    fig.write_html(out_html)
    print(f" [Interactive Map Exported] Indian States Choropleth -> {out_html}")
    try:
        webbrowser.open(os.path.abspath(out_html))
    except Exception:
        pass

def plot_folium_campus_map():
    """Folium map with 2 layers: Student Origins and Campus Reading Room Branches."""
    ensure_dirs()
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles='OpenStreetMap')
    
    state_coords = {
        "Maharashtra": [19.7515, 75.7139], "Karnataka": [15.3173, 75.7139],
        "Gujarat": [22.2587, 71.1924], "Delhi": [28.7041, 77.1025],
        "Tamil Nadu": [11.1271, 78.6569], "Uttar Pradesh": [26.8467, 80.9462],
        "Rajasthan": [27.0238, 74.2179], "Kerala": [10.8505, 76.2711],
        "West Bengal": [22.9868, 87.8550], "Telangana": [18.1124, 79.0193]
    }
    
    geo_df = get_state_geospatial_summary()
    fg_students = folium.FeatureGroup(name="Student Home States")
    for _, row in geo_df.iterrows():
        state = row['home_state']
        if state in state_coords:
            folium.CircleMarker(
                location=state_coords[state],
                radius=float(row['student_count']) * 0.8 + 4,
                popup=f"State: {state}<br>Students: {row['student_count']}<br>Book Loans: {row['total_issues']}",
                color='#1E40AF', fill=True, fill_color='#3B82F6', fill_opacity=0.65
            ).add_to(fg_students)
    fg_students.add_to(m)
    
    campus_branches = {
        "Computer Science Reading Room": [18.5204, 73.8567],
        "Mechanical Engineering Library": [18.5220, 73.8580],
        "Civil Engineering Branch": [18.5190, 73.8550],
        "AIML Research Lab Reading Desk": [18.5215, 73.8590],
        "Electronics Reading Room": [18.5230, 73.8540],
        "E&TC Department Library": [18.5180, 73.8575]
    }
    
    fg_branches = folium.FeatureGroup(name="Campus Reading Rooms (Branches)")
    for name, coords in campus_branches.items():
        folium.Marker(
            location=coords, popup=f"Branch: {name}",
            icon=folium.Icon(color='red', icon='book', prefix='fa')
        ).add_to(fg_branches)
    fg_branches.add_to(m)
    
    folium.LayerControl().add_to(m)
    out_html = os.path.join(INTERACTIVE_DIR, "folium_map.html")
    m.save(out_html)
    print(f" [Interactive Map Exported] Multi-layer Campus & Origins Map -> {out_html}")
    try:
        webbrowser.open(os.path.abspath(out_html))
    except Exception:
        pass

def plot_proportional_cartogram():
    """Proportional Symbol Map (Simplified Cartogram representation of borrow volume by state)."""
    ensure_dirs()
    geo_df = get_state_geospatial_summary()
    
    state_coords = {
        "Maharashtra": (75.7139, 19.7515), "Karnataka": (75.7139, 15.3173),
        "Gujarat": (71.1924, 22.2587), "Delhi": (77.1025, 28.7041),
        "Tamil Nadu": (78.6569, 11.1271), "Uttar Pradesh": (80.9462, 26.8467),
        "Rajasthan": (74.2179, 27.0238), "Kerala": (76.2711, 10.8505),
        "West Bengal": (87.8550, 22.9868), "Telangana": (79.0193, 18.1124)
    }
    
    plt.figure(figsize=(10, 7))
    for _, row in geo_df.iterrows():
        state = row['home_state']
        if state in state_coords:
            lon, lat = state_coords[state]
            issues = row['total_issues']
            size = issues * 45 + 120
            plt.scatter(lon, lat, s=size, alpha=0.55, color='#2563EB', edgecolors='#1E3A8A', linewidth=1.5)
            plt.text(lon, lat, f"{state}\n({int(issues)})", ha='center', va='center', fontsize=8.5, fontweight='bold')
            
    plt.title("Cartogram-Style Proportional Symbol Map\n(Bubble Size Proportional to Total Book Borrow Volume; Projection: WGS84 EPSG:4326)", pad=12)
    plt.xlabel("Longitude (°E)")
    plt.ylabel("Latitude (°N)")
    plt.tight_layout()
    
    out_path = os.path.join(CHARTS_DIR, "cartogram_proportional.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Proportional Cartogram Map -> {out_path}")
    show_and_close()

# ==============================================================================
# SECTION 7: DESIGN PRINCIPLES & INTERACTIVE DASHBOARD
# ==============================================================================

def plot_design_principles_demo():
    """Bad vs Good Chart Demonstration: Poor 3D Clutter vs Clean Horizontal Bar Chart."""
    ensure_dirs()
    summary = get_department_aggregates()
    
    fig = plt.figure(figsize=(14, 5.5))
    
    # 1. Deliberately Poor Chart (Violates Proportional Ink & Minimal Junk)
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    depts = summary['dept_name'].tolist()
    counts = summary['total_copies'].tolist()
    colors = ['#FF0000', '#00FF00', '#FF00FF', '#FFFF00', '#00FFFF', '#FFA500']
    
    x = np.arange(len(depts))
    y = np.zeros(len(depts))
    z = np.zeros(len(depts))
    dx = np.ones(len(depts)) * 0.75
    dy = np.ones(len(depts)) * 0.75
    dz = counts
    
    ax1.bar3d(x, y, z, dx, dy, dz, color=colors, alpha=0.75)
    ax1.set_title("POOR CHART: 3D Distorted Visual Clutter\n(Violates Proportional Ink & Adds Artificial Occlusion)", fontsize=10.5, color='#991B1B', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(depts, rotation=45, fontsize=8)
    
    # 2. Corrected Clean Chart (High Data-Ink Ratio, Accurate Linear Scaling)
    ax2 = fig.add_subplot(1, 2, 2)
    summary_sorted = summary.sort_values('total_copies', ascending=True)
    bars = ax2.barh(summary_sorted['dept_name'], summary_sorted['total_copies'], color='#2563EB', height=0.6)
    
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 1, bar.get_y() + bar.get_height()/2, f'{int(w)}', 
                 va='center', ha='left', fontsize=9.5, fontweight='bold', color='#1E3A8A')
        
    ax2.set_title("CORRECTED CHART: Clean Horizontal Bar Chart\n(High Data-Ink Ratio, Minimal Junk, Proper Encoding)", fontsize=10.5, color='#166534', fontweight='bold')
    ax2.set_xlabel("Total Book Copies Available")
    ax2.set_ylabel("Department")
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "design_principles_comparison.png")
    plt.savefig(out_path, dpi=300)
    print(f" [Chart Saved] Design Principles Comparison -> {out_path}")
    show_and_close()

def plot_interactive_plotly_dashboard():
    """Interactive Plotly Dashboard with tooltips, auto-opened in browser."""
    ensure_dirs()
    summary = get_department_aggregates()
    
    fig = px.bar(
        summary,
        x='dept_name',
        y='total_copies',
        color='available_copies',
        hover_data=['total_unique_titles', 'Active Issued', 'Returned', 'Overdue'],
        title="Interactive College Library Dashboard: Holdings & Real-time Loan Status",
        labels={'dept_name': 'Department', 'total_copies': 'Total Books', 'available_copies': 'Available on Shelf'},
        color_continuous_scale='Teal'
    )
    fig.update_layout(template='plotly_white', font=dict(family="Arial", size=12))
    
    out_html = os.path.join(INTERACTIVE_DIR, "interactive_dashboard.html")
    fig.write_html(out_html)
    print(f" [Interactive Dashboard Exported] -> {out_html}")
    try:
        webbrowser.open(os.path.abspath(out_html))
    except Exception:
        pass

def generate_all_visualizations():
    """Batch generator that generates all visual analytics in one go."""
    print("\n--- Generating Complete Visual Analytics Suite ---")
    plot_department_books()
    plot_author_analytics()
    plot_cleveland_dot_plot()
    plot_loan_status_grouped_stacked()
    plot_duration_distributions()
    plot_statistical_diagnostics()
    plot_vertical_vs_horizontal_layouts()
    plot_proportions_and_treemap()
    plot_associations_and_pca()
    plot_borrowing_pairplot()
    plot_paired_slope_chart()
    plot_time_series_and_trends()
    plot_advanced_time_series()
    plot_monthly_activity_heatmap()
    plot_geospatial_choropleth()
    plot_folium_campus_map()
    plot_proportional_cartogram()
    plot_design_principles_demo()
    plot_interactive_plotly_dashboard()
    print("\n All visualization reports and interactive dashboards generated successfully in /charts and /interactive folders!")

# Backward-compatibility aliases for any existing tests
unit1_bad_vs_good = plot_design_principles_demo
unit2_pairplot = plot_borrowing_pairplot
unit2_violin_plot = plot_duration_distributions
unit2_heatmap = plot_monthly_activity_heatmap
unit2_interactive_plotly = plot_interactive_plotly_dashboard
unit2_grammar_of_graphics = plot_associations_and_pca
unit3_amounts_bar = plot_department_books
unit3_amounts_dot = plot_cleveland_dot_plot
unit3_amounts_grouped_bar = plot_loan_status_grouped_stacked
unit3_amounts_stacked_bar = plot_loan_status_grouped_stacked
unit3_dist_hist_kde = plot_duration_distributions
unit3_dist_overlaid_kde = plot_duration_distributions
unit3_dist_ecdf = plot_statistical_diagnostics
unit3_dist_qq_plot = plot_statistical_diagnostics
unit3_dist_skewed_vs_log = plot_statistical_diagnostics
unit4_vertical_vs_horizontal = plot_vertical_vs_horizontal_layouts
unit4_prop_pie_chart = plot_proportions_and_treemap
unit4_prop_side_by_side_bar = plot_loan_status_grouped_stacked
unit4_prop_stacked_density = plot_duration_distributions
unit4_prop_100pct_stacked_bar = plot_proportions_and_treemap
unit4_prop_treemap = plot_proportions_and_treemap
unit4_assoc_scatter = plot_associations_and_pca
unit4_assoc_correlogram = plot_associations_and_pca
unit4_assoc_pca = plot_associations_and_pca
unit4_assoc_paired_slope = plot_paired_slope_chart
unit5_ts_individual = plot_time_series_and_trends
unit5_ts_multiple = plot_time_series_and_trends
unit5_ts_dose_response = plot_advanced_time_series
unit5_ts_multi_response = plot_advanced_time_series
unit5_trend_smoothing = plot_time_series_and_trends
unit5_trend_functional = plot_time_series_and_trends
unit5_trend_decomposition = plot_advanced_time_series
unit5_geo_choropleth = plot_geospatial_choropleth
unit5_geo_folium_layers = plot_folium_campus_map
unit5_geo_cartogram = plot_proportional_cartogram
