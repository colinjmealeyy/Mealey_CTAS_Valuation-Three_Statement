import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize, root_scalar
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CINTAS (CTAS) Advanced Valuation", layout="wide", page_icon="👔")

st.markdown("""
<style>
.metric-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}
.metric-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-left: 5px solid #005A9C;
    text-align: center;
    flex: 1;
    margin: 0 10px;
}
.metric-card h4 {
    margin: 0;
    color: #6c757d;
    font-size: 14px;
    text-transform: uppercase;
}
.metric-card h2 {
    margin: 10px 0 0 0;
    color: #212529;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)

st.title("👔 CINTAS (CTAS) Advanced Valuation Model")
st.markdown("A specialized DCF & Monte Carlo modeling tool designed for Cintas's sticky, recurring revenue model.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("1. Fundamental Drivers")
retention_rate = st.sidebar.slider("Retention Rate (%)", 80.0, 99.0, 95.0, 0.5) / 100.0
price_increase = st.sidebar.slider("Annual Price Increase (%)", 0.0, 8.0, 3.5, 0.5) / 100.0
new_adds_pct = st.sidebar.slider("New Adds (as % of Prev Rev)", 0.0, 10.0, 7.0, 0.5) / 100.0
ma_spend_pct = st.sidebar.slider("M&A Spend (% of Rev)", 0.0, 10.0, 2.0, 0.5) / 100.0
ma_sales_to_cap = st.sidebar.slider("M&A Sales-to-Capital Ratio", 1.0, 4.0, 1.5, 0.1)

st.sidebar.header("2. Margin & Reinvestment")
operating_margin = st.sidebar.slider("Operating Margin (%)", 15.0, 30.0, 21.0, 0.5) / 100.0
margin_expansion_bps = st.sidebar.slider("Annual Margin Expansion (bps)", 0, 50, 10, 5)
tax_rate = st.sidebar.slider("Tax Rate (%)", 10.0, 30.0, 16.0, 0.5) / 100.0
sales_to_capital = st.sidebar.slider("Organic Sales-to-Capital", 1.0, 5.0, 3.0, 0.1)
dna_pct_rev = st.sidebar.slider("D&A as % of Revenue", 1.0, 8.0, 3.5, 0.1) / 100.0

st.sidebar.header("3. Cost of Capital")
wacc = st.sidebar.slider("WACC / Discount Rate (%)", 5.0, 12.0, 7.5, 0.1) / 100.0
terminal_roic = st.sidebar.slider("Terminal ROIC (%)", 10.0, 40.0, 25.0, 1.0) / 100.0
terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", 1.0, 5.0, 2.5, 0.1) / 100.0

st.sidebar.header("4. Valuation & Margin of Safety")
margin_of_safety = st.sidebar.slider("Required Margin of Safety (%)", 0.0, 50.0, 20.0, 5.0) / 100.0


@st.cache_data
def get_ctas_data():
    ticker = yf.Ticker("CTAS")
    info = ticker.info
    
    current_price = info.get('currentPrice')
    shares = info.get('sharesOutstanding')
    cash = info.get('totalCash') or 0
    debt = info.get('totalDebt') or 0
    revenue = info.get('totalRevenue') or 9500000000 # fallback if none
    
    # Try fetching from financials if info is missing
    if current_price is None:
        try:
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[0]
        except:
             current_price = 700 # Fallback
             
    if shares is None or revenue is None:
        try:
             fin = ticker.financials
             revenue = fin.loc['Total Revenue'].iloc[0]
             shares = info.get('impliedSharesOutstanding') or 100000000
        except:
             pass

    return {
        'price': current_price,
        'shares': shares,
        'cash': cash,
        'debt': debt,
        'revenue': revenue
    }

data_load_state = st.text('Loading CTAS Financials...')
ctas_data = get_ctas_data()
data_load_state.empty()

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card"><h4>Current Price</h4><h2>${ctas_data['price']:.2f}</h2></div>
    <div class="metric-card"><h4>TTM Revenue</h4><h2>${ctas_data['revenue']:,.0f}</h2></div>
    <div class="metric-card"><h4>Total Cash</h4><h2>${ctas_data['cash']:,.0f}</h2></div>
    <div class="metric-card"><h4>Total Debt</h4><h2>${ctas_data['debt']:,.0f}</h2></div>
</div>
""", unsafe_allow_html=True)


# --- Core DCF Engine ---
def run_dcf(rev_base, ret_rate, px_inc, new_add, ма_pct, ma_stc,
            op_mgn, margin_exp_bps, t_rate, stc, dna_pct, wacc_val, t_roic, t_g):
    
    years = 15
    revs = []
    ebits = []
    nopats = []
    reinvestments = []
    fcfs = []
    
    prev_rev = rev_base
    for i in range(years):
        # Organic Revenue
        existing_rev = prev_rev * ret_rate * (1 + px_inc)
        new_rev = prev_rev * new_add
        
        # M&A additions
        ma_spend = prev_rev * ма_pct
        ma_rev = ma_spend * ma_stc
        
        current_rev = existing_rev + new_rev + ma_rev
        revs.append(current_rev)
        
        # Operating Income & NOPAT
        current_op_mgn = min(op_mgn + (i * (margin_exp_bps / 10000.0)), 0.35) # Cap margin at 35%
        ebit = current_rev * current_op_mgn
        nopat = ebit * (1 - t_rate)
        
        ebits.append(ebit)
        nopats.append(nopat)
        
        # Reinvestment via Sales to capital
        delta_rev = current_rev - prev_rev
        reinv_organic = delta_rev / stc
        total_reinv = reinv_organic + ma_spend 
        
        reinvestments.append(total_reinv)
        
        # Free Cash Flow
        fcf = nopat - total_reinv
        fcfs.append(fcf)
        
        prev_rev = current_rev

    # Discounting
    dfs = [1 / ((1 + wacc_val)**(i+1)) for i in range(years)]
    pv_fcfs = [fcf * df for fcf, df in zip(fcfs, dfs)]
    
    # Terminal Value
    terminal_reinvestment_rate = t_g / t_roic
    terminal_nopat = nopats[-1] * (1 + t_g)
    terminal_reinvestment = terminal_nopat * terminal_reinvestment_rate
    
    # Implied Capex / D&A Check
    terminal_dna = revs[-1] * (1 + t_g) * dna_pct
    implied_terminal_capex = terminal_reinvestment + terminal_dna
    terminal_capex_to_dna = implied_terminal_capex / terminal_dna if terminal_dna > 0 else 0
    
    terminal_fcf = terminal_nopat * (1 - terminal_reinvestment_rate)
    
    terminal_value = terminal_fcf / (wacc_val - t_g)
    pv_tv = terminal_value * dfs[-1]
    
    ev = sum(pv_fcfs) + pv_tv
    equity_val = ev + ctas_data['cash'] - ctas_data['debt']
    share_price = equity_val / ctas_data['shares']
    
    return {
        'revenues': revs,
        'ebits': ebits,
        'nopats': nopats,
        'reinvestments': reinvestments,
        'fcfs': fcfs,
        'pv_fcfs': pv_fcfs,
        'tv': terminal_value,
        'pv_tv': pv_tv,
        'ev': ev,
        'eq': equity_val,
        'price': share_price,
        'term_capex_dna_ratio': terminal_capex_to_dna
    }

base_model = run_dcf(
    ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
    ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
    wacc, terminal_roic, terminal_growth
)


st.header("1. DCF Valuation Outputs")
col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"${base_model['ev']:,.0f}")
col2.metric("Equity Value", f"${base_model['eq']:,.0f}")

premium_discount = (base_model['price'] / ctas_data['price'] - 1) * 100
col3.metric("Implied Share Price", f"${base_model['price']:.2f}", f"{premium_discount:.1f}% vs Market")

st.markdown(f"**Sanity Check**: Implied Terminal Capex / D&A Ratio is **{base_model['term_capex_dna_ratio']:.2f}x** (Typically ~1.0x - 1.5x in steady state)")

with st.expander("View Projected Cash Flows"):
    df_proj = pd.DataFrame({
        "Revenue": base_model['revenues'],
        "EBIT": base_model['ebits'],
        "NOPAT": base_model['nopats'],
        "Reinvestment": base_model['reinvestments'],
        "FCF": base_model['fcfs'],
        "PV of FCF": base_model['pv_fcfs']
    }, index=[f"Year {i+1}" for i in range(15)])
    
    st.dataframe(df_proj.style.format("${:,.0f}"))


st.header("2. Reverse DCF Analysis")
st.markdown("Cintas often trades at a premium. Let's find out what **Operating Margin Expansion** or **Retention Rate** is currently priced in.")

def reverse_dcf_margin(target_margin):
    res = run_dcf(
        ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
        ma_spend_pct, ma_sales_to_cap, target_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
        wacc, terminal_roic, terminal_growth
    )
    return res['price'] - ctas_data['price']

def reverse_dcf_retention(target_ret):
    res = run_dcf(
        ctas_data['revenue'], target_ret, price_increase, new_adds_pct,
        ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
        wacc, terminal_roic, terminal_growth
    )
    return res['price'] - ctas_data['price']

col_rev1, col_rev2 = st.columns(2)

try:
    implied_margin = root_scalar(reverse_dcf_margin, bracket=[0.05, 0.50], method='brentq').root
    col_rev1.metric("Priced-in Operating Margin", f"{implied_margin*100:.1f}%", f"{(implied_margin - operating_margin)*100:.1f}% vs Base")
except Exception as e:
    col_rev1.error("Could not converge on Margin")

try:
    implied_retention = root_scalar(reverse_dcf_retention, bracket=[0.50, 1.20], method='brentq').root
    col_rev2.metric("Priced-in Retention Rate", f"{implied_retention*100:.1f}%", f"{(implied_retention - retention_rate)*100:.1f}% vs Base")
except:
    col_rev2.error("Could not converge on Retention")


st.header("3. Scenario Analysis")
st.markdown("Sensitizing non-traditional valuation metrics.")

col_sens1, col_sens2 = st.columns(2)

# Sens 1: Retention vs Margin
with col_sens1:
    st.subheader("Retention vs Operating Margin")
    ret_range = np.array([-0.04, -0.02, 0.0, 0.02, 0.04]) + retention_rate
    mgn_range = np.array([-0.04, -0.02, 0.0, 0.02, 0.04]) + operating_margin
    
    sens_table = []
    for r in ret_range:
        row = []
        for m in mgn_range:
            res = run_dcf(ctas_data['revenue'], r, price_increase, new_adds_pct,
                           ma_spend_pct, ma_sales_to_cap, m, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
                           wacc, terminal_roic, terminal_growth)
            row.append(res['price'])
        sens_table.append(row)
        
    df_sens = pd.DataFrame(sens_table, 
                           index=[f"{r*100:.1f}%" for r in ret_range],
                           columns=[f"{m*100:.1f}%" for m in mgn_range])
    
    st.dataframe(df_sens.style.background_gradient(cmap='RdYlGn', axis=None).format("${:.2f}"))

# Sens 2: Sales-to-Capital vs Terminal ROIC
with col_sens2:
    st.subheader("Organic Sales-to-Capital vs. Terminal ROIC")
    stc_range = np.array([-0.5, -0.25, 0.0, 0.25, 0.5]) + sales_to_capital
    roic_range = np.array([-0.05, -0.025, 0.0, 0.025, 0.05]) + terminal_roic
    
    sens_table2 = []
    for s in stc_range:
        row = []
        for vR in roic_range:
            res = run_dcf(ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
                           ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, s, dna_pct_rev,
                           wacc, vR, terminal_growth)
            row.append(res['price'])
        sens_table2.append(row)
        
    df_sens2 = pd.DataFrame(sens_table2, 
                           index=[f"{s:.1f}x" for s in stc_range],
                           columns=[f"{vR*100:.1f}%" for vR in roic_range])
    
    st.dataframe(df_sens2.style.background_gradient(cmap='RdYlGn', axis=None).format("${:.2f}"))


st.header("4. Monte Carlo Simulation")
st.markdown("Randomizing core drivers across 2,000 iterations assuming normal distributions.")

if st.button("Run Monte Carlo"):
    with st.spinner("Running 2,000 simulations..."):
        iterations = 2000
        
        # Random Distributions
        sim_ret = np.random.normal(retention_rate, 0.015, iterations)
        sim_px = np.random.normal(price_increase, 0.01, iterations)
        sim_mgn = np.random.normal(operating_margin, 0.02, iterations)
        sim_stc = np.random.normal(sales_to_capital, 0.3, iterations)
        
        sim_prices = []
        for i in range(iterations):
            r = min(max(sim_ret[i], 0.7), 1.1)
            p = min(max(sim_px[i], -0.05), 0.1)
            m = min(max(sim_mgn[i], 0.05), 0.4)
            s = min(max(sim_stc[i], 0.5), 6.0)
            
            res = run_dcf(ctas_data['revenue'], r, p, new_adds_pct,
                           ma_spend_pct, ma_sales_to_cap, m, margin_expansion_bps, tax_rate, s, dna_pct_rev,
                           wacc, terminal_roic, terminal_growth)
            sim_prices.append(res['price'])
            
        p10 = np.percentile(sim_prices, 10)
        p50 = np.percentile(sim_prices, 50)
        p90 = np.percentile(sim_prices, 90)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("10th Percentile (Bear)", f"${p10:.2f}")
        col_m2.metric("Median (Expected)", f"${p50:.2f}")
        col_m3.metric("90th Percentile (Bull)", f"${p90:.2f}")

        # Plotly Histogram
        fig = px.histogram(sim_prices, nbins=50, 
                           title="Distribution of Implied Share Prices",
                           labels={'value': 'Implied Share Price ($)', 'count': 'Frequency'}, # This does not work perfectly with x value in newer plotly, better not use it if we get an issue, but standard is fine
                           color_discrete_sequence=['#005A9C'])
                           
        fig.add_vline(x=ctas_data['price'], line_dash="dash", line_color="black", annotation_text="Market Price", annotation_position="top right")
        fig.add_vline(x=p50, line_dash="dot", line_color="orange", annotation_text="Median DCF", annotation_position="top left")
        
        fig.update_layout(showlegend=False, xaxis_title="Implied Share Price ($)", yaxis_title="Frequency")
        st.plotly_chart(fig, use_container_width=True)

# --- NEW SECTION 5: STRATEGIC CONSIDERATIONS ---
st.header("5. Strategic Considerations & Margin of Safety")

col_strat1, col_strat2 = st.columns(2)

with col_strat1:
    st.subheader("🤖 AI & Route Optimization")
    st.info("Cintas's dense route network is highly conducive to AI optimization. By utilizing predictive analytics, automated sorting in facilities, and dynamic route adjustments, CTAS can achieve significant operating leverage, directly translating topline growth into higher operating margins without a proportional increase in assets or fuel costs.")
    
    st.subheader("👔 Management Alignment")
    st.success("Historically, CTAS management compensation has been heavily weighted toward EPS growth and ROIC (Return on Invested Capital). This ensures management doesn't just chase 'topline vanity' via acquisitions but focuses on profitable growth that benefits shareholders.")

with col_strat2:
    st.subheader("🛡️ Target Buy Price")
    st.markdown(f"Using your DCF implied price of **${base_model['price']:.2f}** and requiring a **{margin_of_safety*100:.0f}%** margin of safety for downside protection:")
    
    target_buy_price = base_model['price'] * (1 - margin_of_safety)
    
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #28a745; margin-top: 20px;">
        <h4>Entry Price Threshold</h4>
        <h2 style="color: #28a745;">${target_buy_price:.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if ctas_data['price'] <= target_buy_price:
        st.success(f"Current price of **${ctas_data['price']:.2f}** is below your buy threshold! Favorable risk/reward.")
    else:
        st.warning(f"Current price of **${ctas_data['price']:.2f}** is above your buy threshold. The stock is currently overvalued relative to your required risk compensation.")


# --- NEW SECTION 6: RELATIVE VALUATION ---
st.header("6. Relative Valuation (Forward P/E)")
st.markdown("Comparing CTAS's forward multiples to its closest competitor (UniFirst - UNI) and the S&P 500 (SPY).")

@st.cache_data
def get_forward_pe_data():
    try:
        ctas = yf.Ticker("CTAS").info.get('forwardPE', 0)
        uni = yf.Ticker("UNI").info.get('forwardPE', 0)
        spy = yf.Ticker("SPY").info.get('forwardPE', 21.0) # SPY info might be tricky, hardcode fallback
        if spy == 0:
             spy = 21.0
        return {"CTAS": ctas, "UNI": uni, "S&P 500": spy}
    except:
        return {"CTAS": 45.0, "UNI": 25.0, "S&P 500": 21.0}

pe_data = get_forward_pe_data()

col_pe1, col_pe2 = st.columns([1, 2])

with col_pe1:
    st.metric("CTAS Forward P/E", f"{pe_data['CTAS']:.1f}x")
    st.metric("UniFirst (UNI) Forward P/E", f"{pe_data['UNI']:.1f}x")
    st.metric("S&P 500 Forward P/E", f"{pe_data['S&P 500']:.1f}x")

with col_pe2:
    if pe_data['CTAS'] > 0:
        fig_pe = px.bar(
            x=list(pe_data.keys()), 
            y=list(pe_data.values()),
            title="Forward P/E Comparison",
            labels={'x': 'Asset', 'y': 'Forward P/E Ratio'},
            color=list(pe_data.keys()),
            color_discrete_map={"CTAS": "#005A9C", "UNI": "#6c757d", "S&P 500": "#28a745"}
        )
        fig_pe.update_layout(showlegend=False)
        st.plotly_chart(fig_pe, use_container_width=True)

st.markdown("### Conclusion on Multiples")
if pe_data['CTAS'] > pe_data['UNI']:
    st.write(f"CTAS trades at a significant premium (**{pe_data['CTAS']:.1f}x** vs UNI's **{pe_data['UNI']:.1f}x**). This reflects the market's high confidence in Cintas's operational excellence, tech adoption (AI routing), and historical execution, but requires flawless future performance to justify.")
else:
    st.write("CTAS is trading at a discount or in-line with peers.")
