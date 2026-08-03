import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import root_scalar
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CINTAS (CTAS) Advanced Valuation & 3-Statement Model", layout="wide", page_icon="👔")

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
    font-size: 13px;
    text-transform: uppercase;
}
.metric-card h2 {
    margin: 8px 0 0 0;
    color: #212529;
    font-size: 22px;
}
.status-balanced {
    background-color: #e8f5e9;
    border-left: 5px solid #28a745;
    padding: 10px 15px;
    border-radius: 6px;
    color: #1b5e20;
    font-weight: bold;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("👔 CINTAS (CTAS) Integrated Valuation & Three-Statement Model")
st.markdown("An institutional-grade **Three-Statement Model & Discounted Cash Flow (DCF)** valuation suite tailored for Cintas's sticky, high-ROIC recurring revenue model.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("1. Fundamental Revenue Drivers")
retention_rate = st.sidebar.slider("Retention Rate (%)", 80.0, 99.0, 94.0, 0.5) / 100.0
price_increase = st.sidebar.slider("Annual Price Increase (%)", 0.0, 8.0, 3.5, 0.5) / 100.0
new_adds_pct = st.sidebar.slider("New Adds (as % of Prev Rev)", 0.0, 10.0, 6.0, 0.5) / 100.0
ma_spend_pct = st.sidebar.slider("M&A Spend (% of Rev)", 0.0, 10.0, 2.0, 0.5) / 100.0
ma_sales_to_cap = st.sidebar.slider("M&A Sales-to-Capital Ratio", 1.0, 4.0, 2.5, 0.1)

st.sidebar.header("2. Operating Margins & Reinvestment")
operating_margin = st.sidebar.slider("Operating Margin (%)", 15.0, 30.0, 21.5, 0.5) / 100.0
margin_expansion_bps = st.sidebar.slider("Annual Margin Expansion (bps)", 0, 50, 10, 5)
tax_rate = st.sidebar.slider("Tax Rate (%)", 10.0, 30.0, 16.0, 0.5) / 100.0
sales_to_capital = st.sidebar.slider("Organic Sales-to-Capital", 1.0, 5.0, 3.0, 0.1)
dna_pct_rev = st.sidebar.slider("D&A as % of Revenue", 1.0, 8.0, 3.5, 0.1) / 100.0

st.sidebar.header("3. Capital Structure & 3-Statement Inputs")
div_payout_ratio = st.sidebar.slider("Dividend Payout Ratio (% Net Income)", 0.0, 60.0, 30.0, 2.5) / 100.0
share_buyback_pct = st.sidebar.slider("Share Buybacks (% Net Income)", 0.0, 60.0, 35.0, 2.5) / 100.0
debt_interest_rate = st.sidebar.slider("Interest Rate on Debt (%)", 1.0, 8.0, 4.5, 0.25) / 100.0
cash_yield = st.sidebar.slider("Yield on Cash (%)", 0.0, 6.0, 3.5, 0.25) / 100.0
dso_days = st.sidebar.slider("Accounts Receivable DSO (Days)", 20, 75, 45, 1)
inventory_pct = st.sidebar.slider("Inventory (% Revenue)", 1.0, 10.0, 4.5, 0.5) / 100.0
ap_days = st.sidebar.slider("Accounts Payable DPO (Days)", 15, 60, 30, 1)

st.sidebar.header("4. Cost of Capital & DCF Assumptions")
wacc = st.sidebar.slider("WACC / Discount Rate (%)", 5.0, 12.0, 7.5, 0.1) / 100.0
terminal_roic = st.sidebar.slider("Terminal ROIC (%)", 10.0, 40.0, 27.0, 1.0) / 100.0
terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", 1.0, 5.0, 2.5, 0.1) / 100.0

# --- DATA FETCHING ---
def get_ctas_data():
    ticker = yf.Ticker("CTAS")
    info = ticker.info
    
    current_price = info.get('currentPrice')
    shares = info.get('sharesOutstanding')
    cash = info.get('totalCash') or 289000000
    debt = info.get('totalDebt') or 2705000000
    revenue = info.get('totalRevenue') or 11260000000 # fallback baseline
    
    if current_price is None:
        try:
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[0]
        except:
             current_price = 700.0
             
    if shares is None or shares == 0:
        shares = 400147000

    return {
        'price': float(current_price),
        'shares': float(shares),
        'cash': float(cash),
        'debt': float(debt),
        'revenue': float(revenue)
    }

data_load_state = st.text('Loading CTAS Live Financials...')
ctas_data = get_ctas_data()
data_load_state.empty()

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card"><h4>Market Price</h4><h2>${ctas_data['price']:.2f}</h2></div>
    <div class="metric-card"><h4>TTM Revenue</h4><h2>${ctas_data['revenue']:,.0f}</h2></div>
    <div class="metric-card"><h4>Total Cash</h4><h2>${ctas_data['cash']:,.0f}</h2></div>
    <div class="metric-card"><h4>Total Debt</h4><h2>${ctas_data['debt']:,.0f}</h2></div>
</div>
""", unsafe_allow_html=True)


# --- INTEGRATED THREE-STATEMENT MODEL & DCF ENGINE ---
def run_integrated_model(rev_base, ret_rate, px_inc, new_add, ma_pct, ma_stc,
                         op_mgn, margin_exp_bps, t_rate, stc, dna_pct,
                         div_payout, buyback_pct, debt_rate, c_yield,
                         dso, inv_pct, ap_d,
                         wacc_val, t_roic, t_g):
    
    years = 15
    
    # Financial Statement Arrays
    # 1. Income Statement
    revs, op_costs, ebits, dnas, ebitdas = [], [], [], [], []
    int_expenses, int_incomes, net_interests, ebts, tax_expenses, net_incomes = [], [], [], [], [], []
    
    # 2. Cash Flow Statement
    cfos, cfis, cffs, net_change_cashes = [], [], [], []
    capexs, ma_spends, dividends_paid, buybacks_paid = [], [], [], []
    delta_nwcs = []
    
    # 3. Balance Sheet
    cashes, ars, inventories, net_ppes, intangibles, total_assets = [], [], [], [], [], []
    aps, debts, total_liabilities = [], [], []
    common_stocks, retained_earnings, total_equities, bs_checks = [], [], [], []
    
    # 4. DCF arrays
    nopats, reinvestments, fcfs = [], [], []
    
    # Baseline Year 0 Initialization (from CTAS actual financial structure)
    prev_rev = rev_base
    prev_cash = ctas_data['cash']
    prev_debt = ctas_data['debt']
    prev_ar = prev_rev * (dso / 365.0)
    prev_inv = prev_rev * inv_pct
    prev_nppe = prev_rev * 0.35
    prev_intangibles = prev_rev * 0.40
    prev_ap = prev_rev * (ap_d / 365.0)
    
    # Base Year Equity & Retained Earnings
    prev_total_assets = prev_cash + prev_ar + prev_inv + prev_nppe + prev_intangibles
    prev_total_liab = prev_ap + prev_debt
    prev_common_stock = prev_total_assets * 0.10
    prev_retained_earnings = prev_total_assets - prev_total_liab - prev_common_stock
    
    for i in range(years):
        # --- INCOME STATEMENT ---
        existing_rev = prev_rev * ret_rate * (1 + px_inc)
        new_rev = prev_rev * new_add
        ma_spend = prev_rev * ma_pct
        ma_rev = ma_spend * ma_stc
        
        current_rev = existing_rev + new_rev + ma_rev
        revs.append(current_rev)
        
        current_op_mgn = min(op_mgn + (i * (margin_exp_bps / 10000.0)), 0.35)
        ebit = current_rev * current_op_mgn
        ebits.append(ebit)
        
        dna = current_rev * dna_pct
        dnas.append(dna)
        ebitda = ebit + dna
        ebitdas.append(ebitda)
        
        op_cost = current_rev - ebit
        op_costs.append(op_cost)
        
        # Interest Calculations based on previous year balances
        int_exp = prev_debt * debt_rate
        int_inc = prev_cash * c_yield
        net_int = int_exp - int_inc
        
        int_expenses.append(int_exp)
        int_incomes.append(int_inc)
        net_interests.append(net_int)
        
        ebt = ebit - net_int
        ebts.append(ebt)
        
        tax_exp = max(ebt * t_rate, 0.0)
        tax_expenses.append(tax_exp)
        
        net_inc_val = ebt - tax_exp
        net_incomes.append(net_inc_val)
        
        # NOPAT for DCF
        nopat = ebit * (1 - t_rate)
        nopats.append(nopat)
        
        # --- REINVESTMENT & CAPEX ---
        delta_rev = current_rev - prev_rev
        reinv_organic = delta_rev / stc
        implicit_total_reinv = reinv_organic + ma_spend 
        
        target_capex = dna
        implicit_capex = implicit_total_reinv + dna
        weight = i / (years - 1)
        actual_capex = implicit_capex * (1 - weight) + target_capex * weight
        capexs.append(actual_capex)
        ma_spends.append(ma_spend)
        
        actual_reinv = actual_capex - dna
        reinvestments.append(actual_reinv)
        
        # Free Cash Flow to Firm (DCF)
        fcf = nopat - actual_reinv
        fcfs.append(fcf)
        
        # --- BALANCE SHEET & WORKING CAPITAL DYNAMICS ---
        ar = current_rev * (dso / 365.0)
        inv = current_rev * inv_pct
        ap = current_rev * (ap_d / 365.0)
        
        ars.append(ar)
        inventories.append(inv)
        aps.append(ap)
        
        delta_ar = ar - prev_ar
        delta_inv = inv - prev_inv
        delta_ap = ap - prev_ap
        
        delta_nwc = (delta_ar + delta_inv) - delta_ap
        delta_nwcs.append(delta_nwc)
        
        # Net PP&E roll-forward
        net_nppe = prev_nppe + actual_capex - dna
        net_ppes.append(net_nppe)
        
        # Intangibles roll-forward
        net_intangibles = prev_intangibles + ma_spend
        intangibles.append(net_intangibles)
        
        # --- CASH FLOW STATEMENT ---
        cfo = net_inc_val + dna - delta_nwc
        cfos.append(cfo)
        
        cfi = -(actual_capex + ma_spend)
        cfis.append(cfi)
        
        div_paid = max(net_inc_val * div_payout, 0.0)
        buyback_paid = max(net_inc_val * buyback_pct, 0.0)
        dividends_paid.append(div_paid)
        buybacks_paid.append(buyback_paid)
        
        # Debt changes (assuming stable debt schedule unless cash depleted)
        delta_debt = 0.0
        cff = delta_debt - div_paid - buyback_paid
        cffs.append(cff)
        
        net_change_cash = cfo + cfi + cff
        net_change_cashes.append(net_change_cash)
        
        ending_cash = prev_cash + net_change_cash
        cashes.append(ending_cash)
        
        # Balance Sheet Liabilities & Equity
        debt_end = prev_debt + delta_debt
        debts.append(debt_end)
        
        tot_liab = ap + debt_end
        total_liabilities.append(tot_liab)
        
        common_stock = prev_common_stock
        common_stocks.append(common_stock)
        
        # Retained Earnings roll-forward
        retained_earning = prev_retained_earnings + net_inc_val - div_paid - buyback_paid
        retained_earnings.append(retained_earning)
        
        tot_equity = common_stock + retained_earning
        total_equities.append(tot_equity)
        
        tot_asset = ending_cash + ar + inv + net_nppe + net_intangibles
        total_assets.append(tot_asset)
        
        bs_check = tot_asset - (tot_liab + tot_equity)
        bs_checks.append(bs_check)
        
        # Update previous year trackers for next loop
        prev_rev = current_rev
        prev_cash = ending_cash
        prev_debt = debt_end
        prev_ar = ar
        prev_inv = inv
        prev_nppe = net_nppe
        prev_intangibles = net_intangibles
        prev_ap = ap
        prev_common_stock = common_stock
        prev_retained_earnings = retained_earning

    # --- DCF VALUATION ---
    dfs = [1 / ((1 + wacc_val)**(i+1)) for i in range(years)]
    pv_fcfs = [fcf * df for fcf, df in zip(fcfs, dfs)]
    
    terminal_reinvestment_rate = t_g / t_roic
    terminal_nopat = nopats[-1] * (1 + t_g)
    terminal_reinvestment = terminal_nopat * terminal_reinvestment_rate
    
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
        'ebitdas': ebitdas,
        'net_incomes': net_incomes,
        'nopats': nopats,
        'reinvestments': reinvestments,
        'fcfs': fcfs,
        'pv_fcfs': pv_fcfs,
        'tv': terminal_value,
        'pv_tv': pv_tv,
        'ev': ev,
        'eq': equity_val,
        'price': share_price,
        'term_capex_dna_ratio': terminal_capex_to_dna,
        # 3-Statement Dataframes Data
        'is_data': pd.DataFrame({
            'Revenue': revs,
            'Operating Costs': op_costs,
            'EBIT (Operating Income)': ebits,
            'D&A': dnas,
            'EBITDA': ebitdas,
            'Interest Expense': int_expenses,
            'Interest Income': int_incomes,
            'EBT (Pre-Tax Income)': ebts,
            'Tax Expense': tax_expenses,
            'Net Income': net_incomes
        }, index=[f"Year {i+1}" for i in range(years)]),
        'cfs_data': pd.DataFrame({
            'Net Income': net_incomes,
            'D&A Add-back': dnas,
            'Change in NWC': delta_nwcs,
            'Cash Flow from Operations (CFO)': cfos,
            'CapEx': capexs,
            'M&A Spend': ma_spends,
            'Cash Flow from Investing (CFI)': cfis,
            'Dividends Paid': dividends_paid,
            'Share Buybacks': buybacks_paid,
            'Cash Flow from Financing (CFF)': cffs,
            'Net Change in Cash': net_change_cashes,
            'Ending Cash Balance': cashes
        }, index=[f"Year {i+1}" for i in range(years)]),
        'bs_data': pd.DataFrame({
            'Cash & Cash Equivalents': cashes,
            'Accounts Receivable': ars,
            'Inventories': inventories,
            'Net PP&E': net_ppes,
            'Goodwill & Intangibles': intangibles,
            'Total Assets': total_assets,
            'Accounts Payable & Accrued': aps,
            'Total Debt': debts,
            'Total Liabilities': total_liabilities,
            'Common Stock': common_stocks,
            'Retained Earnings': retained_earnings,
            'Total Equity': total_equities,
            'Total Liab & Equity': [l + e for l, e in zip(total_liabilities, total_equities)],
            'Balance Check ($)': bs_checks
        }, index=[f"Year {i+1}" for i in range(years)])
    }

base_model = run_integrated_model(
    ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
    ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
    div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
    dso_days, inventory_pct, ap_days,
    wacc, terminal_roic, terminal_growth
)


# --- TAB NAVIGATION LAYOUT ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. Three-Statement Model",
    "👔 2. DCF Valuation Engine",
    "📖 3. DCF Parameters Explanation",
    "🔄 4. Sensitivity & Reverse DCF",
    "🎲 5. Monte Carlo & Scenario Analysis",
    "📊 6. Trading Comps & Strategic Rationale"
])



# --- TAB 1: THREE-STATEMENT MODEL ---
with tab1:
    st.header("1. Integrated Three-Statement Forecast")
    
    max_bs_diff = max(abs(base_model['bs_data']['Balance Check ($)']))
    if max_bs_diff < 0.01:
        st.markdown("""
        <div class="status-balanced">
            ✅ Balance Sheet is Equilibrium Verified: Assets = Liabilities + Equity across all 15 forecast years (Max Delta: $0.00).
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"Balance Sheet discrepancy detected: Max variance = ${max_bs_diff:,.2f}")
        
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Year 15 Revenue", f"${base_model['revenues'][-1]:,.0f}")
    c2.metric("Year 15 Net Income", f"${base_model['net_incomes'][-1]:,.0f}")
    c3.metric("Year 15 CFO", f"${base_model['cfs_data']['Cash Flow from Operations (CFO)'].iloc[-1]:,.0f}")
    c4.metric("Year 15 Ending Cash", f"${base_model['cfs_data']['Ending Cash Balance'].iloc[-1]:,.0f}")

    st.subheader("Income Statement (IS)")
    st.dataframe(base_model['is_data'].style.format("${:,.0f}"))
    st.download_button(
        "📥 Download Income Statement (CSV)",
        base_model['is_data'].to_csv(),
        "Cintas_Income_Statement_Forecast.csv",
        "text/csv"
    )

    st.subheader("Cash Flow Statement (CFS)")
    st.dataframe(base_model['cfs_data'].style.format("${:,.0f}"))
    st.download_button(
        "📥 Download Cash Flow Statement (CSV)",
        base_model['cfs_data'].to_csv(),
        "Cintas_Cash_Flow_Statement_Forecast.csv",
        "text/csv"
    )

    st.subheader("Balance Sheet (BS)")
    st.dataframe(base_model['bs_data'].style.format("${:,.0f}"))
    st.download_button(
        "📥 Download Balance Sheet (CSV)",
        base_model['bs_data'].to_csv(),
        "Cintas_Balance_Sheet_Forecast.csv",
        "text/csv"
    )

    st.subheader("Financial Ratios & Solvency Metrics")
    
    # Ratio Calculations
    roics = [(nopat / (d + e - c)) * 100 for nopat, d, e, c in zip(
        base_model['nopats'], 
        base_model['bs_data']['Total Debt'], 
        base_model['bs_data']['Total Equity'], 
        base_model['bs_data']['Cash & Cash Equivalents']
    )]
    roes = [(ni / eq) * 100 for ni, eq in zip(base_model['net_incomes'], base_model['bs_data']['Total Equity'])]
    debt_ebitda = [d / ebitda for d, ebitda in zip(base_model['bs_data']['Total Debt'], base_model['ebitdas'])]
    int_cov = [ebit / int_exp if int_exp > 0 else 999.0 for ebit, int_exp in zip(base_model['ebits'], base_model['is_data']['Interest Expense'])]
    
    df_ratios = pd.DataFrame({
        "ROIC (%)": roics,
        "ROE (%)": roes,
        "Debt / EBITDA (x)": debt_ebitda,
        "Interest Coverage (x)": int_cov
    }, index=[f"Year {i+1}" for i in range(15)])
    
    st.dataframe(df_ratios.style.format({"ROIC (%)": "{:.1f}%", "ROE (%)": "{:.1f}%", "Debt / EBITDA (x)": "{:.2f}x", "Interest Coverage (x)": "{:.1f}x"}))

    st.subheader("Financial Visualization Dashboard")
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        fig_rev_ni = px.line(
            base_model['is_data'], 
            y=['Revenue', 'EBIT (Operating Income)', 'Net Income'],
            title="Revenue, Operating Income & Net Income Trajectory",
            labels={'value': 'USD ($)', 'variable': 'Line Item'},
            color_discrete_sequence=['#005A9C', '#f39c12', '#28a745']
        )
        st.plotly_chart(fig_rev_ni, use_container_width=True)

    with col_v2:
        fig_bs = px.bar(
            base_model['bs_data'],
            y=['Cash & Cash Equivalents', 'Accounts Receivable', 'Net PP&E', 'Goodwill & Intangibles'],
            title="Asset Composition Roll-Forward",
            labels={'value': 'USD ($)', 'variable': 'Asset Class'}
        )
        st.plotly_chart(fig_bs, use_container_width=True)


# --- TAB 2: DCF VALUATION ENGINE ---
with tab2:
    st.header("2. DCF Valuation Outputs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Enterprise Value", f"${base_model['ev']:,.0f}")
    col2.metric("Equity Value", f"${base_model['eq']:,.0f}")

    premium_discount = (base_model['price'] / ctas_data['price'] - 1) * 100
    col3.metric("Implied Share Price", f"${base_model['price']:.2f}", f"{premium_discount:.1f}% vs Market")

    st.markdown(f"**Sanity Check**: Implied Terminal Capex / D&A Ratio is **{base_model['term_capex_dna_ratio']:.2f}x** (Typically ~1.0x - 1.5x in steady state)")

    st.subheader("Projected Free Cash Flows (15-Year Horizon)")
    df_proj = pd.DataFrame({
        "Revenue": base_model['revenues'],
        "EBIT": base_model['ebits'],
        "NOPAT": base_model['nopats'],
        "Reinvestment": base_model['reinvestments'],
        "FCF": base_model['fcfs'],
        "PV of FCF": base_model['pv_fcfs']
    }, index=[f"Year {i+1}" for i in range(15)])
    
    st.dataframe(df_proj.style.format("${:,.0f}"))


# --- TAB 3: DCF PARAMETERS EXPLANATION ---
with tab3:
    st.header("3. DCF Parameters Explanation & Rationale")
    
    st.subheader("1. Explicit Forecast Horizon (15-Year Window)")
    st.markdown("""
    Standard DCF models utilize a 5-year explicit forecasting span before reverting to a permanent terminal growth rate. I opted to use a **15-year window** seeing as Cintas is a *"sticky compounder"* due to its massive competitive advantage (route density) and embedded nature of its subscription-like uniform rental service. 

    The open market values Cintas at a significant premium (often 40x+ P/E) because it prices in over a decade of continuous compounded growth and margin expansion. Constraining this explicit growth phase to just 5 years mathematically caps the valuation and forces a false narrative that Cintas will hit maturity almost immediately. A 15-year window accurately reflects the market's long-term conviction in the company's compounding ability.
    """)

    st.subheader("2. Revenue Driver Modeling Logic")
    st.markdown("""
    Instead of entering a generic "Revenue Growth Rate," I modeled revenue to more accurately capture the way Cintas operators view their business:

    * **Retention Rate (94%)**: Uniform rental is incredibly sticky. A 94% retention rate implies only a 6% annual churn, which is highly realistic for B2B facility services where switching costs (time, contractual friction) outweigh the benefits of changing providers.
    * **Annual Price Increase (3.5%)**: Cintas possesses phenomenal pricing power. Because the weekly cost of uniforms and mats is a tiny fraction of a customer's overall operating budget, Cintas can easily pass through 3.5% annual bumps to cover wage inflation without triggering customer churn.
    * **New Adds (6.0%)**: Represents pure organic growth—new customer wins and cross-selling (e.g., selling first-aid or fire compliance to an existing uniform customer).
    * **M&A Spend (2.0%) & M&A Sales-to-Capital Ratio (2.5x)**: Cintas operates a very effective rollup strategy, constantly acquiring smaller local operators. Allocating 2.0% of revenues to acquisitions at a strong 2.5x Sales-to-Capital ratio reflects the nature of buying local routes and instantly merging them into Cintas's existing infrastructure.

    > **Growth Rate Synthesis**:  
    > Retaining 94% of customers and increasing prices 3.5% means the existing base shrinks slightly to ~97.3% of the prior year. Adding 6.0% in New Adds generates ~3.3% organic growth. The highly efficient M&A tack-ins add another ~5.0% in revenue. **Total modeled growth: ~8.3% annually**, on par with reported growth.
    """)

    st.subheader("3. Operating & Financial Model Assumptions")
    st.markdown("""
    * **Operating Margin (21.5%)**: Conservative but highly profitable operating baseline.
    * **Organic Sales-to-Capital (3.0x)**: A 3.0x ratio means Cintas must inject $1 of capital (vans, washing facilities, working capital) to support every novel $3 of revenue. This metric prevents the model from "over-growing" the company without properly penalizing its free cash flow for the capital required to achieve that growth.
    * **Tax Rate (16.0%)**: A standard effective corporate tax reality for heavily capitalized domestic companies.
    * **WACC (7.5%)**: Because uniform rentals, restroom supplies, and compliance services are defensive and required regardless of macroeconomic headwinds, Cintas has a very low Beta. A 7.5% WACC prices in this non-cyclical safety.
    * **Terminal ROIC (27.0%)**: Even in maturity, Cintas's moat (route density and scale) will prevent competitors from eroding its returns. Constraining terminal Return on Invested Capital stringently to 27% ensures that the terminal value calculation ($\text{Reinvestment Rate} = \frac{g}{\text{ROIC}}$) continues to reward the company for structurally superior capital efficiency.
    * **Terminal Growth Rate (2.5%)**: Matches long-term normalized economic GDP growth and target inflation logic.
    """)

    st.subheader("4. Market Premium & Valuation Perspective")
    st.info("""
    **Valuation Realism**: Cintas is an incredible business, but Wall Street knows it. It routinely trades at a heavy premium (often 40x+ earnings). If you run a standard DCF on it, your implied share price will almost always look horribly undervalued because standard models struggle to project out premium runways. By using the Reverse DCF, the expectations can be seen as near perfect.
    """)


# --- TAB 4: REVERSE DCF & SENSITIVITY ---
with tab4:
    st.header("4. Reverse DCF & Sensitivity Analysis")
    st.markdown("Cintas often trades at a premium. Let's find out what **Operating Margin Expansion** or **Retention Rate** is currently priced in.")

    def reverse_dcf_margin(target_margin):
        res = run_integrated_model(
            ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
            ma_spend_pct, ma_sales_to_cap, target_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
            div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
            dso_days, inventory_pct, ap_days,
            wacc, terminal_roic, terminal_growth
        )
        return res['price'] - ctas_data['price']

    def reverse_dcf_retention(target_ret):
        res = run_integrated_model(
            ctas_data['revenue'], target_ret, price_increase, new_adds_pct,
            ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
            div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
            dso_days, inventory_pct, ap_days,
            wacc, terminal_roic, terminal_growth
        )
        return res['price'] - ctas_data['price']

    col_rev1, col_rev2 = st.columns(2)

    try:
        implied_margin = root_scalar(reverse_dcf_margin, bracket=[0.05, 0.50], method='brentq').root
        col_rev1.metric("Priced-in Operating Margin", f"{implied_margin*100:.1f}%", f"{(implied_margin - operating_margin)*100:.1f}% vs Base")
    except:
        col_rev1.error("Could not converge on Margin")

    try:
        implied_retention = root_scalar(reverse_dcf_retention, bracket=[0.50, 1.20], method='brentq').root
        col_rev2.metric("Priced-in Retention Rate", f"{implied_retention*100:.1f}%", f"{(implied_retention - retention_rate)*100:.1f}% vs Base")
    except:
        col_rev2.error("Could not converge on Retention")

    st.subheader("Dual-Variable Sensitivity Heatmaps")
    col_sens1, col_sens2 = st.columns(2)

    with col_sens1:
        st.write("**Retention Rate vs. Operating Margin**")
        ret_range = np.array([-0.04, -0.02, 0.0, 0.02, 0.04]) + retention_rate
        mgn_range = np.array([-0.04, -0.02, 0.0, 0.02, 0.04]) + operating_margin
        
        sens_table = []
        for r in ret_range:
            row = []
            for m in mgn_range:
                res = run_integrated_model(
                    ctas_data['revenue'], r, price_increase, new_adds_pct,
                    ma_spend_pct, ma_sales_to_cap, m, margin_expansion_bps, tax_rate, sales_to_capital, dna_pct_rev,
                    div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
                    dso_days, inventory_pct, ap_days,
                    wacc, terminal_roic, terminal_growth
                )
                row.append(res['price'])
            sens_table.append(row)
            
        df_sens = pd.DataFrame(sens_table, 
                               index=[f"{r*100:.1f}%" for r in ret_range],
                               columns=[f"{m*100:.1f}%" for m in mgn_range])
        
        st.dataframe(df_sens.style.background_gradient(cmap='RdYlGn', axis=None).format("${:.2f}"))

    with col_sens2:
        st.write("**Organic Sales-to-Capital vs. Terminal ROIC**")
        stc_range = np.array([-0.5, -0.25, 0.0, 0.25, 0.5]) + sales_to_capital
        roic_range = np.array([-0.05, -0.025, 0.0, 0.025, 0.05]) + terminal_roic
        
        sens_table2 = []
        for s in stc_range:
            row = []
            for vR in roic_range:
                res = run_integrated_model(
                    ctas_data['revenue'], retention_rate, price_increase, new_adds_pct,
                    ma_spend_pct, ma_sales_to_cap, operating_margin, margin_expansion_bps, tax_rate, s, dna_pct_rev,
                    div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
                    dso_days, inventory_pct, ap_days,
                    wacc, vR, terminal_growth
                )
                row.append(res['price'])
            sens_table2.append(row)
            
        df_sens2 = pd.DataFrame(sens_table2, 
                               index=[f"{s:.1f}x" for s in stc_range],
                               columns=[f"{vR*100:.1f}%" for vR in roic_range])
        
        st.dataframe(df_sens2.style.background_gradient(cmap='RdYlGn', axis=None).format("${:.2f}"))


# --- TAB 5: MONTE CARLO SIMULATION ---
with tab5:
    st.header("5. Monte Carlo Simulation")
    st.markdown("Randomizing core drivers across 2,000 iterations assuming normal distributions.")

    if st.button("🚀 Run 2,000 Monte Carlo Simulations"):
        with st.spinner("Running 2,000 simulations across 3-Statement & DCF engines..."):
            iterations = 2000
            
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
                
                res = run_integrated_model(
                    ctas_data['revenue'], r, p, new_adds_pct,
                    ma_spend_pct, ma_sales_to_cap, m, margin_expansion_bps, tax_rate, s, dna_pct_rev,
                    div_payout_ratio, share_buyback_pct, debt_interest_rate, cash_yield,
                    dso_days, inventory_pct, ap_days,
                    wacc, terminal_roic, terminal_growth
                )
                sim_prices.append(res['price'])
                
            p10 = np.percentile(sim_prices, 10)
            p50 = np.percentile(sim_prices, 50)
            p90 = np.percentile(sim_prices, 90)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("10th Percentile (Bear)", f"${p10:.2f}")
            col_m2.metric("Median (Expected)", f"${p50:.2f}")
            col_m3.metric("90th Percentile (Bull)", f"${p90:.2f}")

            fig = px.histogram(
                sim_prices, nbins=50, 
                title="Distribution of Implied Share Prices (Monte Carlo)",
                color_discrete_sequence=['#005A9C']
            )
            fig.add_vline(x=ctas_data['price'], line_dash="dash", line_color="black", annotation_text="Market Price")
            fig.add_vline(x=p50, line_dash="dot", line_color="orange", annotation_text="Median Implied Price")
            fig.update_layout(showlegend=False, xaxis_title="Implied Share Price ($)", yaxis_title="Frequency")
            st.plotly_chart(fig, use_container_width=True)


# --- TAB 6: STRATEGIC RATIONALE & MULTIPLES ---
with tab6:
    st.header("6. Strategic Rationale & Relative Valuation")

    col_strat1, col_strat2 = st.columns(2)

    with col_strat1:
        st.subheader("🤖 AI & Route Optimization")
        st.info("Cintas's dense route network is highly conducive to AI optimization. By utilizing predictive analytics, automated sorting in facilities, and dynamic route adjustments, CTAS can achieve significant operating leverage, directly translating topline growth into higher operating margins without a proportional increase in assets or fuel costs.")
        
        st.subheader("👔 Management Alignment")
        st.success("Historically, CTAS management compensation has been heavily weighted toward EPS growth and ROIC (Return on Invested Capital). This ensures management doesn't just chase 'topline vanity' via acquisitions but focuses on profitable growth that benefits shareholders.")

    with col_strat2:
        st.subheader("🎯 Implied Intrinsic Fair Value Assessment")
        implied_p = base_model['price']
        market_p = ctas_data['price']
        diff_pct = ((implied_p / market_p) - 1) * 100
        
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #005A9C; margin-top: 20px;">
            <h4>Implied Intrinsic Fair Value</h4>
            <h2 style="color: #005A9C;">${implied_p:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if market_p <= implied_p:
            st.success(f"Current market price of \\${market_p:.2f} is below implied fair value (\\${implied_p:.2f}, +{diff_pct:.1f}% upside).")
        else:
            st.info(f"Current market price of \\${market_p:.2f} is trading at a premium to base DCF fair value (\\${implied_p:.2f}, {diff_pct:.1f}% delta). See 4. Sensitivity & Reverse DCF tab for priced-in growth expectations.")

    st.subheader("📊 Peer Group Trading Comps (Relative Valuation)")
    
    @st.cache_data
    def get_forward_pe_data():
        try:
            ctas = yf.Ticker("CTAS").info.get('forwardPE', 0)
            unf = yf.Ticker("UNF").info.get('forwardPE', 0)
            armk = yf.Ticker("ARMK").info.get('forwardPE', 0)
            vsts = yf.Ticker("VSTS").info.get('forwardPE', 0)
            spy = yf.Ticker("SPY").info.get('forwardPE', 21.0)
            if spy == 0:
                 spy = 21.0
            return {"CTAS": ctas, "UNF": unf, "ARMK": armk, "VSTS": vsts, "S&P 500": spy}
        except:
            return {"CTAS": 45.0, "UNF": 25.0, "ARMK": 17.0, "VSTS": 18.0, "S&P 500": 21.0}

    pe_data = get_forward_pe_data()

    # Comps Table
    df_comps = pd.DataFrame({
        "Ticker / Asset": ["CTAS", "UNF", "ARMK", "VSTS", "S&P 500"],
        "Company Name": ["Cintas Corporation", "UniFirst Corporation", "Aramark", "Vestis Corporation", "S&P 500 Index"],
        "Forward P/E": [f"{pe_data['CTAS']:.1f}x", f"{pe_data['UNF']:.1f}x", f"{pe_data['ARMK']:.1f}x", f"{pe_data['VSTS']:.1f}x", f"{pe_data['S&P 500']:.1f}x"],
        "Business Segment": ["Uniform Rental & Facility Services", "Uniform & Workwear Services", "Food & Uniform Services", "Workplace Uniforms & Towels", "Broad Market Index"]
    })
    
    st.dataframe(df_comps, use_container_width=True, hide_index=True)

    col_pe1, col_pe2 = st.columns([1, 2])

    with col_pe1:
        st.metric("CTAS Forward P/E", f"{pe_data['CTAS']:.1f}x")
        st.metric("UniFirst (UNF) Forward P/E", f"{pe_data['UNF']:.1f}x")
        st.metric("Aramark (ARMK) Forward P/E", f"{pe_data['ARMK']:.1f}x")
        st.metric("Vestis (VSTS) Forward P/E", f"{pe_data['VSTS']:.1f}x")
        st.metric("S&P 500 Forward P/E", f"{pe_data['S&P 500']:.1f}x")

    with col_pe2:
        if pe_data['CTAS'] > 0:
            fig_pe = px.bar(
                x=list(pe_data.keys()), 
                y=list(pe_data.values()),
                title="Forward P/E Ratio Relative Valuation Comparison",
                labels={'x': 'Company / Index', 'y': 'Forward P/E Multiple (x)'},
                color=list(pe_data.keys()),
                color_discrete_map={"CTAS": "#005A9C", "UNF": "#6c757d", "ARMK": "#f39c12", "VSTS": "#8e44ad", "S&P 500": "#28a745"}
            )
            fig_pe.update_layout(showlegend=False)
            st.plotly_chart(fig_pe, use_container_width=True)
