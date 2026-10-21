# horse-racing
a streamlit app
# Dashboard Justification for Horse Racing Betting App
## Dataset
Horse racing historical race, odds and wager payout dataset. It contains race information, horse profile, starting odds, final odds, bet volume, win/loss status and payout records.

## Step 2 — Justify the Dashboard
### 1. Who looks at it, and how often?
The platform operation & trading team looks at this dashboard every race day (multiple times per race day before and during races), and the business manager reviews it once per week for weekly performance summary.

### 2. What decision does it support?
If the trading manager sees sharp abnormal odds swing paired with unusual heavy bet volume on a single horse, they will pause the market for that horse and trigger a manual risk audit.

### 3. What do they do today without it — and what does that cost them in time, money, or mistakes?
Without this dashboard, staff manually pull separate spreadsheets and raw race logs to spot risk signals. This takes 30–60 minutes for each race, delays risk responses, and occasionally misses hidden risky betting patterns which leads to unexpected payout losses.

### 4. Why a dashboard rather than a weekly email, a report, or an alert?
 Weekly emails/reports are too slow for in-race live risk monitoring. Isolated alerts only fire for pre-set hard rules, while the dashboard lets analysts explore context: checking odds history, bet distribution and linked races to judge whether a signal is genuine risk or normal market fluctuation.

## step3 - Decide What Matters
## Extra: Two things we chose NOT to show, and why
1. Historical weather records of race tracks. Weather was interesting during EDA, but weather rarely changes the immediate betting risk decisions made by the trading team. It only impacts long-term horse performance research and is not used for race-day risk control.
2. Detailed jockey weight history. It correlates weakly with odds movement, and operators will not adjust risk rules based purely on jockey weight data. Including it would clutter the main view.

## Extra: Data issues that could mislead viewers & handling method
1. Outliers: Super-high exotic bet payouts can skew average payout metrics. We add a caption note on the metric card: *"Average payout includes rare large exotic wagers; refer to median payout for regular win/place bets."*
2. Voided/abandoned races: Some races were cancelled and wagers refunded. A filter toggle is provided, plus a warning label when cancelled race data is included in the view.

## Dashboard layout order logic
1. Top (Headline / Urgent checks): Real-time active race risk summary, current total bet volume, high-risk horse alert count. Answers "Is anything wrong right now?"
2. Middle (Explanation charts): Odds trend charts, bet volume distribution, win rate by horse tier, to explain why risk metrics shifted.
3. Bottom (Drill-down table): Raw wager list for high-risk races, only for deep investigation, not required for regular quick checks.

## Step 4 — Decide the Refresh Frequency
### 1. How often should the data be refreshed?
 Core odds and live bet volume refresh every 5 minutes during race days. Historical settled race data refreshes daily after all races finish. Real-time per-second refresh is unnecessary, because the risk team cannot respond faster than 5-minute review cycles and would raise system cost greatly.


### 2. How often should someone review it, and is that the same thing?
 Data refreshes every 5 minutes on race days, but the trading team reviews the dashboard continuously during race windows. Managers complete a formal weekly review every Monday morning, using the daily-settled historical dataset.

### 3. What should be tracked over time, and what should trigger action?
 Track the metric `proportion of heavy unbalanced bets on one horse`. Trigger action: If over 65% of the total race wagers are concentrated on a single horse, the trader must investigate within 10 minutes.

### 4. What does stale data cost? What goes wrong if the dashboard is a day — or a week — out of date?
If the dashboard is 1 day stale, operators cannot spot abnormal betting before race start, which may lead to unexpected large payout liabilities. If it is a week out of date, the team loses visibility into ongoing market bias patterns and cannot adjust risk limits in advance for upcoming race cards.
