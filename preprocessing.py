import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

DB_NAME = "library.db"

def get_connection(db_path=DB_NAME):
    return sqlite3.connect(db_path)

def load_raw_data(db_path=DB_NAME):
    """Loads raw dataframes from sqlite database."""
    conn = get_connection(db_path)
    
    depts_df = pd.read_sql_query("SELECT * FROM departments;", conn)
    students_df = pd.read_sql_query("SELECT * FROM students;", conn)
    books_df = pd.read_sql_query("SELECT * FROM books;", conn)
    txns_df = pd.read_sql_query("SELECT * FROM transactions;", conn)
    
    conn.close()
    return depts_df, students_df, books_df, txns_df

def get_cleaned_transactions(db_path=DB_NAME):
    """
    Cleans raw transaction data, calculates durations, handles missing return dates,
    and enriches with student and book details.
    """
    conn = get_connection(db_path)
    
    query = """
    SELECT 
        t.txn_id,
        t.book_id,
        b.title AS book_title,
        b.author AS book_author,
        b.total_copies,
        b.available_copies,
        b.publisher_state,
        t.student_id,
        s.name AS student_name,
        s.year AS student_year,
        s.home_state AS student_home_state,
        d.dept_id,
        d.dept_name,
        t.issue_date,
        t.due_date,
        t.return_date,
        t.fine_amount
    FROM transactions t
    JOIN books b ON t.book_id = b.book_id
    JOIN students s ON t.student_id = s.student_id
    JOIN departments d ON b.dept_id = d.dept_id;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    today = pd.Timestamp(datetime.now().date())
    
    # Convert dates
    df['issue_date_dt'] = pd.to_datetime(df['issue_date'])
    df['due_date_dt'] = pd.to_datetime(df['due_date'])
    df['return_date_dt'] = pd.to_datetime(df['return_date'])
    
    # Issue Month string (YYYY-MM)
    df['issue_month'] = df['issue_date_dt'].dt.to_period('M').astype(str)
    
    # Calculate days kept and overdue days
    is_returned = df['return_date_dt'].notnull()
    
    # Days kept
    df['days_kept'] = np.where(
        is_returned,
        (df['return_date_dt'] - df['issue_date_dt']).dt.days,
        (today - df['issue_date_dt']).dt.days
    )
    df['days_kept'] = df['days_kept'].clip(lower=1) # at least 1 day
    
    # Overdue days
    df['overdue_days'] = np.where(
        is_returned,
        (df['return_date_dt'] - df['due_date_dt']).dt.days,
        (today - df['due_date_dt']).dt.days
    )
    df['overdue_days'] = df['overdue_days'].clip(lower=0)
    
    # Recalculate fine amount accurately
    df['calculated_fine'] = df['overdue_days'] * 5.0
    # Use max of recorded fine or calculated fine
    df['effective_fine'] = np.maximum(df['fine_amount'], df['calculated_fine'])
    
    # Status categorisation
    conditions = [
        (~is_returned) & (df['overdue_days'] > 0),
        (~is_returned) & (df['overdue_days'] == 0),
        (is_returned) & (df['overdue_days'] > 0),
        (is_returned) & (df['overdue_days'] == 0)
    ]
    choices = ['Active Overdue', 'Active On-Time', 'Returned Overdue', 'Returned On-Time']
    df['status'] = np.select(conditions, choices, default='Unknown')
    
    # Simplified Status for high-level charts (Issued, Returned, Overdue)
    df['simple_status'] = np.where(
        df['status'].str.contains('Overdue'), 'Overdue',
        np.where(df['status'].str.contains('Returned'), 'Returned', 'Active Issued')
    )
    
    # Display friendly return date string
    df['return_date_display'] = df['return_date'].fillna('Active Issue')
    
    return df

def get_department_aggregates(db_path=DB_NAME):
    """Aggregates book count, total copies, active issues, and fines by Department."""
    txns = get_cleaned_transactions(db_path)
    depts, students, books, _ = load_raw_data(db_path)
    
    # Books per department
    books_per_dept = books.groupby('dept_id').agg(
        total_unique_titles=('book_id', 'count'),
        total_copies=('total_copies', 'sum'),
        available_copies=('available_copies', 'sum')
    ).reset_index()
    
    books_per_dept = pd.merge(depts, books_per_dept, on='dept_id', how='left').fillna(0)
    
    # Transaction counts per department
    txn_counts = txns.groupby(['dept_name', 'simple_status']).size().unstack(fill_value=0).reset_index()
    for col in ['Active Issued', 'Returned', 'Overdue']:
        if col not in txn_counts.columns:
            txn_counts[col] = 0
            
    txn_counts['total_transactions'] = txn_counts['Active Issued'] + txn_counts['Returned'] + txn_counts['Overdue']
    
    summary = pd.merge(books_per_dept, txn_counts, left_on='dept_name', right_on='dept_name', how='left').fillna(0)
    return summary

def get_author_aggregates(db_path=DB_NAME):
    """Aggregates book count, total copies, and borrow volume by Author."""
    _, _, books, _ = load_raw_data(db_path)
    txns = get_cleaned_transactions(db_path)
    
    author_books = books.groupby('author').agg(
        book_titles=('book_id', 'count'),
        total_copies=('total_copies', 'sum')
    ).reset_index()
    
    author_txns = txns.groupby('book_author').agg(
        total_borrowed=('txn_id', 'count')
    ).reset_index().rename(columns={'book_author': 'author'})
    
    author_summary = pd.merge(author_books, author_txns, on='author', how='left').fillna(0)
    author_summary['total_borrowed'] = author_summary['total_borrowed'].astype(int)
    return author_summary.sort_values('total_borrowed', ascending=False)

def get_monthly_matrix(db_path=DB_NAME):
    """Pivots transactions into Department x Month issue counts."""
    txns = get_cleaned_transactions(db_path)
    pivot = txns.pivot_table(
        index='dept_name',
        columns='issue_month',
        values='txn_id',
        aggfunc='count',
        fill_value=0
    )
    # Sort months chronologically
    sorted_cols = sorted(pivot.columns)
    return pivot[sorted_cols]

def get_monthly_timeseries(db_path=DB_NAME):
    """Aggregates monthly issue count, return count, and total fines for time series analysis."""
    txns = get_cleaned_transactions(db_path)
    
    monthly = txns.groupby('issue_month').agg(
        issued_count=('txn_id', 'count'),
        returned_count=('return_date_dt', lambda x: x.notnull().sum()),
        overdue_count=('overdue_days', lambda x: (x > 0).sum()),
        total_fines=('effective_fine', 'sum')
    ).reset_index()
    
    monthly['issue_month_dt'] = pd.to_datetime(monthly['issue_month'] + '-01')
    monthly = monthly.sort_values('issue_month_dt').reset_index(drop=True)
    
    # Rolling 3-month average
    monthly['rolling_3m_issues'] = monthly['issued_count'].rolling(window=3, min_periods=1).mean()
    
    return monthly

def get_student_feature_matrix(db_path=DB_NAME):
    """
    Creates a student-level feature matrix showing count of books borrowed per department,
    used for PCA dimension reduction clustering.
    """
    txns = get_cleaned_transactions(db_path)
    students_df = load_raw_data(db_path)[1]
    
    pivot = txns.pivot_table(
        index='student_id',
        columns='dept_name',
        values='txn_id',
        aggfunc='count',
        fill_value=0
    )
    
    # Merge back student metadata
    student_matrix = pd.merge(students_df[['student_id', 'name', 'dept_id', 'home_state']], pivot, on='student_id', how='left').fillna(0)
    depts_map = dict(load_raw_data(db_path)[0][['dept_id', 'dept_name']].values)
    student_matrix['primary_dept'] = student_matrix['dept_id'].map(depts_map)
    
    return student_matrix

def get_state_geospatial_summary(db_path=DB_NAME):
    """Aggregates student count and borrowing volume by Indian home state."""
    txns = get_cleaned_transactions(db_path)
    students_df = load_raw_data(db_path)[1]
    
    student_counts = students_df.groupby('home_state').agg(
        student_count=('student_id', 'count')
    ).reset_index()
    
    txn_counts = txns.groupby('student_home_state').agg(
        total_issues=('txn_id', 'count'),
        total_fines=('effective_fine', 'sum')
    ).reset_index().rename(columns={'student_home_state': 'home_state'})
    
    geo_summary = pd.merge(student_counts, txn_counts, on='home_state', how='left').fillna(0)
    return geo_summary

if __name__ == "__main__":
    print("Testing Preprocessing Module...")
    df = get_cleaned_transactions()
    print(f"Cleaned Transactions shape: {df.shape}")
    print(df[['txn_id', 'student_name', 'book_title', 'days_kept', 'overdue_days', 'effective_fine', 'status']].head())
    print("\nDepartment Aggregate:")
    print(get_department_aggregates())
