import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

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
    ticker1 = col2.text_input("Stock/ETF 1").upper()
    with col3:
        st.write("")
        st.markdown("<p style='text-align: center; font-size: 24px;'>_</p>", unsafe_allow_html=True)
    units2 = col4.number_input("Units", min_value=1, step=1, key="units2")
    ticker2 = col5.text_input("Stock/ETF 2").upper()
    
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
            st.error("")

st.divider()

# Historical Time Series Calculation
if st.session_state.pairs:

    try:
        # Fetch historical data and create required data
        data = yf.download([ticker1, ticker2], start=start_date, end=end_date)["Close"]
        data = data[[ticker1,ticker2]]
        data['Price ratio'] = data[ticker1]/data[ticker2]
        data["Pair value"] = data[ticker1]*units1 - data[ticker2]*units2
        
        # Display DataFrame
        #st.write("### Equation Value Time Series Table")
        #st.dataframe(data, use_container_width=True)
        
    except Exception as e:
        st.error(f"🚨 Error fetching historical data: {e}")

    try:
        returns = data[[ticker1, ticker2]].pct_change().dropna()
        cm_returns = (returns + 1).cumprod() - 1

        # Market Summary inside a dropdown
        with st.expander("View Market Summary"):
    
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

    

    try:
        # View Price Ratio inside a dropdown
        with st.expander("View Price Ratio"):
            st.subheader("Price Ratio")
        
            price_ratio = data[['Price ratio']]
    
            # Create a DataFrame for plotting
            price_ratio_df = pd.DataFrame({
                'Date': price_ratio.index,
                'Price ratio': price_ratio.values.flatten()
            })
    
            # Calculate the mean of the Price ratio
            mean_price_ratio = price_ratio_df['Price ratio'].mean()

            # Enter percentile input 
            # Create columns for layout
            col1, col2 = st.columns([1, 3])
            with col1:
                percentile = st.number_input("Select Percentile", min_value=1, max_value=50, value=5, step=1)
    
            # Calculate percentiles
            lower_percentile = price_ratio_df['Price ratio'].quantile(percentile / 100)
            upper_percentile = price_ratio_df['Price ratio'].quantile(1 - percentile / 100)   
            
            
    
            # Create Plotly figure
            fig2 = px.line(
                price_ratio_df,
                x="Date",
                y="Price ratio",
                title=f"Price ratio ({ticker1} / {ticker2})"
            )
    
            # Update the line color to a custom color (e.g., '#FF5733' for a shade of orange)
            fig2.update_traces(line=dict(color='#005fac'))
    
            # Add a horizontal line for the mean
            fig2.add_shape(
                type="line",
                x0=price_ratio_df['Date'].min(),
                x1=price_ratio_df['Date'].max(),
                y0=mean_price_ratio,
                y1=mean_price_ratio,
                line=dict(
                    color="white",
                    width=2,
                    dash="dot"
                ),
                name="Mean"
            )
    
            # Add horizontal lines for the percentiles
            fig2.add_shape(
                type="line",
                x0=price_ratio_df['Date'].min(),
                x1=price_ratio_df['Date'].max(),
                y0=lower_percentile,
                y1=lower_percentile,
                line=dict(
                    color="grey",
                    width=2
                ),
                name=f"{percentile}th Percentile"
            )
    
            fig2.add_shape(
                type="line",
                x0=price_ratio_df['Date'].min(),
                x1=price_ratio_df['Date'].max(),
                y0=upper_percentile,
                y1=upper_percentile,
                line=dict(
                    color="grey",
                    width=2
                ),
                name=f"{100 - percentile}th Percentile"
            )
    
            # Show chart in Streamlit
            st.plotly_chart(fig2)
        
    except Exception as e:
        st.error(f"🚨 Error analysing price ratio data: {e}")

    # Add a button to display the pair spread plot inside a dropdown
    with st.expander("View Pair Spread"):
    
        try:
            # Ensure the data is available
            if "Pair value" in data.columns:
    
                
                # Create a Plotly figure for the pair spread
                fig3 = px.line(
                    data.reset_index(),
                    x="Date",
                    y="Pair value",
                    title=f"Pair Spread: {units1} {ticker1} - {units2} {ticker2}"
                )
                
                # Show the plot in Streamlit
                st.plotly_chart(fig3)
            else:
                st.error("🚨 Pair value data is not available.")
        except Exception as e:
            st.error(f"🚨 Error displaying pair spread: {e}")


    # Add a button to display the pair spread plot inside a dropdown
    with st.expander("View Monte Carlo VaR"):
        try: 
            st.subheader("How much could I lose over a given period, for a given probability?")

            col1, col2, col3 = st.columns(3)
            with col1:
                analysis_period = st.number_input("Select Analysis Period (Days):", min_value=1, max_value=30, value=5)
            with col2:
                var_percentile = st.number_input("Select VaR Percentile:", min_value=0.01, max_value=99.99, value=95.00, format="%.2f")
            with col3:
                simulations = st.number_input("Number of Monte Carlo Simulations:", min_value=100, max_value=10000, value=2000)

            st.write("")
            try:
                # Button to Run Calculation
                if st.button("Calculate VaR"):
                    st.write("")
                    returns = data["Pair value"].pct_change(analysis_period).dropna()
                    mu, sigma = returns.mean(), returns.std()
                    st.dataframe(returns)
                    st.dataframe(data["Pair value"])
                    
                    
                    # Monte Carlo Simulation
                    simulated_returns = np.random.normal(mu, sigma, simulations)
                    VaR_value = np.percentile(simulated_returns, 100 - var_percentile) * 100
                    # Compute CVaR (Expected Shortfall)
                    CVaR_value = simulated_returns[simulated_returns < (VaR_value / 100)].mean() * 100
        
                    # Custom font color for stock name
                    stock_name_colored = f"<span style='color:white'><b> {units1} {ticker1} - {units2} {ticker2}</b></span>"
                    
                    # Create Interactive Histogram
                    fig = px.histogram(x=simulated_returns, nbins=50, title=f"Monte Carlo Simulated Returns: {stock_name_colored}", labels={"x": "Returns"}, opacity=0.7, color_discrete_sequence=["#6b5d50"])
                    fig.add_vline(x=VaR_value / 100, line=dict(color="red", width=2, dash="dash"))
                    fig.update_layout(xaxis_title="Returns", yaxis_title="Frequency", showlegend=False)
        
                    # Store in Session State
                    st.session_state.var_result = {
                        "VaR_value": VaR_value,
                        "CVaR_value": CVaR_value,
                        "var_percentile": var_percentile
                    }
        
                    st.session_state.histogram_fig = fig
                    st.session_state.data = returns  # Store historical returns for stress testing

                    if st.session_state.var_result:
                        st.plotly_chart(st.session_state.histogram_fig)
                        var_res = st.session_state.var_result
                        st.markdown(f"<h5>VaR {var_res['var_percentile']:.1f}:    <span style='font-size:32px; font-weight:bold; color:#FF5733;'>{var_res['VaR_value']:.1f}%</span></h5>", unsafe_allow_html=True)
                        st.write(f"**There is a {100-var_res['var_percentile']:.1f}% chance of losing more than {var_res['VaR_value']:.1f}% over the period.**")
                        st.write(f"**Expected Shortfall (CVaR) in worst cases: {var_res['CVaR_value']:.2f}%**")
                        st.caption("This helps to manage tail risk")
                    

            except Exception as e:
                st.error(f"🚨 Error displaying pair VaR: {e}")
                
        except Exception as e:
            st.error(f"🚨 Error displaying pair VaR: {e}")
            
                    
