import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Penggunaan Petrol & Diesel CIDB", layout="wide", page_icon="⛽")

# CSS dengan saiz font normal dan sidebar padat
st.markdown("""
    <style>
    .stApp { background-color: #f5f7fb; }
    h1 { font-size: 28px !important; color: #0a2b5e; text-align: center !important; }
    h2 { font-size: 20px !important; color: #1e466e; border-left: 4px solid #f4a261; padding-left: 15px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(145deg, #0f2b4d, #1b3a6b);
        min-width: 260px !important;
        width: 260px !important;
        padding: 15px;
    }
    [data-testid="stSidebar"] * { color: white !important; font-size: 14px !important; }
    .filter-title {
        font-size: 18px !important;
        font-weight: bold;
        margin: 15px 0 10px 0;
        color: #ffd966 !important;
    }
    [data-testid="stSidebar"] label {
        font-size: 14px !important;
        font-weight: 500 !important;
        margin-top: 8px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e3a5f !important;
        border: 1px solid rgba(255,255,255,0.5) !important;
        border-radius: 10px !important;
        min-height: 38px !important;
    }
    div[data-baseweb="select"] * { color: white !important; font-size: 13px !important; }
    div[data-baseweb="select"] ul { background-color: #1e3a5f !important; font-size: 13px !important; }
    div[data-baseweb="select"] ul li { font-size: 13px !important; padding: 6px !important; }
    
    /* KPI */
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        margin-bottom: 5px !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #0a2b5e !important;
    }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        border-left: 4px solid #f4a261;
        padding: 10px 15px;
    }
    
    .stDataFrame { font-size: 13px !important; }
    .stDataFrame table { font-size: 13px !important; }
    .stDataFrame th { font-size: 14px !important; background-color: #e6f0fa !important; }
    .stDataFrame td { font-size: 13px !important; }
    .stSubheader { font-size: 20px !important; font-weight: bold; }
    .stMarkdown p { font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)

# Header
if Path("cidb_logo.png").exists():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("cidb_logo.png", width=80)

st.markdown("<h1 style='text-align: center;'>⛽ Penggunaan Petrol & Diesel (CIDB Malaysia)</h1>", unsafe_allow_html=True)

# Load data
DATA_FOLDER = Path("data")
@st.cache_data
def load_data():
    if not DATA_FOLDER.exists():
        st.error("Folder 'data' tidak dijumpai")
        st.stop()
    files = list(DATA_FOLDER.glob("*.[xX][lL][sS]*"))
    if not files:
        st.warning("Tiada fail Excel")
        return pd.DataFrame()
    df_list = [pd.read_excel(f) for f in files]
    return pd.concat(df_list, ignore_index=True)

df = load_data()
if df.empty:
    st.stop()

# Clean data
df['Posting Date'] = pd.to_datetime(df['Posting Date'], errors='coerce')
df = df.dropna(subset=['Posting Date'])
df['Tahun'] = df['Posting Date'].dt.year
df['Bulan_Num'] = df['Posting Date'].dt.month
bulan_melayu = {1:"Jan",2:"Feb",3:"Mac",4:"Apr",5:"Mei",6:"Jun",7:"Jul",8:"Ogos",9:"Sep",10:"Okt",11:"Nov",12:"Dis"}
df['Bulan'] = df['Bulan_Num'].map(bulan_melayu)
bulan_order = ["Jan","Feb","Mac","Apr","Mei","Jun","Jul","Ogos","Sep","Okt","Nov","Dis"]
df['Bulan'] = pd.Categorical(df['Bulan'], categories=bulan_order, ordered=True)

def get_q(month):
    if month in [1,2,3]: return "Q1"
    elif month in [4,5,6]: return "Q2"
    elif month in [7,8,9]: return "Q3"
    else: return "Q4"
df['Quarter'] = df['Bulan_Num'].apply(get_q)
df['Jenis'] = df['G/L Account'].astype(str).apply(lambda x: "Petrol" if x=="B26101" else ("Diesel" if x=="B26102" else "Other"))

ptj_map = {
    "10110001":"PKE","10110003":"PPUU","10110004":"BAR","10120001":"BSM","10120002":"BTM",
    "10120003":"BKA","10120004":"UPF","10130001":"BPLV","10130003":"BPGK","10130007":"BPKB",
    "10140007":"BPT","10140008":"BPS","10150008":"BPKPB","10150009":"BLA","10160001":"BSTU",
    "10160003":"BKK","10170003":"BPB","10170004":"BPK","10200001":"PL","10200002":"KD",
    "10200003":"PP","10200004":"PR","10200005":"SL","10200006":"WP","10200007":"NS",
    "10200008":"ML","10200009":"JH","10200010":"PH","10200011":"TR","10200012":"KN",
    "10200020":"SR","10200021":"MR","10200022":"BT","10200023":"SI","10200030":"SB",
    "10200031":"TW","10200032":"SD"
}
df['PTJ'] = df['Cost Center'].astype(str).map(ptj_map)

# Slicer di sidebar
st.sidebar.markdown("<div class='filter-title'>🔎 SLICER</div>", unsafe_allow_html=True)

all_tahun = sorted(df['Tahun'].unique())
selected_tahun = st.sidebar.multiselect("📅 Tahun", options=all_tahun, default=all_tahun)

temp_df = df[df['Tahun'].isin(selected_tahun)] if selected_tahun else df
all_ptj = sorted(temp_df['PTJ'].dropna().unique())
selected_ptj = st.sidebar.multiselect("🏢 PTJ", options=all_ptj, default=all_ptj)
if selected_ptj:
    temp_df = temp_df[temp_df['PTJ'].isin(selected_ptj)]

all_bulan = [b for b in bulan_order if b in temp_df['Bulan'].unique()]
selected_bulan = st.sidebar.multiselect("📆 Bulan", options=all_bulan, default=all_bulan)
if selected_bulan:
    temp_df = temp_df[temp_df['Bulan'].isin(selected_bulan)]

all_quarter = sorted(temp_df['Quarter'].unique())
selected_quarter = st.sidebar.multiselect("🗓️ Quarter", options=all_quarter, default=all_quarter)
if selected_quarter:
    temp_df = temp_df[temp_df['Quarter'].isin(selected_quarter)]

all_jenis = ["Petrol", "Diesel"]
selected_jenis = st.sidebar.multiselect("⛽ Jenis Bahan Api", options=all_jenis, default=all_jenis)

# Gabungan penapisan untuk semua chart (berdasarkan slicer)
df_filter = df.copy()
if selected_tahun:
    df_filter = df_filter[df_filter['Tahun'].isin(selected_tahun)]
if selected_ptj:
    df_filter = df_filter[df_filter['PTJ'].isin(selected_ptj)]
if selected_bulan:
    df_filter = df_filter[df_filter['Bulan'].isin(selected_bulan)]
if selected_quarter:
    df_filter = df_filter[df_filter['Quarter'].isin(selected_quarter)]
if selected_jenis:
    df_filter = df_filter[df_filter['Jenis'].isin(selected_jenis)]

# KPI
petrol = df_filter[df_filter['Jenis']=="Petrol"]['Amount in local currency'].sum()
diesel = df_filter[df_filter['Jenis']=="Diesel"]['Amount in local currency'].sum()
jumlah = petrol + diesel

c1, c2, c3 = st.columns(3)
c1.metric("⛽ Petrol", f"RM {petrol:,.2f}")
c2.metric("🚛 Diesel", f"RM {diesel:,.2f}")
c3.metric("💰 Jumlah", f"RM {jumlah:,.2f}")

# Analisis Penggunaan - dua chart dalam satu baris dengan height kecil
st.subheader("📊 Analisis Penggunaan")
colA, colB = st.columns(2)

with colA:
    pie_data = df_filter.groupby('Jenis')['Amount in local currency'].sum().reset_index()
    if not pie_data.empty:
        fig = px.pie(pie_data, names='Jenis', values='Amount in local currency', hole=0.35,
                     color='Jenis', color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"})
        fig.update_traces(textinfo='percent+label', textfont_size=12)
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10), font=dict(size=12), height=300)
        st.plotly_chart(fig, use_container_width=True)

with colB:
    monthly = df_filter.groupby(['Bulan','Jenis'])['Amount in local currency'].sum().reset_index()
    if not monthly.empty:
        fig = px.bar(monthly, x='Bulan', y='Amount in local currency', color='Jenis',
                     barmode='group', color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"},
                     category_orders={"Bulan":bulan_order})
        fig.update_layout(xaxis_title="Bulan", yaxis_title="RM", plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(size=11), height=300)
        fig.update_yaxes(tickformat=",.2f")
        st.plotly_chart(fig, use_container_width=True)

# Chart tahunan
st.subheader("📅 Analisa Penggunaan Mengikut Tahun")
yearly = df_filter.groupby(['Tahun', 'Jenis'])['Amount in local currency'].sum().reset_index()
if not yearly.empty:
    fig_year = px.bar(yearly, x='Tahun', y='Amount in local currency', color='Jenis', barmode='group',
                      color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"},
                      text=yearly['Amount in local currency'].apply(lambda x: f'RM {x:,.2f}'))
    fig_year.update_traces(textposition='outside', textfont=dict(size=10))
    fig_year.update_layout(xaxis_title="Tahun", yaxis_title="RM", plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(size=12), height=300)
    fig_year.update_yaxes(tickformat=",.2f")
    st.plotly_chart(fig_year, use_container_width=True)
else:
    st.info("Tiada data tahunan untuk dipaparkan.")

# Dua chart sebaris: Top 10 PTJ dan Trend PTJ vs Tahun (tanpa filter tambahan)
st.subheader("🏢 Penggunaan Mengikut PTJ (Top 10) & 📈 Trend PTJ vs Tahun")

col1, col2 = st.columns(2)

with col1:
    # Top 10 PTJ (horizontal bar chart)
    ptj_sum = df_filter.groupby('PTJ')['Amount in local currency'].sum().reset_index()
    ptj_sum = ptj_sum.sort_values('Amount in local currency', ascending=True).tail(10)  # Top 10
    if not ptj_sum.empty:
        fig_bar = px.bar(ptj_sum, y='PTJ', x='Amount in local currency', orientation='h',
                         text='Amount in local currency',
                         color='Amount in local currency', color_continuous_scale='Blues')
        fig_bar.update_traces(texttemplate='RM %{x:,.2f}', textposition='outside', textfont=dict(size=10))
        fig_bar.update_layout(xaxis_title="RM", yaxis_title="", coloraxis_showscale=False,
                              height=350, font=dict(size=11))
        fig_bar.update_xaxes(tickformat=",.2f")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Tiada data PTJ.")

with col2:
    # Trend PTJ vs Tahun - plot semua PTJ dalam data (selepas slicer)
    trend_tahunan = df_filter.groupby(['PTJ', 'Tahun'])['Amount in local currency'].sum().reset_index()
    ptj_list = trend_tahunan['PTJ'].dropna().unique()
    if len(ptj_list) > 0:
        # Limit kepada 10 PTJ teratas untuk kebolehbacaan (atau semua jika kurang)
        total_per_ptj = trend_tahunan.groupby('PTJ')['Amount in local currency'].sum().sort_values(ascending=False)
        top_ptj = total_per_ptj.head(10).index.tolist()
        trend_filtered = trend_tahunan[trend_tahunan['PTJ'].isin(top_ptj)]
        
        fig_line = px.line(trend_filtered, x='Tahun', y='Amount in local currency', color='PTJ',
                           markers=True, labels={"Amount in local currency": "RM"})
        fig_line.update_traces(marker=dict(size=6))
        fig_line.update_layout(xaxis_title="Tahun", yaxis_title="RM", font=dict(size=11),
                               height=350, legend=dict(font=dict(size=9)))
        fig_line.update_yaxes(tickformat=",.2f")
        fig_line.update_xaxes(type='category')
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Tiada data PTJ untuk trend.")