# AI Assistant for Trade Analysis – Technical Design

## Executive summary

We design an AI assistant to evaluate trading decisions by combining **chart-pattern recognition**, **ML classification**, **risk modeling**, and **user feedback**. The assistant detects technical patterns (shapelets, motifs, CNN-based image features) in real-time, interprets trader intent from natural language notes, and provides actionable feedback (e.g. “Your stop is too tight given volatility”). The system uses a modular pipeline: trade events stream into feature extraction, then into ML models (classification and risk scoring), generating a composite trade-quality score and feedback. We emphasize explainability (e.g. saliency maps on chart patterns, natural-language rationales) and support both real-time alerts and end-of-day reviews.

**Key techniques** include time-series motif discovery, wavelet multi-resolution analysis, and 2D CNNs on candlestick charts. Risk is quantified via VaR/ES (portfolio-level) and per-trade metrics (MAE/MFE, slippage). We extract trade intent (entry, stop, target, risk) using prompt-based LLM parsing of trader notes, ensuring factual grounding. Trade outcomes feed a supervised classifier (win/loss, strategy category) with robust evaluation (ROC, cross-validation, attention to class imbalance). Feedback is delivered through interactive UI components or chat, with A/B testing to refine messaging.

Data is stored in a hybrid architecture: an OLTP database for trades/annotations, a time-series or columnar store for high-throughput market data, and a feature/model store for ML artifacts. Key tables include Trades, Signals, UserProfiles, and FeedbackLogs. We provide JSON schemas and SQL DDL for these structures. The API supports REST and WebSocket: for trade ingestion, analysis requests, and event subscriptions, with OAuth2 auth and rate limits.

Observability tracks data and concept drift (automated alerts if model accuracy degrades) and system health (latency, error rates). Security measures enforce encryption, data minimisation, and user consent (export capabilities for personal trade data). Testing employs synthetic replay of market conditions and shadow-mode model deployment. Performance targets aim for <50ms inference per trade and capability to handle thousands of trades per minute. A 6-month roadmap is outlined: months 1–2 build core detection models and pipelines; months 3–4 integrate feedback UI and NLP parsing; months 5–6 add risk modules and refine via pilot studies. Our design draws on ML research and best practices (e.g. transformer time-series models, risk literature) to ensure a robust trade-audit assistant.

## Chart pattern recognition methods

Identifying chart patterns is treated as time-series classification or motif detection. **Deterministic templates** (e.g. fixed “head-and-shoulders” shapes) can be matched via cross-correlation or dynamic time warping, but they lack flexibility. **Time-series motifs** (repeated subsequences) can be found via distance-based search. **Shapelets** are learned time-series subsequences that optimally distinguish classes (e.g. bullish vs bearish setups). Shapelet methods measure a subsequence’s distance to sliding windows to detect pattern matches.

**Multi-resolution analysis** (e.g. wavelet transforms) captures patterns at different scales: a wavelet basis decomposes the price series into frequency components, aiding recognition of patterns like funnels or fractals. **CNNs on images** leverage vision techniques: convert price data to images (candlestick charts, Gramian Angular Fields) and apply 2D convolution. Empirically, CNNs can learn subtle visual cues of trend (e.g. Ganguly 2024 found ~90% accuracy on encoded candlesticks). However, pure image CNNs plateau (Sezer et al. reported ~70% accuracy on raw charts). Hybrid CNN-LSTM or multi-channel images (adding indicators) can improve power.

**Time-series transformers** (attention-based models) and 1D CNNs offer state-of-art accuracy in forecasting and classification. They operate directly on numeric sequences, avoiding image encoding. Transformers handle long-range dependencies (e.g. “what happened 3 hours ago?”). These models must be scaled and pruned for low latency if used in real-time.

We apply **scale-normalisation** (e.g. z-score or min-max) to each pattern window to ensure invariance to price levels. For latency, sliding-window detection uses lightweight models (e.g. 1D CNN) for sub-second inference. **Evaluation metrics** for pattern detection include precision/recall on annotated patterns, ROC/AUC for classifiers, and possibly peak F1 for motif discovery. A table of methods:

|Method|Strengths|Weaknesses|Example Use|
|---|---|---|---|
|Template Matching|Simple, fast|Rigid, noise-sensitive|Classic candlestick shapes|
|Time-Series Motifs|Data-driven, exact repeats|Requires many examples|Frequent recurring patterns|
|Shapelets|Interpretable segments|Needs labeled data|Trend vs reversal motifs|
|Wavelets|Multi-scale pattern capture|Can be complex to tune|Identifying volatility regimes|
|2D CNN (Image)|Learns complex visual features|High data req., may hallucinate|Candlestick chart patterns|
|1D CNN / RNN|End-to-end on raw data|Needs more data|Automated trend/noise extraction|
|Transformer Models|Captures long context|Compute heavy|Sequence of market state events|

**Latency/throughput**: For real-time, models must evaluate within few ms per new tick or trade. Heavy CNNs can run on GPUs if needed. Batch offline detection (post-trade analysis) can use larger models.

## AI feedback and UI/UX

The assistant provides two modes: **real-time alerts** and **post-trade review**. Real-time feedback (e.g. via a dashboard or chat bot) warns traders when a new trade violates rules (e.g. “Entry outside expected zone”). Post-trade, it generates a report card with an overall score and suggestions (e.g. “You risked 3% (target 2%), consider scaling out earlier”).

**UX patterns**:

- **Inline hints** on charts (e.g. highlighting pattern matches or stop distance).
- **Modal dialogs or chat messages** for immediate alerts (“Pause! Your stop is very tight.”).
- **Summary dashboards**: visualizing trade history, with annotations for flagged issues.
- **Explainability**: Each warning links to evidence (e.g. show the candlestick pattern that triggered recognition, or highlight how far actual stop was from recommended). Natural language rationales (“Stopped out exactly at predicted support”).
- **Corrective suggestions**: Instead of only criticism, the system suggests actionable fixes: adjusting position size, tighter spread, or waiting for confirmation.
- **Coaching loops**: For repeated issues, schedule a coach session or provide learning content. E.g. after three “over-risk” trades, prompt “It seems you often exceed 2% risk – check our position-sizing guide.”
- **Intervention policies**: Define thresholds to stop trading (self-enforced) or auto-redirect to risk management if a trader repeatedly violates rules. These policies should be configurable (e.g. toggle alerts, snooze).
- **A/B testing**: Experiment with different feedback phrasing or timing, measuring if one reduces future rule breaches more. Key metrics include improvement in trade score and user engagement/retention.

No direct sources were found on trading AI UX, but we adopt established human-centred AI guidelines (explanations, actionable feedback, user control).

## Natural-language trade reasoning analysis

Traders often write notes/rationale in free text (e.g. “Buy on breakout 1.234, RSI ~30”). We use LLMs to extract structured intent: entry level, stop-loss, take-profit, reason. Approaches:

- **Prompt engineering**: Craft prompts to elicit structured JSON from raw notes. E.g. “Extract entry, stop, target from: [text]”. Use few-shot examples in prompt.
- **Fine-tuning vs retrieval**: If we have a corpus of annotated notes, fine-tune a model (like GPT or Bloom) to parse them. Otherwise, use retrieval-augmented generation: index a knowledge base of known trading rules and retrieve relevant passages into the prompt to avoid hallucination.
- **Entity extraction**: Use rule-based / NLP models to identify prices, percentages, indicators in text (named entity recognition fine-tuned on trade logs).
- **Hallucination control**: Avoid making up non-specified information by explicit instruction (“If info missing, output null”). Verify extracted risk values with actual trade data.
- **Evaluation**: Manually label a sample of notes (or simulate notes) and measure accuracy of intent extraction. Metrics: extraction precision/recall, slot-filling accuracy.

Challenges: traders’ language varies (“tight stop” vs numeric). We'll need synonyms. Use robust parsing (regex for numbers, model for context). Without citations, we rely on general NLP techniques (no direct source found).

## Machine learning for trade classification

We frame trade classification tasks (e.g. trade outcome, strategy type) as supervised learning:

- **Features**: trade entry/exit price, indicator values (RSI, MA crossover), volume, spread, time-of-day, order type, etc. Can also use multivariate time windows around entry as inputs to sequence models.
- **Labels**: could be binary (profit/loss), or multi-class (Scalp, Swing, Daytrade, Error). Labeling often requires human definition. Weak supervision: use trade log outcomes as proxy (e.g. “good trade” if profit > target).
- **Models**: Sequence models (RNN, transformer) that take trade timeline; or tree ensembles on summary stats. Transfer learning: pretrain on large market data then fine-tune on trade outcomes.
- **Cross-validation**: Time-series split to avoid lookahead bias. Walk-forward validation recommended.
- **Class imbalance**: Trades often have many small losers or winners; use class weights or resampling. Possibly frame as regression (predict return) instead of classification.
- **Explainability**: Use SHAP or attention maps to highlight which features (indicator spike, pattern) drove the classification.

State-of-art methods include self-supervised learning (e.g. predict masked candlesticks) and weak supervision from related tasks. No single source; we adapt standard ML practices to trades.

## Risk assessment models

We employ both per-trade and portfolio risk metrics:

- **Per-trade risk**: Position size * (entry - stop) gives risk in currency. Compare to account equity to get percentage risk. **Max Adverse Excursion (MAE)** and **Max Favorable Excursion (MFE)** measure trade drawdown and run-up. Slippage and execution quality (difference between expected and actual fill prices) are recorded per trade.
- **VaR/ES**: Use Value-at-Risk to quantify portfolio tail risk. For a trader’s account, compute the p% VaR over next period (e.g. daily) via historical simulation or Monte Carlo. Expected Shortfall (CVaR) estimates average loss beyond VaR, addressing VaR’s blind spot.
- **Scenario stress tests**: Simulate extreme market moves or event-specific shocks on open positions (e.g. 10σ move, rate hike) to see potential losses.
- **Calibration and probability forecasts**: If models output probabilities (e.g. “80% chance trade hits stop”), evaluate calibration with Brier score and reliability diagrams. Use backtesting to compare predicted vs actual trade outcome frequencies.
- **Risk metrics**: Compute Sharpe, Sortino, max drawdown on recent trades and track “runaway risk” flag if drawdown exceeds threshold.
- **Portfolio constraints**: Monitor total exposure (sum of notional) vs capital, enforce margin limits, etc.

VaR definition citation: . MAE definition: .

## Trade quality scoring

A **composite score** rates each trade’s quality along multiple dimensions (risk, strategy adherence, outcome):

- **Components**: e.g. `entry_validity`, `position_sizing`, `stop_followed`, `target_achievement`, `risk_reward`.
- **Weighting & decay**: Older trades contribute less to aggregate “discipline score” (exponential decay). Assign weights reflecting business rules (e.g. violating stop = heavy penalty).
- **Cohort benchmarking**: Convert raw scores to percentiles against similar traders (experience level, instrument) to normalize.
- **Explainability**: Break score into sub-scores. Provide visual breakdown (e.g. pie chart of factors). For example, “50% for risk, 30% for plan adherence, 20% for execution”.
- **Thresholds for intervention**: If score < X, trigger a review or coaching suggestion. The choice of X comes from calibration to trader cohorts.
- **Evaluation**: Retrospectively test if higher scores correlate with profitability. Use precision/recall on “good vs bad trades” labels (if defined). Gather user feedback to refine weights.

We note studies linking behaviours to outcomes: “Outcome-focus leads to high turnover and worse performance”. This motivates including turnover/regret features in scoring.

## Data and schema design

We define core entities: **User**, **Trade**, **Signal**, **AnalysisResult**, **Feedback**.

**JSON examples:**

- _Trade_ (as ingested):

json

Copy

```json
{
  "trade_id": "T1001",
  "user_id": "U123",
  "instrument": "AAPL",
  "side": "BUY",
  "entry_price": 150.5,
  "exit_price": 153.0,
  "quantity": 100,
  "timestamp_entry": "2026-03-08T09:31:00Z",
  "timestamp_exit": "2026-03-08T14:45:00Z",
  "stop_price": 149.0,
  "target_price": 155.0,
  "notes": "Breakout above resistance with RSI divergence"
}
```

- _Pattern Signal_:

json

Copy

```json
{
  "signal_id": "S456",
  "trade_id": "T1001",
  "pattern": "Head_and_Shoulders",
  "confidence": 0.88,
  "timestamp": "2026-03-08T09:35:00Z",
  "details": {"left_shoulder": 151.0, "head": 152.5, "right_shoulder": 151.8}
}
```

- _Risk Analysis Result_:

json

Copy

```json
{
  "result_id": "R789",
  "trade_id": "T1001",
  "VaR_95pct": 2.5,
  "MAE": 1.2,
  "MFE": 3.0,
  "slippage": 0.1
}
```

- _Trade Feedback_:

json

Copy

```json
{
  "feedback_id": "F321",
  "trade_id": "T1001",
  "score": 0.72,
  "issues": ["Entry above resistance", "High risk (3%)"],
  "suggestions": ["Consider entering on close below resistance", "Use 2% risk max"]
}
```

**ER Diagram (core):**

Show code

- **users**: user_id PK, name, etc.
- **trades**: trade_id PK, user_id FK, instrument, side, prices, timestamps, notes.
- **signals**: signal_id PK, trade_id FK, pattern, confidence, metadata.
- **analysis_results**: result_id PK, trade_id FK, VaR, MAE, etc.
- **feedback**: feedback_id PK, trade_id FK, score, issues, suggestions.

## API design

Expose services for ingestion, analysis, and feedback:

- **POST /api/trades**: ingest a trade (JSON).
- **GET /api/trades/{id}**: retrieve trade and analysis.
- **POST /api/analyze/{trade_id}**: trigger (re)analysis of a given trade.
- **WebSocket ws://.../live**: push real-time alerts for patterns or risk breaches.
- **POST /api/feedback/{trade_id}**: save user feedback or coach intervention.
- **GET /api/leaderboard**: (if ranking traders by performance).

Auth via OAuth2/JWT per user. Rate-limit to e.g. 50 req/s to avoid DDOS on analysis.

## Algorithms and pseudocode

**Pattern detection (shapelet-based):**

python

Copy

```python
function detect_shapelet(trade_series, shapelet, threshold):
    distances = sliding_distance(trade_series, shapelet)
    min_dist = min(distances)
    if min_dist < threshold:
        return True, min_dist
    else:
        return False, min_dist
```

**Natural-language extraction (simplified):**

text

Copy

```text
PROMPT = "Extract entry, stop, target, risk from the text: \"" + user_note + "\"."
call LLM with PROMPT
parse JSON output fields {entry: x, stop: y, target: z, risk: r}
```

**Trade classification:**

python

Copy

```python
features = compute_trade_features(trade)
# features may include statistical summary, pattern signals, NL-extracted fields
prob = classifier.predict_proba(features)["profitable"]
label = (prob > 0.5)
```

**Risk scoring (VaR via historical):**

python

Copy

```python
returns = get_historical_returns(instrument)
VaR95 = np.percentile(returns, 5) * trade_value
ES = returns[returns <= VaR95].mean() * trade_value
```

**Composite scoring:**

python

Copy

```python
score = 100
if trade.entry > resistance_level: score -= 20
if actual_risk_pct > trader_max_risk: score -= 30
if trade_hit_stop: score -= 10
score = max(score, 0)
```

## Evaluation metrics

We evaluate each component rigorously:

- **Pattern detectors**: Precision, recall on held-out labeled patterns. Use ROC and F1 for binary pattern detection.
- **Trade classification**: Precision/recall of predicted success vs actual, area under ROC curve, and F1. Also cross-validate by time periods to avoid lookahead bias.
- **Risk models**: Backtest VaR accuracy (e.g. % of days loss exceeds VaR). Use Expected Shortfall errors. Check calibration (e.g. calibration plot, Brier score) for probabilistic outputs.
- **Feedback impact**: A/B test different alerts or wording: measure changes in trader behaviour (e.g. reduction in breach rate). Compute uplift or difference-in-differences.
- **Overall system**: Track uptime, latency (target e.g. <100ms per inference), error rates.

## Storage & processing

- **Data ingestion**: Use a streaming platform (Kafka) to buffer trade events and signals. Trades go to OLTP DB (Postgres), market data (tick prices) to a time-series DB.
- **Feature store**: Precompute static features in a feature DB (Snowflake/Redshift or time-series store) for quick access.
- **OLAP**: For analytics, use a columnar DB (ClickHouse or AWS Redshift) to run ad-hoc queries on trade histories.
- **Model store**: Save ML models (e.g. serialized) in an object store (S3 or similar) with versioning.
- **Object storage**: Raw logs, and large JSON dumps for audit.

**Row vs Column vs Time-series**:

- Row-store (Postgres) for structured trade/annotation records (fast inserts, relational joins).
- Column-store for batch analytics (aggregating KPIs).
- Time-series DB (InfluxDB/TimeScale) for tick-level and feature time-series (high write throughput).

## Monitoring and observability

- **System metrics**: Throughput (trades/sec), queue lags, DB query latency, model inference time.
- **Model metrics**: Drift detectors on input data distributions (e.g. population of MAE values). A drop in classification accuracy signals retraining. Use tools like Evidently for data/ML monitoring.
- **Alerts**: Trigger if model output distribution shifts, if pipeline errors spike, or if feedback mentions key flags.
- **Logging**: All decisions and feedback are logged (no raw PII). Use structured logging to enable tracebacks (each trade has a correlation ID for its processing).
- **Dashboards**: Grafana or Kibana showing usage patterns (requests per endpoint, latency), ML performance over time, error budgets.

## Security, privacy, compliance

- **PII minimisation**: Only store trader IDs (hashed) and anonymised data. Do not store personal notes except as analysis context.
- **Encryption**: TLS for all transport, encrypt DB at rest. API tokens and DB creds in secrets vault.
- **Consent**: Traders must opt-in to analysis. Provide a way to export or delete their data (GDPR).
- **Audit logs**: Immutable record of all model outputs and feedback given, for review.
- **Compliance**: For regulated users, ensure no personal data leaks. Compliance with relevant regulations (e.g. MiFID if in EU, SEC rules if in US) by anonymising trade identifiers.

## Testing and deployment

- **Synthetic replay**: Create simulated trade sequences (including edge cases like rapid news spikes) to test each detection module.
- **Shadow mode**: Deploy models in prediction-only mode on live trades without showing feedback; compare with actual trader outcomes.
- **A/B tests**: Split users into groups with/without real-time nudges to measure effect on discipline metrics.
- **Human labeling**: Periodically have expert traders rate model feedback for correctness (for supervised refinement).
- **Canary releases**: Roll out new analysis features (e.g. a new pattern detector) to a subset of users.
- **Continuous evaluation**: After each model update, run backtests on historical trade logs to ensure no regressions.

## 6-month roadmap

Apr '26May '26Jun '26Jul '26Aug '26Sep '26Oct '26Requirements & Data SchemaChart Pattern Module (image+shapelet)Core Trade Ingestion PipelineRisk Metrics Engine (VaR/MAE)ML Classifier PrototypeFeedback UI/AlertsNatural-Language ParsingComposite Scoring SystemDashboards & LeaderboardsObservability & TestingBeta Launch & IterationPerformance TuningPublic LaunchQ1Q2Q3Q4Trading AI Assistant Roadmap

Show code

- **Milestones**: Data schema done; pattern recognition integrated; risk scoring running; ML model trained; interactive feedback UI; launch pilot.
- **Deliverables**: Ingested trade logs, detected patterns table, risk report API, feedback endpoint, user dashboard, and technical documentation.
- **Success metrics**: Model accuracy (>80% on held-out trades), latency targets met (<100ms inference), positive user feedback (>90% agreement with suggestions), and improved trading outcomes in user group.

**Sources:** State-of-art methods from time-series ML and finance are applied. Key references include Ye & Keogh on shapelets, motif mining, wavelet theory, and CNN-based pattern classification. Risk metrics follow industry standards (VaR from Investopedia, MAE from TradingMetrics). Concepts like patience with A/B testing and explainability follow AI research best practices. Any gaps (e.g. lack of labeled trade notes for NLP) are addressed by assumptions (simulate data, use weak supervision).