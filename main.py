import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

import db_setup
import preprocessing
import visualizations

DB_NAME = "library.db"

def check_db():
    if not os.path.exists(DB_NAME):
        print("\n [Setup] Initializing SQLite database 'library.db' with synthetic engineering library data...")
        db_setup.init_db()
        db_setup.seed_db()
        print(" [Setup] Database ready!\n")

def get_conn():
    return sqlite3.connect(DB_NAME)

# ==============================================================================
# CORE LMS OPERATIONS (ADD, MINUS/REMOVE, SEARCH, ISSUE, RETURN, OVERDUE)
# ==============================================================================

def view_books():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, d.dept_name, b.total_copies, b.available_copies, b.publisher_state
        FROM books b
        JOIN departments d ON b.dept_id = d.dept_id
        ORDER BY d.dept_name, b.title;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*88)
    print("                              LIBRARY BOOK CATALOG")
    print("="*88)
    print(f"{'ID':<4} | {'Title':<33} | {'Author':<20} | {'Dept':<12} | {'Avail/Total':<11} | {'Pub State'}")
    print("-"*88)
    for r in rows:
        avail_str = f"{r[5]}/{r[4]}"
        print(f"{r[0]:<4} | {r[1][:33]:<33} | {r[2][:20]:<20} | {r[3]:<12} | {avail_str:<11} | {r[6]}")
    print("="*88 + "\n")

def add_book():
    print("\n" + "-"*40)
    print("          ADD NEW BOOK (+)")
    print("-"*40)
    title = input("Enter Title: ").strip()
    author = input("Enter Author: ").strip()
    if not title or not author:
        print(" [!] Title and Author cannot be empty.")
        return
        
    conn = get_conn()
    depts = pd.read_sql_query("SELECT * FROM departments;", conn)
    print("\nSelect Academic Department:")
    for _, d in depts.iterrows():
        print(f"  {d['dept_id']}. {d['dept_name']}")
        
    try:
        dept_id = int(input("\nSelect Department ID: "))
        total_copies = int(input("Enter Total Copies: "))
        if total_copies <= 0:
            print(" [!] Copies must be at least 1.")
            conn.close()
            return
            
        pub_state = input("Enter Publisher State (e.g., Maharashtra, Delhi): ").strip()
        if not pub_state:
            pub_state = "Maharashtra"
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, dept_id, total_copies, available_copies, publisher_state)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (title, author, dept_id, total_copies, total_copies, pub_state))
        conn.commit()
        print(f"\n [✓] Success: Added '{title}' by {author} ({total_copies} copies).")
    except Exception as e:
        print(f" [!] Error adding book: {e}")
    finally:
        conn.close()

def remove_book():
    """Allows decreasing copies or completely removing a book from library inventory."""
    print("\n" + "-"*40)
    print("       REMOVE / MINUS BOOK (-)")
    print("-"*40)
    try:
        book_id = int(input("Enter Book ID to remove: "))
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, author, total_copies, available_copies 
            FROM books WHERE book_id = ?;
        """, (book_id,))
        row = cursor.fetchone()
        
        if not row:
            print(" [!] Error: Book ID not found in library.")
            conn.close()
            return
            
        title, author, total, avail = row
        active_loans = total - avail
        print(f"\nFound: '{title}' by {author}")
        print(f"Total Copies: {total} | Available on Shelf: {avail} | Currently Loaned: {active_loans}")
        
        print("\nChoose Action:")
        print(" 1. Decrease copy count by a specific quantity")
        print(" 2. Completely delete this book record from system")
        action = input("Select (1/2): ").strip()
        
        if action == '1':
            minus_count = int(input(f"Enter quantity to deduct (1 - {avail}): "))
            if minus_count <= 0 or minus_count > avail:
                print(f" [!] Invalid quantity. You can only reduce up to {avail} unloaned copies.")
            else:
                new_total = total - minus_count
                new_avail = avail - minus_count
                cursor.execute("""
                    UPDATE books SET total_copies = ?, available_copies = ? WHERE book_id = ?;
                """, (new_total, new_avail, book_id))
                conn.commit()
                print(f"\n [✓] Updated: '{title}' copies reduced by {minus_count}. New Total: {new_total}.")
        elif action == '2':
            if active_loans > 0:
                print(f" [!] Cannot delete completely: {active_loans} copies are currently on loan by students.")
                print("     Please return all active loans before deleting.")
            else:
                confirm = input(f"Are you sure you want to permanently delete '{title}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    cursor.execute("DELETE FROM transactions WHERE book_id = ?;", (book_id,))
                    cursor.execute("DELETE FROM books WHERE book_id = ?;", (book_id,))
                    conn.commit()
                    print(f"\n [✓] Successfully deleted '{title}' from catalog.")
                else:
                    print(" Operation cancelled.")
        conn.close()
    except Exception as e:
        print(f" [!] Error removing book: {e}")

def search_books():
    query_str = input("\nEnter search title / author / department keyword: ").strip()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, d.dept_name, b.available_copies, b.total_copies, b.publisher_state
        FROM books b
        JOIN departments d ON b.dept_id = d.dept_id
        WHERE b.title LIKE ? OR b.author LIKE ? OR d.dept_name LIKE ?;
    """, (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(" [!] No matching books found.")
        return
        
    print(f"\nFound {len(rows)} matching book(s):")
    print("-" * 80)
    for r in rows:
        print(f" [ID {r[0]}] '{r[1]}' by {r[2]} ({r[3]}) | Shelf: {r[4]}/{r[5]} | State: {r[6]}")
    print("-" * 80)

def view_students():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.student_id, s.name, d.dept_name, s.year, s.home_state
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        ORDER BY s.student_id;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*75)
    print("                             STUDENT DIRECTORY")
    print("="*75)
    print(f"{'ID':<5} | {'Student Name':<25} | {'Department':<16} | {'Year':<7} | {'Home State'}")
    print("-"*75)
    for r in rows:
        print(f"{r[0]:<5} | {r[1]:<25} | {r[2]:<16} | Year {r[3]:<2} | {r[4]}")
    print("="*75 + "\n")

def add_student():
    print("\n" + "-"*40)
    print("          ADD NEW STUDENT")
    print("-"*40)
    name = input("Enter Student Full Name: ").strip()
    if not name:
        print(" [!] Name cannot be empty.")
        return
        
    conn = get_conn()
    depts = pd.read_sql_query("SELECT * FROM departments;", conn)
    print("\nSelect Academic Department:")
    for _, d in depts.iterrows():
        print(f"  {d['dept_id']}. {d['dept_name']}")
        
    try:
        dept_id = int(input("\nSelect Department ID: "))
        year = int(input("Enter Academic Year (1-4): "))
        home_state = input("Enter Home State (e.g. Maharashtra, Karnataka): ").strip()
        if not home_state:
            home_state = "Maharashtra"
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (name, dept_id, year, home_state)
            VALUES (?, ?, ?, ?);
        """, (name, dept_id, year, home_state))
        conn.commit()
        print(f"\n [✓] Successfully registered student '{name}'.")
    except Exception as e:
        print(f" [!] Error adding student: {e}")
    finally:
        conn.close()

def issue_book():
    print("\n" + "-"*40)
    print("          ISSUE A BOOK")
    print("-"*40)
    try:
        student_id = int(input("Enter Student ID: "))
        book_id = int(input("Enter Book ID to issue: "))
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM students WHERE student_id = ?;", (student_id,))
        s_row = cursor.fetchone()
        if not s_row:
            print(" [!] Error: Student ID not found.")
            conn.close()
            return
            
        cursor.execute("SELECT title, available_copies FROM books WHERE book_id = ?;", (book_id,))
        b_row = cursor.fetchone()
        if not b_row:
            print(" [!] Error: Book ID not found.")
            conn.close()
            return
            
        if b_row[1] <= 0:
            print(f" [!] Unavailable: '{b_row[0]}' currently has 0 available copies on the shelf.")
            conn.close()
            return
            
        issue_dt = datetime.now()
        due_dt = issue_dt + timedelta(days=14)
        
        issue_str = issue_dt.strftime("%Y-%m-%d")
        due_str = due_dt.strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO transactions (book_id, student_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, NULL, 0.0);
        """, (book_id, student_id, issue_str, due_str))
        
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?;", (book_id,))
        conn.commit()
        conn.close()
        
        print(f"\n [✓] Issued '{b_row[0]}' to {s_row[0]}.")
        print(f"     Loan Period: 14 Days | Due Date: {due_str}")
    except Exception as e:
        print(f" [!] Error issuing book: {e}")

def return_book():
    print("\n" + "-"*40)
    print("      RETURN BOOK & CALCULATE FINE")
    print("-"*40)
    try:
        txn_id = int(input("Enter Transaction ID to return: "))
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.book_id, b.title, t.due_date, t.return_date, s.name
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN students s ON t.student_id = s.student_id
            WHERE t.txn_id = ?;
        """, (txn_id,))
        row = cursor.fetchone()
        
        if not row:
            print(" [!] Error: Transaction ID not found.")
            conn.close()
            return
            
        if row[3] is not None:
            print(f" [i] Notice: Book was already returned previously on {row[3]}.")
            conn.close()
            return
            
        book_id, title, due_str, _, student_name = row
        return_dt = datetime.now()
        due_dt = datetime.strptime(due_str, "%Y-%m-%d")
        return_str = return_dt.strftime("%Y-%m-%d")
        
        overdue_days = max(0, (return_dt.date() - due_dt.date()).days)
        fine_amount = float(overdue_days * 5.0)  # ₹5 / day overdue fine
        
        cursor.execute("""
            UPDATE transactions
            SET return_date = ?, fine_amount = ?
            WHERE txn_id = ?;
        """, (return_str, fine_amount, txn_id))
        
        cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?;", (book_id,))
        conn.commit()
        conn.close()
        
        print(f"\n [✓] Successfully processed return for '{title}' (Borrower: {student_name}).")
        if fine_amount > 0:
            print(f" [!] OVERDUE NOTICE: {overdue_days} days late. Fine Due: ₹{fine_amount:.2f} (@ ₹5/day).")
        else:
            print(" [✓] Returned on-time. Fine Due: ₹0.00.")
    except Exception as e:
        print(f" [!] Error returning book: {e}")

def view_overdue_books():
    print("\n" + "="*88)
    print("                           CURRENTLY OVERDUE LOANS")
    print("="*88)
    df = preprocessing.get_cleaned_transactions()
    overdue_df = df[df['status'].str.contains('Overdue')]
    
    if overdue_df.empty:
        print(" No overdue books at present.")
        return
        
    print(f"{'Txn ID':<7} | {'Student Name':<20} | {'Book Title':<28} | {'Due Date':<10} | {'Days Late':<9} | {'Fine (₹)'}")
    print("-"*88)
    for _, r in overdue_df.iterrows():
        print(f"{r['txn_id']:<7} | {r['student_name'][:20]:<20} | {r['book_title'][:28]:<28} | {r['due_date']:<10} | {r['overdue_days']:<9} | ₹{r['effective_fine']:.2f}")
    print("="*88 + "\n")

def student_history():
    try:
        s_id = int(input("\nEnter Student ID: "))
        df = preprocessing.get_cleaned_transactions()
        s_txns = df[df['student_id'] == s_id]
        
        if s_txns.empty:
            print(" [!] No transaction history found for this student.")
            return
            
        print(f"\nBorrowing History: Student {s_id} - {s_txns['student_name'].iloc[0]} ({s_txns['dept_name'].iloc[0]}):")
        print("="*85)
        print(f"{'Txn ID':<7} | {'Book Title':<30} | {'Issue Date':<10} | {'Due Date':<10} | {'Return Date':<12} | {'Fine (₹)'}")
        print("-"*85)
        for _, r in s_txns.iterrows():
            print(f"{r['txn_id']:<7} | {r['book_title'][:30]:<30} | {r['issue_date']:<10} | {r['due_date']:<10} | {r['return_date_display']:<12} | ₹{r['effective_fine']:.2f}")
        print("="*85 + "\n")
    except Exception as e:
        print(f" [!] Error fetching history: {e}")

def export_for_power_bi():
    """Exports database tables into library_export.xlsx for Power BI modeling."""
    print("\n" + "-"*40)
    print("      EXPORTING DATA FOR POWER BI")
    print("-"*40)
    try:
        conn = get_conn()
        excel_path = "library_export.xlsx"
        
        depts = pd.read_sql_query("SELECT * FROM departments;", conn)
        students = pd.read_sql_query("SELECT * FROM students;", conn)
        books = pd.read_sql_query("SELECT * FROM books;", conn)
        transactions = pd.read_sql_query("SELECT * FROM transactions;", conn)
        conn.close()
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            depts.to_excel(writer, sheet_name='departments', index=False)
            students.to_excel(writer, sheet_name='students', index=False)
            books.to_excel(writer, sheet_name='books', index=False)
            transactions.to_excel(writer, sheet_name='transactions', index=False)
            
        print(f" [✓] SUCCESS: Dataset exported to '{excel_path}' with 4 tables:")
        print("     - departments, students, books, transactions")
        print(" [i] Open POWERBI_GUIDE.md for step-by-step instructions on building the Power BI dashboard.")
    except Exception as e:
        print(f" [!] Error exporting to Excel: {e}")

# ==============================================================================
# DATA VISUALIZATION DASHBOARD SUBMENU (CLEAN, LOGICAL, DOMAIN-DRIVEN)
# ==============================================================================

def visualization_menu():
    while True:
        print("\n" + "="*68)
        print("              LIBRARY DATA VISUALIZATION DASHBOARD")
        print("="*68)
        print("  1.  Collection by Department (CS, Mech, Civil, AIML, etc.)")
        print("  2.  Author Distribution & Most Borrowed Authors")
        print("  3.  Cleveland Dot Plot (High Data-Ink Book Inventory)")
        print("  4.  Loan Status Breakdown (Grouped & Stacked Bar Charts)")
        print("  5.  Loan Duration Spread (Histogram, KDE, Violin Plot)")
        print("  6.  Statistical Diagnostics (ECDF, Normal Q-Q, Log Transform)")
        print("  7.  Axis Orientation Comparison (Ridgeline vs Boxplots)")
        print("  8.  Proportions & Treemap (Pie Chart, 100% Stacked, Treemap)")
        print("  9.  Associations & PCA (Scatter+Regression, Heatmap, PCA 2D)")
        print(" 10.  Pairplot Matrix across Library Metrics")
        print(" 11.  Paired Slope Chart (Due Date vs Actual Return Deviation)")
        print(" 12.  Borrowing Time Series & Trends (Monthly Lines, Smoothing)")
        print(" 13.  Advanced Time Series (Dose-Response Curve & Decomposition)")
        print(" 14.  Monthly Borrowing Intensity Heatmap")
        print(" 15.  Geospatial Demographics: Interactive Indian States Choropleth")
        print(" 16.  Geospatial Layers: Campus Reading Rooms & Student Origins Map")
        print(" 17.  Cartogram: Proportional State Symbol Map")
        print(" 18.  Design Principles Demo: Poor 3D Clutter vs Clean Bar Chart")
        print(" 19.  Open Interactive Plotly Dashboard in Browser")
        print(" 20.  ⚡ Generate All Visual Analytics (Batch Render)")
        print("  0.  ↩ Back to Main Menu")
        print("="*68)
        
        choice = input("Select Visualization Option (0-20): ").strip()
        
        if choice == '1':
            visualizations.plot_department_books()
        elif choice == '2':
            visualizations.plot_author_analytics()
        elif choice == '3':
            visualizations.plot_cleveland_dot_plot()
        elif choice == '4':
            visualizations.plot_loan_status_grouped_stacked()
        elif choice == '5':
            visualizations.plot_duration_distributions()
        elif choice == '6':
            visualizations.plot_statistical_diagnostics()
        elif choice == '7':
            visualizations.plot_vertical_vs_horizontal_layouts()
        elif choice == '8':
            visualizations.plot_proportions_and_treemap()
        elif choice == '9':
            visualizations.plot_associations_and_pca()
        elif choice == '10':
            visualizations.plot_borrowing_pairplot()
        elif choice == '11':
            visualizations.plot_paired_slope_chart()
        elif choice == '12':
            visualizations.plot_time_series_and_trends()
        elif choice == '13':
            visualizations.plot_advanced_time_series()
        elif choice == '14':
            visualizations.plot_monthly_activity_heatmap()
        elif choice == '15':
            visualizations.plot_geospatial_choropleth()
        elif choice == '16':
            visualizations.plot_folium_campus_map()
        elif choice == '17':
            visualizations.plot_proportional_cartogram()
        elif choice == '18':
            visualizations.plot_design_principles_demo()
        elif choice == '19':
            visualizations.plot_interactive_plotly_dashboard()
        elif choice == '20':
            visualizations.generate_all_visualizations()
        elif choice == '0':
            break
        else:
            print(" [!] Invalid option. Please enter a number between 0 and 20.")

# ==============================================================================
# MAIN APPLICATION MENU
# ==============================================================================

def main_menu():
    check_db()
    
    while True:
        print("\n" + "="*66)
        print("   ENGINEERING COLLEGE LIBRARY MANAGEMENT SYSTEM (LMS)")
        print("           DATA VISUALIZATION & ANALYTICS PLATFORM")
        print("="*66)
        print("  1. 📚 View Library Catalog")
        print("  2. ➕ Add New Book")
        print("  3. ➖ Remove / Minus Book (Reduce copies or delete)")
        print("  4. 🔍 Search Books by Title / Author / Department")
        print("  5. 👥 View Student Directory")
        print("  6. ➕ Add New Student")
        print("  7. 📖 Issue a Book (Auto 14-day due date)")
        print("  8. 📥 Return a Book (Auto ₹5/day fine calculation)")
        print("  9. ⚠️ View Overdue Loans")
        print(" 10. 📜 Student Borrowing History")
        print(" 11. 📊 Open Data Visualization Dashboard (Interactive Menu)")
        print(" 12. ⚡ Generate All Visual Analytics (One-Click Render)")
        print(" 13. 📑 Export Dataset for Power BI (library_export.xlsx)")
        print("  0. ❌ Exit")
        print("="*66)
        
        choice = input("Enter choice (0-13): ").strip()
        
        if choice == '1':
            view_books()
        elif choice == '2':
            add_book()
        elif choice == '3':
            remove_book()
        elif choice == '4':
            search_books()
        elif choice == '5':
            view_students()
        elif choice == '6':
            add_student()
        elif choice == '7':
            issue_book()
        elif choice == '8':
            return_book()
        elif choice == '9':
            view_overdue_books()
        elif choice == '10':
            student_history()
        elif choice == '11':
            visualization_menu()
        elif choice == '12':
            visualizations.generate_all_visualizations()
        elif choice == '13':
            export_for_power_bi()
        elif choice == '0':
            print("\n [✓] Thank you for using Engineering College Library Management System. Goodbye!\n")
            sys.exit(0)
        else:
            print(" [!] Invalid selection. Please enter a valid menu number (0-13).")

if __name__ == "__main__":
    main_menu()
