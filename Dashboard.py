import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Sales Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] { color: #ff9900 !important; font-weight: bold; }
    .main-title { color: #ff9900; font-size: 40px; font-weight: 800; text-align: center; margin-bottom: 30px; }
    /* Fix for sidebar text color */
    section[data-testid="stSidebar"] .stMarkdown { color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# Data Loading
def load_and_clean_data():
    df = pd.read_csv("Amazon Sale Report.csv", low_memory=False)
    
    # Standardize all column names 
    df.columns = df.columns.str.strip().str.replace('-', '_').str.replace(' ', '_')
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    #Null Values Elimination
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
    df['Category'] = df['Category'].str.title().fillna("Unknown")
    df['Status'] = df['Status'].fillna("Unknown")
    
    # Remove duplicates 
    df.drop_duplicates(inplace=True)
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

try:
    df = load_and_clean_data()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# Customizing Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=150)
st.sidebar.title("Dashboard Controls")

# Date range selection
min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)

# Category/Status Filter
selected_cat = st.sidebar.multiselect("Select Category", df['Category'].unique())
selected_status = st.sidebar.multiselect("Order Status", df['Status'].unique())

# Filter Logic
filtered_df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
if selected_cat:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_cat)]
if selected_status:
    filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]

#MAIN DASHBOARD
st.markdown('<div class="main-title">Amazon Retail Data Matrix</div>', unsafe_allow_html=True)

# KPI Rows
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Revenue", f"₹{filtered_df['Amount'].sum():,.0f}")
with k2:
    st.metric("Total Orders", f"{len(filtered_df):,}")
with k3:
    st.metric("Avg Order Value", f"₹{filtered_df['Amount'].mean():,.2f}")
with k4:
    st.metric("Quantity Sold", f"{int(filtered_df['Qty'].sum()):,}")

st.markdown("---")

# Row 1: Sales Trend & Category
c1, c2 = st.columns([6, 4])

with c1:
    st.subheader("📈 Revenue Growth Trend")
    trend = filtered_df.groupby(filtered_df['Date'].dt.date)['Amount'].sum().reset_index()
    fig_trend = px.area(trend, x='Date', y='Amount', template="plotly_dark", color_discrete_sequence=['#ff9900'])
    fig_trend.update_layout(height=400, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.subheader("📂 Sales by Category")
    cat_sales = filtered_df.groupby('Category')['Amount'].sum().reset_index()
    fig_pie = px.pie(cat_sales, values='Amount', names='Category', hole=0.5, template="plotly_dark")
    fig_pie.update_layout(height=400, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 2: Location and Status
st.markdown("---")
c3, c4 = st.columns(2)

with c3:
    st.subheader("📍 Top 10 Cities by Revenue")
    city_sales = filtered_df.groupby('ship_city')['Amount'].sum().nlargest(10).reset_index()
    fig_city = px.bar(city_sales, x='Amount', y='ship_city', orientation='h', template="plotly_dark")
    fig_city.update_traces(marker_color='#37475a')
    st.plotly_chart(fig_city, use_container_width=True)

with c4:
    st.subheader("🚛 Logistics Fulfillment Mix")
    fig_status = px.bar(filtered_df['Fulfilment'].value_counts().reset_index(), 
                        x='Fulfilment', y='count', template="plotly_dark", color='Fulfilment')
    st.plotly_chart(fig_status, use_container_width=True)

# Row 3: Raw Data Table
st.subheader("🔍 Transaction Detail (Top 100)")
st.dataframe(
    filtered_df[['Order_ID', 'Date', 'Status', 'Category', 'Size', 'Amount', 'ship_city']].head(100),
    use_container_width=True
)

# Export Functionality
st.sidebar.markdown("---")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Download Filtered Data", data=csv, file_name="Amazon_Sales_Export.csv", mime="text/csv")