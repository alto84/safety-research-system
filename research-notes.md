# Agentic Memory Research Notes

_Date: March 13, 2026_

---

## 1. Claude Opus 4.6 — 1M Context Window (Now GA)

- **1M token context window** is generally available as of March 12, 2026
- No beta header needed for Opus 4.6 or Sonnet 4.6
- **No pricing premium** — same per-token rate at 900K as at 9K
- **128K max output tokens** on Opus 4.6 (doubled from 64K)
- Available on: Claude API, Amazon Bedrock, Vertex AI, Microsoft Foundry
- Requirement: Usage tier 4 or custom rate limits for API access
- Prefill latency at 1M tokens can exceed 2 minutes
- Built-in **context compaction** auto-summarizes older context

### API Usage (No Special Config Needed)

```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=128000,
    messages=[{"role": "user", "content": your_large_context}]
)
```

### Relevant Features for Agentic Memory

| Feature | Description |
|---------|-------------|
| Context awareness | Claude tracks remaining token budget, reports after tool calls |
| Compaction | Auto-summarizes older context when approaching limits (beta) |
| Extended thinking | Previous thinking blocks auto-stripped to save space |
| Memory tool | Multi-session pattern for agents spanning multiple sessions |

**Sources:**
- [1M context GA announcement](https://claude.com/blog/1m-context-ga)
- [Context windows docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [What's new in Claude 4.6](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6)

---

## 2. Claude Platform Growth (March 2026)

- **1M+ new users per day** (confirmed March 6 by Anthropic CPO Mike Krieger)
- Daily signups quadrupled from ~250K/day (Jan 2026) to 1M+ (March 2026)
- **18.9M monthly active users**, 202.9M visits in January 2026
- **#1 free app** on App Store & Google Play in US and 20+ countries
- $14B annualized revenue (Feb 2026), $380B valuation (Series G)
- 70% of Fortune 100 use Claude; 29% enterprise AI assistant market share
- Claude Code reached ~$2.5B run-rate by early 2026
- QuitGPT boycott (1.5M participants) drove 295% surge in ChatGPT uninstalls

### Infrastructure Strain

- 291 tracked outages in 5 months (StatusGator)
- March 11, 2026: Login issues + slow performance, 1,400+ Down Detector reports
- March 2, 2026: Major global outage, ~10 hours of instability
- Mobile app known to hang/freeze — scrolling issues on Claude Code app

**Sources:**
- [Claude AI Stats 2026 - fatjoe](https://fatjoe.com/blog/claude-ai-stats/)
- [Claude AI 1M Daily Signups](https://www.adwaitx.com/claude-ai-now-adds-over-1-million-users-every-day-the-numbers-behind-the-surge/)
- [Claude Statistics - Backlinko](https://backlinko.com/claude-users)
- [March 11 outage - 9to5Mac](https://9to5mac.com/2026/03/11/claude-ai-and-code-are-experiencing-log-in-issues-and-slow-performance/)

---

## 3. ArXiv 2603.10062 — Multi-Agent Memory from a Computer Architecture Perspective

**Authors:** Zhongming Yu, Naicheng Yu, Hejia Zhang, Wentao Ni, Mingrui Yin, Jiaying Yang, Yujie Zhao, Jishen Zhao
**Submitted:** March 9, 2026

### Key Ideas

- Frames multi-agent memory as a **computer architecture problem**
- Distinguishes **shared vs. distributed memory** paradigms for agents
- Proposes a **three-layer memory hierarchy**: I/O, cache, and memory
- Identifies two critical protocol gaps:
  1. **Cache sharing** across agents
  2. **Structured memory access control**
- Most pressing open challenge: **multi-agent memory consistency**

### Relevance to Agentic Memory Project

This paper provides architectural foundations for how multiple agents should share and manage memory — directly applicable to building a memory system that persists across sessions and agents.

**Source:** [arxiv.org/abs/2603.10062](https://arxiv.org/abs/2603.10062)

---

## 4. Karpathy's Autoresearch (March 7, 2026)

Andrej Karpathy published **"Autoresearch"** — a minimal repo demonstrating autonomous agents running LLM training experiments unsupervised.

### Setup

- **8 agents** running simultaneously: 4 Claude instances + 4 OpenAI Codex instances
- Different organizational structures tested
- **110+ commits in 12 hours** across 8 NVIDIA H100 GPUs
- Agents autonomously iterated on training code for a small language model
- Optimized hyperparameters and architectures without human intervention

### Relevance

Demonstrates real-world viability of multi-agent autonomous systems — the kind of system that would benefit from the memory architecture described in the arxiv paper above.

**Sources:**
- [Karpathy Autoresearch - Context Studios](https://www.contextstudios.ai/blog/karpathy-autoresearch-prompt-replaces-paper)
- [Exploring Karpathy's Autoresearch - Substack](https://kenhuangus.substack.com/p/exploring-andrej-karpathys-autoresearch)

---

## Next Steps

- [ ] Design agentic memory architecture leveraging 1M context window
- [ ] Evaluate shared vs. distributed memory paradigms (per arxiv paper)
- [ ] Prototype multi-session memory persistence using Claude's memory tool patterns
- [ ] Consider Autoresearch-style multi-agent setup for parallel experimentation
