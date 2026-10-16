# A pattern language for games that teach symbols and vocabulary

*Researched 2026-10-16 for learny and for [rbxloop](https://github.com/thorwhalen/rbxloop) (educational games on Roblox), as a first answer to: which abstract game patterns suit learning characters of other scripts and foreign vocabulary, and how do the matching games fit into a hierarchy of them?*

Nothing under `docs/research/` or in `learny/` covered this before: the existing notes are about learner modelling and symbol order, and the 11+ games under `games/` are quiz apps. So this note starts the topic. It is a design catalogue plus an evidence audit, not a literature review of a settled field.

## Summary

- **A game is a point in a six-axis space, not a leaf in a tree.** The axes are: the learning family (what the learner does), the pattern inside the family (how prompts and answers are laid out), the pressure (what the clock looks like), the feedback rule, the progression rule, and the wrapper (the theme and fiction). "Matching" is one family. The user's examples (multiple choice with a timer, a falling object to pop, balloons in a box) are three patterns inside it that differ mostly by *pressure*, which is a separate axis and can be swapped.
- **Ten families:** Match, Produce, Construct, Order, Discriminate and classify, Context, Explore and collect, Encode (mnemonics, songs), Schedule (spaced repetition, mastery gates), Assess. Sections 2 and 3 list the patterns in each, with their knobs.
- **Matching has six patterns** (M1 to M6): pick the match among k options; pair off in a visible field; hidden-pair memory; route a streaming item to a target; find the targets in a field; chain matches (shiritori-style). Cross-modal matching (sound to glyph, picture to word) is not a seventh pattern but a setting of the modality axis.
- **Pressure is its own axis with nine renderings**: none, countdown bar, falling deadline, capacity overflow, time bank, chasing threat, round timer, opponent race, rhythm. Each pressures a different quantity (latency per item, throughput, capacity, rank, beat).
- **Evidence is by component, not by pattern.** I found no controlled study comparing matching forms, and none that tests a falling-object or overflow timer on learning. What exists: integrating the learning act into the core mechanic beats attaching it as a reward [4]; recognition tests build memory but lures can intrude later [5]; timers mostly raise practice volume and speed, not accuracy [7]; fast guessing is a known failure mode [9]. The catalogue's status is therefore *design hypotheses grounded in component evidence*.
- **Every pattern should emit the same record** (item, outcome, latency, options shown) so `learny.tracing` can model the learner whatever the game; section 5 gives each pattern's guessing rate, which is a property of the pattern and not of the model (`guess=`).
- **A phase ladder is the sensible way to combine them**: encode, recognise untimed, discriminate look-alikes, recall by production, build fluency under pressure, transfer to words and sentences. This ordering is an inference from the evidence below and is untested.

## 1. The framework

Prior frameworks I found, all reached through abstracts or secondary summaries (no full text read):

- Bedwell et al. built a taxonomy of 18 serious-game attributes from a literature review and expert card sorts, grouped into themes such as challenge, conflict, fantasy, rules and surprise [1].
- The learning-mechanics / game-mechanics (LM-GM) model maps pedagogical elements (the abstract side) onto game mechanics (the concrete side) so a designer can draw how a game's play delivers its teaching [2].
- Björk and Holopainen's *Patterns in Game Design* catalogues over 200 reusable gameplay patterns, grouped by aspect of play [3].

None of these is specific to drilling symbols, and none says how to vary a game while keeping the learning act fixed. The six axes below do that. They are in the spirit of LM-GM (the *family* is the pedagogical side, the other axes are the game side) but are my own organisation.

| # | Axis | Question it answers | Values (examples) |
|---|---|---|---|
| 1 | Family | What does the learner do with the item? | match, produce, construct, order, discriminate, context, explore, encode, schedule, assess |
| 2 | Pattern | How are prompts and answers laid out? | M1 pick-the-match, M2 pair-off, P1 type-the-answer, and so on |
| 3 | Pressure | What does the clock look like, and what does it press on? | none, countdown bar, falling deadline, overflow, time bank, threat, round timer, race, rhythm |
| 4 | Feedback | What happens after an answer? | reveal, retry, hint, explain, lives, combo, delayed review |
| 5 | Progression | What changes as the learner improves? | item selection, option count, distractor similarity, speed, field size, unlocks |
| 6 | Wrapper | What is the fiction? | arcade, collection, RPG, tower defence, runner, shop |

Settings that look like patterns but are not: **modality** (glyph to sound, sound to glyph, picture to word, handwriting to print) and **direction** (recognise versus produce) change what is learned but not the layout, so they belong to the item set, not the pattern. One pattern with four modality settings is cheaper to build than four patterns.

One design rule cuts across the wrapper axis: **intrinsic integration**. Habgood and Ainsworth found that a maths game whose core mechanic *was* the learning act (Zombie Division) taught more than the same content gated behind the play, and children played the integrated version about seven times longer in free choice [4]. A 2022 pre-registered replication (n=210) again found more learning from the integrated version, and found no difference in motivation or cognitive load, which the authors read as an attention effect [4]. I read only abstracts. Matching games satisfy the rule by construction (the answer *is* the move); wrappers that award play-time for answering do not. Prefer the former.

## 2. Matching: six patterns

Notation: *k* options per prompt, *n* pairs in a field.

| ID | Pattern | Layout | Main knobs | What a response yields |
|---|---|---|---|---|
| M1 | Pick the match | One prompt, k options, one correct | k (2 to 8), distractor source, modality, direction | one item, outcome, latency, the options shown |
| M2 | Pair off in a visible field | 2n tiles (or two columns of n) all visible; select two that match | n, refill (endless or cleared), pair look-alikes, tile form (mixed pile, two columns, connect-by-line, drag to slot) | pair outcomes, per-pair latency, wrong-pair confusions |
| M3 | Hidden pair | Face-down tiles; flip two; matched pairs stay | grid size, peek time | pair outcomes; confounded with spatial memory |
| M4 | Route the arriving item | Items stream in; player sends each to one of a few fixed targets (lanes, bins, catchers) | stream rate, target count, item mix | item, outcome, latency; overlaps with classification |
| M5 | Find the targets in a field | One prompt, a field of many items; tap every match | field size, look-alike density | hits, false alarms, search time |
| M6 | Chain | The match of one item becomes the prompt of the next (word chains, shiritori) | chain constraints, lexicon | production-like; leans on word knowledge more than symbols |

How the user's examples place:

- Multiple choice, untimed = M1 with pressure none. With a countdown bar = M1 with a bar. With an object that falls and must be popped before it lands = M1 with a **falling deadline** (the options sit at the bottom, or the falling object *is* the prompt and the player taps its match before it lands).
- Balloons in a box, popped by selecting matching pairs, with the box overflowing if you are too slow = M2 with **capacity overflow**. Spawn rate is the difficulty knob and the box is the clock.
- The same M2 with a shrinking time bank that refills on each match is a different pressure on the same layout.

The pressure values are independent of the layout. Section 4 gives the full pressure list.

### Notes per pattern (design consequences)

- **M1**
  - Distractor choice is the main lever. Look-alike distractors train discrimination (シ against ツ) but raise confusion for beginners; random distractors are easy. Source distractors from a confusability table, not from chance.
  - Reading lures can later intrude as wrong answers on a recall test (negative suggestion), most for weaker learners [5]. So avoid showing wrong *spellings* of the target as distractors for words; for symbols, wrong glyphs are the point.
  - Guessing rate is 1/k.
- **M2**
  - Elimination lets a player clear the field with little knowledge: leave the hard tiles for last, then the remainder is forced. A penalty for a wrong pair, or tiles that change when a pair fails, reduces this.
  - A random first tap and a random second tap hit a pair with probability 1/(2n−1), but that rate falls as the field shrinks and elimination applies, so for the learner model treat M2 outcomes as weaker evidence than M1 outcomes at the same *k*.
  - Overflow pressure punishes slow pairs globally, which rewards skipping the hard pair (the one you most need to practise). Consider tying the overflow to a *specific* tile that ages.
- **M3**: costs two skills at once (item knowledge and board memory). Good as a warm-up or social game; weak for diagnosing symbol knowledge.
- **M4**: the best fit for the "fluency" phase because the player must respond to a stream; also the easiest to turn into a runner or tower-defence wrapper.
- **M5**: the right tool for look-alike discrimination (find every ツ among シ, ソ, ン). Records false alarms, which are the learning signal.
- **M6**: a vocabulary pattern, not a symbol pattern. It needs a lexicon and works best late.

## 3. The other families

| Family | Pattern | What the learner does | Notes |
|---|---|---|---|
| Produce | P1 Type the answer | Type the reading (romaji for kana), or the character from a prompt | Cued recall is the strongest single practice form with feedback [5]; falling-words typing games are P1 with a falling deadline |
| | P2 Draw or trace | Write the character; stroke order is scored | Needs a drawing surface; check the platform supports it |
| | P3 Say it | Record or speak | Needs speech recognition; outside v1 on most platforms |
| | P4 Self-graded recall | See a cue, recall privately, reveal, grade yourself | The flashcard; cheap, honest-system |
| Construct | C1 Assemble a word | Tiles to a word from a bank (listen, then build) | Duolingo's tap-the-words form [10] |
| | C2 Build a character | Components to a character (radicals; kana base plus mark) | Fits the diacritic-pair question in `symbol-introduction-order.md` |
| | C3 Assemble a sentence | Order words | Syntax, not symbols |
| | C4 Crossword or word search | Fill a grid from clues | Search is M5 on a grid |
| Order | O1 Sort into sequence | Put symbols in the standard order (gojūon rows) | Teaches ordering conventions and dictionary use |
| | O2 Stroke order | Order the strokes | Subset of P2 |
| Discriminate | D1 Odd one out | Which of these does not belong | Look-alike practice |
| | D2 Same or different | Two items, same symbol or not | Perceptual discrimination without naming |
| | D3 Sort into bins | Classify by category (hiragana or katakana, voiced or not) | M4 with a classification target |
| | D4 True or false | Judge a statement | Cheapest to write; weakest evidence of knowledge |
| Context | X1 Cloze | Fill the gap in a sentence | Transfer from symbol to word |
| | X2 Listen and tap | Hear a phrase, tap the words | A listen-and-tap form was added to Duolingo for all courses [10] |
| | X3 Read and respond | Short text, a question | Late-phase transfer |
| Explore and collect | E1 Find in the world | Read signs, labels, menus in a scene | The only family that is open-world; strong with a 3D engine |
| | E2 Collect | Earned symbols become a collection | Progress display, not a drill |
| | E3 Build or decorate | Spend earned symbols on a world | A wrapper, not a pattern |
| Encode | N1 Mnemonic picture | Shape-to-sound story | Before testing, not instead |
| | N2 Song or rhyme | Sound pattern as memory aid | Mixed evidence; see `symbol-introduction-order.md` |
| | N3 Component breakdown | Explain the parts | Kanji and diacritics |
| Schedule | S1 Spaced repetition | Items re-appear when due | A scheduler, not a game; every pattern should draw its items from it |
| | S2 Mastery gate | Unlock when the model says so | `LearnerModel.weakest` and its credibility gate |
| | S3 Daily review | A short fixed session | Habit pattern |
| Assess | A1 Placement quiz | Find the starting level | Adaptive; few items |
| | A2 Boss or exam round | Mixed items, no hints | Consolidation |
| | A3 Fluency probe | Timed run over known items | Measures speed; Segalowitz's automaticity work uses response-time variability (coefficient of variation) as the index [8] |

The Duolingo list is what a mass-market app uses: listening, dictation, multiple choice, pair matching, translation and speaking, plus picture matching and tap-the-words variants [10]. That is a small number of tightly constrained formats recycled over many items, a useful reminder that variety of *pressure and wrapper* is cheap and variety of *layout* is expensive.

## 4. Pressure: nine renderings

Pressure is an axis because it can be swapped on any layout, and because each rendering presses on a different quantity.

| Rendering | What the player sees | Presses on | Fits |
|---|---|---|---|
| None | nothing | nothing; accuracy only | all; first exposure |
| Countdown bar | a draining bar per item | per-item latency | M1, P1 |
| Falling deadline | an object descends; popped by answering | per-item latency, shown as distance | M1, P1, M4 |
| Capacity overflow | a container fills; clearing pairs lowers it | throughput; slow play accumulates | M2, M4 |
| Time bank | a shared clock that gains a bonus per correct answer | streak speed | M1, M2 |
| Chasing threat | an enemy approaches a base; correct answers push it back | sustained accuracy | M1, M4, tower defence |
| Round timer | a fixed round, score is correct answers | throughput | any |
| Opponent race | another player (or a ghost) answers the same items | rank | multiplayer |
| Rhythm | answers land on a beat | tempo | songs, `syllabary-songs` |

What the evidence says about pressure is thin and mixed:

- A study of 62 Japanese students learning English words compared a 3-second limit per item with no limit. Time pressure did not improve immediate recognition speed or scores, but the timed group made more practice attempts and had higher retention two weeks later. The reading is that pressure raised the *amount* of practice. One small study, recognition rather than recall, and I could not confirm its author list [7].
- In arithmetic facts, pressure interacted with the spacing schedule: faster responses at some spacings, slower at others, and similar forgetting [7].
- Fluency work treats speed as the goal of the late phase: automatised word knowledge predicted speaking fluency better than declarative knowledge in a 210-student study (press summary only) [8].
- The learny multidimensional note records that increases in difficulty helped when they were *adaptive* and not when they were fixed steps, and that experienced learners benefited less [12].

So the defaults that follow from this are design choices, not findings: start with no pressure; add pressure only after accuracy is stable; set the time limit as a multiple of that learner's own median response time and move it with their performance; and use overflow or falling pressure for the fluency phase.

## 5. What every pattern must hand to the learner model

`learny.tracing` takes a `Response` (student, item, outcome) and a `guess=` parameter that is "a property of the assessment, not of the model" [12]. Patterns differ in exactly the properties the model needs, so each pattern should declare them:

| Pattern | `guess` | Latency informative | Notes |
|---|---|---|---|
| M1, k options | 1/k | yes | the clean case |
| M2, visible field of n pairs | about 1/(2n−1) on a random pick; higher once elimination applies | per pair | weaker evidence per response |
| M3 | depends on flips seen | partly | confounded with spatial memory |
| M4, k targets | 1/k | yes | like M1 |
| M5 | low per tap; log false alarms | search time | hit and false-alarm rates together |
| P1 | near 0 | yes | strongest evidence |
| A3 | as the underlying pattern | the point | speed profile |

Three rules for the records, from the evidence above:

1. **Log the options shown and the wrong choice**, not just right or wrong. Confusions (シ chosen for ツ) are the signal for distractor selection and for `restrict_labels`.
2. **Log latency and flag guess-like play.** Baker's work on gaming the system finds fast guessing associated with less learning when the learner lacks the knowledge, but not harmful on steps they already know [9]. A fast wrong answer on a symbol the model thinks is weak is evidence of guessing, not of ignorance; downweight it. Timers and overflow make this worse by rewarding any answer.
3. **Select items through the model, not the game.** The pattern asks for `n` items; the scheduler (`weakest`, or S1) chooses them. That is the seam between this note and `learny.tracing`.

## 6. A phase ladder for symbols

Combining the families gives the following progression. It is an inference from the evidence above and the symbol-order note, not a tested curriculum.

| Phase | Goal | Patterns | Pressure |
|---|---|---|---|
| 1 Encode | first exposure, 3 to 5 new symbols | N1 to N3 | none |
| 2 Recognise | symbol to sound, sound to symbol | M1 (k=2 to 4) | none |
| 3 Discriminate | separate look-alikes | M5, D1, D2; M1 with look-alike distractors | none, then light |
| 4 Recall | produce the answer | P1, P4 | none |
| 5 Fluency | speed and automaticity | M4, M2 with overflow, M1 with falling deadline, A3 | adaptive |
| 6 Transfer | words and sentences | C1, X1, X2, M6 | per taste |

The "3 to 5 new symbols per step" rule, the case for keeping look-alikes apart first and contrasting them later, and interleaving are in [`symbol-introduction-order.md`](symbol-introduction-order.md).

## 7. What the vocabulary-game literature adds, and does not

- Reviews and meta-analyses of digital game-based vocabulary learning report large average effects against alternative activities, with strong heterogeneity and effects that vary by game genre, learner level and duration. A Bayesian meta-analysis of 12 studies gave a posterior median g of about 1.11 within-study, and a separate meta-analysis found larger effects for console than for PC or mobile games [6]. Treat those as signs that games *can* work, not as estimates for any pattern here.
- A 2010 to 2025 review of 110 studies put Adventure and RPG at 35.5 percent of the sample and Puzzle, Quiz and Tutorial at 19.1 percent, and reports puzzle-style genres favoured for foundational skills [6]. That fits putting matching in the early phases.
- **None of the reviews I found breaks out matching or drill mechanics**, and I found no study of a falling-character kana game. One 2020 Malaysian project built a memory-song game and a match-puzzle game for hiragana and katakana and tested usability with 13 students, not learning [11].

## 8. Open questions

1. Does a falling or overflow pressure produce more learning per minute than the same layout untimed? No study found. The play data from the games will answer it if the pattern, pressure and phase are logged as fields.
2. How much does M2's elimination inflate scores? A simulation of random and elimination players on fields of size n would settle the `guess` value for M2.
3. Which distractor policy (random, same row, confusable, previously missed) gives the best retention for kana? Untested; the confusability table is the data to collect.
4. Is overflow pressure better tied to a specific aging tile than to the whole field? A design hypothesis.
5. The six axes were chosen by inspection of examples. A card sort with a second reader would test whether they are exhaustive.

## How this was compiled

Searches only, run 2026-10-16. Every reference was reached through a search result page, abstract or summary; I did not read any paper in full and I note below where even the author list was uncertain. Dates, effect sizes and counts are quoted from those summaries. Statements marked as design choices or inferences are mine.

## REFERENCES

1. Bedwell WL, Pavlas D, Heyne K, Lazzara EH, Salas E. Toward a taxonomy linking game attributes to learning: an empirical study. *Simulation & Gaming* 2012;43(6):729-760. doi:10.1177/1046878112439444. [USF record](https://digitalcommons.usf.edu/psy_facpub/936). Abstract and summaries only.
2. Arnab S, Lim T, Carvalho MB, et al. Mapping learning and game mechanics for serious games analysis. *Br J Educ Technol* 2015. Model proposed by Lim et al. 2013. [PDF at GSA](https://radar.gsa.ac.uk/3824/1/mapping-for-serious-games-analysis.pdf). Search summary only.
3. Björk S, Holopainen J. *Patterns in Game Design*. Charles River Media; 2005. Precursor: Björk S, Lundgren S, Holopainen J. Game design patterns. Level Up conference; 2003. [Chalmers record](https://research.chalmers.se/en/publication/9284). Catalogue contents not read.
4. Habgood MPJ, Ainsworth SE. Motivating children to learn effectively: exploring the value of intrinsic integration in educational games. *J Learn Sci* 2011;20(2):169-206. [Sheffield Hallam record](https://shura.shu.ac.uk/3556/). Replication: Cutting J, Iacovides I. 2022, [White Rose repository](https://eprints.whiterose.ac.uk/189921/1/LearningByDoingCuttingAndIacovides090822.pdf). Abstracts and summaries only.
5. Kang SHK, McDermott KB, Roediger HL. Test format and corrective feedback modify the effect of testing on long-term retention. *Eur J Cogn Psychol* 2007;19(4-5):528-558 ([summary](https://notes.andymatuschak.org/zTxLkeaWCdBHQYW73o5n6Ka)). Roediger HL, Marsh EJ. The positive and negative consequences of multiple-choice testing. *J Exp Psychol Learn Mem Cogn* 2005 ([record](https://profiles.wustl.edu/en/publications/the-positive-and-negative-consequences-of-multiple-choice-testing/)). Marsh, Agarwal and Roediger 2009 and Fazio et al. 2010, via the same search summary. Secondary summary for Kang et al.
6. Shahiwala et al. A Bayesian meta-analysis of digital game-enhanced vocabulary learning. *J Comput Assist Learn* 2026 ([Wiley](https://onlinelibrary.wiley.com/doi/10.1002/jcal.70246?af=R)). Beyond scores: a systematic review of digital game-based language learning, 2010-2025 ([ResearchGate](https://www.researchgate.net/publication/398514543_Beyond_scores_a_systematic_review_of_learning_and_psychological_outcomes_of_digital_game-based_language_learning_2010-2025)). Video-game based instruction for vocabulary acquisition: a Bayesian meta-analysis ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1747938X19302155)). Do mobile games improve language learning? A meta-analysis ([T&F](https://www.tandfonline.com/doi/full/10.1080/09588221.2025.2528786)). Search summaries only.
7. Optimizing vocabulary acquisition through time-pressured practice: a cognitive load perspective ([TESOL Union](https://www.tesolunion.org/archives-info/332)). Distributed practice and time pressure interact to affect learning and retention of arithmetic facts ([ResearchGate](https://www.researchgate.net/publication/372799534_Distributed_practice_and_time_pressure_interact_to_affect_learning_and_retention_of_arithmetic_facts)). Summaries only; author list of the first not confirmed.
8. Segalowitz N, Segalowitz S. 1993 *Appl Psycholinguist*, on separating speed-up from automatization effects in second-language word recognition ([Cambridge](https://cambridge.org/core/journals/applied-psycholinguistics/article/assessing-the-development-of-automaticity-in-second-language-word-recognition/58465581E3C8C24144D881FD8F1ACD52)); coefficient-of-variation use via [Tanabe summary](https://scholarspace.manoa.hawaii.edu/bitstream/10125/66717/1/28_1_10125_66717_tanabe.pdf); speaking-fluency study via a [press summary](https://scienceblog.com/quick-word-recall-predicts-second-language-speaking-fluency/).
9. Baker RS et al. on gaming the system in intelligent tutors ([Baker 2005](https://learninganalytics.upenn.edu/ryanbaker/BCKR2005Final.pdf)); Zhang, Borchers, Baker. Understanding gaming the system by analyzing self-regulated learning in think-aloud protocols. 2026 ([arXiv 2601.04487](https://arxiv.org/pdf/2601.04487)). Abstracts and excerpts only.
10. Duolingo exercise formats: [Duolingo Wiki](https://duolingo.fandom.com/wiki/Exercise) and [Duostories exercise guide](https://duostories.org/docs/story-editing/exercises); listen-and-tap from release notes on [APKMirror](https://www.apkmirror.com/?p=462722). Community and third-party sources, possibly dated.
11. Mobile application for learning and memorizing Japanese characters using game-based learning (2020, UiTM Jasin) ([record](https://oalib-perpustakaan.upi.edu/Record/repouitm_422/Description)). Usability test only.
12. learny, internal: [`symbol-introduction-order.md`](symbol-introduction-order.md), [`multidimensional-skill-spaces.md`](multidimensional-skill-spaces.md), [`../learner-model-design.md`](../learner-model-design.md).
