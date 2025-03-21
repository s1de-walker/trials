
import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.express as px

#Libraries--------------------------------------------------------------------------------------

# Sidebar instructions-----------------------------------------------------------------------------

# Title
st.title("Pairs @ Risk")
st.write("")
st.write("")

if 'pairs' not in st.session_state:
    st.session_state.pairs = []


# Date Input Section
col_date1, col_date2 = st.columns(2)

# Default values (1-year difference)
default_start = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
default_end = datetime.today().strftime('%Y-%m-%d')

# Take user inputs for start and end date
start_date = col_date1.date_input("Start Date", datetime.strptime(default_start, '%Y-%m-%d'))
end_date = col_date2.date_input("End Date", datetime.strptime(default_end, '%Y-%m-%d'))

# Ensure start_date is before end_date
if start_date >= end_date:
    st.error("🚨 Start Date must be before End Date!")

# Calculate month difference
month_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
st.write(f"Selected period: **{month_diff} months**")

st.write("")
st.write("Enter the pair details:")

# Form for user input
with st.form("pairs_form"):
    col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 2, 3])
    
    units1 = col1.number_input("Units", min_value=1, step=1, key="units1")
    ticker1 = col2.text_input("Stock/ETF 1", key="SPY").upper()
    with col3:
        st.write("")
        st.markdown("<p style='text-align: center; font-size: 24px;'>_</p>", unsafe_allow_html=True)
    units2 = col4.number_input("Units", min_value=1, step=1, key="units2")
    ticker2 = col5.text_input("Stock/ETF 2", key="QQQ").upper()
    
    submit = st.form_submit_button("Confirm Pair")

    if submit and ticker1 is not None and ticker2 is not None:
        # Fetch latest stock prices from Yahoo Finance
        try:
            data = yf.download([ticker1, ticker2], start=start_date, end=end_date)["Close"]
            
            st.session_state.pairs.append({
                "Units 1": units1,
                "Stock/ETF 1": ticker1,
                "Units 2": units2,
                "Stock/ETF 2": ticker2,
            })
        except Exception as e:
            st.error(f"🚨 Error fetching data: {e}")



# Historical Time Series Calculation
if st.session_state.pairs:

    try:
        # Fetch historical data and create required data
        data = yf.download([ticker1, ticker2], start=start_date, end=end_date)["Close"]
        data = data[[ticker1,ticker2]]
        data['Price ratio'] = data[ticker1]/data[ticker2]
        data["Pair value"] = data[ticker1]*units1 - data[ticker2]*units2
        
        # Display DataFrame
        st.write("### Equation Value Time Series Table")
        st.dataframe(data, use_container_width=True)
        


    except Exception as e:
        st.error(f"🚨 Error fetching historical data: {e}")

    try:
        returns = data[[ticker1, ticker2]].pct_change().dropna()
        cm_returns = (returns + 1).cumprod() - 1
    
        # Plot cumulative returns
        st.subheader("Market Summary")

        # Fetch the last traded price (close) for each stock
        last_close_ticker1 = data[ticker1].iloc[-1]
        last_close_ticker2 = data[ticker2].iloc[-1]
        
        # Calculate the percentage change for each stock
        pct_change_ticker1 = returns[ticker1].iloc[-1] * 100
        pct_change_ticker2 = returns[ticker2].iloc[-1] * 100
        
        
        # Display metrics in two columns without labels
        col1, col2 = st.columns(2)
        
        col1.metric(f"{ticker1}", f"${last_close_ticker1:.2f}", f"{pct_change_ticker1:.2f}%")
        col2.metric(f"{ticker2}", f"${last_close_ticker2:.2f}", f"{pct_change_ticker2:.2f}%")

        # Reshape data for Plotly
        cm_returns_melted = cm_returns.reset_index().melt(id_vars="Date", var_name="Stock", value_name="Cumulative Return")
        
        # Define custom colors
        color_map = {
            cm_returns.columns[0]: "#fb580d",  # Fiery Orange
            cm_returns.columns[1]: "#5cc8e2",  # Electric Blue
        }
        
        # Create Plotly figure
        fig = px.line(
            cm_returns_melted,
            x="Date",
            y="Cumulative Return",
            color="Stock",
            title="Cumulative Returns",
            color_discrete_map=color_map
        )
        
        # Show chart in Streamlit
        st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"🚨 Error analysing data: {e}")

st.divider()
