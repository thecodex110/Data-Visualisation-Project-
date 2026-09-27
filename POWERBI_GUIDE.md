# Power BI Integration & Dashboard Build Guide
## Engineering College Library Management System (LMS)

---

### Executive Summary & Architecture Overview
This companion guide details how to integrate the **Engineering College Library Management System (LMS)** data with **Microsoft Power BI** for business intelligence, executive reporting, and institutional analytics. 

The python-based CLI application generates structured data across SQLite database `library.db` and exports formatted multi-sheet Excel workbooks (`library_export.xlsx`).

---

## 1. Power BI Architecture & Components

Power BI ecosystem consists of three main components:

1. **Power BI Desktop**:
   - **Role**: Free Windows application used to ingest, clean, model data (via Power Query), author DAX measures, and design interactive dashboards.
   - **Use Case for LMS**: Primary authoring environment for library administrators and data analysts.
2. **Power BI Service (SaaS)**:
   - **Role**: Cloud-based portal (`app.powerbi.com`) for sharing, collaborating, scheduling automated dataset refreshes, and embedding reports.
   - **Use Case for LMS**: Distributing real-time read-only dashboards to HODs, Deans, and college management.
3. **Power BI On-Premises Data Gateway**:
   - **Role**: Secure bridge connecting on-premises data sources (e.g. SQLite `library.db` on campus servers) to the Power BI Service cloud.
   - **Use Case for LMS**: Enabling daily scheduled auto-refreshes from local SQLite DB without manual export.

> **Recommendation**: For this project, use **Power BI Desktop** for building and modeling, then publish to **Power BI Service** for web-based access.

---

## 2. Data Export & Loading Options

### Option A: Loading via Excel Export (Primary Connection)
1. Run CLI Option `11` in `main.py`: **"Export Data for Power BI"**.
2. This generates `library_export.xlsx` containing four separate worksheets:
   - `departments`
   - `students`
   - `books`
   - `transactions`
3. In **Power BI Desktop**:
   - Click **Get Data** -> **Excel Workbook**.
   - Select `library_export.xlsx`.
   - Check all four tables in the Navigator dialog and click **Transform Data**.

### Option B: Direct Database Connection (SQLite via ODBC)
1. Install **SQLite ODBC Driver** (32-bit or 64-bit matching Power BI Desktop).
2. In Power BI Desktop:
   - Click **Get Data** -> **ODBC**.
   - Connection String: `DRIVER=SQLite3 ODBC Driver;Database=C:\path\to\library.db;`
   - Select tables: `departments`, `students`, `books`, `transactions`.

### Option C: Web API Endpoint (Cloud Native Integration)
If hosting LMS backend on Python FastAPI / Flask:
1. In Power BI Desktop: Click **Get Data** -> **Web**.
2. URL: `https://api.college.edu/lms/transactions`.
3. Power Query automatically parses JSON payload into tabular structure.

---

## 3. Data Transformation in Power Query Editor

Once ingested into Power Query Editor, perform the following data cleaning steps:

### Step 1: Set Explicit Data Types
- `transactions`: Set `issue_date`, `due_date`, `return_date` to **Date** type.
- `transactions[fine_amount]`: Set to **Fixed Decimal Number (Currency - ₹)**.
- `books[total_copies]`, `books[available_copies]`: Set to **Whole Number**.

### Step 2: Handle Null Values & Add Custom Columns
1. **Active Return Date Flag**:
   - Select Column `return_date` -> **Replace Values**: Replace `null` with `null` (leave as null or fill text `"Active Issue"`).
2. **Add Custom Column - Overdue Status**:
   - Click **Add Column** -> **Custom Column**.
   - Name: `Is_Overdue`
   - Formula:
     ```powerquery
     if [return_date] = null and DateTime.Date(DateTime.LocalNow()) > [due_date] then 1
     else if [return_date] <> null and [return_date] > [due_date] then 1
     else 0
     ```

### Step 3: Establish Data Model Relationships
In Power BI **Model View**, configure star schema relationships:
- `departments[dept_id]` 1 : * `students[dept_id]` (Single direction)
- `departments[dept_id]` 1 : * `books[dept_id]` (Single direction)
- `books[book_id]` 1 : * `transactions[book_id]` (Single direction)
- `students[student_id]` 1 : * `transactions[student_id]` (Single direction)

---

## 4. Key Visuals & Dashboard Layout

Build an executive single-page dashboard containing:

| Visual Type | Configuration & Data Fields | Purpose |
| :--- | :--- | :--- |
| **Card Visuals** | `Total Books`, `Active Issues`, `Overdue Books`, `Total Fines (₹)` | Immediate KPI headline figures |
| **KPI Visual** | Indicator: `Monthly Fines Collected`<br>Target: `Prior Month Fines` | Track monthly revenue/fine collection trend |
| **Gauge Visual** | Value: `Occupied Copies`<br>Target: `Total Copies` | Measure overall campus library utilization % |
| **Slicers (Filters)** | 1. Department Name (`departments[dept_name]`)<br>2. Student Year (`students[year]`) | Interactive cross-filtering across entire page |
| **Drill-Down Bar Chart** | Hierarchy Level 1: `dept_name`<br>Hierarchy Level 2: `book_title`<br>Value: `Transaction Count` | Enable HODs to drill down from Dept to specific titles |

---

## 5. DAX (Data Analysis Expressions) Measures

Create a **_Measures** table in Power BI and add the following DAX calculations:

```dax
// 1. Total Fines Collected
Total Fines Collected = 
SUM(transactions[fine_amount])

// 2. Total Books Issued
Total Books Issued = 
COUNTROWS(transactions)

// 3. Overdue Rate %
Overdue Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(transactions), transactions[Is_Overdue] = 1),
    COUNTROWS(transactions),
    0
)

// 4. Library Utilization %
Library Utilization % = 
VAR TotalCopies = SUM(books[total_copies])
VAR AvailableCopies = SUM(books[available_copies])
VAR IssuedCopies = TotalCopies - AvailableCopies
RETURN
DIVIDE(IssuedCopies, TotalCopies, 0)
```

---

## 6. Row-Level Security (RLS) & Portal Embedding

### Row-Level Security (RLS)
To ensure Department Heads (e.g. Computer Science HOD) can only view borrowing statistics for their respective department:
1. In Power BI Desktop: Click **Modeling** -> **Manage Roles**.
2. Create Role: `CS_Department_Staff`.
3. Under `departments` table filter:
   ```dax
   [dept_name] = "Computer Science"
   ```
4. Assign staff email addresses to roles in **Power BI Service** under Dataset Security.

### Power BI Embedded (College Portal Integration)
To embed this dashboard directly into the college intranet portal (e.g. `portal.college.edu/library`):
1. In Power BI Service: Go to **File** -> **Embed Report** -> **Website or Portal** (or **Power BI Embedded** for custom React/Vue applications).
2. Copy iframe string:
   ```html
   <iframe width="1140" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=YOUR_REPORT_ID&autoAuth=true" frameborder="0" allowFullScreen="true"></iframe>
   ```
3. Users authenticate via Microsoft Entra ID (Azure AD) single sign-on (SSO).

---
*Guide generated for Engineering College Library Management System (DV Mini Project).*
