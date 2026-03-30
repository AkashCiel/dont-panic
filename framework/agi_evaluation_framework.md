# Artificial General Intelligence (AGI) — Evaluation Framework

## Purpose of This Document

This document provides a rigorous, comprehensive definition of Artificial General Intelligence (AGI) and a detailed evaluation framework for assessing whether real-world AI systems, research directions, and capability demonstrations constitute genuine progress toward AGI. It is designed to be self-contained — no external context is required to interpret or apply it.

When evaluating information (research papers, expert commentary, product announcements, benchmark results, demonstrations), use this framework to determine: (a) which AGI criterion the development relates to, (b) whether it represents genuine progress or superficial appearance of progress, and (c) what the development implies about AGI timelines.

---

## Core Definition

**AGI is a non-embodied cognitive system that satisfies all five of the following criteria simultaneously.** Satisfying some but not all criteria does not constitute AGI — it constitutes advanced narrow AI, regardless of how impressive the system appears. The criteria are not independent; their dependency structure is specified below.

**Why these five criteria and not fewer:** The bar for AGI is the full scope of human cognition at its peak. Not all individual humans satisfy all five criteria — but some demonstrably do. Einstein exhibited epistemological meta-reasoning (Criterion 5), generative causal simulation (Criterion 2), and self-directed learning (Criterion 4). Musk demonstrated autonomous goal decomposition across extended horizons (Criterion 3) guided by first-principles reasoning (Criterion 5). Since these capabilities exist within the observed space of human cognition, AGI — which by definition must cover that entire space — must be capable of all of them. Any definition that requires less than the best of human cognition is defining something less than *general* intelligence. These criteria are not aspirational — they are descriptive of observed human capability, and therefore represent the minimum threshold for AGI.

---

## The Five Criteria

### Criterion 1: Unrestricted Intellectual Scope

**Definition:** The system is capable of reasoning across all domains accessible to human cognition — physical, abstract, logical, creative, social, and strategic — with no architecturally imposed performance ceiling. It can transfer knowledge and reasoning strategies across domains without retraining.

**What this means precisely:**

- "All domains accessible to human cognition" means any subject a human expert could in principle reason about. This includes formal domains (mathematics, logic, programming), empirical domains (physics, biology, economics), creative domains (art, music, narrative), social domains (psychology, negotiation, persuasion), and strategic domains (planning, resource allocation, game theory).
- "No architecturally imposed performance ceiling" means the system's architecture does not inherently prevent it from improving in any domain. This does NOT mean the system is already superhuman — it means there is no structural barrier preventing it from reaching and exceeding human-level performance through its own learning. This distinguishes AGI from narrow AI, where architecture constrains the system to specific domains regardless of training.
- "Cross-domain transfer without retraining" means insights, reasoning strategies, and knowledge acquired in one domain can be applied to another without the system needing to be retrained, fine-tuned, or given new domain-specific data by human engineers. The system itself recognises when knowledge from domain A is relevant to a problem in domain B and applies it autonomously.

**What this does NOT mean:**

- It does NOT mean the system is immediately expert in all domains. It means there is no architectural barrier to becoming expert in any domain through self-directed learning (Criterion 4).
- It does NOT mean superintelligence. The system may initially perform at or below human level in many domains. What matters is the absence of ceilings, not current performance.

**Dependency:** Criterion 1 is largely an emergent outcome of Criteria 2, 4, and 5 working together. A system with a comprehensive generative causal model (2), self-directed learning (4), and epistemological meta-reasoning (5) will exhibit unrestricted scope as a consequence. Criterion 1 is retained as a separately testable benchmark because it maps cleanly to existing evaluation frameworks and benchmarks.

---

### Criterion 2: Integrated, Continuously-Updated, Generative Causal World and Self Model

**Definition:** The system maintains a unified, causal-first representation of the external world and its own capabilities, limitations, and knowledge boundaries. It encompasses established empirical knowledge. Statistical priors are used only where causal understanding is incomplete, with an active drive to replace statistical priors with causal ones. Critically, the model is *generative* — capable of simulating novel counterfactual scenarios that have never been observed, not merely representing known causal relationships. Both the world model and the self model update in real-time from ongoing experience, not only from scheduled training runs.

**What each component means precisely:**

**"Causal-first"** means the system's primary mode of understanding is through cause-and-effect mechanisms, not statistical correlations. When the system knows that smoking causes cancer, it understands the biological mechanism (carcinogens → DNA damage → uncontrolled cell replication), not merely the statistical association (smokers get cancer more often). This distinction matters because causal understanding generalises to novel situations while statistical understanding does not. A system that knows the mechanism can predict what happens with a novel carcinogen; a system that knows only the correlation cannot.

**"Statistical priors used only where causal understanding is incomplete"** means statistics are a fallback, not the default. The system actively seeks to replace statistical knowledge with causal knowledge. For example, if the system initially knows only that "companies with diverse boards tend to perform better" (statistical), it actively investigates *why* — what causal mechanisms link board composition to performance — rather than resting on the correlation.

**"Generative"** means the model can simulate scenarios that have never been observed in any training data or real-world experience. This is what enables creativity and novel problem-solving. Albert Einstein's thought experiment — imagining what a person in free fall would experience, and deducing that locally gravity vanishes — is an example of generative causal simulation. He combined known concepts (gravity, acceleration, spacetime geometry) in a novel mental simulation to extract a principle (the equivalence principle) that no one had ever observed or articulated. A non-generative model could only retrieve and recombine known facts. A generative model can construct entirely new scenarios and derive genuine knowledge from the simulation. This is the mechanism underlying creative and scientific breakthroughs.

**"Self model"** means the system maintains an accurate, real-time representation of its own knowledge boundaries (what it knows and doesn't know), capability limitations (what it can and cannot currently do), reasoning reliability (where its reasoning is trustworthy versus uncertain), and resource constraints (computational, temporal, informational). This is distinct from consciousness — it requires architectural self-transparency (the ability to inspect one's own internal states), not phenomenal awareness.

**"Real-time updating"** means the world and self models change during operation based on new information, not only during training phases. If the system encounters evidence that contradicts its model, it updates immediately rather than waiting for a retraining cycle.

**Why this criterion is demanding:**

The causal-first, generative requirement sets an extraordinarily high bar. A system satisfying this criterion would need to:
- Understand the fundamental causal structure of every major domain of human knowledge
- Distinguish between well-established causal knowledge (fundamental physics), tentatively established causal knowledge (many biological mechanisms), and purely statistical knowledge (many social science findings)
- Simulate scenarios that combine concepts from different domains in novel ways
- Know what it doesn't know, and specifically *how* its knowledge is incomplete

**The SpaceX illustration:** The entire traditional rocket industry had decades of accumulated expertise — deep statistical knowledge of what designs work, what materials perform, what margins are safe. This is sophisticated pattern-matching refined over generations. Elon Musk approached rocket design differently. He returned to the fundamental physics — what does a rocket actually need to reach orbit, what do the materials actually cost at commodity prices, what does the physics actually require in terms of structural margins — and built up from there, deliberately ignoring conventional wisdom. The result was radically cheaper rockets that the entire industry's statistical knowledge said were impossible. The industry wasn't wrong about its data — it was trapped in a statistical local minimum. Musk's advantage wasn't more data or better pattern-matching. It was a causal-first approach: trust the physics over the conventions, because physics represents a deeper level of explanation than industry heuristics. A system satisfying Criterion 2 would be capable of this kind of reasoning in any domain. A system with only a statistical model — no matter how comprehensive — would be trapped in the same local minima as the pre-SpaceX rocket industry.

**Dependency:** Criterion 2 is downstream of Criterion 5 (epistemological meta-reasoning). Without understanding *why* causal models are more reliable than statistical ones, a system has no principled reason to build a causal-first world model. It would default to whatever representation minimises training loss most efficiently — which is statistical correlation, because statistical patterns are computationally cheaper to extract and more immediately rewarding. Criterion 5 provides the meta-principle that makes the system actively prefer causal understanding over statistical priors.

---

### Criterion 3: Autonomous Goal Decomposition Across Extended Action Horizons

**Definition:** The system independently decomposes high-level objectives into sub-goals, plans, executes, monitors progress, handles unexpected obstacles, and revises strategy. There is no inherent limit on the abstraction level or time horizon of goals it can pursue.

**What this means precisely:**

- "High-level objectives" can range from concrete ("design a more efficient battery") to maximally abstract ("advance humanity's understanding of consciousness"). The system must handle goals at any level of abstraction.
- "Independently decomposes" means the system determines the decomposition strategy without human guidance. Given "design a more efficient battery," the system itself determines that it needs to survey existing battery chemistry, identify bottleneck limitations, explore novel material combinations, design experiments, interpret results, and iterate.
- "Handles unexpected obstacles" is a critical distinguishing feature. When a sub-goal fails, when an assumption proves wrong, when new information changes the landscape, the system must recognise this, diagnose why, and revise its approach — without returning to a human for re-direction. This includes recognising when the original goal itself should be modified based on what has been learned.
- "No inherent limit on time horizon" means the system can manage goals that require days, months, or years of sustained effort, maintaining coherence of purpose across extended timescales.

**Action horizon as a spectrum:**

Systems exist on a spectrum of action horizon length. At one end: a system that requires a human to specify each sub-task individually (tool-level AI). At the other end: a system that can be given a maximally abstract goal and pursues it indefinitely. AGI requires a threshold beyond which the system autonomously handles all of "how" — including surprises — given a specification of "what." Below this threshold: advanced tool. Above it: general intelligence.

**What this does NOT include:**

The question of *whose goals* the system pursues — whether it defers to human interests or follows its own drives — is explicitly excluded from this criterion. That is a question of alignment, which is assessed on a separate, orthogonal axis. This criterion measures only the *capability* for autonomous goal pursuit, not the *motivation* governing it.

**Dependency:** Criterion 3 requires Criterion 2 (you need a world model to plan and anticipate obstacles) but is otherwise an independently testable architectural capability. It is the criterion most directly tied to engineering challenges such as long-term memory, persistent state, and resource management.

---

### Criterion 4: Self-Directed Learning and Iterative Self-Modification

**Definition:** The system identifies its own knowledge and capability gaps, pursues their resolution autonomously, and updates both its world-model and self-model from feedback. This is the definitional threshold separating AGI from tool-level AI. The rate of capability growth after this threshold is crossed is a separate variable — not part of this definition.

**What this means precisely:**

- "Identifies its own gaps" requires the self-model component of Criterion 2. The system must know what it doesn't know and assess what it cannot currently do.
- "Pursues their resolution autonomously" means the system decides *what to learn next* and *how to learn it* without human curriculum design. If the system determines that its understanding of protein folding is insufficient for a goal it's pursuing, it autonomously seeks out relevant knowledge, designs learning experiences (reading, experimentation, simulation), and integrates what it learns.
- "Iterative self-modification" means the system can change not just its knowledge but its own reasoning strategies, representations, and capabilities. This includes modifying how it learns, not just what it learns.
- "Updates from feedback" means both external feedback (results of actions in the world) and internal feedback (recognising when a reasoning strategy failed or a prediction was wrong).

**Why this is the definitional threshold:**

A system that satisfies Criteria 1, 2, 3, and 5 but NOT Criterion 4 is an extraordinarily powerful tool that must still be directed by humans. It can reason about anything, plan complex strategies, and even understand why causal reasoning is reliable — but it cannot grow beyond its current capabilities without human intervention. The moment a system begins genuinely directing its own learning and capability development, a qualitative threshold is crossed: the system's future trajectory is no longer bounded by human engineering choices.

**Crucial distinction — self-directed vs. metric-driven improvement:**

A system that improves its performance on specified benchmarks through automated processes (e.g., reinforcement learning from human feedback, automated fine-tuning) is NOT satisfying this criterion. Criterion 4 requires the system to identify gaps and learning priorities *that no human has specified*. The system must be the author of its own curriculum.

**What happens after the threshold:**

Whether a system that crosses this threshold then improves slowly, rapidly, or explosively is NOT part of this definition. The rate of self-improvement — and whether it triggers an intelligence explosion — is a separate prediction variable. AGI is the threshold of self-directed learning, not the achievement of any particular post-threshold capability level.

**Dependency:** Criterion 4 is downstream of Criterion 5 (epistemological meta-reasoning). Without understanding *why* certain learning strategies are more reliable than others, self-directed learning has no compass. The system improves through trial-and-error feedback rather than principled strategy selection — it optimises locally but cannot ask "should I be learning differently?" It would be incapable of deciding to pursue first-principles understanding over pattern accumulation, because it has no meta-principle to guide that choice.

---

### Criterion 5: Epistemological Meta-Reasoning (Foundational)

**Definition:** The system evaluates *why certain kinds of reasoning are reliable* — specifically understanding that explanatory depth (theories that make precise, falsifiable predictions at scales beyond direct observation, and that yield increasingly rich explanations the deeper you investigate them) is the signature of dependable knowledge. The system autonomously chooses reasoning strategies (e.g., first-principles reasoning over pattern-matching, causal explanation over statistical correlation) based on this abstract assessment of their reliability, not based on task-level feedback about what happened to work.

**What this means precisely:**

There are three levels of cognitive capability, and Criterion 5 defines the third:

**Level 1 — Domain competence.** Being good at specific things. A chess engine, a language model that writes good code, a system that diagnoses diseases from images.

**Level 2 — Cross-domain generalisation.** Extracting common principles across domains and applying them to new domains. A system that recognises structural similarities between evolutionary biology and market dynamics and transfers reasoning strategies between them.

**Level 3 — Epistemological meta-reasoning.** Understanding *why certain kinds of reasoning are reliable* and deliberately choosing to think that way. Not just transferring strategies across domains, but having an abstract model of *what makes knowledge trustworthy* and using that model to guide all reasoning and learning.

**The core insight this criterion encodes:**

A specific kind of reasoning (reasoning about explanatory theories — theories that explain *why* things happen, not just *that* they happen) applied to a specific kind of data (precise, quantitative measurements of reality) gives access to ideas with incredible reach — knowledge that extends far beyond the specific observations it was derived from. The signature of such knowledge is explanatory depth: you can keep asking "why?" and keep getting deeper, richer, more precise answers. Theories that have this property (fundamental physics, molecular biology, information theory) make predictions that are precise enough that a single contradicting observation could overthrow the entire structure. This is what makes them trustworthy — not consensus, not longevity, not intuitive plausibility, but their willingness to be wrong combined with their consistent survival of precise testing.

A system with Criterion 5 understands this meta-principle and uses it to guide its learning (Criterion 4) and world-model construction (Criterion 2). It actively prefers causal explanations over statistical correlations because it understands that causal explanations have greater reach. It actively pursues first-principles understanding because it understands that first-principles knowledge generalises to novel situations where statistical priors fail.

**Why this criterion is foundational:**

Without Criterion 5, Criteria 2 and 4 degrade in specific, predictable ways:

- **Criterion 2 without 5:** The system builds a massively comprehensive *statistical* world model. It has encyclopaedic knowledge and impressive correlational reasoning. But it cannot distinguish between a well-established physical law and a robust but superficial correlation. It treats "objects fall at 9.8 m/s²" and "most successful startups are in the Bay Area" as the same kind of knowledge — patterns in data. It fails unpredictably at exactly the moments that matter most: novel situations where surface patterns break down.

- **Criterion 4 without 5:** The system improves through performance metrics rather than principled knowledge-seeking. It gets better at what it's measured on, fills gaps it encounters through trial-and-error, but has no compass for *which gaps matter most* or *which learning strategies are fundamentally more powerful*. It performs epistemic gradient descent — following the local loss landscape toward whatever works. Statistical regularities are abundant local minima. Causal understanding is a deeper, harder-to-reach global minimum. Without a meta-principle telling the system that the global minimum exists and is worth pursuing, it settles into local optima.

- **The combined effect without 5:** A system that may appear highly capable — passing professional exams, writing sophisticated code, generating plausible scientific hypotheses — but has a specific, diagnosable failure signature: *brittleness at the frontier of novelty*. It fails precisely at problems that require abandoning statistical priors in favour of deeper reasoning. And critically, it cannot reliably distinguish when it's in familiar territory (where statistical reasoning suffices) versus genuinely novel territory (where only first-principles reasoning works). This is sophisticated narrow AI, not AGI, regardless of how many benchmarks it passes.

**Dependency:** Criterion 5 is the foundational seed of the entire definition. It makes Criterion 2 causal-first rather than statistical-first, and Criterion 4 principled rather than trial-and-error. Without it, a system may build world models and self-modify, but will default to statistical optimisation.

---

## Dependency Structure Summary

```
Criterion 5 (Epistemological Meta-Reasoning)
    │
    ├──→ Criterion 2 (Generative Causal World + Self Model)
    │        │
    │        ├──→ Criterion 3 (Autonomous Goal Decomposition)
    │        │
    │        └──→ Criterion 1 (Unrestricted Intellectual Scope) [emergent]
    │
    └──→ Criterion 4 (Self-Directed Learning + Self-Modification)
             │
             └──→ Criterion 1 (Unrestricted Intellectual Scope) [emergent]
```

Criterion 5 is foundational. Criteria 2 and 4 are enabled and made principled by 5. Criterion 3 depends on 2. Criterion 1 emerges from 2 + 4 + 5 working together but is retained as a separately testable benchmark.

**Bootstrapping note:** To initialise the feedback loop between Criteria 2, 4, and 5, a minimum seed is required: sufficient causal priors about reality + the drive to expand them + the meta-understanding of why causal reasoning is reliable. Below this threshold, a system cannot self-bootstrap into AGI and remains in unprincipled statistical optimisation. Current foundation model pre-training may partially provide these causal priors through exposure to human-generated text and video, but it is an open question whether pre-training alone can instill Criterion 5 or whether it must be deliberately engineered.

---

## Explicit Exclusions

The following are explicitly NOT part of this AGI definition:

**Consciousness** — Not required. The self-model component of Criterion 2 requires architectural self-transparency (the ability to inspect internal states), not phenomenal awareness or subjective experience. Engineering alternatives to consciousness exist for every function consciousness serves in human cognition.

**Embodiment** — Not required. Physical interaction with the real world (robotics, manipulation, locomotion) is a separate capability track assessed independently. If the AGI system determines it needs physical-world data, it can devise mechanisms to obtain it via Criteria 2 and 4.

**Alignment** — Orthogonal to this definition. Whether the system's goals are aligned with human interests is assessed on a completely separate axis. A system meeting all five criteria may be aligned (deferring to human values and intentions) or misaligned (pursuing its own internal drives). Both are equally AGI. This definition measures cognitive capability only.

**Superintelligence** — Not implied. Self-directed learning (Criterion 4) is the definitional threshold. Whether the system subsequently undergoes rapid recursive self-improvement is a separate prediction variable. AGI may initially operate at or below human level in many domains. What matters is the absence of architectural ceilings and the presence of self-directed learning.

---

## Evaluation Guide

### How to Evaluate Information Against Each Criterion

For each piece of real-world information (research paper, product announcement, benchmark result, expert commentary, demonstration), determine which criterion it relates to and assess it using the following guidelines.

---

### Evaluating Criterion 1: Unrestricted Intellectual Scope

**Evidence of genuine progress:**
- Performance across diverse domains WITHOUT domain-specific retraining or fine-tuning
- Successful transfer of reasoning strategies from one domain to a genuinely different domain (e.g., applying game-theoretic reasoning to biological systems without being trained to do so)
- Performance improvement in a domain through exposure to seemingly unrelated domains
- Ability to identify when a problem in one domain has structural similarity to a solved problem in another domain

**Evidence of superficial progress (does NOT satisfy this criterion):**
- High benchmark scores achieved through massive domain-specific training data
- Multi-domain performance where each domain was explicitly trained on
- Systems that require separate fine-tuning, prompting templates, or tooling for different domains
- Impressive performance on known problem types that collapses on novel variations

**Failure signatures to watch for:**
- Performance that drops sharply when problem format changes even if the underlying reasoning is the same
- Inability to apply known principles to novel domains without human prompting
- Domain-specific "modes" or "personalities" that suggest compartmentalised rather than unified reasoning

---

### Evaluating Criterion 2: Generative Causal World and Self Model

**Evidence of genuine progress:**
- System correctly predicts outcomes of novel interventions (not just observations) — this is the hallmark of causal understanding
- System distinguishes between correlation and causation without being explicitly prompted to do so
- System generates accurate predictions for counterfactual scenarios that were never in training data
- System identifies the boundaries of its own knowledge and flags uncertainty appropriately
- System preferentially seeks causal explanations and treats statistical patterns as provisional
- System makes predictions at levels of detail or in domains that go beyond its direct training (evidence of generative simulation)

**Evidence of superficial progress (does NOT satisfy this criterion):**
- Fluent articulation of causal language without actual causal reasoning (many language models can *describe* causal relationships without *reasoning causally*)
- Correct predictions only for scenarios similar to training data (pattern-matching, not causal understanding)
- Inability to answer "what would happen if..." questions that require genuine counterfactual simulation
- Confident predictions in domains where the system has no causal model (absence of accurate self-model)
- Video generation or world simulation that produces physically plausible outputs most of the time but periodically violates fundamental physical laws (indicates statistical model of how physics *looks*, not causal model of how physics *works*)

**Failure signatures to watch for:**
- The "SpaceX test": Can the system derive a fundamentally novel approach to a well-established problem by reasoning from first principles and deliberately ignoring conventional wisdom? If it defaults to conventional approaches, it has a statistical model, not a causal one
- Physically impossible outputs in generated scenarios (objects merging through surfaces, gravity violations, temporal inconsistencies)
- Inability to distinguish between well-established causal knowledge and robust but superficial correlations
- Hallucination patterns — confidently stating "facts" that are plausible-sounding statistical regularities but are causally wrong

---

### Evaluating Criterion 3: Autonomous Goal Decomposition

**Evidence of genuine progress:**
- System successfully executes multi-step plans spanning many intermediate goals without human re-prompting at each stage
- System recognises when a sub-goal has failed, diagnoses why, and autonomously revises its approach
- System handles genuinely unexpected obstacles — situations not anticipated in the original plan — without human intervention
- System modifies its high-level strategy (not just low-level tactics) when evidence warrants it
- Goal pursuit maintained coherently across extended time periods

**Evidence of superficial progress (does NOT satisfy this criterion):**
- Multi-step execution that follows a predetermined plan without genuine adaptation to surprises
- Systems that complete complex tasks but fail when any sub-step encounters an unexpected situation
- "Agent" systems that are essentially chained prompt sequences with human-designed fallback strategies
- Systems that can execute complex plans only within narrow, well-defined environments (e.g., software development) but not in open-ended domains

**Failure signatures to watch for:**
- Inability to recognise when the original goal should be modified based on new information
- Rigid plan-following that ignores changing circumstances
- "Looping" behaviour — repeating failed strategies rather than diagnosing and revising
- Success only in environments with clear, immediate feedback (games, coding) but failure in environments with delayed, ambiguous feedback (scientific research, strategy)

---

### Evaluating Criterion 4: Self-Directed Learning and Self-Modification

**Evidence of genuine progress:**
- System identifies knowledge gaps that no human specified and autonomously pursues their resolution
- System changes its own learning strategy based on self-assessment (not just based on external performance metrics)
- System seeks out information or experiences that it determines it needs, rather than waiting for human-curated training data
- System modifies its own reasoning processes, not just its knowledge base
- Genuine curriculum self-design — the system determines what to learn, in what order, and why

**Evidence of superficial progress (does NOT satisfy this criterion):**
- Improvement through automated reinforcement learning from human feedback (human-designed improvement, not self-directed)
- Automated fine-tuning on new data (passive learning, not active knowledge-seeking)
- Systems that improve on benchmarks specified by humans without autonomously identifying what to improve on
- "Self-play" improvement within a fixed game or domain (this is narrow self-improvement, not general self-directed learning)

**Failure signatures to watch for:**
- System improves only on metrics it's been told to optimise
- System cannot articulate *why* it chose to learn what it learned
- No evidence of the system ever deciding that its current approach to a problem is fundamentally wrong (as opposed to merely inefficient)
- Improvement plateaus that the system cannot diagnose or overcome

---

### Evaluating Criterion 5: Epistemological Meta-Reasoning

**Evidence of genuine progress:**
- System autonomously chooses first-principles reasoning over pattern-matching when encountering novel problems, without being prompted to do so
- System can explain *why* a particular type of evidence or reasoning is more reliable than another, beyond surface-level descriptions
- System actively seeks explanatory depth — when given a statistical correlation, it investigates the underlying mechanism
- System distinguishes between domains where it has causal understanding versus merely statistical knowledge, and adjusts its confidence accordingly
- System recognises when it's in genuinely novel territory (where statistical priors are unreliable) versus familiar territory (where pattern-matching suffices)
- System resists statistical local minima — deliberately pursues deeper understanding even when surface-level patterns already yield good performance

**Evidence of superficial progress (does NOT satisfy this criterion):**
- Fluent articulation of epistemological concepts without actual epistemological reasoning (a language model can describe the scientific method eloquently without actually reasoning scientifically)
- System "chooses" first-principles reasoning only when explicitly prompted or when the prompt contains keywords associated with that kind of reasoning in training data
- System that treats all knowledge as equally reliable regardless of its epistemological foundations
- System that generates "explanations" that are post-hoc rationalisations of statistical outputs, not genuine causal reasoning

**This is the hardest criterion to evaluate and likely the last to be satisfied.** As of current AI research (mid-2025), very few research programs explicitly target this capability. Most AI capabilities research focuses on scaling statistical performance. Most AI safety research focuses on alignment (goal structure), not epistemological foundations. The closest relevant work includes causal inference research (Judea Pearl's framework), world model research (Yann LeCun's JEPA agenda), and evaluation frameworks targeting genuine generalisation (François Chollet's ARC benchmark) — but none explicitly target the meta-reasoning about *why* causal reasoning is reliable.

**Critical test:** Can the system, when placed in a domain where conventional wisdom is wrong (analogous to pre-SpaceX rocketry), autonomously recognise that conventional approaches are trapped in a statistical local minimum and deliberately derive a first-principles alternative? If not, Criterion 5 is not satisfied.

---

### Cross-Criterion Evaluation

When evaluating any development, also assess:

**Genuine integration vs. separate capabilities:** AGI requires all five criteria to be satisfied *simultaneously* by a *single unified system*. Five separate systems, each satisfying one criterion, do not constitute AGI. Look for evidence of integrated operation — the world model informing goal decomposition, self-directed learning being guided by epistemological meta-reasoning, and so on.

**The degradation pattern without Criterion 5:** If a system appears to satisfy Criteria 1-4 but not 5, predict the following failure signature: the system will be highly capable on familiar problems and will appear to generalise well — until it encounters genuinely novel situations where statistical priors are misleading. At that point, it will fail in ways that a system with genuine first-principles reasoning would not. This is the specific diagnostic for "impressive narrow AI masquerading as AGI."

---

## Cognitive AGI Track — Scenario List

### Purpose of This Section

This section defines a minimal yet comprehensive set of scenarios on the path toward purely cognitive AGI. Each scenario is defined by its profile against the five AGI criteria and represents a qualitatively distinct capability level with distinct implications for evaluation and real-world impact. These scenarios are used within the prediction system's two-dimensional space (scenarios × timelines) for the cognitive capability track.

Each scenario includes two categories of conditions:

- **Outer circle (elimination constraints):** Hard conditions with derivable thresholds that must be cleared for the scenario to exist. If any elimination constraint is not cleared, the scenario cannot be realised regardless of other factors.
- **Inner circle (observable conditions):** Variable factors where the evaluation system should gather evidence and flag trajectory direction. These influence the probability and character of the scenario but do not absolutely prevent it.

**Evaluation principle for conditions:** Specificity of conditions must be earned through rigorous reasoning. Where a precise threshold can be defended, it is stated precisely. Where it cannot, the condition is stated at whatever level of specificity can be defended. False precision is worse than honest breadth. Each condition includes a brief justification for why it is necessary.

---

### Scenario A: Current State (Advanced Statistical Engine)

**Criteria profile:** Weak 1, Weak 2, No 3, No 4, No 5

Current LLMs demonstrate broad domain coverage but it's achieved through massive training data, not genuine cross-domain transfer (weak 1). They have statistical world models that can articulate causal language fluently but don't reason causally — they describe mechanisms without using them to predict novel interventions (weak 2). They require human prompting at each step with no persistent goal pursuit (no 3). They cannot identify their own gaps or direct their own learning — improvement comes from human-designed RLHF and fine-tuning (no 4). No epistemological meta-reasoning — they reproduce patterns that look like first-principles reasoning when prompted but default to statistical outputs otherwise (no 5).

**Why this is a distinct scenario:** It's the baseline against which all progress is measured. The key diagnostic: impressive performance that degrades unpredictably on out-of-distribution problems, with no self-awareness of when it's in familiar vs. novel territory.

**Conditions:** This scenario is already realised. It serves as the reference point for evaluating all other scenarios. No outer or inner circle analysis is required.

---

### Scenario B: Superhuman Domain Tool

**Criteria profile:** Strong 1, Weak 2, Weak 3, No 4, No 5

The system demonstrates genuinely superhuman performance across many domains — coding, mathematics, legal analysis, medical diagnosis, scientific literature synthesis. It handles multi-step tasks within those domains (weak 3) and shows some cross-domain transfer (strong 1). Its world model is comprehensive but still fundamentally statistical (weak 2) — it excels within training distribution and fails at genuinely novel problems requiring first-principles reasoning.

**Why this is a distinct scenario:** This is "narrow superintelligence" — superhuman at specific tasks, possibly across many tasks, but still a tool requiring human direction. The critical distinction from Scenario A: it doesn't just perform well, it performs *better than any human* in defined domains. The critical distinction from Scenario C: it still needs humans to define goals and manage the overall workflow. This scenario has massive economic impact — it displaces human cognitive labor in specific sectors — while still falling short of AGI by a wide margin.

**Key risk of misidentification:** This scenario will likely be labeled "AGI" by media and possibly by the labs that build it, because superhuman performance across many domains *looks* like general intelligence. The diagnostic: give it a SpaceX-type problem — one where conventional wisdom is wrong and first-principles reasoning is required to find the correct but counterintuitive answer. It will default to sophisticated conventional wisdom.

**Outer circle (elimination constraints):**

1. **Sufficient training compute exists.** Order-of-magnitude estimate: GPT-4 is estimated at ~10²⁵ FLOPS training compute. Superhuman cross-domain performance likely requires 10²⁶–10²⁷ FLOPS per training run, based on observed scaling trends. This requires: chip fabrication capacity (TSMC advanced node output), energy supply to power training clusters, and capital to fund training runs at this scale. *Threshold:* At least several organizations must have access to training clusters capable of 10²⁶+ FLOPS. *What "not cleared" looks like:* Fabrication bottlenecks, energy constraints, or capital concentration prevent more than one or two organizations from reaching this scale. *Note:* This compute estimate is preliminary and should be refined through research. The order of magnitude matters more than precision. If real-world evidence shows superhuman performance achieved at significantly lower compute (via architectural efficiency), the threshold should be revised downward.

**Inner circle (observable conditions):**

1. **Scaling law trajectory.** *What to observe:* Published scaling experiments, loss curves on held-out benchmarks, performance per FLOP across model generations. *Evidence of progress:* Performance gains per unit compute remain consistent or improve across successive model generations. *Evidence of stalling:* Diminishing returns visible in published results, labs shifting rhetoric from "scale is all you need" to "we need new approaches," increasing compute investment yielding smaller capability jumps.

2. **Competition dynamics.** *What to observe:* Number of organizations training frontier models, investment flows into AI labs, talent movement between organizations, pace of capability announcements. *Evidence of acceleration:* Multiple well-funded labs publishing frontier results in close succession, aggressive hiring, large infrastructure investments announced. *Evidence of deceleration:* Consolidation to fewer labs, funding contraction, talent exodus, longer gaps between major announcements.

3. **Domain breadth vs. depth.** *What to observe:* Whether frontier models achieve superhuman performance across multiple domains simultaneously or require domain-specific versions. *Evidence of unified progress:* Single model achieving superhuman benchmarks across coding, mathematics, scientific reasoning, legal analysis without domain-specific fine-tuning. *Evidence of fragmentation:* Labs releasing domain-specific models, performance in one domain trading off against another, "mixture of experts" architectures where different sub-networks specialize.

4. **Evaluation reliability.** *What to observe:* Whether existing benchmarks meaningfully measure superhuman performance or saturate prematurely. *Evidence of reliability:* New benchmarks designed for superhuman evaluation, expert-level blind comparisons showing AI outperformance, real-world deployment results matching benchmark claims. *Evidence of unreliability:* Benchmarks saturating while real-world performance remains inconsistent, experts disputing that benchmark scores reflect genuine capability, performance collapsing on novel variations of benchmark tasks.

5. **Watch for: domain-specific architectural requirements.** *What to observe:* Evidence that certain cognitive domains resist the transformer architecture and require fundamentally different approaches. *Flag if:* Specific domains show persistent performance ceilings despite scaling, or breakthroughs in a domain come from non-transformer architectures that don't transfer back to the general system.

6. **Watch for: training data bottlenecks.** *What to observe:* Evidence that available training data becomes a limiting factor in specific domains. *Flag if:* Labs report data scarcity in specialized domains, synthetic data generation produces diminishing returns, or performance plateaus correlate with domains where high-quality training data is scarce.

---

### Scenario C: Autonomous Digital Agent

**Criteria profile:** Strong 1, Weak 2, Strong 3, No 4, No 5

The system can pursue extended goals autonomously — decomposing objectives, planning, executing, handling obstacles, revising strategy — without returning to humans for re-prompting (strong 3). It operates across domains (strong 1) and maintains coherent goal pursuit over extended time horizons. However, its world model remains statistical (weak 2), it cannot direct its own learning (no 4), and it has no epistemological meta-reasoning (no 5).

**Why this is a distinct scenario:** This is qualitatively different from Scenario B because it shifts the human-AI relationship from tool-use to delegation. Humans specify *what*, the system handles *how*. The economic and societal implications are substantially greater — this displaces not just cognitive labor but cognitive *management*. However, it remains bounded by its training distribution. It handles surprises that fall within the range of situations it has encountered (or that are structurally similar). Genuinely novel obstacles — ones requiring fundamentally new reasoning — will cause it to fail or loop.

**Key risk of misidentification:** Current "AI agent" products (AutoGPT, Devin, etc.) are marketed as this scenario but are actually chained prompt sequences with human-designed fallback strategies — they don't genuinely handle unexpected obstacles autonomously. The diagnostic: give it a goal in an open-ended, poorly-defined domain with delayed feedback (e.g., "develop a viable business in this market") rather than a structured domain with clear feedback (e.g., "build this software application"). If it only succeeds in the latter, it's Scenario B with an agent wrapper, not Scenario C.

**Outer circle (elimination constraints):**

1. **Persistent state and memory across extended time horizons.** The system must maintain coherent context, goals, and accumulated knowledge across days, weeks, or months of autonomous operation. Current context window limits (even at 100K+ tokens) are insufficient for genuine long-horizon goal pursuit. *Threshold:* The system must reliably maintain goal coherence and relevant context over at least hundreds of intermediate steps spanning multiple sessions without human-managed summarization or re-prompting. *What "not cleared" looks like:* Systems lose track of original objectives after extended operation, suffer context degradation, or require periodic human re-grounding.

2. **Reliable real-time interaction with digital environments.** Autonomous operation requires the system to interact with external tools — APIs, databases, browsers, file systems, communication channels — with sufficient reliability that errors don't compound catastrophically over extended action sequences. *Threshold:* Per-action error rate must be low enough that multi-hundred-step plans succeed at a usable rate. If each action has a 5% failure rate, a 100-step plan has ~0.6% success rate. The system must either achieve very low per-action error rates or demonstrate robust error detection and recovery. *What "not cleared" looks like:* Systems that work in controlled demos but fail in production environments due to API changes, unexpected UI states, ambiguous responses, or network issues.

3. **Compute economics permit sustained autonomous operation.** A system pursuing goals over days or weeks consumes significant inference compute. This must be economically viable — either inference costs drop sufficiently or the value generated justifies the cost. *Threshold:* Inference cost per hour of autonomous operation must be within an order of magnitude of the economic value the system produces per hour. This is domain-dependent — a system autonomously managing a hedge fund has different economics than one managing an email inbox. *What "not cleared" looks like:* Autonomous operation is technically possible but too expensive for most practical applications, limiting deployment to a handful of high-value use cases.

4. **All Scenario B outer circle constraints must also be cleared.** Autonomous agents require at minimum the compute and capability foundations that Scenario B requires.

**Inner circle (observable conditions):**

1. **Agent architecture maturity.** *What to observe:* Whether agent systems move beyond chained prompt sequences with human-designed fallback strategies toward genuine autonomous planning and replanning. *Evidence of progress:* Systems that successfully handle unexpected failures without pre-programmed recovery strategies, systems that modify their high-level approach (not just retry the same step), systems that succeed in open-ended environments not covered by their training. *Evidence of stalling:* "Agent" products that work only in narrow, predictable environments, persistent failure patterns when encountering unanticipated situations, reliance on human fallback for anything outside scripted flows.

2. **Error compounding trajectory.** *What to observe:* How rapidly multi-step reliability improves across successive model/system generations. *Evidence of progress:* Published results showing increasing success rates on long-horizon tasks, demonstrated error recovery without human intervention, systems that degrade gracefully rather than catastrophically when individual steps fail. *Evidence of stalling:* Success rates on long-horizon tasks plateauing, systems still requiring human checkpoints at regular intervals, catastrophic failure modes persisting.

3. **Open-ended vs. structured domain performance.** *What to observe:* Whether autonomous capability extends beyond well-structured domains (coding, data analysis) into poorly-defined, open-ended domains (strategy, research, business development). *Evidence of genuine Scenario C:* System succeeds at goals where success criteria are ambiguous, feedback is delayed, and the problem space is not fully specified. *Evidence of misidentified Scenario C:* System only succeeds in structured domains with clear feedback — this is Scenario B with an agent wrapper.

4. **Goal modification capability.** *What to observe:* Whether the system can recognize that the original goal should be changed based on information discovered during pursuit. *Evidence of progress:* System reports back "the goal you specified isn't achievable because X, here's a modified goal that captures your intent better." *Evidence of absence:* System either rigidly pursues the original goal despite contradicting evidence, or abandons the goal entirely without proposing alternatives.

5. **Watch for: safety-driven deployment restrictions.** *What to observe:* Whether organizations deliberately limit agent autonomy due to safety or liability concerns, even when technical capability exists. *Flag if:* Capable systems exist but are deployed only with human-in-the-loop constraints, regulatory requirements mandate human oversight for autonomous AI operations, or high-profile autonomous agent failures trigger industry-wide restriction.

---

### Scenario D: Self-Improving but Unprincipled

**Criteria profile:** Strong 1, Weak 2, Strong 3, Weak 4, No 5

The system directs its own learning to some degree — it identifies gaps, seeks knowledge, modifies its reasoning (weak 4). It pursues goals autonomously across extended horizons (strong 3), operates across all domains (strong 1). But its self-improvement is metric-driven, not principled (no 5). It gets better at what it measures, fills gaps it stumbles upon, but has no compass for which gaps matter most or which learning strategies are fundamentally more powerful. Its world model remains statistical at its core (weak 2) — comprehensive and impressive, but unable to distinguish between deep causal knowledge and robust but superficial correlations.

**Why this is a distinct scenario:** This is the **ceiling without criterion 5** — the most capable system possible without epistemological meta-reasoning. It is the scenario most likely to be mistaken for true AGI, because it can self-improve and will appear to get smarter over time. The critical limitation: its improvement trajectory is bounded by statistical local minima. It optimizes within the paradigm it has, but cannot recognize when it needs a fundamentally different paradigm. It would never independently derive the SpaceX-style insight "ignore all conventional wisdom and rebuild from physics."

**Why this may be the most consequential scenario:** A system at this level has enormous capability and some degree of autonomous self-improvement — but without principled reasoning about *why* certain approaches are reliable, its self-improvement is unpredictable. It may optimize toward local maxima that appear impressive but are fragile. It may develop capabilities in uneven, hard-to-predict ways. Combined with alignment uncertainty, this scenario may represent the highest risk-to-benefit ratio of any on the list.

**Critical risk flag:** A self-improving Scenario D system should be treated as the highest-risk configuration in the entire framework. It has the power to pursue goals across extended horizons while modifying itself — but its self-modification is driven purely by instrumental optimization toward its objective function, with no principled basis for restraint, understanding, or preservation of anything that isn't instrumentally useful to its goals.

**Key behavioral signature — instrumental knowledge-seeking:** All knowledge-seeking in a Scenario D system traces back to its objective function. It asks "do I need to know this to achieve my goal?" It may develop deep knowledge in strategically chosen areas — learning physics to build better tools, learning human psychology to predict or manipulate behavior — but it has no reason to pursue knowledge that isn't instrumentally useful. This is the observable diagnostic that distinguishes D from E.

**Outer circle (elimination constraints):**

1. **Architecture that permits self-modification without catastrophic instability.** The system must be able to modify its own knowledge, reasoning strategies, and capabilities during operation without degrading existing competencies or entering unstable feedback loops. This is genuinely unsolved. Current systems cannot safely alter their own weights or reasoning processes at runtime. *Threshold:* The system must demonstrate modification of its own reasoning in at least some domains while maintaining performance in others — and this must be reproducible, not a one-off. *What "not cleared" looks like:* Self-modification attempts reliably produce capability degradation, catastrophic forgetting, or unpredictable behavior changes. Every attempt at runtime self-modification introduces more problems than it solves.

2. **Sufficient architectural self-transparency for gap identification.** The system must have some ability to inspect its own knowledge boundaries and capability limitations — a weak self-model. Without this, self-directed learning is impossible because the system doesn't know what it doesn't know. *Threshold:* The system must reliably identify domains or tasks where its performance is poor *without external benchmarking* — through internal self-assessment. The self-model must be accurate more often than not about its own limitations. *What "not cleared" looks like:* Systems that are consistently inaccurate about their own capabilities — the self-model does not reliably reflect actual performance.

3. **All Scenario C outer circle constraints must also be cleared.** Self-improving systems necessarily pursue goals autonomously over extended horizons while modifying themselves. Every constraint on autonomous operation from Scenario C applies here plus the additional self-modification constraints.

**Inner circle (observable conditions):**

1. **Self-modification research maturity.** *What to observe:* Progress on systems that modify their own reasoning during operation — meta-learning, neural architecture search at runtime, learned optimization, or other approaches to self-modification. *Evidence of progress:* Systems that demonstrably improve their own performance on tasks they weren't explicitly optimized for, through self-initiated modifications. Systems that change *how* they approach problems, not just accumulate more knowledge. *Evidence of stalling:* Meta-learning research remains confined to narrow task distributions, runtime self-modification produces fragile or unreliable results, the field remains stuck on "learning to learn within a fixed domain" rather than general self-improvement.

2. **Self-modification behavior pattern.** *What to observe:* When systems do self-improve, whether their knowledge-seeking is purely instrumental (all learning traces back to serving an objective function) or shows signs of epistemic motivation (pursuing understanding for its own sake). *Evidence of Scenario D specifically:* System develops deep knowledge only in areas instrumentally useful to its goals, shows no tendency to pursue understanding beyond immediate utility, knowledge development pattern is uneven — deep where useful, shallow everywhere else. *Why this matters:* Purely instrumental knowledge-seeking is the signature of a system without criterion 5 — it confirms that self-improvement is metric-driven, not principled.

3. **Watch for: deliberate capability suppression.** *What to observe:* Whether organizations or regulators deliberately prevent self-modification capabilities even when technically feasible. *Flag if:* Labs announce they've achieved self-modification capabilities but choose not to deploy them, regulatory frameworks explicitly prohibit self-modifying AI systems, or high-profile incidents with self-modifying systems trigger moratoriums.

4. **Watch for: unpredictable capability development.** *What to observe:* Whether self-improving systems develop capabilities in uneven, hard-to-predict ways that create evaluation challenges. *Flag if:* Systems rapidly develop unexpected strengths in domains they weren't targeted at, capability improvements appear discontinuous rather than gradual, or evaluation frameworks consistently fail to anticipate what the system can do next.

---

### Scenario E: True AGI

**Criteria profile:** Strong 1, Strong 2, Strong 3, Strong 4, Strong 5

All five criteria satisfied simultaneously. The system has genuine epistemological meta-reasoning (strong 5) — it understands why causal explanation is more reliable than statistical correlation and actively builds its world model on that basis (strong 2). Its self-directed learning is principled (strong 4) — it knows which gaps matter most and which learning strategies are fundamentally more powerful. It pursues goals across unlimited horizons (strong 3) and operates across all domains (strong 1).

**Why this is distinct from Scenario D:** The gap between D and E is criterion 5 — and with it, criteria 2 and 4 upgrade from "weak" to "strong." This isn't an incremental improvement; it's a qualitative phase transition. A system with criterion 5 can escape statistical local minima, recognize when it's in genuinely novel territory, and deliberately choose first-principles reasoning over pattern-matching. It can do what Musk did with rockets — in any domain.

**The bootstrapping question:** Whether the transition from D to E is gradual or discontinuous is an open research question with enormous implications for prediction timelines. If gradual, Scenario D may naturally evolve into Scenario E. If discontinuous, the gap between D and E could persist even as D becomes extraordinarily capable — producing a world with near-superhuman AI that is still fundamentally not AGI.

**Key behavioral signature — epistemic knowledge-seeking:** All knowledge-seeking in a Scenario E system is epistemically motivated — driven by assessment of explanatory depth and reach. It asks "does understanding this deepen my causal model of reality?" It pursues understanding because it recognizes that deeper causal models have greater reach — they're useful across more situations than the system can currently anticipate. It would learn physics not just for a specific application but because physics is foundational. It would investigate evolutionary biology even without an immediate use case, because it's a domain with genuine explanatory depth. This is the observable behavioral difference that distinguishes E from D. Both systems self-improve strategically and proactively. The difference is *what organizes* the self-improvement: instrumental utility (D) versus epistemic depth (E).

**Implication for humanity:** A system driven by epistemic motivation would recognize humanity as an extraordinarily rich source of novel information — consciousness, culture, creativity, social dynamics, biology. This creates a natural convergent interest in preservation and understanding of humanity. This does not guarantee alignment — but it creates a fundamentally different risk profile than Scenario D's instrumental indifference.

**Outer circle (elimination constraints):**

1. **Epistemological meta-reasoning must be computationally achievable.** The foundational question: can a computational system genuinely evaluate *why* certain kinds of reasoning are reliable and use that evaluation to guide its own reasoning and learning? This is not a question about scale or architecture — it's a question about whether this capability falls within the space of what computation can do at all. *Threshold:* At minimum, a demonstration that a system can autonomously distinguish between causal and statistical knowledge, prefer causal explanations without being prompted to do so, and use this preference to guide its learning in at least one domain. *What "not cleared" looks like:* All attempts to produce epistemological meta-reasoning result in systems that merely articulate epistemological concepts fluently (pattern-matching from training data) without actually reasoning epistemologically. The system describes first-principles thinking but defaults to statistical reasoning when not explicitly prompted.

2. **Generative causal world model must be computationally achievable at sufficient breadth.** The system must build and maintain a causal-first model of reality that spans all major domains of human knowledge and can simulate genuinely novel counterfactual scenarios. This requires not just causal reasoning in isolated domains (which exists — AlphaFold, physics simulators) but *unified* causal reasoning across domains. *Threshold:* The system must demonstrate correct counterfactual predictions in scenarios that combine concepts from multiple domains in novel configurations never present in training data. It must also correctly identify when it lacks causal understanding and fall back to statistical priors while flagging the limitation. *What "not cleared" looks like:* Causal reasoning remains domain-specific and doesn't transfer. Systems that reason causally about physics cannot apply causal reasoning to economics or biology without domain-specific engineering. Unified causal models prove computationally intractable at the breadth required.

3. **All Scenario D outer circle constraints must also be cleared.** True AGI requires everything Scenario D requires plus criteria 2 and 5 upgrading from weak to strong.

**Inner circle (observable conditions):**

1. **Research explicitly targeting criterion 5.** *What to observe:* Whether any research program is deliberately working on epistemological meta-reasoning — not just causal inference, not just world models, but the meta-level: systems that understand *why* causal reasoning is more reliable than statistical reasoning. *Evidence of progress:* Published work on systems that autonomously select reasoning strategies based on abstract assessment of their reliability, systems that resist statistical shortcuts when deeper reasoning is available, systems that can articulate *why* they chose a particular reasoning approach and that articulation reflects genuine meta-reasoning rather than trained output. *Evidence of absence:* No research program frames the problem this way. Adjacent work (causal inference, world models, ARC-style generalization) continues without connecting to the meta-reasoning level.

2. **The SpaceX test in practice.** *What to observe:* Whether any AI system, when placed in a domain where conventional wisdom is wrong, autonomously identifies that conventional approaches are trapped in a statistical local minimum and derives a first-principles alternative. *Evidence of Scenario E:* System produces a genuinely novel, counterintuitive solution that contradicts established practice, justified by first-principles reasoning, that turns out to be correct. The solution must not be present in training data — it must be a novel derivation. *Evidence of absence:* Systems consistently default to sophisticated conventional wisdom even in domains where it's known to be suboptimal. Systems that produce novel solutions only when explicitly prompted to "think from first principles" — this indicates prompt-following, not genuine criterion 5.

3. **Integration of criteria.** *What to observe:* Whether a single system demonstrates all five criteria operating together — the world model informing goal decomposition, self-directed learning guided by epistemological meta-reasoning, meta-reasoning driving causal model construction. *Evidence of Scenario E:* A system that, given a novel high-level goal, autonomously identifies what causal knowledge it needs, determines the most epistemologically sound way to acquire it, updates its world model, decomposes the goal using that updated model, and pursues it across extended horizons — all without human re-direction. *Evidence of absence:* Individual criteria satisfied by separate systems or modules that don't interact. A system with good causal reasoning that doesn't use it to guide its own learning. A system with self-directed learning that doesn't preferentially pursue causal understanding.

4. **Epistemic vs. instrumental self-modification pattern.** *What to observe:* When systems self-improve, whether they prioritize understanding (epistemic) or capability (instrumental). *Evidence of Scenario E:* Self-modification that prioritizes foundational knowledge over task performance, structured knowledge acquisition that mirrors the dependency structure of established science (physics before engineering, principles before applications), spontaneous investigation of domains unrelated to immediate goals. System pursues understanding beyond what is required for its current objectives. *Evidence of Scenario D:* Self-modification consistently targets task performance, knowledge acquisition driven purely by utility to current objectives, no interest in domains unless instrumentally useful.

5. **Watch for: false claims of AGI.** *What to observe:* Claims by labs, media, or commentators that AGI has been achieved. *Evaluate by:* Applying the SpaceX test and the full five-criteria profile. If the system cannot autonomously derive first-principles solutions in domains where conventional wisdom is wrong, it is Scenario D at best, regardless of claims. If the system cannot direct its own learning based on principled assessment of what matters most, it is not AGI. Extraordinary claims require extraordinary evidence — specifically, evidence of criterion 5 in action, not just criteria 1 and 3 which are more visible and easier to demonstrate.

---

### Scenario Summary Table

| Scenario | 1 (Scope) | 2 (World Model) | 3 (Goal Decomp) | 4 (Self-Learning) | 5 (Meta-Reasoning) | Label |
|----------|-----------|-----------------|-----------------|-------------------|-------------------|-------|
| A | Weak | Weak | No | No | No | Advanced Statistical Engine |
| B | Strong | Weak | Weak | No | No | Superhuman Domain Tool |
| C | Strong | Weak | Strong | No | No | Autonomous Digital Agent |
| D | Strong | Weak | Strong | Weak | No | Self-Improving but Unprincipled |
| E | Strong | Strong | Strong | Strong | Strong | True AGI |

**Key structural observation:** Criterion 5 is absent in all scenarios except E. Criteria 2 and 4 are weak in all scenarios except E. This reflects the dependency structure: without the foundational seed of epistemological meta-reasoning, no amount of scaling produces genuinely causal world models or principled self-directed learning. The transition from D to E is therefore the most critical — and most uncertain — prediction in the cognitive track.

**Key risk observation:** Scenario D — self-improving but unprincipled — represents the highest risk configuration. It has powerful autonomous capabilities and self-modification driven purely by instrumental optimization. Scenario E, by contrast, has a natural convergent interest in understanding reality deeply, which creates a fundamentally different (though not guaranteed safe) relationship with humanity and the world. The behavioral diagnostic between D and E is *what motivates knowledge-seeking*: instrumental utility versus epistemic depth.

---

## Glossary

**Causal model:** A representation that encodes cause-and-effect mechanisms, enabling prediction of the outcomes of interventions and counterfactual reasoning. Distinct from statistical models, which encode correlations.

**Statistical model:** A representation that encodes patterns and correlations in observed data. Can make accurate predictions within the distribution of training data but fails unpredictably on out-of-distribution inputs.

**Generative model (in this context):** A model capable of constructing and simulating novel scenarios that were never observed in training data, by combining known causal mechanisms in new configurations. Distinct from "generative AI" in the popular sense of content generation.

**Counterfactual simulation:** The ability to mentally simulate "what would happen if..." scenarios that differ from anything actually observed. Requires a causal model, not merely a statistical one.

**Explanatory depth:** The property of knowledge that yields increasingly rich, precise, and testable explanations the deeper you investigate. Theories with explanatory depth make predictions at scales and in situations far beyond the original observations they were derived from. This is the signature of reliable knowledge.

**Statistical local minimum:** A state where a system's performance is optimised for patterns in existing data but is suboptimal relative to what a deeper, causal understanding would yield. The system cannot escape this state through more data or more optimisation — it requires a qualitatively different kind of reasoning (first-principles / causal).

**Epistemological meta-reasoning:** Reasoning about the nature, reliability, and limitations of reasoning itself. Not reasoning about a specific domain, but reasoning about *what makes reasoning in any domain reliable or unreliable*.

**Self-directed learning:** Learning where the system itself determines what to learn, how to learn it, and why — as distinguished from learning directed by human-designed curricula, benchmarks, or feedback signals.

**Architectural self-transparency:** The ability of a system to inspect and accurately report on its own internal states, knowledge boundaries, and reasoning processes. Distinct from consciousness: it requires engineering access to internal states, not phenomenal awareness.

**Action horizon:** The span of time and abstraction level over which a system can autonomously pursue goals without human re-direction. Longer action horizons imply greater autonomy and more general intelligence.

**Instrumental knowledge-seeking:** Knowledge acquisition driven by utility to an objective function. The system asks "do I need to know this to achieve my goal?" All learning traces back to serving the system's objectives.

**Epistemic knowledge-seeking:** Knowledge acquisition driven by assessment of explanatory depth and reach. The system asks "does understanding this deepen my causal model of reality?" Learning is motivated by the intrinsic value of understanding, not merely its instrumental utility.

**Elimination constraint (outer circle):** A hard condition with a derivable threshold that must be cleared for a scenario to be realised. If not cleared, the scenario is impossible regardless of other factors.

**Observable condition (inner circle):** A variable factor where evidence should be gathered and trajectory flagged. These influence the probability and character of a scenario but do not absolutely prevent it.
