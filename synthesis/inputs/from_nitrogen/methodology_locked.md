# Locked methodology — synthesis_phase_s1

This document is a self-contained extract of the methodological discipline that governs Nitrogen's `violence-abrahamic` repository. Boron should operate under the same rules when consuming this export.

Source of authority: `CLAUDE.md` at the root of `violence-abrahamic`. If anything below is unclear, defer to `CLAUDE.md`. Do not relax these rules in synthesis without an explicit phase decision recorded in both repositories.

---

## Evidence hierarchy

Every claim in cases, reports, and downstream analysis must be locatable on this hierarchy. A control-axis claim only becomes strong at Levels 4–5.

| Level | What it shows |
|-------|---------------|
| 1 | Text-only — the passage makes a structure available |
| 2 | Commentary / reception — interpreters understood it a particular way |
| 3 | Lived-religion — communities, clergy, missionaries, courts, schools, rulers, movements actually used it |
| 4 | Institutional-control — the passage / idea entered law, schooling, discipline, conversion systems, slavery, colonial policy, child removal |
| 5 | Incentive / causal — the text supplied authority, absolution, moral courage, coordination, recruitment, legal basis, or sanction *beyond* ordinary non-textual motives (greed, empire, race, fear, revenge) |

Important: commentary alone (Level 2) does not prove institutional use. Institutional use (Level 4) does not prove text was causal — that requires Level 5 evidence distinguishing text from non-textual forces.

---

## Locked rule chain

```
No context, no escalation.
No source, no claim.
No lived uptake, no implementation claim.
No institutional coupling, no control-axis claim.
No evidence of incentive amplification, no causal claim.
```

These five rules are not stylistic. They are the project's working epistemology. Any export, derived analysis, or rescore must respect them.

---

## Claim-discipline labels

Every assertion in tables, reports, and manuscript text must carry one of these labels:

- **`observed`** — documented text, event, policy, sermon, law, institution, or testimony directly attested in a primary source.
- **`source-backed plausible`** — evidence has been attached, but the evidence layer is not exhaustive (e.g. covers structure but not denominational / regional / testimony layers). The current `christian_baseline_v1` is at this level for 15 of 16 cases.
- **`documented`** — exhaustive evidence, including denominational / regional / testimony layers where applicable. Phase 3.10+ deep-dives lift specific cases toward this status.
- **`derived`** — inference from text + lived uptake + institutional coupling. Must cite all three layers.
- **`speculative`** — plausible causal role needing more evidence. Must be explicitly flagged.
- **`rejected`** — claims not supported by evidence. Should still be retained with rationale to prevent re-emergence.

Important: `plausible` does not mean proven. Commentary evidence does not prove institutional use. Institutional use does not prove text was causal. Each of these must be coded separately.

---

## `text_role_assessment` allowed values

This field captures whether the text actually played a causal role in the case, or whether it functioned as ornament around non-textual motives. It is the most important single field for the synthesis question "did the text matter?"

| Value | Meaning |
|-------|---------|
| `decorative_after_the_fact` | Text attached as ornament after the action; not causally central. |
| `legitimating` | Text justifies / moralizes a project mainly driven by empire, race, land, labor, state. |
| `motivating` | Text gives moral colouring that strengthens motivation without supplying authority. |
| `coordinating` | Text functions as a shared signal that aligns dispersed actors on a common script. |
| `authorizing` | Text supplies institutional or sacred authority for action; without the text, the authorization fails. |
| `identity_boundary_marker` | Text used to draw and police inside / outside lines, not to direct specific action. |
| `recruitment_tool` | Text used to mobilize participants; primary effect is on recruitment, not authorization. |
| `legal_basis` | Text functions as an explicit legal premise, cited in courts, charters, or statutes. |
| `contested` | Multiple incompatible readings circulated within the same regime; the case cannot be reduced to a single role. |
| `unclear` | Insufficient evidence to assign a role. Different from `decorative_after_the_fact`, which is itself a finding. |

Coding rule: any case scored higher than `legitimating` (i.e. `motivating` and above) requires Level 4 or Level 5 evidence under the hierarchy.

---

## Three-alternative test (working hypothesis)

When a case appears to involve missionary or evangelizing institutions, the working hypothesis is that *missionaries are implementation agents at the junction of sacred text and institutional power: the text supplies authority, absolution, moral courage, religious sanction; power supplies institutional machinery.*

This is a **hypothesis to test**, not a settled claim. For every such case, code the three alternatives separately and pick the best-supported:

1. **Text as driver** — text actively authorizes, motivates, and sanctifies the action.
2. **Text as legitimizer** — text justifies / moralizes a project mainly driven by empire, race, land, labor, or state control.
3. **Text as decoration** — text is attached afterward and is not causally central.

The `text_role_assessment` field encodes the answer.

---

## Scope discipline (Christian-only active)

The active phase scope is methodological development plus full application to **Christianity only**. Islam, Hindu / Indic, Buddhist / Jain, and other comparative cases are deferred to a later comparative phase under `data/lived_religion/future_comparative_cases/`. Boron synthesis should not introduce non-Christian cases into this phase's analysis without an explicit phase decision recorded in both repositories.

---

## Frozen-baseline rule

`christian_baseline_v1/` is immutable. Refinements create a new freeze label; they do not edit the frozen copy. Any drift between live data and the freeze must be flagged, not silently merged. See `EXPORT_NOTES.md` for the drift status at export time.

---

## Terminology cautions

- **Residential / boarding schools:** use `unmarked graves` or `possible unmarked burials`, not `mass graves`, unless a specific source documents excavated mass graves. Loose terminology is exploited by denialists.
- **Pratt motto** — `"Kill the Indian in him, and save the man"` is associated with the U.S. Carlisle Indian Industrial School. Don't misattribute it to the Canadian residential school system; the assimilationist *logic* is shared, the *phrase* is not.
- **Regime, not tradition.** Score `Counter-Reformation Catholicism under the Roman Inquisition`, not `Catholicism`. Inherited from the parent `code-geometry-abm` rubric on Boron.

---

## Reference

For full context on how this discipline was developed, see:

- `CLAUDE.md` (Nitrogen) — the canonical statement of these rules.
- `Religious Framework and Violence.md` (Nitrogen) — the design transcript that produced them.
- `manuscript/manuscript.tex` (Boron) — the parent ABM paper that establishes the regime-not-tradition standard.
