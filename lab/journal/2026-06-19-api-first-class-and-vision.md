---
title: API inference goes first-class, and the project gets a lighthouse
date: 2026-06-19
tags: [journal, vision, benchmarks, api, strategy]
---

# API inference goes first-class, and the project gets a lighthouse

Today the project stopped being "a place to poke at local models" and got an
actual north star. The trigger was a deceptively simple question I asked myself
while staring at the benchmark harness: *why am I only ever pointing this thing at
Ollama?*

## The realization

The end vision here was always vague-but-present: a **home-automation system run by
a local agent**. Everything else — the wiki, the harness, the scorers — is
scaffolding toward picking the right brain for that agent. Once I said that out
loud, two things fell out of it.

First, the honest version of "which model should run my house" is **not** "which
*local* model." It's "which model, full stop — measured on capability *and* cost."
A $20/month API budget for something like Z.AI's GLM 5.2 is plausibly a better
deal than buying a bigger GPU to run a weaker model locally. The repo is named
`local-models` and local will stay the daily driver and the bias — but refusing to
even benchmark an API model would be optimizing for a label instead of the goal.

Second, the custom benchmarks I'd hand-seeded (decision-reasoning, code-basics)
had already done their real job: they proved the harness works end to end (the
opus-4.8 judge, the Podman sandbox). Six hand-written questions can't *rank* models
— and authoring more of them before I have a concrete use-case is just building a
measuring instrument before knowing what I'm measuring. The discipline is
**external-first**: wrap existing benchmarks that match my interests
(decision-making, agentic/triage), and let the home-automation system itself
generate the custom benchmarks later, from real traces. Those will be perfectly
uncontaminated and perfectly relevant in a way nothing public can be.

## The lighthouse

> Evaluate models — local *and* API — to decide which should run a local-agent
> home-automation system. External benchmarks where they fit my interests
> (decision-making, agentic/triage); custom benchmarks for my use-cases (home
> automation, email triage); capability **and cost** captured uniformly.

I wrote that into the README and AGENTS.md so I'd stop re-deriving the direction
every session. Build toward it.

## BFCL is a better fit than I expected

I went looking for the first external benchmark to wrap and landed on the Berkeley
Function-Calling Leaderboard. Two pleasant surprises. One: it runs here without a
GPU-heavy serving stack — point it at Ollama's OpenAI-compatible `:11434/v1`
endpoint with `--skip-server-setup` and skip vLLM/sglang entirely; the *same*
command runs an API model, so it does the local-vs-API comparison natively. Two:
its hardest categories are exactly the home-agent skill I care about — *irrelevance
detection* (don't call a tool that doesn't fit), *missing parameters* (ask instead
of guessing), *missing functions* (recognize the toolset is insufficient). That's
the "should I act, ask, or do nothing" judgment a thing controlling my house had
better get right before it turns the heat off at 2am. (Install gotcha for later:
the package is `bfcl-eval`, not `bfcl`.)

## What I actually changed today

A top-down docs pass to make the vision real before touching runtime: the
lighthouse in README + AGENTS; the schema generalized from *per-machine* to
*per-environment* (per-machine for local, per-provider+date for API, since prices
drift); API inference named as a first-class runner with **cost** as a recorded
metric; the four workflow prompts taught about `--provider`/cost; and the wiki
benchmark overview rewritten around external-first + a local-vs-API section.

Still ahead (deliberately *after* the docs, so a behavior change ships isolated):
the harness code itself — a provider abstraction that keeps the native Ollama
client (for `think`/`num_ctx`/real tok-timing) and adds an OpenAI-compatible one,
a `cost_usd` column, and a `benchmark-harness` skill so the agent stops
re-deriving how to drive the runner. Then the payoff: wrap BFCL and do the first
real API run.

The whole pivot took one good question. The repo's named for local models, but
it's really about answering one decision well — and that decision doesn't care
where the tokens come from, only what they cost and whether they're right.
