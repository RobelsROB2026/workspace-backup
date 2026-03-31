# Static Syntax Analysis v2: Computational Signature of Hypnotic Induction Language

**Corpus:** 166 files (~373,000 words total). After filtering for actual hypnotic script content (second-person density ≥ 50/1k words), the **core analysis corpus** is **26 pure scripts, 17,819 word tokens, 1,816 unique types, 839 sentences**. Theory/textbook material (129 files, ~206k words) and mixed-content files (11 files, ~149k words) are used as control baselines.

**Method:** Regex pattern matching, NLTK tokenization and POS tagging, frequency analysis, n-gram extraction, sentence-type classification, collocational analysis.

**Date:** 2026-03-31
**Supersedes:** v1 (24 scripts, 10,685 tokens — pilot study)

---

## 0. Corpus Structure and Filtering

The raw 166-file corpus is heterogeneous. Automated you-density classification reveals three strata:

| Stratum | Files | Words | You-density | Content Type |
|---|---|---|---|---|
| Pure scripts | 26 | 17,819 | ≥50/1k | Direct hypnotic inductions, deepeners, guided visualizations |
| Mixed content | 11 | ~149k | 20–50/1k | Self-help books with embedded scripts (*Creative Visualization*, *Practical Guide to Self-Hypnosis*) |
| Theory/navigation | 129 | ~206k | <20/1k | Textbook chapters, website navigation pages, non-English texts, academic prose |

**Critical finding:** Only **4.8% of the corpus by word count** (17,819 of 373,030 words) is pure hypnotic script text. The remaining 95.2% is *about* hypnosis rather than *performing* it. This contamination ratio is itself revealing: hypnotic language is radically distinct from analytical language about the same subject. The two registers share vocabulary but diverge on every structural metric measured below.

The 26 pure scripts subdivide into:
- **24 induction scripts** (~12,500 words): arm levitation, progressive relaxation, Elman, NLP, rapid inductions, guided imagery
- **2 therapeutic/instructional scripts** (~5,300 words): self-hypnosis guide chapter, theta meditation protocol

All quantitative findings below are from the **pure script** subcorpus unless stated otherwise.

---

## 1. Syntactic Structure: Commands vs. Permissions

### 1.1 Sentence-Type Distribution (n = 839)

| Type | Count | % |
|---|---|---|
| Verb-initial imperatives | 109 | 13.0% |
| Permissive framing (`can`/`may`/`might`/`could`/`perhaps`) | 25 | 3.0% |
| You-initial declaratives (covert directives) | 96 | 11.4% |
| Questions | 50 | 6.0% |
| Other declarative | 546 | 65.1% |

### 1.2 The Imperative-to-Permissive Ratio

**Full corpus: 4.36:1**

This is the first major departure from the v1 pilot. The pilot found 1.70:1. At scale, after removing analytical prose contamination, the ratio more than doubles. Hypnotic scripts are **overwhelmingly imperative**, not suggestive. The Ericksonian myth of hypnosis-as-indirect-suggestion is not supported by the structural data — at least not at the sentence level.

When you-initial declaratives are reclassified as covert directives (which they functionally are — "Your eyes are getting heavy" is a command wearing a description's clothing), the **true directive rate rises to 24.4%** of all sentences. One in four sentences is a directive of some kind.

### 1.3 Induction vs. Therapeutic Scripts

| Metric | Induction (n=502) | Therapeutic (n=343) |
|---|---|---|
| Imperatives | 18.1% | 5.8% |
| Permissive | 3.2% | 2.6% |
| You-initial | 9.6% | 14.3% |
| Questions | 2.6% | 10.8% |
| **Imp:Perm ratio** | **5.69:1** | **2.22:1** |
| **True directive rate** | **27.7%** | **20.1%** |

**The ratio does change.** Inductions are nearly 3x more imperative than therapeutic scripts. But even therapeutic scripts maintain a 2.22:1 command-to-permission ratio — the grammar never flips to permissive-dominant.

The key shift is *how* directives are delivered:
- **Inductions** use overt imperatives (18.1%) — "Close your eyes," "Let your body relax"
- **Therapeutic scripts** shift to you-initial covert directives (14.3% vs. 9.6%) — "You are finding yourself more comfortable," "Your confidence is growing"
- **Therapeutic scripts ask more questions** (10.8% vs. 2.6%) — but these are rhetorical presuppositions, not genuine inquiries

The grammar modulates its *surface* from direct command to descriptive assertion, but the deep structure remains directive throughout.

### 1.4 Directive Verb Hierarchy

The top 10 sentence-initial imperative verbs:

| Rank | Verb | Count | Function |
|---|---|---|---|
| 1 | **let** | 25 | Paradoxical command (imperative of permission) |
| 2 | feel | 7 | Command to generate internal state |
| 3 | close | 7 | Behavioral instruction |
| 4 | notice | 7 | Directed attention |
| 5 | take | 7 | Behavioral instruction ("take a breath") |
| 6 | look | 4 | Directed attention |
| 7 | sleep | 4 | State command (Elman tradition) |
| 8 | make | 4 | Behavioral instruction |
| 9 | continue | 4 | Continuity presupposition as command |
| 10 | breathe | 3 | Behavioral instruction |

`let` dominates imperative-initial position at nearly 4x the frequency of any other verb. Its imperative use is the defining syntactic act of the corpus.

---

## 2. Trance Grammar: The Milton Model in Quantitative Detail

### 2.1 Nominalizations

**221 tokens across 29 types. Rate: 12.40 per 1,000 words.**

| Nominalization | Count | Function |
|---|---|---|
| relaxation | 60 | Central process-as-entity; autonomous agent ("relaxation moves through") |
| feeling | 48 | Reified internal state |
| experience | 26 | Meta-nominalization (nominalizes everything) |
| imagination | 12 | Reified cognitive process |
| sensation | 8 | Reified somatic perception |
| attention | 8 | Reified cognitive targeting |
| awareness | 7 | Reified meta-cognition |
| healing | 7 | Reified therapeutic process |
| visualization | 6 | Reified imaging process |
| consciousness | 6 | Reified awareness-of-awareness |

**Scale comparison with v1:** The pilot found 89 nominalization tokens (8.3/1k words). At scale, the rate rises to **12.40/1k** — a 49% increase. The pure script subcorpus is denser in nominalizations than the contaminated pilot sample suggested.

`relaxation` remains the dominant nominalization (27.1% of all nominalization tokens). It functions as an autonomous agent in the grammar: relaxation "moves," "spreads," "flows," "deepens." This agentive nominalization pattern is the core mechanism of hypnotic vagueness — the subject cannot resist a noun.

### 2.2 Unspecified Verbs

**534 tokens across 15+ types.**

| Verb | Count | Rate/1k |
|---|---|---|
| let | 107 | 6.00 |
| feel | 82 | 4.60 |
| go | 60 | 3.37 |
| become | 40 | 2.24 |
| move | 40 | 2.24 |
| notice | 32 | 1.80 |
| allow | 28 | 1.57 |
| experience | 26 | 1.46 |
| know | 19 | 1.07 |
| find | 18 | 1.01 |
| sense | 16 | 0.90 |
| drift | 14 | 0.79 |
| come | 11 | 0.62 |
| happen | 10 | 0.56 |
| grow | 9 | 0.50 |

The unspecified verb rate is **30.0 per 1,000 words** — roughly 1 in every 33 words is a semantically underspecified verb. These verbs share a common property: they delete critical information about *what* is being felt/experienced/noticed/allowed, forcing the listener into trance-generative internal search.

The trio of **let** (6.00/1k), **feel** (4.60/1k), and **go** (3.37/1k) accounts for 46.6% of all unspecified verb tokens. This is the engine of hypnotic indeterminacy.

### 2.3 Embedded Commands

**179 embedded commands identified. Rate: 10.05 per 1,000 words.**

| Pattern | Count | Top Embedded Verbs |
|---|---|---|
| "you can [V]" | 66 | relax (8), continue (4), let (3) |
| "you will [V]" | 53 | be (9), find (4), want (4) |
| "I want you to [V]" | 30 | imagine (6), concentrate (3), be (2) |
| "allow yourself to [V]" | 7 | be (3), relax (2), think (2) |
| "you might [V]" | 6 | like (2), be (2) |
| "I wonder if you..." | 5 | — |
| "don't [try/need] to [V]" | 4 | resist (1), breathe (1) |
| "you don't need to [V]" | 3 | — |
| "you find yourself [V]" | 3 | — |

**"you can [V]"** is the dominant embedding frame (36.9% of all embedded commands). The modal `can` performs double duty: it grants permission (permissive surface) while directing action (imperative deep structure). "You can relax" is functionally identical to "Relax" but frames the command as the subject's own capability.

**"I want you to [V]"** (16.8%) is the most explicit embedding — the hypnotist's desire is stated directly as the subject's task. It appears almost exclusively in the Elman tradition scripts.

**"you will [V]"** (29.6%) functions as predictive command — the hypnotist describes a future state as fact, presupposing compliance. The most common object verb is `be` (9 instances): "you will be" asserts the subject's becoming as already determined.

### 2.4 Pacing and Leading

**180 pacing/leading phrase tokens. Rate: 10.10 per 1,000 words.**

| Phrase | Count |
|---|---|
| as you | 71 |
| when you | 25 |
| and now | 21 |
| more and more | 13 |
| while you | 12 |
| deeper and deeper | 10 |
| the more you | 9 |
| with each | 8 |
| each time | 8 |
| with every | 3 |

**`as you` dominates at 71 tokens** — nearly 40% of all pacing phrases. This temporal-connective is the fundamental pacing→leading bridge: "As you [observable behavior], you [desired state]." It links a truism (what the subject is already doing) to a suggestion (what the hypnotist wants them to do), creating a logical-seeming causal chain that doesn't exist.

**Complete pacing→leading transitions** (where both halves of the pattern are present in a single sentence): **19 instances identified.** These are structurally: `[temporal connector] + [pacing clause] + [leading clause]`. Example: "As you continue to breathe deeply, you begin to feel even more relaxed."

### 2.5 Presuppositions

**123 presupposition markers. Rate: 6.90 per 1,000 words.**

| Type | Marker | Count |
|---|---|---|
| Comparative | deeper | 51 |
| Comparative | even more | 16 |
| Comparative | further | 16 |
| Process | beginning to | 13 |
| Continuity | continue to | 12 |
| Continuity | still | 9 |
| Temporal | already | 3 |
| Awareness | notice that | 3 |

`deeper` alone accounts for 41.5% of all presupposition markers. The word presupposes that the subject is already *in* a state that has depth — it asserts the existence of trance as a precondition of talking about it. Every "go deeper" presupposes that you are already deep.

The presupposition stack is: **comparative (67.5%) > process (20.3%) > continuity (17.1%) > temporal/awareness (4.9%)**. The grammar is overwhelmingly oriented toward asserting *more of something already happening*, not initiating something new.

---

## 3. Cadence and Repetition

### 3.1 Lexical Density

| Subcorpus | Lexical Density |
|---|---|
| **Pure scripts** | **47.16%** |
| Induction scripts | 46.29% |
| Therapeutic scripts | 48.41% |
| Mixed content (books) | 49.84% |

**47.16% lexical density is extremely low.** For comparison:
- Academic prose: 60–70%
- Conversation: 40–50%
- Fiction: 50–55%
- Hypnotic script: **47%**

Hypnotic language sits at the *conversational* end of the spectrum, even lower than fiction. More than half of all words are function words: pronouns, auxiliaries, conjunctions, prepositions. This produces the characteristic "flow" of hypnotic language — a stream of grammatical connective tissue with relatively few content anchors, each content word carrying disproportionate weight because the surrounding matrix is semantically thin.

**The induction/therapeutic split is negligible** (46.29% vs. 48.41%). Both register at the same density floor.

### 3.2 Type-Token Ratio and Vocabulary Repetition

| Metric | Value |
|---|---|
| Type-Token Ratio (TTR) | 0.1019 |
| Moving Average TTR (MATTR, w=500) | 0.3848 |

**TTR of 0.10** means that for every 10 words spoken, only 1 is a word not already used. The vocabulary is extremely repetitive. MATTR (which controls for text length) at **0.38** confirms this is not an artifact of corpus size — within any 500-word window, only 38% of words are unique. This is low even for spoken language (typical spoken MATTR: 0.42–0.50).

This repetition is not a defect. It is a design feature. The same small vocabulary cycles through different syntactic frames, producing a **lexical loop** — the listener hears the same words rearranged, creating familiarity without boredom, trance without content.

### 3.3 Structural Repetition: "X and X" Intensifiers

| Pattern | Count |
|---|---|
| more and more | 13 |
| deeper and deeper | 10 |
| tighter and tighter | 5 |
| farther and farther | 3 |
| stronger and stronger | 1 |
| lighter and lighter | 1 |
| harder and harder | 1 |
| less and less | 1 |

The **"X and X" doubling** pattern occurs 36 times in 17,819 words (2.02/1k). It is a rhythmic intensifier that performs three functions simultaneously:
1. **Semantic:** asserts progressive intensification
2. **Temporal:** implies ongoing process (presupposes the state already exists)
3. **Prosodic:** creates a rhythmic beat that entrains the listener's attention

"more and more [X]" is always followed by a state adjective: `relaxed` (7), `comfortable` (1). The pattern is frozen: it does not generate novel combinations.

### 3.4 Key Bigrams and Trigrams

**Top content bigrams** (at least one non-stopword):

| Bigram | Count | Note |
|---|---|---|
| your eyes | 97 | Primary body focus |
| your body | 46 | Whole-body reference |
| your hands | 43 | Somatic anchor |
| close your | 36 | Core behavioral command |
| i want | 31 | Hypnotist-desire frame |
| want you | 31 | ... continuation |
| my voice | 28 | Auditory anchor |
| your eyelids | 28 | Micro-focus |
| just let | 26 | Permissive imperative |
| let your | 26 | ... continuation |

**Top content trigrams:**

| Trigram | Count | Function |
|---|---|---|
| close your eyes | 28 | The canonical command |
| your subconscious mind | 17 | Invocation of unconscious agency |
| open your eyes | 13 | Emergence command |
| your conscious mind | 12 | Conscious/unconscious frame |
| heavy and relaxed | 11 | State descriptor |
| your whole body | 11 | Whole-body generalization |
| deeper and deeper | 11 | Progressive intensification |
| the hypnotic state | 10 | Meta-reference to trance |
| going to count | 10 | Countdown frame |
| closing closing closing | 8 | Pure rhythmic repetition |

**"close your eyes" (28) / "open your eyes" (13)** form a bookend pair — the entry and exit gates of trance. The 2.15:1 close:open ratio reflects the corpus's bias toward induction over emergence.

**"closing closing closing" (8)** is a pure rhythmic device — tripling a single word for prosodic entrainment. It has no semantic content beyond the first token; the repetitions are pure cadence.

### 3.5 Sentence Length Distribution

| Range | % | Interpretation |
|---|---|---|
| 1–5 words | 7.4% | Micro-commands ("Sleep now.") |
| 6–10 words | 17.4% | Short directives |
| 11–15 words | 22.4% | **Modal range** — typical hypnotic sentence |
| 16–20 words | 14.3% | Extended suggestions |
| 21–30 words | 19.1% | Compound pacing/leading |
| 31–50 words | 12.4% | Complex embedded structures |
| 51+ words | 7.0% | Run-on trance language |

**Mean: 24.6 words. Median: 17 words.** The mean-median gap (7.6 words) reflects a right-skewed distribution: most sentences are short and direct, with a long tail of extended compound sentences. The modal range (11–15 words) is exactly where short-enough-to-parse meets long-enough-to-embed-suggestion.

---

## 4. The Master Verbs

### 4.1 Full Verb Frequency Table

| Rank | Verb | Count | Rate/1k | Function Class |
|---|---|---|---|---|
| 1 | **let** | 107 | 6.00 | Paradoxical command |
| 2 | relax | 87 | 4.88 | State command |
| 3 | feel | 82 | 4.60 | Internal-state command |
| 4 | want | 65 | 3.65 | Desire-framing |
| 5 | close | 63 | 3.54 | Behavioral |
| 6 | go | 60 | 3.37 | Movement/release |
| 7 | open | 43 | 2.41 | Behavioral |
| 8 | become | 40 | 2.24 | State transition |
| 9 | move | 40 | 2.24 | Somatic |
| 10 | begin | 36 | 2.02 | Process initiation |
| 11 | count | 35 | 1.96 | Procedural |
| 12 | notice | 32 | 1.80 | Directed attention |
| 13 | take | 32 | 1.80 | Behavioral |
| 14 | think | 32 | 1.80 | Cognitive direction |
| 15 | allow | 28 | 1.57 | Permissive |

### 4.2 "Let": The Dominant Paradoxical Command

**`let` is confirmed as the master verb at 6.00 per 1,000 words** — a rate 23% higher than `relax` (4.88/1k) and 30% higher than `feel` (4.60/1k).

The v1 pilot identified `let` as dominant. At scale, this finding holds and strengthens. `let` appears at nearly 1.5x the rate of any other content word except `eyes` (111 tokens, but as a noun, not a verb).

#### 4.2.1 "Let" + Object Patterns

| Pattern | Count | Interpretation |
|---|---|---|
| let go | 21 | Release command (intransitive — what is released is deleted) |
| let yourself | 13 | Reflexive permission |
| let them | 10 | Third-person reference to body parts ("let them grow limp") |
| let it | 7 | Pronoun without clear antecedent — forced ambiguity |
| let your eyes | 5 | Specific body part |
| let us | 4 | Inclusive plural (rapport building) |
| let your subconscious | 4 | Invocation of unconscious agency |
| let your shoulders | 4 | Descending body scan |
| let your neck | 3 | ... continuation |
| let your face | 3 | ... continuation |
| let every muscle | 3 | Universal quantifier |
| let all | 3 | Universal quantifier |

**"let go" (21)** is the single most common `let` construction — and it is maximally vague. "Let go" of *what*? The object is deleted, forcing the listener to supply their own referent. This is a textbook example of deletional syntax producing trance depth.

**"let your [body part]" (22 total)** forms a descending body scan pattern: eyes → subconscious → shoulders → neck → face → eyelids → mind → chest → body. This is the canonical progressive relaxation sequence encoded in verb collocations.

#### 4.2.2 "Let" Verb Neighborhood

Verbs appearing within 8 words of `let` (collocational cluster):

| Verb | Co-occurrences | Interpretation |
|---|---|---|
| go | 51 | **Primary satellite.** "Let go" cluster |
| relax | 34 | State achievement |
| close | 14 | Behavioral pair |
| drift | 9 | Dissociative movement |
| open | 9 | Counterpoint |
| become | 9 | State transition |
| drop | 8 | Gravity/release |
| want | 7 | Desire framing |
| feel | 6 | Internal state |

The `let`-`go`-`relax` triangle is the collocational core of hypnotic induction. These three verbs co-occur within 8 words of each other with extreme frequency: `go` appears near `let` 47.7% of the time. This is not a cluster — it is a **collocational lock**: in hypnotic syntax, `let` *predicts* `go`, and `go` *predicts* `relax`.

#### 4.2.3 "Let" vs. "Allow": The Permission Hierarchy

| Verb | Count | Rate/1k |
|---|---|---|
| let | 107 | 6.00 |
| allow | 28 | 1.57 |

**let:allow ratio = 3.82:1**

The v1 pilot found `allow` at 21% of `let`'s frequency. At scale, `allow` drops to **26.2%** of `let`'s frequency. The grammar's preference for the imperative form of permission over the formal permissive form is confirmed and amplified.

`allow` is more formal, more explicit, more Latinate. `let` is more direct, more Anglo-Saxon, more rhythmically abrupt (one syllable vs. two). In the context of trance rhythm, `let` is the superior choice: it occupies less prosodic space and delivers its paradox — a command to stop commanding — with maximum compression.

### 4.3 Verb Functional Clusters

The top 15 verbs sort into five functional classes:

**1. Permission/Release** (135 tokens, 7.58/1k): `let` (107), `allow` (28)
The paradoxical cluster: commands to stop resisting.

**2. State Assertion** (209 tokens, 11.73/1k): `relax` (87), `feel` (82), `become` (40)
Commands that assert internal states into existence.

**3. Behavioral Instruction** (138 tokens, 7.75/1k): `close` (63), `open` (43), `take` (32)
Direct physical commands.

**4. Attention Directing** (64 tokens, 3.59/1k): `notice` (32), `think` (32)
Commands that steer internal focus.

**5. Movement/Process** (136 tokens, 7.63/1k): `go` (60), `move` (40), `begin` (36)
Kinetic verbs that presuppose ongoing process.

The distribution is: **State Assertion > Movement/Process ≈ Behavioral Instruction ≈ Permission/Release > Attention Directing.** The grammar spends more energy asserting states than any other single function.

---

## 5. Additional Structural Metrics

### 5.1 Pronoun Distribution

| Form | Count | Rate/1k |
|---|---|---|
| you | 818 | 45.9 |
| your | 783 | 43.9 |
| **Total you-forms** | **1,601** | **89.8** |
| i | — | — |
| my | — | — |
| **Total I-forms** | **249** | **14.0** |
| **You:I ratio** | | **6.43:1** |

**89.8 you-forms per 1,000 words** means roughly 1 in every 11 words is a second-person pronoun. The script is, structurally, a sustained act of addressing: the subject is named (via `you`/`your`) with relentless frequency.

The **6.43:1 You:I ratio** is higher than the v1 pilot or the mixed-content subcorpus (4.62:1). Pure hypnotic scripts are *more* other-directed than any surrounding text. The hypnotist linguistically effaces themselves.

### 5.2 Sensory Channel Distribution

| Channel | Count | % |
|---|---|---|
| Kinesthetic | 321 | **60.3%** |
| Visual | 134 | 25.2% |
| Auditory | 77 | 14.5% |

**Kinesthetic dominance at 60.3%** is a defining feature. Hypnotic language is body language. The grammar is organized around somatic experience — feeling, heaviness, warmth, tension, comfort — not visual imagery or sound. This inverts the common assumption that hypnosis is primarily a visual/imaginative phenomenon. The data says it is primarily a *felt-sense* phenomenon.

The V-A-K ordering from most to least frequent is **K > V > A** — the opposite of normal prose (where visual metaphors dominate) and different from the whole-corpus ratio (where V and K were nearly equal at 41.5% and 38.7%). Filtering out theory text dramatically shifts the channel balance toward the kinesthetic.

### 5.3 Negation

**68 negation tokens. Rate: 3.82 per 1,000 words.**

| Form | Count |
|---|---|
| not | 37 |
| don't | 14 |
| no | 10 |
| won't | 7 |
| nothing | 6 |
| never | 1 |

The negation rate is low — about 1 negation per 262 words. Hypnotic language is overwhelmingly **affirmative**. When negation does appear, it typically takes the form "you don't need to [resist/try/think]" — a negative permission that functions as a positive command by presupposing the possibility of resistance and dismissing it.

### 5.4 Temporal Architecture

| Marker | Count | Function |
|---|---|---|
| now | 182 | Anchoring to present moment |
| continue | 28 | Continuity presupposition |
| slowly | 24 | Pace modulation |
| deeper | 51 | Progressive intensification |
| soon | 16 | Near-future presupposition |
| further | 16 | Spatial/depth extension |
| deeply | 16 | State intensifier |
| even | 36 | Comparative presupposition |
| beginning | 13 | Process initiation |

`now` at **182 tokens (10.21/1k)** is the most frequent temporal marker — occurring more often than any verb except `let`. This anchors the language perpetually in the present tense and present moment. Hypnotic grammar is an eternal present: things are always happening *now*, always *beginning*, always *continuing*, never complete.

---

## 6. Synthesis: The Computational Fingerprint

The formal linguistic fingerprint of hypnotic induction scripts, extracted from 26 pure scripts (17,819 words), is defined by eight quantitative signatures:

### Signature 1: Imperative Dominance (4.36:1)
Hypnotic language is 4.36x more imperative than permissive. The Ericksonian myth of pure indirection is not supported at scale. Commands outnumber suggestions at every level of analysis. The directive rate rises to 24.4% when covert you-initial directives are included.

### Signature 2: The "Let" Singularity (6.00/1k words)
`let` is the single most frequent verb, occurring at 6.00/1k words — 23% more than `relax`, the next most frequent. It is the paradoxical command: an imperative whose content is permission. Its primary collocational partner is `go` (51 co-occurrences within 8 words), forming the `let`-`go`-`relax` collocational lock.

### Signature 3: Nominalization Density (12.40/1k words)
The nominalization rate is 49% higher than the pilot estimate. `relaxation` accounts for 27.1% of all nominalization tokens and functions as an autonomous grammatical agent.

### Signature 4: Embedded Command Rate (10.05/1k words)
One in every 100 words participates in an embedded command pattern. "you can [V]" is the dominant frame (36.9%), performing the same paradox as `let` — framing command as capability.

### Signature 5: Extreme Lexical Poverty (MATTR = 0.38, LD = 47%)
Hypnotic language is more lexically repetitive than typical conversation. A vocabulary of ~1,800 types cycles through 17,800 tokens with a moving-average uniqueness rate of only 38%. More than half of all words are function words.

### Signature 6: Kinesthetic Primacy (60.3%)
The sensory channel distribution is K > V > A at 60:25:15, inverting the normal prose pattern. Hypnosis is computationally a somatic-language phenomenon.

### Signature 7: Perpetual Present (now = 10.21/1k)
`now` is the most frequent content word after `let`, anchoring all language in the present moment. Combined with progressive presuppositions (`deeper`, `continue`, `beginning to`), the grammar constructs an eternal present that is always intensifying.

### Signature 8: Extreme Other-Direction (You:I = 6.43:1)
The subject is addressed ~90 times per 1,000 words. The hypnotist linguistically vanishes. The grammar is a sustained act of constructing the listener as the center of all experience.

---

## 7. Methodological Notes and Limitations

1. **Corpus contamination:** 95.2% of the raw corpus is *about* hypnosis, not *performing* it. The you-density filter (≥50/1k) was essential for extracting pure script content. Future corpora should be curated at the collection stage.

2. **Sample size:** 26 pure scripts / 17,819 words is sufficient for frequency analysis and pattern identification but below the threshold for robust statistical testing (chi-squared, log-likelihood) on low-frequency patterns. The embedded command and presupposition rates should be treated as estimates, not population parameters.

3. **Genre bias:** The corpus over-represents Elman-tradition rapid inductions and under-represents Ericksonian conversational induction. An Ericksonian-heavy corpus would likely show lower imperative:permissive ratios and higher embedded command rates.

4. **Sentence boundary detection:** NLTK's `sent_tokenize` struggles with the atypical punctuation of hypnotic scripts (fragments, ellipses, run-on suggestion sequences). The sentence count of 839 may undercount by 10–15%.

5. **Induction vs. therapeutic comparison is unbalanced:** 24 induction scripts vs. 2 therapeutic/instructional texts. The therapeutic findings should be treated as suggestive, not conclusive.

---

*Analysis pipeline: `analyze_final.py` (pattern matching, frequency analysis, NLTK tokenization/POS tagging)*
*Raw data runs: `analyze_corpus_v2.py` (full 166-file corpus), `analyze_clean_pass.py` (filtered pass)*
