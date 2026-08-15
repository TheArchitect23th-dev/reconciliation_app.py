# reconciliation_app_10.py
from datetime import date, datetime, timezone
import calendar
import pandas as pd
from streamlit import runtime
import streamlit as st
from supabase import Client, create_client

# --- FULL MULTI-LANGUAGE INTEGRATION ---
LANGUAGES = {
    "en": "English",
    "sw": "Swahili",
    "zh": "Chinese",
    "de": "German",
    "fr": "French",
}

# Translation dictionary for key UI elements
TRANSLATIONS = {
    "en": {
        "nav_title": "🧭 Navigation Tabs",
        "view_daily": "Daily Data Entry & Audit",
        "view_report": "REPORT (Pro)",
        "view_monthly": "MONTHLY REVIEW (Pro)",
        "sub_status": "💎 Subscription Status",
        "pro_active": "🌟 **PRO TIER ACTIVE**\nAll advanced range and monthly features unlocked.",
        "free_active": "🔒 **Free Tier Active**\nUpgrade to Pro for multi-date reports and monthly statements.",
        "choose_plan": "💳 Choose Subscription Plan",
        "billing_cycle": "Select Billing Cycle",
        "session_control": "Session Control",
        "logout": "🔒 Logout",
        "secure_login": "🔒 Secure Login",
        "login_sub": "<b>Cash Tracker</b><br>Daily sales & Subscriptions",
        "enter_pwd": "Enter Password",
        "login_btn": "Login to System",
        "pwd_error": "😕 Password incorrect. Please try again.",
        "daily_title": "Daily Sales & Audit",
        "daily_desc": "Record live sales and expenses per date, track drawer balances securely, and print clean single-page reports.",
        "business_date": "Business Date",
        "business_name": "Business Name",
        "live_overview": "📈 Live Day Sales Overview",
        "cash_received": "💵 Total Cash Received",
        "mobile_money": "📱 Total Mobile Money",
        "add_trans": "2. Add Live Sales Transactions",
        "trans_amount": "Transaction Amount",
        "payment_method": "Payment Method",
        "trans_note": "Item / Customer Description (Optional)",
        "add_trans_btn": "➕ Add Transaction to System",
        "trans_feed": "Today's Recorded Transactions Feed:",
        "add_expense": "3. Add Cash Payouts / Expenses",
        "expense_amount": "Amount Taken Out",
        "expense_reason": "Reason / Explanation",
        "add_expense_btn": "➖ Add Expense / Cash Out",
        "expense_feed": "Today's Recorded Expenses Feed:",
        "drawer_audit": "4. End-of-Day Drawer Audit & Signatures",
        "opening_float": "Opening Float / Change in Drawer",
        "actual_cash": "Actual Physical Cash Counted at Close",
        "counted_by": "Cash Counted By (Staff Name)",
        "manager_name": "Manager Reviewing / Seen By",
        "gen_report": "📈 Generate Final Day Report",
        "print_pdf": "🖨️ Print / Save Report as PDF",
        "download_csv": "📥 Download Daily Summary (CSV)",
        "monthly_report_title": "Monthly Sales Report",
        "total_sales_label": "Total Sales",
        "monthly_total_sales": "Total Monthly Sales",
        "monthly_total_cash": "Total Monthly Cash",
        "monthly_report_button": "Generate Monthly Report",
    },
    "sw": {
        "nav_title": "🧭 Vichupo vya Urambazaji",
        "view_daily": "Uingizaji Data wa Kila Siku na Ukaguzi",
        "view_report": "RIPOTI (Pro)",
        "view_monthly": "MAPITIO YA MWEZI (Pro)",
        "sub_status": "💎 Hali ya Usajili",
        "pro_active": "🌟 **KIPENGERE CHA PRO KIMEWASHWA**\nVipengele vyote vya juu vimefunguliwa.",
        "free_active": "🔒 **Kipengere cha Bure Kimewashwa**\nBoresha hadi Pro kwa ripoti za tarehe nyingi.",
        "choose_plan": "💳 Chagua Mpango wa Usajili",
        "billing_cycle": "Chagua Mzunguko wa Malipo",
        "session_control": "Udhibiti wa Kikao",
        "logout": "🔒 Toka Nje",
        "secure_login": "🔒 Kuingia Salama",
        "login_sub": "<b>Cash Tracker</b><br>Mauzo ya kila siku na Usajili",
        "enter_pwd": "Weka Nenosiri",
        "login_btn": "Ingia Kwenye Mfumo",
        "pwd_error": "😕 Nenosiri si sahihi. Tafadhali jaribu tena.",
        "daily_title": "Mauzo ya Kila Siku na Ukaguzi",
        "daily_desc": "Rekodi mauzo na matumizi kwa tarehe, fuatilia salio la droo, na uchapishe ripoti.",
        "business_date": "Tarehe ya Biashara",
        "business_name": "Jina la Biashara",
        "live_overview": "📈 Muhtasari wa Mauzo ya Siku",
        "cash_received": "💵 Jumla ya Pesa Taslimu",
        "mobile_money": "📱 Jumla ya Pesa za Simu",
        "add_trans": "2. Ongeza Miamala ya Mauzo",
        "trans_amount": "Kiasi cha Muamala",
        "payment_method": "Njia ya Malipo",
        "trans_note": "Maelezo ya Bidhaa / Mteja (Hiari)",
        "add_trans_btn": "➕ Ongeza Muamala kwenye Mfumo",
        "trans_feed": "Mirija ya Miamala Iliyorekodiwa Leo:",
        "add_expense": "3. Ongeza Matumizi / Matumizi ya Pesa",
        "expense_amount": "Kiasi Kilichotolewa",
        "expense_reason": "Sababu / Ufafanuzi",
        "add_expense_btn": "➖ Ongeza Gharama / Toa Pesa",
        "expense_feed": "Matumizi Yaliyorekodiwa Leo:",
        "drawer_audit": "4. Ukaguzi wa Droo Mwisho wa Siku na Sahihi",
        "opening_float": "Pesa ya Awali ya Chenji kwenye Droo",
        "actual_cash": "Pesa Halisi Iliyohesabiwa Kwenye Droo",
        "counted_by": "Pesa Imehesabiwa Na (Jina la Mfanyakazi)",
        "manager_name": "Meneja Anayekagua / Aliyeona",
        "gen_report": "📈 Tengeneza Ripoti ya Mwisho ya Siku",
        "print_pdf": "🖨️ Chapisha / Hifadhi Ripoti kama PDF",
        "download_csv": "📥 Pakua Muhtasari wa Kila Siku (CSV)",
        "monthly_report_title": "Ripoti ya Mauzo ya Mwezi",
        "total_sales_label": "Jumla ya Mauzo",
        "monthly_total_sales": "Jumla ya Mauzo ya Mwezi",
        "monthly_total_cash": "Jumla ya Fedha ya Mwezi",
        "monthly_report_button": "Tengeneza Ripoti ya Mwezi",
    },
    "zh": {
        "nav_title": "🧭 导航选项卡",
        "view_daily": "每日数据录入与审计",
        "view_report": "专业版报告 (Pro)",
        "view_monthly": "专业版月度审查 (Pro)",
        "sub_status": "💎 订阅状态",
        "pro_active": "🌟 **专业版已激活**\n所有高级区间和月度功能已解锁。",
        "free_active": "🔒 **免费版已激活**\n升级至专业版以解锁多日期报告。",
        "choose_plan": "💳 选择订阅计划",
        "billing_cycle": "选择计费周期",
        "session_control": "会话控制",
        "logout": "🔒 登出",
        "secure_login": "🔒 安全登录",
        "login_sub": "<b>现金追踪器</b><br>每日销售与订阅",
        "enter_pwd": "输入密码",
        "login_btn": "登录系统",
        "pwd_error": "😕 密码错误，请重试。",
        "daily_title": "每日销售与审计",
        "daily_desc": "记录每日实时销售和支出，安全追踪钱箱余额并打印整洁的单页报告。",
        "business_date": "营业日期",
        "business_name": "企业名称",
        "live_overview": "📈 实时日销售概览",
        "cash_received": "💵 收到现金总额",
        "mobile_money": "📱 移动支付总额",
        "add_trans": "2. 添加实时销售交易",
        "trans_amount": "交易金额",
        "payment_method": "支付方式",
        "trans_note": "商品 / 客户备注（可选）",
        "add_trans_btn": "➕ 添加交易到系统",
        "trans_feed": "今日记录的交易流：",
        "add_expense": "3. 添加现金支出 / 费用",
        "expense_amount": "提取金额",
        "expense_reason": "原因 / 说明",
        "add_expense_btn": "➖ 添加支出 / 提现",
        "expense_feed": "今日记录的费用流：",
        "drawer_audit": "4. 日结抽屉审计与签名",
        "opening_float": "开班零钱 / 抽屉备用金",
        "actual_cash": "结班盘点实际清点现金",
        "counted_by": "点钞人（员工姓名）",
        "manager_name": "审核经理 / 查阅人",
        "gen_report": "📈 生成最终日报表",
        "print_pdf": "🖨️ 打印 / 保存报告为 PDF",
        "download_csv": "📥 下载每日汇总 (CSV)",
        "monthly_report_title": "月度销售报告",
        "total_sales_label": "总销售额",
        "monthly_total_sales": "本月总销售额",
        "monthly_total_cash": "本月现金总额",
        "monthly_report_button": "生成月度报告",
    },
    "de": {
        "nav_title": "🧭 Navigation",
        "view_daily": "Tägliche Dateneingabe & Prüfung",
        "view_report": "BERICHT (Pro)",
        "view_monthly": "MONATLICHE RÜCKSCHAU (Pro)",
        "sub_status": "💎 Abostatus",
        "pro_active": "🌟 **PRO-STUFE AKTIV**\nAlle erweiterten Berichte freigeschaltet.",
        "free_active": "🔒 **Kostenlose Stufe Aktiv**\nAuf Pro upgraden für erweiterte Berichte.",
        "choose_plan": "💳 Abonnementplan wählen",
        "billing_cycle": "Abrechnungszeitraum wählen",
        "session_control": "Sitzungskontrolle",
        "logout": "🔒 Abmelden",
        "secure_login": "🔒 Sichere Anmeldung",
        "login_sub": "<b>Cash Tracker</b><br>Tägliche Verkäufe & Abos",
        "enter_pwd": "Passwort eingeben",
        "login_btn": "Im System anmelden",
        "pwd_error": "😕 Falsches Passwort. Bitte erneut versuchen.",
        "daily_title": "Tägliche Verkäufe & Prüfung",
        "daily_desc": "Verfassen Sie Live-Verkäufe und Ausgaben, verfolgen Sie Kassenbestände.",
        "business_date": "Geschäftsdatum",
        "business_name": "Unternehmensname",
        "live_overview": "📈 Live-Tagesumsatzübersicht",
        "cash_received": "💵 Gesamtes Bargeld",
        "mobile_money": "📱 Mobiles Geld Gesamt",
        "add_trans": "2. Live-Verkaufstransaktionen hinzufügen",
        "trans_amount": "Transaktionsbetrag",
        "payment_method": "Zahlungsmethode",
        "trans_note": "Artikel / Kundenbeschreibung (Optional)",
        "add_trans_btn": "➕ Transaktion zum System hinzufügen",
        "trans_feed": "Heutiger Transaktionsfeed:",
        "add_expense": "3. Barauszahlungen / Ausgaben hinzufügen",
        "expense_amount": "Entnommener Betrag",
        "expense_reason": "Grund / Erklärung",
        "add_expense_btn": "➖ Ausgabe / Barauszahlung hinzufügen",
        "expense_feed": "Heutiger Spesenfeed:",
        "drawer_audit": "4. Kassenprüfung & Unterschriften",
        "opening_float": "Wechselgeld / Eröffnungskasse",
        "actual_cash": "Tatsächliches Bargeld bei Feierabend",
        "counted_by": "Gezählt von (Mitarbeiter)",
        "manager_name": "Manager Überprüfung / Gesehen von",
        "gen_report": "📈 Endgültigen Tagesbericht erstellen",
        "print_pdf": "🖨️ Bericht drucken / als PDF speichern",
        "download_csv": "📥 Tagesübersicht herunterladen (CSV)",
        "monthly_report_title": "Monatlicher Verkaufsbericht",
        "total_sales_label": "Gesamtumsatz",
        "monthly_total_sales": "Gesamtumsatz des Monats",
        "monthly_total_cash": "Gesamtbargeld des Monats",
        "monthly_report_button": "Monatsbericht erstellen",
    },
    "fr": {
        "nav_title": "🧭 Onglets de Navigation",
        "view_daily": "Saisie de Données & Audit Quotidien",
        "view_report": "RAPPORT (Pro)",
        "view_monthly": "REVUE MENSUELLE (Pro)",
        "sub_status": "💎 Statut d'Abonnement",
        "pro_active": "🌟 **MODE PRO ACTIF**\nToutes les fonctionnalités avancées sont déverrouillées.",
        "free_active": "🔒 **Mode Gratuit Actif**\nMettez à niveau vers Pro pour les rapports avancés.",
        "choose_plan": "💳 Choisir un Plan d'Abonnement",
        "billing_cycle": "Sélectionner le Cycle de Facturation",
        "session_control": "Contrôle de Session",
        "logout": "🔒 Déconnexion",
        "secure_login": "🔒 Connexion Sécurisée",
        "login_sub": "<b>Cash Tracker</b><br>Ventes quotidiennes et abonnements",
        "enter_pwd": "Entrer le Mot de Passe",
        "login_btn": "Se Connecter au Système",
        "pwd_error": "😕 Mot de passe incorrect. Veuillez réessayer.",
        "daily_title": "Ventes Quotidiennes & Audit",
        "daily_desc": "Enregistrez les ventes en direct et suivez les soldes de caisse.",
        "business_date": "Date Commerciale",
        "business_name": "Nom de l'Entreprise",
        "live_overview": "📈 Aperçu des Ventes du Jour",
        "cash_received": "💵 Total Espèces Reçu",
        "mobile_money": "📱 Total Paiement Mobile",
        "add_trans": "2. Ajouter des Transactions de Vente",
        "trans_amount": "Montant de la Transaction",
        "payment_method": "Mode de Paiement",
        "trans_note": "Description Article / Client (Facultatif)",
        "add_trans_btn": "➕ Ajouter la Transaction",
        "trans_feed": "Flux des transactions enregistrées aujourd'hui :",
        "add_expense": "3. Ajouter des Sorties de Caisse / Dépenses",
        "expense_amount": "Montant Retiré",
        "expense_reason": "Motif / Explication",
        "add_expense_btn": "➖ Ajouter la Dépense",
        "expense_feed": "Flux des dépenses enregistrées aujourd'hui :",
        "drawer_audit": "4. Audit de Caisse & Signatures",
        "opening_float": "Fonds de Caisse Initial",
        "actual_cash": "Espèces Réelles Comptées à la Clôture",
        "counted_by": "Espèces Comptées Par (Nom du Personnel)",
        "manager_name": "Manager Vérificateur",
        "gen_report": "📈 Générer le Rapport Final du Jour",
        "print_pdf": "🖨️ Imprimer / Enregistrer le Rapport en PDF",
        "download_csv": "📥 Télécharger le Résumé Quotidien (CSV)",
        "monthly_report_title": "Rapport Mensuel des Ventes",
        "total_sales_label": "Ventes Totales",
        "monthly_total_sales": "Ventes Totales du Mois",
        "monthly_total_cash": "Total de Caisse du Mois",
        "monthly_report_button": "Générer le rapport mensuel",
    },
}


# Helper translation function using TRANSLATIONS dictionary
def t_func(key, lang):
  return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# Corrected Monthly Aggregation Function
def get_monthly_summary(df):
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month").agg({
        "sales": "sum",
        "cash": "sum"
    }).reset_index()

    return monthly.head(10)


# Page Configuration
st.set_page_config(
    page_title="Cash Tracker", page_icon="📊", layout="centered"
)

# --- SUPABASE & SUBSCRIPTION FUNCTIONS ---
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
    .stApp { background-color: #0e1726; color: #e2e8f0; }
    .login-card { background-color: #1b2a4a; padding: 35px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); text-align: center; max-width: 500px; margin: 40px auto 20px auto; border: 1px solid #273e70; }
    .login-card h2 { color: #38bdf8; font-family: Arial, sans-serif; margin-bottom: 5px; font-size: 28px; }
    .login-card p { color: #94a3b8; font-size: 14px; margin-top: 0; }
    .paywall-card { background: linear-gradient(135deg, #1b2a4a 0%, #0f172a 100%); border: 2px solid #38bdf8; padding: 30px; border-radius: 12px; text-align: center; margin: 20px 0; box-shadow: 0 10px 25px rgba(56, 189, 248, 0.15); }
    .stButton button { background-color: #1b365d !important; color: #ffffff !important; border: 1px solid #273e70 !important; border-radius: 6px !important; font-weight: 500 !important; letter-spacing: 0.5px !important; transition: all 0.3s ease !important; width: 100% !important; }
    .stButton button:hover { background-color: #24487a !important; border-color: #38bdf8 !important; }
    @media print {
        header, footer, [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
        body, html, .stApp { background-color: #ffffff !important; color: #000000 !important; }
        body * { visibility: hidden !important; }
        #printable-report, #printable-report * { visibility: visible !important; }
        #printable-report { position: absolute !important; left: 0 !important; top: 0 !important; width: 100% !important; }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- LANGUAGE SELECTOR & STATE SETUP ---
if "lang" not in st.session_state:
  st.session_state["lang"] = "en"

selected_lang_code = st.sidebar.selectbox(
    "🌐 Language / Lugha / 语言 / Sprache",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    index=list(LANGUAGES.keys()).index(st.session_state["lang"]),
)
st.session_state["lang"] = selected_lang_code
t = TRANSLATIONS[st.session_state["lang"]]
lang = st.session_state["lang"]


# --- PASSWORD PROTECTION & LOGIN SCREEN ---
def check_password():
  if (
      "password_correct" not in st.session_state
      or not st.session_state["password_correct"]
  ):
    st.markdown(
        f"""
            <div class="login-card">
                <h2>{t['secure_login']}</h2>
                <p>{t['login_sub']}</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    with col_login:
      pwd = st.text_input(
          t["enter_pwd"],
          type="password",
          key="password_input",
          label_visibility="collapsed",
          placeholder=t["enter_pwd"],
      )
      if st.button(t["login_btn"]):
        if pwd == "Godslove":
          st.session_state["password_correct"] = True
          st.session_state["user_id"] = "owner-user-id"
          st.session_state["user_email"] = "owner@cashtracker.com"
          st.rerun()
        else:
          st.error(t["pwd_error"])
    return False
  else:
    return True


if not check_password():
  st.stop()

# --- SUBSCRIPTION & TIER MANAGEMENT SYSTEM ---
current_user_id = st.session_state.get("user_id", "owner-user-id")
active_sub = get_subscription(current_user_id)
is_pro = active_sub is not None
current_tier = active_sub.get("tier", "Free") if active_sub else "Free"

# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
  st.write(f"### {t['nav_title']}")

  app_mode = st.radio(
      "Select View",
      [
          t["view_daily"],
          t["view_report"],
          t["view_monthly"],
      ],
  )

  st.divider()
  st.write(f"### {t['sub_status']}")

  if is_pro:
    st.success(f"{t['pro_active']} ({current_tier.upper()})")
  else:
    st.info(t["free_active"])
    with st.expander(t["choose_plan"]):
      plan_choice = st.selectbox(
          t["billing_cycle"],
          [
              "Monthly (15,000 TZS)",
              "Annual (120,000 TZS)",
              "Lifetime (350,000 TZS)",
          ],
      )

  st.divider()
  st.write(f"### {t['session_control']}")
  if st.button(t["logout"]):
    st.session_state["password_correct"] = False
    st.rerun()

if "daily_records" not in st.session_state:
  st.session_state.daily_records = {}


# --- UPDATED GLOBAL-READY PDF GENERATION FUNCTION ---
def generate_monthly_pdf(month_data, lang):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    file_name = f"monthly_report_{lang}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    title = t_func("monthly_report_title", lang)
    total_sales_label = t_func("monthly_total_sales", lang)
    total_cash_label = t_func("monthly_total_cash", lang)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, title)

    c.setFont("Helvetica", 12)

    y = 760
    for _, row in month_data.iterrows():
        # Prevent drawing past page boundaries
        if y < 80:
            c.showPage()
            y = 800
            c.setFont("Helvetica", 12)
            
        month_str = str(row["month"])
        c.drawString(50, y, f"Month: {month_str}")
        y -= 20
        c.drawString(70, y, f"{total_sales_label}: {row['sales']:,.2f} TZS")
        y -= 20
        c.drawString(70, y, f"{total_cash_label}: {row['cash']:,.2f} TZS")
        y -= 40

    c.showPage()
    c.save()

    return file_name


# ---------------------------------
# VIEW 1: DAILY DATA ENTRY & AUDIT
# ---------------------------------
if app_mode == t["view_daily"]:
  st.markdown(
      f"<h1><b>Cash Tracker</b><br><span style='font-size: 20px; font-weight:"
      f" normal;'>{t['daily_title']}</span></h1>",
      unsafe_allow_html=True,
  )
  st.write(t["daily_desc"])

  col1, col2 = st.columns(2)
  with col1:
    entry_date = st.date_input(t["business_date"], value=datetime.now())
  with col2:
    business_name = st.text_input(t["business_name"], "")

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
      [item["Amount"] for item in current_data["transactions"] if item["Type"] == "Cash"]
  )
  mobile_money = sum(
      [
          item["Amount"]
          for item in current_data["transactions"]
          if item["Type"] == "Mobile Money"
      ]
  )
  card_sales = sum(
      [
          item["Amount"]
          for item in current_data["transactions"]
          if item["Type"] == "Card / Bank"
      ]
  )
  credit_sales = sum(
      [
          item["Amount"]
          for item in current_data["transactions"]
          if item["Type"] == "Credit (Owed)"
      ]
  )
  total_revenue = cash_sales + mobile_money + card_sales + credit_sales

  st.write(
      f"### {t['live_overview']} for {entry_date.strftime('%Y-%m-%d')}"
  )
  metric_col1, metric_col2 = st.columns(2)
  metric_col1.metric(t["cash_received"], f"{cash_sales:,.2f} TZS")
  metric_col2.metric(t["mobile_money"], f"{mobile_money:,.2f} TZS")

  st.divider()

  st.subheader(t["add_trans"])
  with st.form(f"transaction_form_{date_str}", clear_on_submit=True):
    col3, col4 = st.columns(2)
    with col3:
      trans_amount = st.number_input(
          t["trans_amount"], min_value=0.0, step=500.0, format="%.2f"
      )
      trans_type = st.selectbox(
          t["payment_method"],
          ["Cash", "Mobile Money", "Card / Bank", "Credit (Owed)"],
      )
    with col4:
      trans_note = st.text_input(t["trans_note"])
    add_trans_btn = st.form_submit_button(t["add_trans_btn"])

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
    st.write(f"### {t['trans_feed']}")
    st.dataframe(pd.DataFrame(current_data["transactions"]), use_container_width=True)

  st.divider()

  st.subheader(t["add_expense"])
  with st.form(f"expense_form_{date_str}", clear_on_submit=True):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
      expense_amount = st.number_input(
          t["expense_amount"], min_value=0.0, step=500.0, format="%.2f"
      )
    with col_e2:
      expense_reason = st.text_input(t["expense_reason"])
    add_expense_btn = st.form_submit_button(t["add_expense_btn"])

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
    st.write(f"### {t['expense_feed']}")
    st.dataframe(pd.DataFrame(current_data["expenses"]), use_container_width=True)

  st.divider()

  st.subheader(t["drawer_audit"])
  opening_float = st.number_input(
      t["opening_float"],
      min_value=0.0,
      step=1000.0,
      format="%.2f",
      value=current_data["opening_float"],
  )
  actual_cash_counted = st.number_input(
      t["actual_cash"],
      min_value=0.0,
      step=1000.0,
      format="%.2f",
      value=current_data["actual_cash_counted"],
  )

  col_sig1, col_sig2 = st.columns(2)
  with col_sig1:
    counted_by = st.text_input(
        t["counted_by"], value=current_data["counted_by"]
    )
  with col_sig2:
    manager_name = st.text_input(
        t["manager_name"], value=current_data["manager_name"]
    )

  current_data["opening_float"] = opening_float
  current_data["actual_cash_counted"] = actual_cash_counted
  current_data["counted_by"] = counted_by
  current_data["manager_name"] = manager_name

  if st.button(t["gen_report"]):
    expected_cash_drawer = opening_float + cash_sales - total_cash_paid_out
    cash_difference = actual_cash_counted - expected_cash_drawer
    all_reasons = (
        ", ".join(
            [f"{e['Reason']} ({e['Amount']:,.2f})" for e in current_data["expenses"]]
        )
        if current_data["expenses"]
        else "None specified"
    )

    report_html = f"""
        <div id="printable-report" style="width: 100%; max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px; background-color: #f9f9f9; color: #000; font-family: Arial, sans-serif;">
            <h2 style="text-align: center; margin-bottom: 2px;"><b>Cash Tracker</b></h2>
            <p style="text-align: center;">{business_name if business_name else t['monthly_report_title']}</p>
            <p><b>Date:</b> {entry_date.strftime('%Y-%m-%d')}</p>
            <p><b>{t['total_sales_label']}:</b> {total_revenue:,.2f} TZS</p>
            <p><b>Expected Cash in Drawer:</b> {expected_cash_drawer:,.2f} TZS</p>
            <p><b>Actual Physical Cash Counted:</b> {actual_cash_counted:,.2f} TZS</p>
            <p><b>Drawer Variance:</b> {cash_difference:,.2f} TZS</p>
        </div>
        """
    st.markdown(report_html, unsafe_allow_html=True)
    st.download_button(
        label=t["download_csv"],
        data=pd.DataFrame({"Metric": ["Date", t["total_sales_label"]], "Value": [str(entry_date), total_revenue]}).to_csv(index=False).encode("utf-8"),
        file_name=f"sales_report_{entry_date}.csv",
        mime="text/csv",
    )

# ----------------------------------------------------
# VIEW 2 & 3: PRO REPORTS
# ----------------------------------------------------
elif app_mode in [t["view_report"], t["view_monthly"]]:
  if not is_pro:
    st.markdown(
        f"""
            <div class="paywall-card">
                <h2>🔒 Pro Feature Locked</h2>
                <p>Advanced Range Reporting and Monthly Statements require an active subscription.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()
  st.title(app_mode)
  
  st.write(f"### {t_func('monthly_report_title', lang)}")
  
  # Build aggregated mock or real dataframe using stored session records
  flattened_records = []
  for d_str, d_dict in st.session_state.get("daily_records", {}).items():
      t_sales = sum([item["Amount"] for item in d_dict.get("transactions", [])])
      c_sales = sum([item["Amount"] for item in d_dict.get("transactions", []) if item["Type"] == "Cash"])
      flattened_records.append({"date": d_str, "sales": t_sales, "cash": c_sales})
  
  if flattened_records:
      df_days = pd.DataFrame(flattened_records)
      month_summary_df = get_monthly_summary(df_days)
  else:
      # Fallback sample DataFrame if no records are logged yet
      month_summary_df = pd.DataFrame({
          "month": ["2026-07", "2026-08"],
          "sales": [1500000.0, 900000.0],
          "cash": [900000.0, 500000.0]
      })
      
  st.dataframe(month_summary_df, use_container_width=True)

  # Integrated Multi-Language Streamlit Button snippet
  if st.button(t("monthly_report_button", lang)):
      monthly = get_monthly_summary(df_days)
      pdf_file = generate_monthly_pdf(monthly, lang)

      with open(pdf_file, "rb") as f:
          st.download_button(
              label=t("monthly_report_button", lang),
              data=f,
              file_name=pdf_file,
              mime="application/pdf"
          )
