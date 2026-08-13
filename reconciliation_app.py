import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Daily Sales & Cash Reconciliation", page_icon="📊", layout="centered")

# Custom CSS with strict A4 page sizing and media print styling to fix blank page/white looping issues
st.markdown("""
    <style>
    @media print {
        /* Hide all Streamlit layout chrome, sidebars, headers, and navigation */
        header, footer, [data-testid="stSidebar"], [data-testid="stHeader"], .stToolbar, .stActionButton {
            display: none !important;
        }
        
        /* Force full white page background and zero out margins */
        body, html, .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Hide everything on the page by default when printing */
        body * {
            visibility: hidden !important;
        }
        
        /* Make ONLY the printable report container and its children fully visible */
        #printable-report, #printable-report * {
            visibility: visible !important;
        }
        
        /* Lock dimensions to a single A4 page and position cleanly at top-left */
        #printable-report {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            width: 210mm !important;
            height: 297mm !important;
            margin: 0 !important;
            padding: 15mm !important;
            background-color: #ffffff !important;
            border: none !important;
            box-shadow: none !important;
            box-sizing: border-box !important;
            page-break-after: avoid !important;
            page-break-inside: avoid !important;
        }
        
        /* Explicitly hide all buttons and interactive widgets */
        button, .stButton, .stDownloadButton, iframe {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# App Header
st.title("📊 Daily Sales & Cash Reconciliation")
st.write("Record live sales and expenses per date, track drawer balances securely, and print clean single-page reports.")

# 1. Date & Business Info
col1, col2 = st.columns(2)
with col1:
    entry_date = st.date_input("Business Date", datetime.today())
with col2:
    business_name = st.text_input("Business Name", "ELITE BRAID & HAIR STYLIST")

st.divider()

# Initialize multi-date dictionary storage in session state so previous dates are never lost
date_str = str(entry_date)
if 'daily_records' not in st.session_state:
    st.session_state.daily_records = {}

if date_str not in st.session_state.daily_records:
    st.session_state.daily_records[date_str] = {
        "transactions": [],
        "expenses": [],
        "opening_float": 0.0,
        "actual_cash_counted": 0.0,
        "counted_by": "",
        "manager_name": ""
    }

# Shortcuts to current date's data block
current_data = st.session_state.daily_records[date_str]

# Calculate running totals dynamically for this specific date
cash_sales = sum([t["Amount"] for t in current_data["transactions"] if t["Type"] == "Cash"])
mobile_money = sum([t["Amount"] for t in current_data["transactions"] if t["Type"] == "Mobile Money"])
card_sales = sum([t["Amount"] for t in current_data["transactions"] if t["Type"] == "Card / Bank"])
credit_sales = sum([t["Amount"] for t in current_data["transactions"] if t["Type"] == "Credit (Owed)"])
total_revenue = cash_sales + mobile_money + card_sales + credit_sales

# Big Display Cards for Cash Received and Mobile Money Side-by-Side
st.write(f"### 📈 Live Day Sales Overview for {entry_date.strftime('%Y-%m-%d')}")
metric_col1, metric_col2 = st.columns(2)
metric_col1.metric("💵 Total Cash Received", f"{cash_sales:,.2f} TZS")
metric_col2.metric("📱 Total Mobile Money", f"{mobile_money:,.2f} TZS")

st.divider()

# 2. Live Transaction Entry Section
st.subheader("2. Add Live Sales Transactions")
with st.form(f"transaction_form_{date_str}", clear_on_submit=True):
    col3, col4 = st.columns(2)
    with col3:
        trans_amount = st.number_input("Transaction Amount", min_value=0.0, step=500.0, format="%.2f")
        trans_type = st.selectbox("Payment Method", ["Cash", "Mobile Money", "Card / Bank", "Credit (Owed)"])
    with col4:
        trans_note = st.text_input("Item / Customer Description (Optional)", placeholder="e.g., Braids / John Doe")
    
    add_trans_btn = st.form_submit_button("➕ Add Transaction to System")

if add_trans_btn and trans_amount > 0:
    current_data["transactions"].append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Type": trans_type,
        "Amount": trans_amount,
        "Note": trans_note if trans_note else "-"
    })
    st.success(f"Added {trans_amount:,.2f} under {trans_type} for {date_str}!")
    st.rerun()

if current_data["transactions"]:
    st.write("### Today's Recorded Transactions Feed:")
    df_trans = pd.DataFrame(current_data["transactions"])
    st.dataframe(df_trans, use_container_width=True)

st.divider()

# 3. Live Expenses / Cash-Out Entry Section
st.subheader("3. Add Cash Payouts / Expenses")
with st.form(f"expense_form_{date_str}", clear_on_submit=True):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        expense_amount = st.number_input("Amount Taken Out", min_value=0.0, step=500.0, format="%.2f")
    with col_e2:
        expense_reason = st.text_input("Reason / Explanation", placeholder="e.g., tea break, transport")
    
    add_expense_btn = st.form_submit_button("➖ Add Expense / Cash Out")

if add_expense_btn and expense_amount > 0:
    current_data["expenses"].append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Amount": expense_amount,
        "Reason": expense_reason if expense_reason else "Unspecified expense"
    })
    st.success(f"Recorded cash out of {expense_amount:,.2f}!")
    st.rerun()

total_cash_paid_out = sum([e["Amount"] for e in current_data["expenses"]])

if current_data["expenses"]:
    st.write("### Today's Recorded Expenses Feed:")
    df_exp = pd.DataFrame(current_data["expenses"])
    st.dataframe(df_exp, use_container_width=True)
    st.info(f"**Total Expenses / Cash Taken Out:** {total_cash_paid_out:,.2f} TZS")

st.divider()

# 4. End-of-Day Drawer Audit & Signatures
st.subheader("4. End-of-Day Drawer Audit & Signatures")
opening_float = st.number_input("Opening Float / Change in Drawer", min_value=0.0, step=1000.0, format="%.2f", value=current_data["opening_float"])
actual_cash_counted = st.number_input("Actual Physical Cash Counted at Close", min_value=0.0, step=1000.0, format="%.2f", value=current_data["actual_cash_counted"])

st.write("") 

col_sig1, col_sig2 = st.columns(2)
with col_sig1:
    counted_by = st.text_input("Cash Counted By (Staff Name)", value=current_data["counted_by"], placeholder="e.g., Jane (Staff)")
with col_sig2:
    manager_name = st.text_input("Manager Reviewing / Seen By", value=current_data["manager_name"], placeholder="e.g., Peter (Manager)")

# Save states back dynamically
current_data["opening_float"] = opening_float
current_data["actual_cash_counted"] = actual_cash_counted
current_data["counted_by"] = counted_by
current_data["manager_name"] = manager_name

if st.button("📈 Generate Final Day Report"):
    expected_cash_drawer = opening_float + cash_sales - total_cash_paid_out
    cash_difference = actual_cash_counted - expected_cash_drawer

    all_reasons = ", ".join([f"{e['Reason']} ({e['Amount']:,.2f})" for e in current_data["expenses"]]) if current_data["expenses"] else "None specified"

    st.divider()
    
    # Strictly structured A4 single-page report container with id="printable-report"
    report_html = f"""
    <div id="printable-report" style="width: 100%; max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px; background-color: #f9f9f9; color: #000; font-family: Arial, sans-serif; font-size: 13px;">
        <h2 style="text-align: center; margin-bottom: 2px; font-size: 20px;">{business_name}</h2>
        <p style="text-align: center; font-size: 13px; color: #555; margin-top: 0;">Report</p>
        <hr style="border: 0; border-top: 1px solid #ddd; margin: 10px 0;">
        <p style="margin: 4px 0;"><b>Date:</b> {entry_date.strftime('%Y-%m-%d')}</p>
        <p style="margin: 4px 0;"><b>Cash Sales Collected:</b> {cash_sales:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Mobile Money Collected:</b> {mobile_money:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Card/Bank Sales:</b> {card_sales:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Credit Sales:</b> {credit_sales:,.2f} TZS</p>
        <hr style="border: 0; border-top: 1px solid #ddd; margin: 10px 0;">
        <p style="margin: 4px 0;"><b>Total Revenue:</b> {total_revenue:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Opening Float:</b> {opening_float:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Total Cash Deducted / Paid Out:</b> {total_cash_paid_out:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Expense Breakdown:</b> {all_reasons}</p>
        <hr style="border: 0; border-top: 1px solid #ddd; margin: 10px 0;">
        <p style="margin: 4px 0;"><b>Expected Cash in Drawer:</b> {expected_cash_drawer:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Actual Physical Cash Counted:</b> {actual_cash_counted:,.2f} TZS</p>
        <p style="margin: 4px 0;"><b>Drawer Variance:</b> {cash_difference:,.2f} TZS</p>
        <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0 10px 0;">
        <h3 style="margin: 0 0 10px 0; font-size: 14px;">Signatures</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 15px;">
                    <p style="margin: 0; font-size: 12px;"><b>Cash Counted By:</b></p>
                    <p style="margin-top: 6px; font-size: 13px; font-weight: bold;">{counted_by if counted_by else '_________________________'}</p>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 15px;">
                    <p style="margin: 0; font-size: 12px;"><b>Manager Signed / Seen By:</b></p>
                    <p style="margin-top: 6px; font-size: 13px; font-weight: bold;">{manager_name if manager_name else '_________________________'}</p>
                </td>
            </tr>
        </table>
    </div>
    """
    
    # Render report on the normal Streamlit page view
    st.markdown(report_html, unsafe_allow_html=True)

    st.write("")
    
    # Fully working direct print trigger button using Streamlit components
    st.components.v1.html(
        f"""
        <div style="padding: 10px 0; text-align: center;">
            <button onclick="parent.window.print();" style="width: 100%; background-color: #2e7d32; color: white; padding: 14px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                🖨️ Click Here to Print / Save Report as PDF
            </button>
        </div>
        """,
        height=80
    )

    st.write("")

    # CSV Data export utility
    report_data = pd.DataFrame({
        "Metric": ["Date", "Business", "Cash Sales", "Mobile Money", "Card Sales", "Credit Sales", "Total Revenue", "Opening Float", "Total Cash Paid Out", "Expense Breakdown", "Expected Cash", "Actual Cash", "Difference", "Counted By", "Manager Name"],
        "Value": [str(entry_date), business_name, cash_sales, mobile_money, card_sales, credit_sales, total_revenue, opening_float, total_cash_paid_out, all_reasons, expected_cash_drawer, actual_cash_counted, cash_difference, counted_by, manager_name]
    })
    
    st.download_button(
        label="📥 Download Daily Summary (CSV)",
        data=report_data.to_csv(index=False).encode('utf-8'),
        file_name=f"sales_report_{entry_date}.csv",
        mime="text/csv",
    )