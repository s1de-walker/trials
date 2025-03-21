
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

    if submit and stock1 and stock2:
        # Fetch latest stock prices from Yahoo Finance
        try:
            data = yf.download([ticker1, ticker2], start=start_date, end=end_date)["Close"]
            
            st.session_state.pairs.append({
                "Units 1": units1,
                "Stock/ETF 1": ticker1,
                "Price 1": round(price1, 2),
                "Units 2": units2,
                "Stock/ETF 2": ticker2,
                "Price 2": round(price2, 2),
            })
        except Exception as e:
            st.error(f"🚨 Error fetching data: {e}")




# Historical Time Series Calculation
if st.session_state.pairs:
    st.write("### Equation Value Time Series")

    try:
        # Fetch historical data
        df1 = yf.download(stock1, start=start_date, end=end_date)['Close']
        df2 = yf.download(stock2, start=start_date, end=end_date)['Close']
        st.write(df1*units1)
        st.write(df2.tail()*units2)
        # Compute the equation time series while keeping it as a DataFrame
        equation_df = (units1 * df1[['Close']]) - (units2 * df2[['Close']])
        
        # Display DataFrame
        st.write("### Equation Value Time Series Table")
        st.dataframe(equation_df, use_container_width=True)

        # Plot the time series
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equation_df.index, y=equation_df["Equation Value"], mode='lines', name='Equation Value'))
        fig.update_layout(title="Equation Value Over Time",
                          xaxis_title="Date",
                          yaxis_title="Value",
                          template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"🚨 Error fetching historical data: {e}")
