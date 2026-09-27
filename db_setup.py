import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

DB_NAME = "library.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Drop existing tables to ensure clean seed
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute("DROP TABLE IF EXISTS books;")
    cursor.execute("DROP TABLE IF EXISTS students;")
    cursor.execute("DROP TABLE IF EXISTS departments;")
    
    # Create tables
    cursor.execute("""
    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL UNIQUE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        home_state TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL,
        publisher_state TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        fine_amount REAL DEFAULT 0.0,
        FOREIGN KEY (book_id) REFERENCES books(book_id),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)
    
    conn.commit()
    conn.close()

def seed_db():
    fake = Faker('en_IN')
    Faker.seed(42)
    random.seed(42)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Seed Departments
    departments = [
        "Computer Science",
        "Mechanical",
        "Civil",
        "AIML",
        "Electronics",
        "E&TC"
    ]
    for dept in departments:
        cursor.execute("INSERT INTO departments (dept_name) VALUES (?);", (dept,))
    
    conn.commit()
    
    # Fetch department IDs mapping
    cursor.execute("SELECT dept_name, dept_id FROM departments;")
    dept_map = dict(cursor.fetchall())
    dept_ids = list(dept_map.values())
    
    # 2. Seed Students (90 students)
    indian_states = [
        "Maharashtra", "Karnataka", "Gujarat", "Delhi", "Tamil Nadu",
        "Uttar Pradesh", "Rajasthan", "Kerala", "West Bengal", "Telangana"
    ]
    
    students_data = []
    for _ in range(90):
        name = fake.name()
        dept_id = random.choice(dept_ids)
        year = random.randint(1, 4)
        home_state = random.choice(indian_states)
        students_data.append((name, dept_id, year, home_state))
        
    cursor.executemany("""
    INSERT INTO students (name, dept_id, year, home_state)
    VALUES (?, ?, ?, ?);
    """, students_data)
    
    # 3. Seed Books (54 realistic books, 9 per department)
    book_titles_by_dept = {
        "Computer Science": [
            ("Introduction to Algorithms", "Thomas H. Cormen"),
            ("Clean Code", "Robert C. Martin"),
            ("Operating System Concepts", "Abraham Silberschatz"),
            ("Computer Networks", "Andrew S. Tanenbaum"),
            ("Database System Concepts", "Henry F. Korth"),
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell"),
            ("Design Patterns", "Erich Gamma"),
            ("Compilers: Principles, Techniques, and Tools", "Alfred V. Aho"),
            ("Computer Organization and Design", "David A. Patterson")
        ],
        "Mechanical": [
            ("Thermodynamics: An Engineering Approach", "Yunus A. Cengel"),
            ("Fluid Mechanics", "Frank M. White"),
            ("Theory of Machines", "S. S. Rattan"),
            ("Strength of Materials", "R. K. Bansal"),
            ("Heat and Mass Transfer", "P. K. Nag"),
            ("Manufacturing Engineering and Technology", "Serope Kalpakjian"),
            ("Design of Machine Elements", "V. B. Bhandari"),
            ("Engineering Mechanics: Statics and Dynamics", "R. C. Hibbeler"),
            ("Internal Combustion Engines", "V. Ganesan")
        ],
        "Civil": [
            ("Basic and Applied Soil Mechanics", "Gopal Ranjan"),
            ("Design of Reinforced Concrete Structures", "N. Krishna Raju"),
            ("Surveying Vol. 1", "B. C. Punmia"),
            ("Structural Analysis", "R. C. Hibbeler"),
            ("Environmental Engineering", "S. K. Garg"),
            ("Transportation Engineering", "C. Justo & A. Veeraragavan"),
            ("Fluid Mechanics & Hydraulic Machines", "R. K. Rajput"),
            ("Building Construction", "S. C. Rangwala"),
            ("Engineering Geology", "Parbin Singh")
        ],
        "AIML": [
            ("Pattern Recognition and Machine Learning", "Christopher M. Bishop"),
            ("Deep Learning", "Ian Goodfellow"),
            ("Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", "Aurélien Géron"),
            ("Python for Data Analysis", "Wes McKinney"),
            ("Reinforcement Learning: An Introduction", "Richard S. Sutton"),
            ("Data Mining: Concepts and Techniques", "Jiawei Han"),
            ("Speech and Language Processing", "Daniel Jurafsky"),
            ("Computer Vision: Algorithms and Applications", "Richard Szeliski"),
            ("Mathematics for Machine Learning", "Marc Peter Deisenroth")
        ],
        "Electronics": [
            ("Microelectronic Circuits", "Adel S. Sedra"),
            ("Electronic Devices and Circuit Theory", "Robert L. Boylestad"),
            ("Op-Amps and Linear Integrated Circuits", "Ramakant A. Gayakwad"),
            ("Digital Design", "M. Morris Mano"),
            ("Power Electronics", "M. H. Rashid"),
            ("VLSI Design", "Debaprasad Das"),
            ("Embedded Systems Architecture", "Tammy Noergaard"),
            ("Control Systems Engineering", "I. J. Nagrath & M. Gopal"),
            ("Fundamentals of Electric Circuits", "Charles K. Alexander")
        ],
        "E&TC": [
            ("Signals and Systems", "Alan V. Oppenheim"),
            ("Modern Digital and Analog Communication Systems", "B. P. Lathi"),
            ("Optical Fiber Communications", "Gerd Keiser"),
            ("Antennas and Wave Propagation", "John D. Kraus"),
            ("Wireless Communications", "Theodore S. Rappaport"),
            ("Digital Signal Processing", "John G. Proakis"),
            ("Electromagnetic Waves and Radiating Systems", "E. C. Jordan"),
            ("Satellite Communications", "Timothy Pratt"),
            ("Microprocessors and Interfacing", "Douglas V. Hall")
        ]
    }
    
    publisher_states = [
        "Maharashtra", "Delhi", "Tamil Nadu", "Karnataka", "West Bengal", "Gujarat"
    ]
    
    books_data = []
    for dept_name, books_list in book_titles_by_dept.items():
        d_id = dept_map[dept_name]
        for title, author in books_list:
            total_copies = random.randint(4, 10)
            available_copies = total_copies  # will adjust after seeding transactions
            pub_state = random.choice(publisher_states)
            books_data.append((title, author, d_id, total_copies, available_copies, pub_state))
            
    cursor.executemany("""
    INSERT INTO books (title, author, dept_id, total_copies, available_copies, publisher_state)
    VALUES (?, ?, ?, ?, ?, ?);
    """, books_data)
    
    conn.commit()
    
    # 4. Seed Transactions (280 transactions over the past 365 days)
    cursor.execute("SELECT book_id FROM books;")
    book_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT student_id FROM students;")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    today = datetime.now()
    transactions_data = []
    
    # We will keep track of currently active issues to update available_copies accurately
    active_issues_per_book = {b_id: 0 for b_id in book_ids}
    
    for _ in range(280):
        b_id = random.choice(book_ids)
        s_id = random.choice(student_ids)
        
        # Issue date between 365 days ago and 2 days ago
        days_ago = random.randint(2, 365)
        issue_date_dt = today - timedelta(days=days_ago)
        issue_date_str = issue_date_dt.strftime("%Y-%m-%d")
        
        due_date_dt = issue_date_dt + timedelta(days=14)
        due_date_str = due_date_dt.strftime("%Y-%m-%d")
        
        # Status outcome:
        # 70% Returned on-time or early
        # 20% Returned late (overdue fine)
        # 10% Active issue (not returned yet)
        status_rand = random.random()
        
        if status_rand < 0.70:
            # Returned on or before due date
            kept_days = random.randint(1, 14)
            ret_dt = issue_date_dt + timedelta(days=kept_days)
            # Ensure return date is not in future
            if ret_dt > today:
                ret_dt = today
            ret_date_str = ret_dt.strftime("%Y-%m-%d")
            fine = 0.0
        elif status_rand < 0.90:
            # Returned late (overdue)
            kept_days = random.randint(15, 45)
            ret_dt = issue_date_dt + timedelta(days=kept_days)
            if ret_dt > today:
                ret_dt = today
            ret_date_str = ret_dt.strftime("%Y-%m-%d")
            overdue_days = max(0, (ret_dt - due_date_dt).days)
            fine = float(overdue_days * 5.0)  # ₹5 per overdue day
        else:
            # Currently active issue (not returned yet)
            # Only if issue date was not too far in past, or simulates an unreturned book
            ret_date_str = None
            fine = 0.0
            active_issues_per_book[b_id] += 1
            
        transactions_data.append((b_id, s_id, issue_date_str, due_date_str, ret_date_str, fine))
        
    cursor.executemany("""
    INSERT INTO transactions (book_id, student_id, issue_date, due_date, return_date, fine_amount)
    VALUES (?, ?, ?, ?, ?, ?);
    """, transactions_data)
    
    # Update available_copies for books based on active issues
    for b_id, active_cnt in active_issues_per_book.items():
        cursor.execute("UPDATE books SET available_copies = MAX(0, total_copies - ?) WHERE book_id = ?;", (active_cnt, b_id))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Initializing database schema...")
    init_db()
    print("Seeding synthetic data...")
    seed_db()
    print("Database setup complete! 'library.db' created successfully.")
