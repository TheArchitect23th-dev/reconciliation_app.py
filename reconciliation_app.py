from datetime import date, datetime, timezone
import calendar
import pandas as pd
from streamlit import runtime
import streamlit as st
from supabase import Client, create_client

# Page Configuration
st.set_page_config(
    page_title="Cash Tracker", page_icon="📊", layout="centered"
)

# --- SUPABASE & SUBSCRIPTION FUNCTIONS ---
# Load credentials safely from Streamlit secrets
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
  supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  supabase = None


def get_subscription(user_id: str):
  if not supabase:
    return None
  try:
    res = (
        supabase.table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )

    if not res.data:
      return None

    sub = res.data[0]

    # Check expiry for monthly/annual
    if sub["expires_at"] is not None:
      expires = datetime.fromisoformat(sub["expires_at"].replace("Z", "+00:00"))
      if expires < datetime.now(timezone.utc):
        return None

    return sub
  except Exception:
    return None


def is_subscribed(user_id: str):
  return get_subscription(user_id) is not None


def get_plan(user_id: str):
  sub = get_subscription(user_id)
  if not sub:
    return None
  return sub.get("plan")


# --- CUSTOM EXECUTIVE LOGIN & APP STYLING ---
st.markdown(
    """
    <style>
    /* Dark executive theme styling for login & app */
    .stApp {
        background-color: #0e1726;
        color: #e2e8f0;
    }
    
    /* Elegant Login Card Box */
    .login-card {
        background-color: #1b2a4a;
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        text-align: center;
        max-width: 500px;
        margin: 40px auto 20px auto;
        border: 1px solid #273e70;
    }
    
    .login-card h2 {
        color: #38bdf8;
        font-family: Arial, sans-serif;
        margin-bottom: 5px;
        font-size: 28px;
    }
    
    .login-card p {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 0;
    }

    /* Paywall Upgrade Card */
    .paywall-card {
        background: linear-gradient(135deg, #1b2a4a 0%, #0f172a 100%);
        border: 2px solid #38bdf8;
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(56, 189, 248, 0.15);
    }

    /* Classic, elegant styling for primary action buttons */
    .stButton button {
        background-color: #1b365d !important;
        color: #ffffff !important;
        border: 1px solid #273e70 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(27, 54, 93, 0.2) !important;
        width: 100% !important;
    }
    
    .stButton button:hover {
        background-color: #24487a !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 4px 8px rgba(56, 189, 248, 0.25) !important;
    }

    /* --- STRICT PRINT MEDIA OPTIMIZATION FOR READABILITY --- */
    @media print {
        header, footer, [data-testid="stSidebar"], [data-testid="stHeader"], .stToolbar, .stActionButton {
            display: none !important;
        }
        
        body, html, .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        body * {
            visibility: hidden !important;
        }
        
        #printable-report, #printable-report * {
            visibility: visible !important;
        }
        
        #printable-report {
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 10mm !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            border: none !important;
            box-shadow: none !important;
            box-sizing: border-box !important;
        }

        #printable-report table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin-top: 10px !important;
            margin-bottom: 15px !important;
        }
        
        #printable-report th, #printable-report td {
            border: 1px solid #444444 !important;
            padding: 6px 8px !important;
            color: #000000 !important;
            font-size: 11pt !important;
        }
        
        #printable-report th {
            background-color: #e2e8f0 !important;
            font-weight: bold !important;
            text-align: left !important;
        }

        button, .stButton, .stDownloadButton, iframe {
            display: none !important;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- PASSWORD PROTECTION & LOGIN SCREEN ---
def check_password():
  if (
      "password_correct" not in st.session_state
      or not st.session_state["password_correct"]
  ):
    st.markdown(
        """
            <div class="login-card">
                <h2>🔒 Secure Login</h2>
                <p><b>Cash Tracker</b><br>Daily sales & Subscriptions</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    with col_login:
      pwd = st.text_input(
          "Enter Password",
          type="password",
          key="password_input",
          label_visibility="collapsed",
          placeholder="Enter Password",
      )
      if st.button("Login to System"):
        if pwd == "Godslove":
          st.session_state["password_correct"] = True
          # Initialize default user context tracking / user_id
          st.session_state["user_id"] = "owner-user-id"
          st.session_state["user_email"] = "owner@cashtracker.com"
          st.rerun()
        else:
          st.error("😕 Password incorrect. Please try again.")
    return False
  else:
    return True


if not check_password():
  st.stop()

# --- SUBSCRIPTION & TIER MANAGEMENT SYSTEM (SUPABASE BACKED) ---
current_user_id = st.session_state.get("user_id", "owner-user-id")

# Check subscription status dynamically using Supabase functions
active_sub = get_subscription(current_user_id)
is_pro = active_sub is not None
current_tier = active_sub.get("tier", "Free") if active_sub else "Free"

# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
  st.write("### 🧭 Navigation Tabs")

  app_mode = st.radio(
      "Select View",
      [
          "Daily Data Entry & Audit",
          "REPORT (Pro)",
          "MONTHLY REVIEW (Pro)",
      ],
  )

  st.divider()
  st.write("### 💎 Subscription Status")

  if is_pro:
    st.success(
        f"🌟 **PRO TIER ACTIVE ({current_tier.upper()})**\nAll advanced range"
        " and monthly features unlocked."
    )
  else:
    st.info(
        "🔒 **Free Tier Active**\nUpgrade to Pro for multi-date reports and"
        " monthly statements."
    )

    with st.expander("💳 Choose Subscription Plan"):
      plan_choice = st.selectbox(
          "Select Billing Cycle",
          [
              "Monthly (15,000 TZS)",
              "Annual (120,000 TZS)",
              "Lifetime (350,000 TZS)",
          ],
      )
      st.markdown(
          "_To activate your plan securely, please complete payment via your"
          " integrated billing provider._"
      )

  st.divider()
  st.write("### Session Control")
  if st.button("🔒 Logout"):
    st.session_state["password_correct"] = False
    st.rerun()

# Initialize multi-date dictionary storage in session state
if "daily_records" not in st.session_state:
  st.session_state.daily_records = {}

# ---------------------------------
# VIEW 1: DAILY DATA ENTRY & AUDIT
# ---------------------------------
if app_mode == "Daily Data Entry & Audit":
  st.markdown(
      "<h1><b>Cash Tracker</b><br><span style='font-size: 20px; font-weight:"
      " normal;'>Daily sales</span></h1>",
      unsafe_allow_html=True,
  )
  st.write(
      "Record live sales and expenses per date, track drawer balances securely,"
      " and print clean single-page reports."
  )

  col1, col2 = st.columns(2)
  with col1:
    entry_date = st.date_input("Business Date", value=datetime.now())
  with col2:
    business_name = st.text_input("Business Name", "")

  st.divider()

  date_str = str(entry_date)
  if date_str not in st.session_state.daily_records:
    st.session_state.daily_records[date_str] = {
        "transactions": [],
        "expenses": [],
        "opening_float": 0.0,
        "actual_cash_counted": 0.0,
        "counted_by": "",
        "manager_name": "",
    }

  current_data = st.session_state.daily_records[date_str]

  cash_sales = sum(
      [t["Amount"] for t in current_data["transactions"] if t["Type"] == "Cash"]
  )
  mobile_money = sum(
      [
          t["Amount"]
          for t in current_data["transactions"]
          if t["Type"] == "Mobile Money"
      ]
  )
  card_sales = sum(
      [
          t["Amount"]
          for t in current_data["transactions"]
          if t["Type"] == "Card / Bank"
      ]
  )
  credit_sales = sum(
      [
          t["Amount"]
          for t in current_data["transactions"]
          if t["Type"] == "Credit (Owed)"
      ]
  )
  total_revenue = cash_sales + mobile_money + card_sales + credit_sales

  st.write(
      f"### 📈 Live Day Sales Overview for {entry_date.strftime('%Y-%m-%d')}"
  )
  metric_col1, metric_col2 = st.columns(2)
  metric_col1.metric("💵 Total Cash Received", f"{cash_sales:,.2f} TZS")
  metric_col2.metric("📱 Total Mobile Money", f"{mobile_money:,.2f} TZS")

  st.divider()

  st.subheader("2. Add Live Sales Transactions")
  with st.form(f"transaction_form_{date_str}", clear_on_submit=True):
    col3, col4 = st.columns(2)
    with col3:
      trans_amount = st.number_input(
          "Transaction Amount", min_value=0.0, step=500.0, format="%.2f"
      )
      trans_type = st.selectbox(
          "Payment Method",
          ["Cash", "Mobile Money", "Card / Bank", "Credit (Owed)"],
      )
    with col4:
      trans_note = st.text_input(
          "Item / Customer Description (Optional)",
          placeholder="e.g., Braids / John Doe",
      )

    add_trans_btn = st.form_submit_button("➕ Add Transaction to System")

  if add_trans_btn and trans_amount > 0:
    current_data["transactions"].append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Type": trans_type,
        "Amount": trans_amount,
        "Note": trans_note if trans_note else "-",
    })
    st.success(f"Added {trans_amount:,.2f} under {trans_type} for {date_str}!")
    st.rerun()

  if current_data["transactions"]:
    st.write("### Today's Recorded Transactions Feed:")
    df_trans = pd.DataFrame(current_data["transactions"])
    st.dataframe(df_trans, use_container_width=True)

  st.divider()

  st.subheader("3. Add Cash Payouts / Expenses")
  with st.form(f"expense_form_{date_str}", clear_on_submit=True):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
      expense_amount = st.number_input(
          "Amount Taken Out", min_value=0.0, step=500.0, format="%.2f"
      )
    with col_e2:
      expense_reason = st.text_input(
          "Reason / Explanation", placeholder="e.g., tea break, transport"
      )

    add_expense_btn = st.form_submit_button("➖ Add Expense / Cash Out")

  if add_expense_btn and expense_amount > 0:
    current_data["expenses"].append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Amount": expense_amount,
        "Reason": expense_reason if expense_reason else "Unspecified expense",
    })
    st.success(f"Recorded cash out of {expense_amount:,.2f}!")
    st.rerun()

  total_cash_paid_out = sum([e["Amount"] for e in current_data["expenses"]])

  if current_data["expenses"]:
    st.write("### Today's Recorded Expenses Feed:")
    df_exp = pd.DataFrame(current_data["expenses"])
    st.dataframe(df_exp, use_container_width=True)
    st.info(
        f"**Total Expenses / Cash Taken Out:** {total_cash_paid_out:,.2f} TZS"
    )

  st.divider()

  st.subheader("4. End-of-Day Drawer Audit & Signatures")
  opening_float = st.number_input(
      "Opening Float / Change in Drawer",
      min_value=0.0,
      step=1000.0,
      format="%.2f",
      value=current_data["opening_float"],
  )
  actual_cash_counted = st.number_input(
      "Actual Physical Cash Counted at Close",
      min_value=0.0,
      step=1000.0,
      format="%.2f",
      value=current_data["actual_cash_counted"],
  )

  st.write("")

  col_sig1, col_sig2 = st.columns(2)
  with col_sig1:
    counted_by = st.text_input(
        "Cash Counted By (Staff Name)",
        value=current_data["counted_by"],
        placeholder="e.g., Jane (Staff)",
    )
  with col_sig2:
    manager_name = st.text_input(
        "Manager Reviewing / Seen By",
        value=current_data["manager_name"],
        placeholder="e.g., Peter (Manager)",
    )

  current_data["opening_float"] = opening_float
  current_data["actual_cash_counted"] = actual_cash_counted
  current_data["counted_by"] = counted_by
  current_data["manager_name"] = manager_name

  if st.button("📈 Generate Final Day Report"):
    expected_cash_drawer = opening_float + cash_sales - total_cash_paid_out
    cash_difference = actual_cash_counted - expected_cash_drawer
    all_reasons = (
        ", ".join(
            [f"{e['Reason']} ({e['Amount']:,.2f})" for e in current_data["expenses"]]
        )
        if current_data["expenses"]
        else "None specified"
    )

    st.divider()

    report_html = f"""
        <div id="printable-report" style="width: 100%; max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px; background-color: #f9f9f9; color: #000; font-family: Arial, sans-serif; font-size: 13px;">
            <h2 style="text-align: center; margin-bottom: 2px; font-size: 20px;"><b>Cash Tracker</b><br><span style="font-size: 14px; font-weight: normal;">Daily sales</span></h2>
            <p style="text-align: center; font-size: 13px; color: #555; margin-top: 0;">{business_name if business_name else "Daily Summary Report"}</p>
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

    st.markdown(report_html, unsafe_allow_html=True)
    st.write("")

    st.components.v1.html(
        f"""
            <div style="padding: 10px 0; text-align: center;">
                <button onclick="parent.window.print();" style="width: 100%; background-color: #1b365d; color: white; padding: 12px 20px; border: 1px solid #273e70; border-radius: 6px; font-weight: 500; letter-spacing: 0.5px; cursor: pointer; font-size: 15px; box-shadow: 0 2px 4px rgba(27, 54, 93, 0.2);">
                    🖨️ Print / Save Report as PDF
                </button>
            </div>
            """,
        height=70,
    )

    report_data = pd.DataFrame({
        "Metric": [
            "Date",
            "Business",
            "Cash Sales",
            "Mobile Money",
            "Card Sales",
            "Credit Sales",
            "Total Revenue",
            "Opening Float",
            "Total Cash Paid Out",
            "Expense Breakdown",
            "Expected Cash",
            "Actual Cash",
            "Difference",
            "Counted By",
            "Manager Name",
        ],
        "Value": [
            str(entry_date),
            business_name,
            cash_sales,
            mobile_money,
            card_sales,
            credit_sales,
            total_revenue,
            opening_float,
            total_cash_paid_out,
            all_reasons,
            expected_cash_drawer,
            actual_cash_counted,
            cash_difference,
            counted_by,
            manager_name,
        ],
    })

    st.download_button(
        label="📥 Download Daily Summary (CSV)",
        data=report_data.to_csv(index=False).encode("utf-8"),
        file_name=f"sales_report_{entry_date}.csv",
        mime="text/csv",
    )

# ----------------------------------------------------
# VIEW 2: MULTI-DATE RANGE REPORT (PRO PAYWALL ENFORCED)
# ----------------------------------------------------
elif app_mode == "REPORT (Pro)":
  if not is_pro:
    st.markdown(
        """
            <div class="paywall-card">
                <h2>🔒 Pro Feature Locked</h2>
                <p>Multi-Date Range Reporting and deep custom summaries require an active subscription tier.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

  st.title("📅 Multi-Date Range Report (Pro Print)")
  st.write(
      "Select a custom date range to aggregate all cash, mobile money,"
      " expenses, and drawer totals between any two dates for client review and"
      " printing."
  )

  col_r1, col_r2 = st.columns(2)
  with col_r1:
    start_date = st.date_input("Start Date", value=date.today())
  with col_r2:
    end_date = st.date_input("End Date", value=date.today())

  report_business_name = st.text_input(
      "Business Name for Range Report", "BUSINESS CLIENT"
  )

  if st.button("📊 Generate Multi-Date Range Report"):
    filtered_dates = []
    agg_cash_sales = 0.0
    agg_mobile_money = 0.0
    agg_card_sales = 0.0
    agg_credit_sales = 0.0
    agg_expenses = 0.0
    agg_actual_cash_counted = 0.0

    daily_summary_rows = []

    for d_str, data in st.session_state.daily_records.items():
      d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
      if start_date <= d_obj <= end_date:
        filtered_dates.append(d_str)
        c_sales = sum(
            [t["Amount"] for t in data["transactions"] if t["Type"] == "Cash"]
        )
        m_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Mobile Money"
            ]
        )
        cd_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Card / Bank"
            ]
        )
        cr_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Credit (Owed)"
            ]
        )
        t_rev = c_sales + m_sales + cd_sales + cr_sales

        exp_sum = sum([e["Amount"] for e in data["expenses"]])
        act_cash = data["actual_cash_counted"]

        agg_cash_sales += c_sales
        agg_mobile_money += m_sales
        agg_card_sales += cd_sales
        agg_credit_sales += cr_sales
        agg_expenses += exp_sum
        agg_actual_cash_counted += act_cash

        daily_summary_rows.append({
            "Date": d_str,
            "Cash Sales": c_sales,
            "Mobile Money": m_sales,
            "Card/Bank": cd_sales,
            "Credit": cr_sales,
            "Total Revenue": t_rev,
            "Expenses Out": exp_sum,
            "Actual Cash Counted": act_cash,
        })

    total_agg_revenue = (
        agg_cash_sales + agg_mobile_money + agg_card_sales + agg_credit_sales
    )

    st.divider()

    range_report_html = f"""
        <div id="printable-report" style="background: #ffffff; color: #000000; padding: 25px; font-family: Arial, sans-serif; max-width: 800px; margin: auto;">
            <div style="text-align: center; border-bottom: 2px solid #000000; padding-bottom: 15px; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 24px; font-weight: bold; color: #000000;">CASH TRACKER FINANCIAL STATEMENT</h1>
                <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold; color: #333333;">{report_business_name}</p>
                <p style="margin: 3px 0 0 0; font-size: 13px; color: #555555;">Report Period: {start_date} to {end_date}</p>
            </div>

            <h3 style="font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px; color: #000;">1. Executive Summary Totals</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold; width: 60%;">Total Cash Collected:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; width: 40%;">{agg_cash_sales:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Mobile Money Collected:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{agg_mobile_money:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Card / Bank Sales:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{agg_card_sales:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Credit Sales:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{agg_credit_sales:,.2f} TZS</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Combined Total Revenue:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; font-weight: bold;">{total_agg_revenue:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold; color: #900;">Total Expenses / Cash Paid Out:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; color: #900;">{agg_expenses:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Physical Cash Counted:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{agg_actual_cash_counted:,.2f} TZS</td>
                </tr>
            </table>

            <h3 style="font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; color: #000;">2. Daily Breakdown Schedule</h3>
        """

    if daily_summary_rows:
      range_report_html += """
            <table style="width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #e2e8f0; color: #000;">
                        <th style="border: 1px solid #999; padding: 6px;">Date</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Cash</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Mobile</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Revenue</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Expenses</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Drawer Count</th>
                    </tr>
                </thead>
                <tbody>
            """
      for row in daily_summary_rows:
        range_report_html += f"""
                    <tr>
                        <td style="border: 1px solid #999; padding: 6px;">{row['Date']}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Cash Sales']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Mobile Money']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right; font-weight: bold;">{row['Total Revenue']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right; color: #900;">{row['Expenses Out']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Actual Cash Counted']:,.2f}</td>
                    </tr>
                """
      range_report_html += "</tbody></table>"
    else:
      range_report_html += (
          "<p style='font-style: italic; color: #555;'>No recorded"
          " transactions found within this date range.</p>"
      )

    range_report_html += """
            <div style="margin-top: 40px; border-top: 1px solid #000; padding-top: 15px;">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="border: none; width: 50%;"><b>Prepared By:</b> ___________________________</td>
                        <td style="border: none; width: 50%; text-align: right;"><b>Authorized Signature:</b> ___________________________</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    st.markdown(range_report_html, unsafe_allow_html=True)
    st.write("")

    st.components.v1.html(
        """
            <div style="padding: 10px 0; text-align: center;">
                <button onclick="parent.window.print();" style="width: 100%; background-color: #1b365d; color: white; padding: 12px 20px; border: 1px solid #273e70; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 15px;">
                    🖨️ Print / Save Clean PDF Report
                </button>
            </div>
            """,
        height=70,
    )

    if daily_summary_rows:
      df_range_summary = pd.DataFrame(daily_summary_rows)
      st.download_button(
          label="📥 Download Range Report Summary (CSV)",
          data=df_range_summary.to_csv(index=False).encode("utf-8"),
          file_name=f"range_report_{start_date}_to_{end_date}.csv",
          mime="text/csv",
      )

# ----------------------------------------------------
# VIEW 3: MONTHLY REVIEW & STATEMENT (PRO PAYWALL ENFORCED)
# ----------------------------------------------------
elif app_mode == "MONTHLY REVIEW (Pro)":
  if not is_pro:
    st.markdown(
        """
            <div class="paywall-card">
                <h2>🔒 Pro Feature Locked</h2>
                <p>Full Month Statements and rolling monthly analytics require an active subscription plan.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

  st.title("🗓️ Monthly Review & Full Month Statement")
  st.write(
      "Select a specific month and year to view, aggregate, and print the"
      " complete daily log and monthly summary without losing any individual"
      " daily data."
  )

  col_m1, col_m2 = st.columns(2)
  with col_m1:
    selected_year = st.selectbox(
        "Select Year", [2024, 2025, 2026, 2027], index=2
    )
  with col_m2:
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }
    selected_month_num = st.selectbox(
        "Select Month",
        options=list(month_names.keys()),
        format_func=lambda x: month_names[x],
        index=datetime.now().month - 1,
    )

  monthly_business_name = st.text_input(
      "Business Name for Monthly Statement", "BUSINESS CLIENT"
  )

  if st.button("📊 Generate Complete Monthly Report"):
    m_cash_sales = 0.0
    m_mobile_money = 0.0
    m_card_sales = 0.0
    m_credit_sales = 0.0
    m_expenses = 0.0
    m_actual_cash = 0.0

    monthly_rows = []

    for d_str, data in st.session_state.daily_records.items():
      d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
      if d_obj.year == selected_year and d_obj.month == selected_month_num:
        c_sales = sum(
            [t["Amount"] for t in data["transactions"] if t["Type"] == "Cash"]
        )
        m_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Mobile Money"
            ]
        )
        cd_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Card / Bank"
            ]
        )
        cr_sales = sum(
            [
                t["Amount"]
                for t in data["transactions"]
                if t["Type"] == "Credit (Owed)"
            ]
        )
        t_rev = c_sales + m_sales + cd_sales + cr_sales

        exp_sum = sum([e["Amount"] for e in data["expenses"]])
        act_cash = data["actual_cash_counted"]

        m_cash_sales += c_sales
        m_mobile_money += m_sales
        m_card_sales += cd_sales
        m_credit_sales += cr_sales
        m_expenses += exp_sum
        m_actual_cash += act_cash

        monthly_rows.append({
            "Date": d_str,
            "Cash Sales": c_sales,
            "Mobile Money": m_sales,
            "Card/Bank": cd_sales,
            "Credit": cr_sales,
            "Total Revenue": t_rev,
            "Expenses Out": exp_sum,
            "Actual Cash Counted": act_cash,
        })

    monthly_rows = sorted(monthly_rows, key=lambda x: x["Date"])
    total_monthly_revenue = (
        m_cash_sales + m_mobile_money + m_card_sales + m_credit_sales
    )

    st.divider()

    monthly_report_html = f"""
        <div id="printable-report" style="background: #ffffff; color: #000000; padding: 25px; font-family: Arial, sans-serif; max-width: 800px; margin: auto;">
            <div style="text-align: center; border-bottom: 2px solid #000000; padding-bottom: 15px; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 24px; font-weight: bold; color: #000000;">MONTHLY FINANCIAL STATEMENT</h1>
                <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold; color: #333333;">{monthly_business_name}</p>
                <p style="margin: 3px 0 0 0; font-size: 13px; color: #555555;">Statement Period: {month_names[selected_month_num]} {selected_year}</p>
            </div>

            <h3 style="font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px; color: #000;">1. Monthly Summary Totals</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold; width: 60%;">Total Cash Collected:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; width: 40%;">{m_cash_sales:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Mobile Money Collected:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{m_mobile_money:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Card / Bank Sales:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{m_card_sales:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Total Credit Sales:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right;">{m_credit_sales:,.2f} TZS</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold;">Combined Monthly Revenue:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; font-weight: bold;">{total_monthly_revenue:,.2f} TZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #999; font-weight: bold; color: #900;">Total Monthly Expenses:</td>
                    <td style="padding: 8px; border: 1px solid #999; text-align: right; color: #900;">{m_expenses:,.2f} TZS</td>
                </tr>
            </table>

            <h3 style="font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; color: #000;">2. Daily Logs for {month_names[selected_month_num]} {selected_year}</h3>
        """

    if monthly_rows:
      monthly_report_html += """
            <table style="width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #e2e8f0; color: #000;">
                        <th style="border: 1px solid #999; padding: 6px;">Date</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Cash</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Mobile</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Card</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Revenue</th>
                        <th style="border: 1px solid #999; padding: 6px; text-align: right;">Expenses</th>
                    </tr>
                </thead>
                <tbody>
            """
      for row in monthly_rows:
        monthly_report_html += f"""
                    <tr>
                        <td style="border: 1px solid #999; padding: 6px;">{row['Date']}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Cash Sales']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Mobile Money']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right;">{row['Card/Bank']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right; font-weight: bold;">{row['Total Revenue']:,.2f}</td>
                        <td style="border: 1px solid #999; padding: 6px; text-align: right; color: #900;">{row['Expenses Out']:,.2f}</td>
                    </tr>
                """
      monthly_report_html += "</tbody></table>"
    else:
      monthly_report_html += (
          f"<p style='font-style: italic; color: #555;'>No entries recorded for"
          f" {month_names[selected_month_num]} {selected_year}.</p>"
      )

    monthly_report_html += """
            <div style="margin-top: 40px; border-top: 1px solid #000; padding-top: 15px;">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="border: none; width: 50%;"><b>Prepared By:</b> ___________________________</td>
                        <td style="border: none; width: 50%; text-align: right;"><b>Authorized Signature:</b> ___________________________</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    st.markdown(monthly_report_html, unsafe_allow_html=True)
    st.write("")

    st.components.v1.html(
        """
            <div style="padding: 10px 0; text-align: center;">
                <button onclick="parent.window.print();" style="width: 100%; background-color: #1b365d; color: white; padding: 12px 20px; border: 1px solid #273e70; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 15px;">
                    🖨️ Print / Save Clean PDF Monthly Statement
                </button>
            </div>
            """,
        height=70,
    )

    if monthly_rows:
      df_monthly_summary = pd.DataFrame(monthly_rows)
      st.download_button(
          label="📥 Download Monthly Statement (CSV)",
          data=df_monthly_summary.to_csv(index=False).encode("utf-8"),
          file_name=(
              "monthly_statement_"
              f"{month_names[selected_month_num]}_{selected_year}.csv"
          ),
          mime="text/csv",
      )

st.divider()

st.write("### 🚶‍♂️ Walk Away / Quick Lock")
st.write("Leaving your desk temporarily? Click below to instantly lock the screen.")
if st.button("🔒 Lock Work Session"):
  st.session_state["password_correct"] = False
  st.rerun()
