import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Penggunaan Petrol & Diesel CIDB", layout="wide", page_icon="⛽")

# CSS dengan saiz font normal dan sidebar padat (sama seperti asal)
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

# =========================================================
# SLICER DI SIDEBAR (VERSI ASAL, TANPA BUTANG TAMBAHAN)
# =========================================================
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

# Gabungan penapisan
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

# Chart tahunan
st.subheader("📅 Analisa Penggunaan Mengikut Tahun")
yearly = df_filter.groupby(['Tahun', 'Jenis'])['Amount in local currency'].sum().reset_index()
if not yearly.empty:
    fig_year = px.bar(yearly, x='Tahun', y='Amount in local currency', color='Jenis', barmode='group',
                      color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"},
                      text=yearly['Amount in local currency'].apply(lambda x: f'RM {x:,.2f}'))
    fig_year.update_traces(textposition='outside', textfont=dict(size=10))
    fig_year.update_layout(
        xaxis_title="Tahun", yaxis_title="RM",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12), height=300
    )
    fig_year.update_yaxes(tickformat=",.2f")
    st.plotly_chart(fig_year, use_container_width=True)
else:
    st.info("Tiada data tahunan untuk dipaparkan.")

# Analisis Penggunaan
st.subheader("📊 Analisis Penggunaan")
colA, colB = st.columns(2)
with colA:
    pie_data = df_filter.groupby('Jenis')['Amount in local currency'].sum().reset_index()
    if not pie_data.empty:
        fig = px.pie(pie_data, names='Jenis', values='Amount in local currency', hole=0.35,
                     color='Jenis', color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"})
        fig.update_traces(textinfo='percent+label', textfont_size=12)
        fig.update_layout(
            showlegend=False, margin=dict(t=10,b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12), height=300
        )
        st.plotly_chart(fig, use_container_width=True)
with colB:
    monthly = df_filter.groupby(['Bulan','Jenis'])['Amount in local currency'].sum().reset_index()
    if not monthly.empty:
        fig = px.bar(monthly, x='Bulan', y='Amount in local currency', color='Jenis',
                     barmode='group', color_discrete_map={"Petrol":"#2c7da0","Diesel":"#d98c2b"},
                     category_orders={"Bulan":bulan_order})
        fig.update_layout(
            xaxis_title="Bulan", yaxis_title="RM",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=11), height=300
        )
        fig.update_yaxes(tickformat=",.2f")
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# SEMUA PTJ (bukan top 10) - bar chart dengan amount jelas
# =========================================================
st.subheader("🏢 Penggunaan Mengikut PTJ")

ptj_sum = df_filter.groupby('PTJ')['Amount in local currency'].sum().reset_index()
ptj_sum = ptj_sum.sort_values('Amount in local currency', ascending=True)

if not ptj_sum.empty:
    # Tinggi dinamik: 25px setiap bar + 100px ruang
    chart_height = max(300, len(ptj_sum) * 25 + 50)
    fig_bar = px.bar(ptj_sum, y='PTJ', x='Amount in local currency', orientation='h',
                     text='Amount in local currency',
                     color='Amount in local currency', color_continuous_scale='Blues')
    fig_bar.update_traces(texttemplate='RM %{x:,.2f}', textposition='outside', textfont=dict(size=9))
    fig_bar.update_layout(
        xaxis_title="RM", yaxis_title="",
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=chart_height,
        font=dict(size=11),
        margin=dict(l=100, r=20, t=30, b=20)  # ruang kiri untuk label PTJ
    )
    fig_bar.update_xaxes(tickformat=",.2f")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("Tiada data PTJ.")

# =========================================================
# SEMUA PTJ (trend line chart) - semua PTJ berdasarkan slicer
# =========================================================
st.subheader("📈 Trend PTJ vs Tahun")

trend_tahunan = df_filter.groupby(['PTJ', 'Tahun'])['Amount in local currency'].sum().reset_index()
if not trend_tahunan.empty and len(trend_tahunan['PTJ'].dropna().unique()) > 0:
    fig_line = px.line(trend_tahunan, x='Tahun', y='Amount in local currency', color='PTJ',
                       markers=True, labels={"Amount in local currency": "RM"})
    fig_line.update_traces(marker=dict(size=5))
    fig_line.update_layout(
        xaxis_title="Tahun", yaxis_title="RM",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11),
        height=500,
        legend=dict(font=dict(size=8), itemsizing='constant')
    )
    fig_line.update_yaxes(tickformat=",.2f")
    fig_line.update_xaxes(type='category')
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Tiada data PTJ untuk trend.")
    import numpy as np

import numpy as np
st.subheader("🤖 AI Forecast (Trend + Seasonal)")

# =========================
# PREP DATA BULANAN
# =========================
forecast_df = df_filter.groupby(['Tahun','Bulan_Num'])['Amount in local currency'].sum().reset_index()

if len(forecast_df) >= 12:

    # Tukar kepada time index
    forecast_df = forecast_df.sort_values(['Tahun','Bulan_Num'])
    forecast_df['t'] = range(len(forecast_df))

    # =========================
    # TREND (Polynomial degree 2)
    # =========================
    x = forecast_df['t']
    y = forecast_df['Amount in local currency']

    trend_coef = np.polyfit(x, y, 2)
    trend_model = np.poly1d(trend_coef)

    # =========================
    # SEASONAL (bulan)
    # =========================
    seasonal_avg = forecast_df.groupby('Bulan_Num')['Amount in local currency'].mean()

    # =========================
    # FORECAST NEXT 12 BULAN
    # =========================
    future = []
    last_t = forecast_df['t'].max()

    for i in range(1, 13):
        t_val = last_t + i
        bulan = (forecast_df.iloc[-1]['Bulan_Num'] + i -1) % 12 + 1

        trend_val = trend_model(t_val)
        seasonal_val = seasonal_avg.get(bulan, 0)

        forecast_val = (trend_val * 0.7) + (seasonal_val * 0.3)

        future.append({
            "Index": t_val,
            "Forecast": forecast_val,
            "Bulan": bulan
        })

    future_df = pd.DataFrame(future)

    # Label bulan
    bulan_map = {1:"Jan",2:"Feb",3:"Mac",4:"Apr",5:"Mei",6:"Jun",
                 7:"Jul",8:"Ogos",9:"Sep",10:"Okt",11:"Nov",12:"Dis"}
    future_df['Bulan'] = future_df['Bulan'].map(bulan_map)

    # =========================
    # COMBINE ACTUAL + FORECAST
    # =========================
    actual_plot = forecast_df.copy()
    actual_plot['Type'] = 'Actual'
    actual_plot.rename(columns={'Amount in local currency':'Value'}, inplace=True)

    future_df['Type'] = 'Forecast'
    future_df.rename(columns={'Forecast':'Value'}, inplace=True)

    combined = pd.concat([
        actual_plot[['t','Value','Type']],
        future_df[['Index','Value','Type']].rename(columns={'Index':'t'})
    ])

    # =========================
    # PLOT
    # =========================
    fig_ai = px.line(
        combined,
        x='t',
        y='Value',
        color='Type',
        markers=True
    )

    fig_ai.update_layout(
        title="Trend + Seasonal Forecast (12 Bulan Akan Datang)",
        xaxis_title="Timeline",
        yaxis_title="RM",
        font=dict(size=12)
    )

    fig_ai.update_yaxes(tickformat=",.2f")

    st.plotly_chart(fig_ai, use_container_width=True)

    # =========================
    # OUTPUT SUMMARY
    # =========================
    total_forecast = future_df['Value'].sum()

    st.success(f"📊 Anggaran 12 bulan akan datang: RM {total_forecast:,.2f}")

else:
    st.warning("Data tidak cukup (perlu sekurang-kurangnya 12 bulan)")