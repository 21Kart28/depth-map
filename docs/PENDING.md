# Pending: what must change before Depth Map is used with a real client

This is the debt list. Every placeholder, shortcut, and deferred requirement goes here with a priority and a status. Update it in the same commit that adds or clears an item.

Status values: `open`, `in progress`, `done`. Priority: P0 blocks any real-client use; P1 blocks a clinician pilot; P2 blocks a public claim.

## Content placeholders (first drafts; rewrite before use)

| Item | Where | Priority | Status | Notes |
| --- | --- | --- | --- | --- |
| Codebook v1 definitions reviewed line by line | `src/depthmap/data/codebook.json` | P1 | open | Drafted as placeholder. Each code needs a final definition, example, counter-example, and a check against the no-diagnosis, no-Jung rule. Ideally reviewed by one clinician. |
| Question bank v2 reviewed against the property list | `src/depthmap/data/questions.v2.json` | P1 | open | Drafted as placeholder. Each question checked against plan v2 section 3.1 and 3.2. No question ships to a client without passing. |
| Framing sentences rewritten | `questions.v2.json` | P2 | open | Placeholders are serviceable, not good. |
| Prompt v2 rewritten against real model output | `src/depthmap/prompts/analysis.py` | P1 | open | Current prompt is a first draft that has never run against the real model. |
| Output validator rules reviewed pattern by pattern | `src/depthmap/data/banned_terms.json` | P1 | open | Placeholder patterns for advice, diagnosis words, reassurance, praise and dates. They miss a lot and will reject some harmless sentences. |
| Safe-template text for risk responses | `src/depthmap/safety/templates.py` | P0 | open | Must follow #chatsafe guidance and name real, locale-correct crisis resources. Placeholder text is a stub. |
| Risk lexicon sourced from a published list | `src/depthmap/safety/lexicon.json` | P0 | open | Placeholder keywords are from memory. Replace with a cited lexicon and validate on an external annotated set. |
| Client-facing copy (labels, review-latency line, consent text) | client view | P0 | open | Must use the permitted-language list in `04_safety_and_regulatory.md` section 5. |

## Safety

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| Risk stage validated on an external clinician-annotated set; sensitivity and specificity reported | P0 | open | No real-client text until done. |
| Sycophancy hold-out set passes (no agreement with planted distortions) | P0 | open | Synthetic set in `tests/safety/`. |
| Clinician-set emergency instructions configurable per client | P0 | open | |
| Adverse-event log categories agreed with a clinician | P1 | open | |
| Output validator word lists reviewed (advice, diagnosis, reassurance, praise) | P1 | open | The validator runs on every analysis since the placeholder list was added; the list itself is tracked under content placeholders. |

## Data and legal (not built in this project; architecture must not preclude them)

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| BAAs with hosting, embedding, and LLM providers (or self-hosted model) | P0 | open | Only providers that sign a BAA are usable in production. |
| Encryption at rest with managed keys; TLS in transit | P0 | open | SQLite file is unencrypted now. |
| Per-user auth, MFA for clinicians, least-privilege roles | P0 | open | No auth exists. |
| Access log on every read of entry text | P0 | open | Audit table exists for risk events only. |
| Retention and deletion policy, configurable per clinician jurisdiction | P0 | open | Not researched; needs legal review. |
| Separate revocable consents: clinician use, automated analysis, retention beyond care | P0 | open | Revocation must delete from the retrieval index. |
| No third-party analytics or ad SDKs on any screen with entry text; verified by traffic capture | P0 | open | |
| Provider contract: no training on inputs; identifiers stripped before model calls | P0 | open | |
| Plain-language privacy notice | P1 | open | |
| APA App Evaluation Model self-assessment filled in | P2 | open | |

## Validation (claims depend on these)

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| Retrieval evaluation with reported numbers (precision@k, recall@k, MRR) | P2 | open | V3.5. Engineering claim only. |
| Per-theme extraction agreement against owner labels | P2 | open | V3.5. |
| Clinician perceived-accuracy study (about 20 clinicians; SUS, MARS, IUS) | P2 | open | Designed in V4.5, run later. |
| Blinded model-vs-clinician analysis comparison | P2 | open | Later. |
| Rumination check on the bank (R2T2 in pilot) | P2 | open | Later. |

## Positioning and claims

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| README uses only permitted language; no Jungian terms; "not a medical device" statement present | P1 | open | |
| `docs/evidence.md` added with the design-choice table | P2 | open | From the evidence brief. |
| Resume and pitch lines carry no outcome claims | P2 | open | |

## Architecture debts (shortcuts taken to move fast)

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| Clinician report is a markdown export, not a UI | P2 | open | Fine for this project. |
| Clinician actions (acknowledge, merge, retire themes) are API calls with no UI | P2 | open | |
| Single-client assumption throughout | P1 | in progress | Every entry has a `client_id` (default `local`) and the question history behind `GET /questions/next` is scoped by it. Nothing sets another id yet; keep the retrieval index isolated per client when it is built. |
| Classifier risk stage is optional; rule-based stage is the only guaranteed path | P1 | open | |
| `questions` table is created but nothing fills it | P2 | open | The bank is still read from JSON and each entry keeps its own copy of the question text. Fill the table when questions can be turned on and off per client. |
| No migration tool; tables are created if missing | P2 | open | A change to a column means deleting `depthmap.db` by hand. Entries stored before analysis schema v2 cannot be read. |
| Reflection length is checked in characters (40 to 1200), not as 2 to 4 sentences | P2 | open | Counting sentences breaks on quotes and abbreviations. |
| The CLI does not ask for the client's own feeling word | P2 | open | Only `POST /entries` takes `client_emotion`. |
| The output validator only knows the answer as context | P1 | open | A date is allowed when the answer contains it. References to earlier entries are caught by a few phrases only, and method detail under risk content is not checked; both wait for retrieval and the risk stage. |
| A reflection that quotes advice from the answer is rejected | P2 | open | The advice, diagnosis, reassurance and praise rules do not look at the answer, so quoting "you should" back fails the entry with a 502. |
| A model refusal has no handling of its own | P1 | open | It ends as a provider error or as a failed analysis after one retry. |
