# The Vision

## From Characterization to Prediction

For decades, drug safety has been fundamentally backward-looking. A patient experiences an adverse event. It gets reported. Patterns emerge — sometimes months or years later. Regulatory action follows. By then, patients have been harmed, programs have been delayed, and billions have been lost.

Cell therapy makes this problem acute. CRS, ICANS, and HLH are not edge cases — they are the defining safety challenge. CGT trials represent 40% of all FDA clinical holds. The question is not whether immune-mediated events will occur, but *which patients*, *when*, and *how severely*.

The Predictive Safety Platform answers that question before it's asked.

---

## What We're Actually Building

Imagine a system that sees a patient's complete picture — their genomics, their baseline labs, their disease burden, their treatment history — and renders a mechanistic risk landscape in real time. Not a black-box score, but a transparent, pathway-grounded prediction that a clinician can interrogate.

"This patient has a 73% probability of Grade 2+ CRS within 72 hours of infusion, driven primarily by elevated baseline IL-6 and high tumor burden. The predicted cytokine cascade initiates at the IL-6/sIL-6R axis with secondary TNF-alpha amplification. Recommended monitoring: q4h cytokine panel, tocilizumab staged at bedside."

That prediction is not a static number. It evolves. As real-time labs come in, as the patient's trajectory unfolds, the system updates its model — a living digital twin of the patient's immune response.

---

## The Three Revolutions in One

### 1. From Reactive to Predictive
Traditional pharmacovigilance detects signals after the fact. The platform predicts them before they manifest. Population-level risk profiles guide portfolio decisions. Patient-level scores guide clinical ones. The same engine, operating at different scales.

### 2. From Statistical to Mechanistic
Current approaches fit curves to historical data. The platform reasons about biology. It encodes cytokine cascades, receptor dynamics, and pathway interactions in a knowledge graph. When it predicts CRS, it can show you *why* — tracing the predicted cascade from CAR-T expansion through IL-6 release to endothelial activation. This isn't just interpretability for regulators. It's how the system generates novel hypotheses.

### 3. From Isolated to Integrated
Safety data lives in silos: clinical databases, lab systems, imaging, genomics, literature, spontaneous reports, social media signals. The platform doesn't just aggregate — it reasons across modalities. A genomic variant, combined with a lab value, combined with a literature finding about a related pathway, produces an insight none could generate alone.

---

## The Compounding Advantage

This platform is designed to get smarter over time. Not through manual retraining, but through three built-in feedback loops:

**Foundation Model Absorption**: As Claude, GPT, and Gemini improve, the platform improves automatically. No re-engineering. The platform calls models through versioned APIs — when a model gets better at biomedical reasoning, every prediction benefits.

**Knowledge Graph Growth**: Every validated hypothesis enriches the graph. Every confirmed adverse event adds evidence weight to mechanistic pathways. The graph becomes an institutional asset — a living map of safety biology that compounds with every trial.

**Clinical Feedback**: Prospective deployment creates ground truth. Predictions are logged, outcomes are observed, and the system calibrates itself against reality. Over years, this feedback loop creates a dataset that doesn't exist anywhere else: longitudinal predictions paired with outcomes at scale.

---

## Why Cell Therapy First

Cell therapy is the perfect proving ground:

- **High-stakes events**: CRS and ICANS are common, severe, and mechanistically understood well enough to model
- **Rich data**: CAR-T programs generate dense longitudinal data (cytokine panels, expansion kinetics, imaging)
- **Clear value**: A single avoided clinical hold saves 6+ months and delivers ~6:1 ROI
- **Extensible mechanisms**: The cytokine-mediated mechanisms in CRS share pathways with immune reactions to TCEs, checkpoint inhibitors, and bispecific antibodies

What works for cell therapy will generalize. The platform architecture is mechanism-agnostic — it can encode any biological pathway and reason about any adverse event with a known or hypothesized mechanism.

---

## The Enterprise Endgame

Stage 1 proves the engine works on 3 clinical studies.
Stage 2 proves it works prospectively, in real trials, with real stakes.
Stage 3 is where the vision fully materializes:

**Cross-TA Deployment**: Oncology, immunology, rare diseases — every therapeutic area benefits from predictive safety.

**Regulatory Integration**: Platform-generated risk profiles become part of IND submissions, informing regulatory strategy with quantitative safety predictions rather than retrospective characterizations.

**Portfolio Optimization**: Population-level safety indices become a factor in investment decisions. Which molecules advance? Which combinations are pursued? Predictive safety quantifies what was previously intuition.

**Industry Standard**: The organization publishes the methodology. The Safety Index becomes a recognized metric. Competitors adopt, but the organization maintains a data advantage — years of accumulated predictions, outcomes, and graph enrichment that can't be replicated.

---

## What Success Looks Like

**Year 1**: A clinician monitoring a CAR-T patient opens the platform dashboard and sees a risk trajectory that accurately predicted the timing and severity of CRS 24 hours before onset. The patient received preemptive intervention. The event was managed as Grade 1 instead of Grade 3.

**Year 3**: The organization's cell therapy portfolio has zero unplanned clinical holds attributable to safety events that the platform was deployed against. Risk profiles are a standard component of every safety section in regulatory submissions.

**Year 5**: The Predictive Safety Index is referenced in FDA guidance documents as an example of validated AI-assisted pharmacovigilance. Three other major pharma companies have licensed the methodology. The organization's knowledge graph contains 50,000+ validated mechanistic relationships.

**Year 10**: Predictive safety is table stakes. No one runs a trial without it. And the company that started it — that built the first knowledge graph, that established the first validation framework, that published the first regulatory-accepted AI safety predictions — owns the standard.

---

## The Bet

$20M to shift the paradigm from characterizing harm to preventing it.

The technology is ready. Foundation models can reason about biology. Graph networks can encode mechanisms. Agentic systems can orchestrate complex workflows. The data exists across the organization's clinical portfolio.

What's missing is the architecture that connects them — the engine that takes a patient's data, reasons through biological pathways, consults multiple foundation models, and delivers an interpretable, mechanistic prediction into a clinician's workflow.

That's what we're building.
