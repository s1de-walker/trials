# Libraries
# ------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go


# Input
# ------------------------------------
# Title
st.title("Pairs @ Risk")
st.caption("Monitor your trading pairs with risk metrics and alerts.")
st.write("")

if 'pairs' not in st.session_state:
    st.session_state.pairs = []

# Date Input Section
col_date1, col_date2 = st.columns(2)

# Default values (1-year difference)
default_start = (datetime.today() - timedelta(days=730)).strftime('%Y-%m-%d')
default_end = datetime.today().strftime('%Y-%m-%d')

# Take user inputs for start and end date
start_date = col_date1.date_input("Start Date", datetime.strptime(default_start, '%Y-%m-%d'))
end_date = col_date2.date_input("End Date", datetime.strptime(default_end, '%Y-%m-%d'))

# Ensure start_date is before end_date
if start_date >= end_date:
    st.error("🚨 Start Date must be before End Date!")
    st.stop()  # Stops execution immediately after showing error

# Calculate month difference
st.write(f"Selected period: **{(end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)} months**")

st.write("")
st.write("Enter the pair details:")

# Form for user input
with st.form("pairs_form"):
    col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 2, 3])
    
    units1 = col1.number_input("Units", min_value=1, step=1, key="units1")
    ticker1 = col2.text_input("Stock/ETF 1").upper()
    with col3:
        st.write("")
        st.markdown("<p style='text-align: center; font-size: 24px;'>_</p>", unsafe_allow_html=True)
    units2 = col4.number_input("Units", min_value=1, step=1, key="units2")
    ticker2 = col5.text_input("Stock/ETF 2").upper()
    
    submit = st.form_submit_button("Confirm Pair")

    if submit and ticker1 == ticker2:
            st.error("🚨 Error: Both tickers cannot be the same! Please select different stocks or ETFs.")
            st.stop()  # Stops execution immediately after showing error

    if submit and ticker1 and ticker2:
        st.session_state.pairs.append({"Units 1": units1, "Stock/ETF 1": ticker1, "Units 2": units2, "Stock/ETF 2": ticker2})

    
st.divider()
# Input End------------------------------------


# Fetching data
# ------------------------------------
# Historical Time Series Calculation
if st.session_state.pairs:

    try:
        # Fetch historical data and create required data
        data = yf.download([ticker1, ticker2], start=start_date, end=end_date)["Close"]
        data = data[[ticker1,ticker2]]
        data['Price Ratio'] = data[ticker1]/data[ticker2]
        data["Pair Value"] = data[ticker1]*units1 - data[ticker2]*units2
        # Check if data is empty (invalid ticker)
        if data.empty or ticker1 not in data.columns or ticker2 not in data.columns:
            st.error("🚨 Error: One or both tickers are invalid. Please enter correct stock/ETF symbols.")
            st.stop()  # Stop execution if tickers are invalid
        
    except Exception as e:
        st.error(f"🚨 Error fetching historical data: {e}")
        st.stop()  # Stops execution immediately after showing error
        
    returns = data[[ticker1, ticker2]].pct_change().dropna()
    cm_returns = (returns + 1).cumprod() - 1

    # Market Summary
    # ------------------------------------
    with st.expander(f"Market Summary"):
        col1, col2 = st.columns(2)
        col1.metric(f"{ticker1}", f"${data[ticker1].iloc[-1]:.2f}", f"{returns[ticker1].iloc[-1] * 100:.2f}%")
        col2.metric(f"{ticker2}", f"${data[ticker2].iloc[-1]:.2f}", f"{returns[ticker2].iloc[-1] * 100:.2f}%")
    # Price Ratio
    # ------------------------------------
    with st.expander(f"Price Ratio"):
        mean_ratio = data['Price Ratio'].mean()
        col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 2, 3])
        percentile = col1.number_input("Select Percentile:", min_value=50.00, max_value=99.99, value=95.00, format="%.2f")
        upper_bound = np.percentile(data['Price Ratio'], 100-percentile)
        lower_bound = np.percentile(data['Price Ratio'], percentile)
    
        fig = px.line(data, x=data.index, y='Price Ratio', title=f"Price Ratio ({ticker1}/{ticker2})", line_shape='linear')
        fig.update_traces(line=dict(color='#A55B4B'))  # Custom orange-red color for better contrast
        
        # Mean line with annotation on the left
        fig.add_hline(y=mean_ratio, line_dash="dot", line_color="white", line_width=1.5)
        fig.add_annotation(
            x=data.index.min(), y=mean_ratio, text="Mean",
            showarrow=False, xanchor="left", font=dict(color="grey", size=10), bgcolor="black"
        )
    
        # Lower Bound with annotation on the left
        fig.add_hline(y=lower_bound, line_dash="solid", line_color="#F2F2F2", line_width=1.5)
        fig.add_annotation(
            x=data.index.min(), y=lower_bound, text=f"{percentile}th Percentile",
            showarrow=False, xanchor="left", font=dict(color="grey", size=10), bgcolor="black"
        )
    
        # Upper Bound with annotation on the left
        fig.add_hline(y=upper_bound, line_dash="solid", line_color="#F2F2F2", line_width=1.5)
        fig.add_annotation(
            x=data.index.min(), y=upper_bound, text=f"{100 - percentile}th Percentile",
            showarrow=False, xanchor="left", font=dict(color="grey", size=10), bgcolor="black"
        )
    
        st.plotly_chart(fig)
        
        if data['Price Ratio'].iloc[-1] < lower_bound:
            st.success("✅ Long Signal: Price Ratio below lower bound")
        elif data['Price Ratio'].iloc[-1] > upper_bound:
            st.warning("⚠️ Short Signal: Price Ratio above upper bound")
            
    # Pair spread
    # ------------------------------------
    with st.expander(f"Pair Spread"):
        fig_spread = px.line(data, x=data.index, y='Pair Value', title=f"Pair Spread: {units1} {ticker1} - {units2} {ticker2}", line_shape='linear')
        fig_spread.update_traces(line=dict(color='#4A4A4A'))  
        st.plotly_chart(fig_spread)
