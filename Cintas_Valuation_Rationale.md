# Cintas DCF Valuation Rationale

Standard DCF models utilize a 5-year explicit forecasting span before reverting to a permanent terminal growth rate. I opted to use a 15-year window seeing as Cintas is a "sticky compounder” due to its massive competitive advantage (route density) and embedded nature of its subscription-like uniform rental service. The open market values Cintas at a significant premium (often 40x+ P/E) because it prices in over a decade of continuous compounded growth and margin expansion. Constraining this explicit growth phase to just 5 years mathematically caps the valuation and forces a false narrative that Cintas will hit maturity almost immediately. A 15-year window accurately reflects the market's long-term conviction in the company's compounding ability.

Instead of entering a generic "Revenue Growth Rate," I modeled revenue to more accurately capture the way Cintas operators view their business:

* **Retention Rate (94%)**: Uniform rental is incredibly sticky. A 94% retention rate implies only a 6% annual churn, which is highly realistic for B2B facility services where switching costs (time, contractual friction) outweigh the benefits of changing providers.
* **Annual Price Increase (3.5%)**: Cintas possesses phenomenal pricing power. Because the weekly cost of uniforms and mats is a tiny fraction of a customer's overall operating budget, Cintas can easily pass through 3.5% annual bumps to cover wage inflation without triggering customer churn.
* **New Adds (6.0%)**: Represents pure organic growth—new customer wins and cross-selling (e.g., selling first-aid or fire compliance to an existing uniform customer).
* **M&A Spend (2.0%) & M&A Sales-to-Capital Ratio (2.5x)**: Cintas operates a very effective rollup strategy, constantly acquiring smaller local operators. Allocating 2.0% of revenues to acquisitions at a strong 2.5x Sales-to-Capital ratio reflects the nature of buying local routes and instantly merging them into Cintas's existing infrastructure.

Retaining 94% of customers and increasing prices 3.5% means the existing base shrinks slightly to ~97.3% of the prior year. Adding 6.0% in New Adds generates ~3.3% organic growth. The highly efficient M&A tack-ins add another ~5.0% in revenue. Total modeled growth: ~8.3% annually, on par with reported growth.

* **Operating Margin (21.5%)**: Conservative but highly profitable operating baseline.
* **Organic Sales-to-Capital (3.0x)**: A 3.0x ratio means Cintas must inject $1 of capital (vans, washing facilities, working capital) to support every novel $3 of revenue. This metric prevents the model from "over-growing" the company without properly penalizing its free cash flow for the capital required to achieve that growth.
* **Tax Rate (16.0%)**: A standard effective corporate tax reality for heavily capitalized domestic companies.
* **WACC (7.5%)**: Because uniform rentals, restroom supplies, and compliance services are defensive and required regardless of macroeconomic headwinds, Cintas has a very low Beta. A 7.5% WACC prices in this non-cyclical safety.
* **Terminal ROIC (27.0%)**: Even in maturity, Cintas's moat (route density and scale) will prevent competitors from eroding its returns. Constraining terminal Return on Invested Capital stringently to 27% ensures that the terminal value calculation (Reinvestment Rate = g / ROIC) continues to reward the company for structurally superior capital efficiency.
* **Terminal Growth Rate (2.5%)**: Matches long-term normalized economic GDP growth and target inflation logic.

Cintas is an incredible business, but Wall Street knows it. It routinely trades at a heavy premium (often 40x+ earnings). If you run a standard DCF on it, your implied share price will almost always look horribly undervalued because standard models struggle to project out premium runways. By using the Reverse DCF, you quickly pull the "priced for perfection" reality out into the light.
