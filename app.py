import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# Initialize or connect to our production schema
conn = sqlite3.connect('shop_plaza.db', check_same_thread=False)
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_code TEXT UNIQUE,
    account_name TEXT,
    account_type TEXT
);
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    product_name TEXT,
    category TEXT,
    unit_cost REAL,
    retail_price REAL,
    stock_quantity INTEGER
);
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT,
    description TEXT,
    reference TEXT
);
CREATE TABLE IF NOT EXISTS journal_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER REFERENCES journal_entries(entry_id),
    account_id INTEGER REFERENCES accounts(account_id),
    debit REAL DEFAULT 0,
    credit REAL DEFAULT 0
);
""")

# Seed core system accounts if missing
cursor.execute("SELECT COUNT(*) FROM accounts")
if cursor.fetchone()[0] == 0:
    accounts_seed = [
        ('1000', 'Cash & Bank', 'Asset'),
        ('1200', 'Inventory Asset', 'Asset'),
        ('4000', 'Retail Sales Revenue', 'Revenue'),
        ('4100', 'Plaza Rental Revenue', 'Revenue'),
        ('5000', 'Cost of Goods Sold (COGS)', 'Expense'),
        ('5500', 'Operational Expenses', 'Expense')
    ]
    cursor.executemany("INSERT INTO accounts (account_code, account_name, account_type) VALUES (?, ?, ?)", accounts_seed)
    conn.commit()

# --- DESIGN & SKINNING SYSTEM ---
st.set_page_config(page_title="Nexis Core ERP", layout="wide")

# Custom CSS injector for Zoho-style executive dark-blue/teal branding
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #003366; font-size: 32px; font-weight: 700; }
    div[data-testid="stMetricLabel"] { color: #5a6a85; font-size: 14px; }
    .stButton>button { background-color: #007bff; color: white; border-radius: 6px; padding: 10px 24px; border: none; }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    .card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Application Navigation Context
st.sidebar.markdown("<h2 style='text-align: center; color: #003366;'>🌐 Nexis ERP Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: gray;'>V2.4.0 (ACCA Compliant)</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
module = st.sidebar.radio("Navigate Workspace", [
    "📊 Executive Command Center",
    "📦 Inventory Management", 
    "🛒 Point of Sale Terminal", 
    "🚛 Supply Chain Procurement",
    "📈 Advanced Ledger & Financials"
])

# ---------------------------------------------------------
# MODULE: EXECUTIVE COMMAND CENTER (CHARTS, SUGGESTIONS & INSIGHTS)
# ---------------------------------------------------------
if module == "📊 Executive Command Center":
    st.markdown("<h1 style='color: #003366;'>Financial Command Center</h1>", unsafe_allow_html=True)
    st.write("Real-time metric synthesis and corporate health indexes.")
    
    # Financial Query Math for KPI Tiles
    cursor.execute("SELECT SUM(credit - debit) FROM journal_lines WHERE account_id IN (SELECT account_id FROM accounts WHERE account_type='Revenue')")
    rev_res = cursor.fetchone()[0]
    total_rev = rev_res if rev_res else 0.0
    
    cursor.execute("SELECT SUM(debit - credit) FROM journal_lines WHERE account_id IN (SELECT account_id FROM accounts WHERE account_type='Expense')")
    exp_res = cursor.fetchone()[0]
    total_exp = exp_res if exp_res else 0.0
    
    net_profit = total_rev - total_exp
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE stock_quantity < 5")
    low_stock_count = cursor.fetchone()[0]

    # Executive Summary Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Gross Revenue YTD", f"${total_rev:,.2f}", delta="Base Revenue")
    with kpi2:
        st.metric("Total Operational Expenses", f"${total_exp:,.2f}", delta="- Outflows", delta_color="inverse")
    with kpi3:
        st.metric("Net Profit Margin", f"${net_profit:,.2f}", delta=f"{((net_profit/total_rev)*100 if total_rev else 0):.1f}% Balance Ratio")
    with kpi4:
        st.metric("Critical Low-Stock SKU Alerts", f"{low_stock_count} Items", delta="Action Required", delta_color="inverse" if low_stock_count > 0 else "normal")

    st.markdown("---")
    
    # Graphs Layout
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.subheader("📦 Inventory Asset Distribution")
        df_stock = pd.read_sql_query("SELECT product_name, (stock_quantity * unit_cost) AS Total_Asset_Value FROM products", conn)
        if df_stock.empty:
            st.info("No active stock valuation available to render visual analytics.")
        else:
            fig_pie = px.pie(df_stock, values='Total_Asset_Value', names='product_name', hole=0.4, color_discrete_sequence=px.colors.sequential.YlGnBu_r)
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, width="stretch")

    with graph_col2:
        st.subheader("💡 System AI Audits & Smart Suggestions")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Build accounting/business validation notifications dynamically
        if low_stock_count > 0:
            st.warning(f"⚠️ **Inventory Warning:** You have {low_stock_count} item lines nearing zero stock. Run a Purchase Order in the 'Supply Chain Procurement' tab to prevent localized stockouts.")
        else:
            st.success("✅ **Stock Efficiency:** Inventory turns look stable. No imminent retail stock depletion risks detected.")
            
        if total_rev > 0 and (net_profit / total_rev) < 0.20:
            st.error("📉 **Margin Alert:** Your operational profitability margin is tracking below 20%. Consider evaluating vendor supply pricing structures or optimizing retail markups.")
        elif total_rev > 0:
            st.success("🚀 **Healthy Performance:** Gross-to-net operational ratios verify a strong business infrastructure model.")
            
        st.info("🏢 **Upcoming Shopping Plaza Hint:** When your physical units open, utilize our multi-tenant accounting hooks to automate lease receivables matching directly inside this ledger core.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MODULE: INVENTORY MANAGEMENT
# ---------------------------------------------------------
elif module == "📦 Inventory Management":
    st.header("Stock & Product Portfolio Portfolio")
    
    with st.form("add_product"):
        st.subheader("Create a New Product Line")
        c1, c2, c3 = st.columns(3)
        sku = c1.text_input("SKU Code / Barcode String")
        name = c1.text_input("Item Name")
        cat = c2.selectbox("Product Segment Category", ["Shirts", "Trousers", "Jackets", "Traditional", "Accessories"])
        qty = c2.number_input("Opening Inventory Volume", min_value=0, step=1)
        cost = c3.number_input("Wholesale Inbound Unit Cost ($)", min_value=0.0)
        price = c3.number_input("Standard Selling Price Tag ($)", min_value=0.0)
        
        if st.form_submit_button("Log Product Portfolio Entry"):
            if sku and name:
                try:
                    cursor.execute("INSERT INTO products (sku, product_name, category, unit_cost, retail_price, stock_quantity) VALUES (?,?,?,?,?,?)", (sku, name, cat, cost, price, qty))
                    conn.commit()
                    st.success("Item committed to system records successfully.")
                    st.rerun()
                except: st.error("Duplicate SKU key violation. Entry rejected.")

    st.subheader("Master Asset Inventory Log")
    df_prod = pd.read_sql_query("SELECT sku AS SKU, product_name AS [Item Name], category AS Category, unit_cost AS [Cost Basis], retail_price AS [Retail Price], stock_quantity AS [Current Qty] FROM products", conn)
    st.dataframe(df_prod, width="stretch")

# ---------------------------------------------------------
# MODULE: POINT OF SALE TERMINAL
# ---------------------------------------------------------
elif module == "🛒 Point of Sale Terminal":
    st.header("Point of Sale Retail Counter")
    products_list = pd.read_sql_query("SELECT product_id, sku, product_name, retail_price, stock_quantity FROM products WHERE stock_quantity > 0", conn)
    
    if products_list.empty:
        st.warning("No available retail items in database. Configure stock logs first.")
    else:
        product_options = {f"{row['product_name']} [{row['sku']}] - Qty Available: {row['stock_quantity']}": row for _, row in products_list.iterrows()}
        selected_prod = st.selectbox("Select Item for Current Checkout Queue", list(product_options.keys()))
        item_data = product_options[selected_prod]
        
        qty_sale = st.number_input("Transaction Quantity", min_value=1, max_value=int(item_data['stock_quantity']), step=1)
        total_bill = qty_sale * item_data['retail_price']
        st.markdown(f"### Total Sale Invoicing Balance: <span style='color:green;'>${total_bill:,.2f}</span>", unsafe_allow_html=True)
        
        if st.button("Authorize Transaction / Print Cash Slip"):
            cursor.execute("SELECT unit_cost FROM products WHERE product_id = ?", (int(item_data['product_id']),))
            unit_cost = cursor.fetchone()[0]
            total_cogs = qty_sale * unit_cost
            
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?", (qty_sale, int(item_data['product_id'])))
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)", (date_str, f"POS Checkout Line Item: {qty_sale}x {item_data['product_name']}", "POS-SYS"))
            inv_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='1000'), ?, 0)", (inv_id, total_bill))
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='4000'), 0, ?)", (inv_id, total_bill))
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='5000'), ?, 0)", (inv_id, total_cogs))
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='1200'), 0, ?)", (inv_id, total_cogs))
            conn.commit()
            st.success("Sale executed. Balancing General Ledger entries pushed.")
            st.rerun()

# ---------------------------------------------------------
# MODULE: SUPPLY CHAIN PROCUREMENT
# ---------------------------------------------------------
elif module == "🚛 Supply Chain Procurement":
    st.header("Procurement Reorder Interface")
    products_list = pd.read_sql_query("SELECT product_id, sku, product_name, unit_cost FROM products", conn)
    
    if products_list.empty:
        st.warning("Define a shell inventory matrix item profile prior to batch restocking operations.")
    else:
        product_options = {f"{row['product_name']} ({row['sku']})": row for _, row in products_list.iterrows()}
        selected_prod = st.selectbox("Select Product to Order", list(product_options.keys()))
        item_data = product_options[selected_prod]
        
        qty_pur = st.number_input("Vendor Inbound Batch Order Quantity", min_value=1, step=1)
        custom_cost = st.number_input("Negotiated Wholesale Settlement Cost per Unit ($)", min_value=0.0, value=float(item_data['unit_cost']))
        total_cost = qty_pur * custom_cost
        
        st.metric("Total Batch Expenditure Line (Cash Account Decrease)", f"${total_cost:,.2f}")
        
        if st.button("Finalize Inbound Batch Posting"):
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ?, unit_cost = ? WHERE product_id = ?", (qty_pur, custom_cost, int(item_data['product_id'])))
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)", (date_str, f"Wholesale Restock Batch: {qty_pur}x {item_data['product_name']}", "PO-INBOUND"))
            po_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='1200'), ?, 0)", (po_id, total_cost))
            cursor.execute("INSERT INTO journal_lines (entry_id, account_id, debit, credit) VALUES (?, (SELECT account_id FROM accounts WHERE account_code='1000'), 0, ?)", (po_id, total_cost))
            conn.commit()
            st.success("Procurement matched. Physical counts recalculated.")
            st.rerun()

# ---------------------------------------------------------
# MODULE: ADVANCED Ledger & FINANCIALS
# ---------------------------------------------------------
elif module == "📈 Advanced Ledger & Financials":
    st.header("General Ledger Audit Environment")
    
    query_tb = """
    SELECT a.account_code AS Code, a.account_name AS [Account Name], a.account_type AS Type,
           SUM(jl.debit) as Debits, SUM(jl.credit) as Credits
    FROM accounts a
    LEFT JOIN journal_lines jl ON a.account_id = jl.account_id
    GROUP BY a.account_id HAVING Debits > 0 OR Credits > 0;
    """
    df_tb = pd.read_sql_query(query_tb, conn)
    
    t1, t2 = st.tabs(["🏛️ General Ledger Trial Balance", "📋 Consolidated Profit or Loss Statement"])
    
    with t1:
        st.subheader("Auditable Master Trial Balance")
        if df_tb.empty: st.info("Ledgers empty. No active postings detected.")
        else: st.dataframe(df_tb, width="stretch")
            
    with t2:
        st.subheader("Statement of Profit or Loss (IFRS Standardized)")
        query_pl = """
        SELECT a.account_name, a.account_type, SUM(jl.credit - jl.debit) as Net_Balance
        FROM accounts a
        JOIN journal_lines jl ON a.account_id = jl.account_id
        WHERE a.account_type IN ('Revenue', 'Expense') GROUP BY a.account_id;
        """
        df_pl = pd.read_sql_query(query_pl, conn)
        
        if df_pl.empty: st.info("No profit-loss account activity logged.")
        else:
            df_pl['Amount'] = df_pl.apply(lambda r: r['Net_Balance'] if r['account_type']=='Revenue' else -r['Net_Balance'], axis=1)
            st.table(df_pl[['account_name', 'Amount']])
            st.metric("Net Financial Margin", f"${df_pl['Amount'].sum():,.2f}")
