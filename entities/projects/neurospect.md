---
tags: [entity, project, neurospect, trading, journal, ai-assistant, ict]
aliases: [Neurospect, NeuroSpect]
sources: [sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Trading Journal Systems and Backend Architecture for a Trading Journal Platform.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/AI Assistant for Trade Analysis – Technical Design.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Behavioural Analytics for Traders – Design of an Analytics Engine.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Broker API Integration and Trade Import Infrastructure.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Rule Engines for Trading Strategies and Automated Trade-Compliance Evaluation.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Scalable Discord Bot Architecture for Trading Communities.md, sources/obsidian-import/research/Neurospect/v2/Design and Planning/Reports/Trading Mentor Industry With Emphasis on Discord Based Trading Communities.md, sources/obsidian-import/research/Neurospect/v2-moonshot/Research + Planning/Foundations.md, sources/obsidian-import/research/Neurospect/v2-moonshot/Research + Planning/Moonshot Ideas.md]
created: 2026-04-16
updated: 2026-04-16
---

# Neurospect

Neurospect is a trading journal and AI-powered trade analysis platform designed specifically for ICT (Inner Circle Trader) / Smart Money Concepts traders. It goes beyond generic journaling to capture decision structure, market narrative, execution quality, and behavioral patterns, with the goal of becoming a personalized trading intelligence system.

**One-line vision**: "NeuroSpect helps ICT traders turn smart-money concepts into clearer narratives, better execution, and fewer low-quality trades."

## Vision / Goal

Start as an ICT trade journal and analytics platform that captures narrative, context, and execution quality deeply enough to later become a personalized trading intelligence system. The core principle: do not build "just a journal" -- build a system that captures what the trader saw, why they took the trade, what the market context was, how they executed, what happened after, and what pattern it belongs to.

The strongest product framing is not "track trades" but:
- Identify their real edge
- See which ICT setups actually work for them
- Spot recurring mistakes
- Improve execution discipline
- Convert screenshots and narratives into a personal playbook

## Current State

In the design and planning phase (v2) with extensive research reports covering:
- Trading journal backend architecture (event-sourced, multi-tenant SaaS)
- AI assistant for trade analysis (chart pattern recognition, ML classification, risk modeling)
- Behavioral analytics engine design
- Broker API integration infrastructure
- Rule engines for strategy compliance
- Discord bot architecture for trading communities
- Trading mentor industry analysis

A v2-moonshot track explores more ambitious future features.

## Architecture (v2 Design)

### Backend: Event-Sourced Journal

The backend is fundamentally an **event-normalization and reconciliation system**:
- **Append-only event log** with idempotent ingestion (broker feeds are inherently eventful)
- **Canonical schema**: Accounts, Instruments, Orders, Fills, Positions, Events, Tags, Audit Logs
- **Trade lifecycle state machine** supporting partial fills, cancels/replaces, OCO/bracket orders, scaling in/out
- **Dual storage**: OLTP (write-heavy journal data) + OLAP/time-series (rolling metrics, heatmaps, attribution)
- **Raw broker payload retention** in object storage for auditability
- **Postgres core** with JSONB for flexible broker payloads, partitioned event tables

### AI Assistant

- **Chart pattern recognition**: Time-series motifs, shapelets, wavelet multi-resolution analysis, 2D CNNs on candlestick images, transformer models
- **Trade classification**: Supervised ML on trade features (price, indicators, volume, time-of-day) with walk-forward validation
- **Risk assessment**: Per-trade (MAE/MFE, slippage) and portfolio-level (VaR/ES, scenario stress tests)
- **Composite trade quality scoring**: Multi-dimensional score (entry validity, position sizing, stop adherence, target achievement, risk/reward) with cohort benchmarking
- **NLP trade reasoning**: LLM-based extraction of structured intent from free-text trader notes (entry, stop, target, rationale)
- **Feedback modes**: Real-time alerts and post-trade review reports with explainability (saliency maps, natural-language rationales)

## Key Decisions

1. **ICT-specific, not generic**: The platform speaks ICT language (liquidity sweeps, MSS/BOS, FVGs, order blocks, premium/discount, kill zones, SMT) rather than offering generic trading analytics
2. **Structured trade schema**: ICT-specific fields (HTF bias, draw on liquidity, setup type, displacement quality, FVG presence, session/kill zone) alongside standard fields
3. **Narrative builder**: Pre-trade thesis capture (bias, dealing range, liquidity target, invalidation) compared against actual market behavior post-trade
4. **Event sourcing + projections**: Append-only broker events table with derived current-state tables, because broker feeds are eventful and reprocessing is inevitable
5. **Screenshot-first journaling**: Visual chart capture at multiple points (before entry, entry, exit, higher timeframe) because ICT trading is highly visual and screenshots become future training data

## Phased Roadmap

### Phase 1 -- MVP
- Manual trade journal with ICT-specific structured schema
- Screenshot uploads with markup tools
- Basic analytics dashboard (by setup type, session, instrument, bias alignment)
- Pre-trade narrative form and post-trade ICT review form
- Mistake tagging and setup quality grading
- Personal playbook page

### Phase 2 -- Sticky Product
- Broker import / automatic trade sync
- Chart screenshot markup tools
- Replay mode for trade review
- Rule violation tracking
- Confidence/emotion tracking
- Auto-generated weekly reviews
- Top mistake and best-condition insights

### Phase 3 -- AI Intelligence Layer
- Auto-tagging from chart/image/context
- AI-generated ICT trade reviews in ICT language
- Personal edge detection
- A+ setup scoring
- Execution warnings
- Narrative consistency analysis
- Personalized coaching feed

## Moonshot Ideas

The v2-moonshot track explores 10 ambitious future directions, with the top 4:

1. **Execution Guardian**: Detects likely self-sabotage (revenge trading, FOMO, plan deviation) and adds friction (cooldowns, forced checklists, reduced-size mode)
2. **Regime Shift Detector**: Identifies when the market environment has structurally changed and strategies should adapt
3. **Autonomous Catalyst Mapper**: Maps second- and third-order effects from news across asset classes in real time
4. **Personalized Market Twin**: Builds a live simulation of the trader's behavior, risk tolerance, and patterns

ICT-specific moonshots include: Narrative-to-Execution Engine, A+ Setup Filter, Liquidity Map OS, Kill Zone Decision Assistant, Market Structure Interpreter, Personal ICT Coach, Replay Tutor, SMT + Intermarket Intelligence Layer, Entry Model Builder, and ICT Trade Review Engine.

## Open Questions / Next Steps

- Choosing technology stack for MVP implementation
- Broker API integration strategy (which brokers first, auth flows, rate limiting)
- Discord bot integration for community features
- Data pipeline for market context snapshots at trade entry time
- Model training data strategy for chart pattern recognition
- Multi-account / prop-firm tracking requirements

## See Also

- [[openclaw]] -- potential agent runtime for autonomous analysis features
- [[ai-driven-dev-workflow]] -- methodology for building Neurospect itself
