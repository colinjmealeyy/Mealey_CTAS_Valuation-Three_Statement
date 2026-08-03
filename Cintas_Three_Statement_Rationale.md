# Dynamic Three-Statement Financial Model for Cintas Corporation (CTAS)

## Overview & Executive Summary

To complement the explicit **15-year Discounted Cash Flow (DCF)** valuation model, this **Three-Statement Model** projects Cintas Corporation's **Income Statement (IS)**, **Balance Sheet (BS)**, and **Cash Flow Statement (CFS)** in an integrated financial ecosystem. 

Standard DCF models operate in a "silo," projecting revenues, operating margins, and free cash flows without explicitly auditing the company's balance sheet capacity, debt interest burden, or capital allocation strategy (dividends vs. share repurchases). This integrated Three-Statement model bridges that gap by demonstrating how Cintas's operational decisions translate into balance sheet growth, financial leverage shifts, and equity compounding.

---

## 1. Core Model Structure & Inter-Statement Linkages

The three financial statements are dynamically linked through standard double-entry accounting mechanics:

```
                      ┌───────────────────────────┐
                      │     INCOME STATEMENT      │
                      │  Revenue → EBIT → EBT     │
                      │       → Net Income        │
                      └─────────────┬─────────────┘
                                    │
                                    │ Net Income
                                    ▼
┌───────────────────────────┐ Net Cash  ┌───────────────────────────┐
│    CASH FLOW STATEMENT    ├──────────►│       BALANCE SHEET       │
│  CFO = NI + D&A - ΔNWC    │  from     │  Assets = Liabilities     │
│  CFI = -CapEx - M&A       │ Fin/Inv/  │           + Equity        │
│  CFF = ΔDebt - Div - Buy  │    Op     │  (Cash = Dynamic Plug)    │
└───────────────────────────┴───────────┴───────────────────────────┘
```

### Key Financial Linkages:
1. **Net Income $\rightarrow$ Retained Earnings**:
   $$\text{Ending Retained Earnings}_t = \text{Beginning Retained Earnings}_{t-1} + \text{Net Income}_t - \text{Dividends}_t - \text{Share Repurchases}_t$$
2. **CapEx & Depreciation $\rightarrow$ Net PP&E**:
   $$\text{Net PP\&E}_t = \text{Net PP\&E}_{t-1} + \text{CapEx}_t - \text{Depreciation}_t$$
3. **M&A Spend $\rightarrow$ Goodwill & Intangibles**:
   $$\text{Goodwill \& Intangibles}_t = \text{Goodwill \& Intangibles}_{t-1} + \text{Acquisition Capital}_t$$
4. **Working Capital Dynamics $\rightarrow$ CFO**:
   $$\Delta \text{NWC}_t = (\Delta \text{Accounts Receivable}_t + \Delta \text{Inventory}_t) - \Delta \text{Accounts Payable \& Accrued Expenses}_t$$
   $$\text{Cash Flow from Operations (CFO)}_t = \text{Net Income}_t + \text{D\&A}_t - \Delta \text{NWC}_t$$
5. **Cash Balance Reconciliation**:
   $$\text{Ending Cash}_t = \text{Beginning Cash}_{t-1} + \text{CFO}_t + \text{CFI}_t + \text{CFF}_t$$
   This Ending Cash value plugs into the Balance Sheet under Current Assets, guaranteeing that:
   $$\text{Total Assets}_t - (\text{Total Liabilities}_t + \text{Total Equity}_t) = 0$$

---

## 2. Income Statement Assumptions & Logic

| Line Item | Modeling Logic / Formula | Cintas Structural Context |
| :--- | :--- | :--- |
| **Revenue** | $\text{Rev}_t = \text{Rev}_{t-1} \times (1 + g_{\text{organic}} + g_{\text{M\&A}})$ | Driven by customer retention (~95%), price increases (~3.5%), new account adds (~7.0%), and bolt-on acquisitions (~2.0%). |
| **Operating Expenses** | $\text{OpEx}_t = \text{Rev}_t \times (1 - \text{Op Margin}_t)$ | Scaled with annual margin expansion (+10 bps/yr) from route optimization and automated sorting. |
| **EBIT (Operating Income)**| $\text{Revenue}_t \times \text{Op Margin}_t$ | Clean measure of core profitability prior to capital structure impacts. |
| **D&A** | $\text{Revenue}_t \times \text{D\&A \% of Rev}$ | Explicitly modeled (typically 3.5% of revenue) for capital intensity. |
| **EBITDA** | $\text{EBIT}_t + \text{D\&A}_t$ | Operational cash generation proxy. |
| **Interest Expense** | $\text{Total Debt}_{t-1} \times r_{\text{debt}}$ | Interest paid on senior notes and credit facilities (modeled at ~4.5%). |
| **Interest Income** | $\text{Cash}_{t-1} \times r_{\text{cash}}$ | Yield earned on cash & cash equivalents (modeled at ~3.5%). |
| **Pre-Tax Income (EBT)**| $\text{EBIT}_t - \text{Interest Expense}_t + \text{Interest Income}_t$ | Taxable earnings base. |
| **Tax Expense** | $\text{EBT}_t \times \text{Effective Tax Rate}$ | Effective tax rate set at ~16.0%. |
| **Net Income** | $\text{EBT}_t - \text{Tax Expense}_t$ | Bottom-line profit attributable to common shareholders. |

---

## 3. Cash Flow Statement Mechanics

### A. Operating Activities (CFO)
* **Net Income**: Starting point from the Income Statement.
* **+ Depreciation & Amortization**: Non-cash add-back.
* **- Change in Net Working Capital ($\Delta$NWC)**: Accounts Receivable (DSO ~45 days) + Inventories (Inv Days ~35 days) - Accounts Payable/Accrueds (AP Days ~30 days).

### B. Investing Activities (CFI)
* **Capital Expenditures (CapEx)**:
  $$\text{CapEx}_t = \text{Reinvestment Organic}_t + \text{Depreciation}_t$$
  CapEx fades gradually over the 15-year period to converge with Depreciation in Year 15, matching steady-state equilibrium.
* **M&A Acquisitions**: Capital allocated to bolt-on route acquisitions ($\text{Revenue}_{t-1} \times \text{M\&A Spend \%}$).
* **$\text{CFI}_t = -(\text{CapEx}_t + \text{M\&A Spend}_t)$**

### C. Financing Activities (CFF)
* **Dividends Paid**: $\text{Net Income}_t \times \text{Dividend Payout Ratio}$ (modeled at ~30%).
* **Share Repurchases**: Surplus cash flows allocated to buybacks ($\text{FCF}_t \times \text{Buyback \% of FCF}$ or % of Net Income).
* **Debt Issuance / Repayment**: Modeled to maintain target leverage or fund capital deficits.
* **$\text{CFF}_t = \Delta \text{Debt}_t - \text{Dividends}_t - \text{Share Buybacks}_t$**

---

## 4. Balance Sheet Equilibrium & Financial Ratios

The balance sheet updates dynamically each year:

$$\begin{aligned}
\text{Total Assets} &= \text{Cash} + \text{Accounts Receivable} + \text{Inventory} + \text{Net PP\&E} + \text{Goodwill \& Intangibles} \\
\text{Total Liabilities} &= \text{Accounts Payable \& Accrueds} + \text{Short-Term Debt} + \text{Long-Term Debt} \\
\text{Total Equity} &= \text{Common Stock} + \text{Retained Earnings}
\end{aligned}$$

### Key Solvency & Efficiency Metrics Analyzed:
1. **Return on Invested Capital (ROIC)**:
   $$\text{ROIC}_t = \frac{\text{NOPAT}_t}{\text{Total Debt}_{t-1} + \text{Total Equity}_{t-1} - \text{Cash}_{t-1}}$$
   *Cintas maintains industry-leading ROIC (>20-25%), driven by high route density.*
2. **Return on Equity (ROE)**:
   $$\text{ROE}_t = \frac{\text{Net Income}_t}{\text{Average Total Equity}_t}$$
3. **Financial Leverage (Debt / EBITDA)**:
   $$\text{Leverage}_t = \frac{\text{Total Debt}_t}{\text{EBITDA}_t}$$
4. **Interest Coverage Ratio**:
   $$\text{Interest Coverage}_t = \frac{\text{EBIT}_t}{\text{Interest Expense}_t}$$

---

## 5. Bridging the Three-Statement Model to the DCF

The **Unlevered Free Cash Flow (FCFF)** utilized in the DCF valuation is explicitly derived from the Three-Statement model:

$$\text{NOPAT} = \text{EBIT} \times (1 - t)$$
$$\text{Reinvestment} = \text{CapEx} - \text{D\&A} + \Delta \text{NWC}$$
$$\text{FCFF} = \text{NOPAT} - \text{Reinvestment}$$

This ensures 100% mathematical consistency between the operational forecasting in the Three-Statement model and the DCF intrinsic share price calculation.
