# The order in which to introduce a set of symbols

*Researched 2026-10-11 for [syllabary-songs](https://github.com/thorwhalen/syllabary-songs) (katakana through short songs), as the first case of a general question for learny: given a set of symbols and a lexicon written with them, in what order, and in what step sizes, should the symbols be taught?*

The note has three parts. Part I is the learning-science evidence: grow one set or merge separate subsets, interleaving versus blocking, how many symbols per step, look-alike symbols and diacritic pairs (カ/ガ), and songs. Part II is the algorithmic literature on choosing a symbol subset that spells the most words, and on ordering a sequence of subsets. Part III records what happened when both were applied to a real katakana lexicon. The decision built on this note, an ordered sequence of katakana subsets, is in the syllabary-songs repository (`docs/curriculum.md`).

Parts I and II were compiled by two literature-search agents, which checked every reference against Crossref, arXiv or a publisher page. Each part says where it could read only an abstract or a secondary source, and it marks its own inferences and expectations as such. The two reference lists are merged into one, Vancouver style.

## Summary

- **Grow one set cumulatively, keeping everything learned in rotation.** This is the best-supported default: one direct letter-sound experiment [1], the spacing and retrieval literatures [2-4], and a flashcard study in which one large stack beat several small ones [3]. Interleaving helps most where items are similar [11]. Learning small disjoint subsets *in isolation* is mildly disfavoured (part-task transfer is poor when the whole task needs the parts together).
- **Three to five new symbols per step** is a defensible starting rule (working-memory limits, drill-ratio evidence), but no study measures it for kana or any syllabary. Treat it as a parameter to tune from play data.
- **Keep look-alikes apart at first, then contrast them** once each is known (シ/ツ, ソ/ン, ク/ケ). The separation half has direct support [1]; the contrast half is inferred from category-learning work.
- **Diacritic pairs (カ/ガ) are untested.** Indirect evidence (transparent, compositional graphs are learned better [12]) favours teaching the base first and the mark as a rule, over several pairs in one run (ガ ザ ダ バ パ), then testing transfer to a pair that was not taught. Model the voiced form as cheaper than a new shape, and vary that discount.
- **Songs** helped phrase learning in two experiments and not in a third. Nothing tests symbol–sound mapping through song, so the game's own logs are the evidence to collect.
- **The coverage problem is not maximum coverage.** A word counts only when *all* its symbols are known, so the objective is supermodular: greedy has no 1−1/e guarantee [84]. Choosing one subset is the densest k-subhypergraph problem [78], or the set-union knapsack once symbols have costs [80]. Ordering nested subsets is minimum-latency set cover, which is 2-approximable [85]. At a few thousand words and about 80 symbols, both are small enough to solve well with beam search and to certify with an ILP.
- **Nobody seems to have published this optimisation for a syllabary.** The closest work is word-aware Chinese character ordering [76] and the phonics tradition of choosing first letters for blending potential (s a t i p n) [51, 89].
- **On our katakana lexicon (Part III):** an optimised order spells seven to ten times more words than the textbook gojūon order at the same learning cost. Small first steps spell almost nothing on their own, because of supermodularity. The union of two small, disjoint subsets spells far more than the two halves do separately (the existing seven-glyph song: 25 + 22 words for its halves, 114 for their union).

## Part I. Learning science: order, pace, look-alikes, diacritics, songs

Research note for the syllabary-songs game: the learner hears a syllable (inside a short song) and taps the matching katakana glyph; the open design question is the order and pace in which glyphs are introduced. Compiled 2026-10-11.

### How to read this note

Every reference below was checked against a bibliographic registry (Crossref DOI record) and, wherever an abstract or full text was obtainable (PubMed, OpenAlex, publisher or repository PDF), the numbers quoted here were read from that abstract or text. Where I could only verify that a paper exists (title, venue, year) and not its results, the text says so or makes no claim beyond the title. Numbers I could not verify are not given.

One framing point matters for all four questions. Most of the interleaving literature studies category induction (many different exemplars per category, such as paintings by an artist), whereas a katakana glyph is a single, always identical exemplar paired with a sound. The nearest analogues are therefore paired-associate learning (vocabulary, letter-sound pairs) and discrimination learning among confusable stimuli, not painting-style induction. Where I extrapolate from one to the other this is flagged as inference.

### Bottom line

- Cumulative introduction with continuing review of everything already learned is the best-supported default. It is the one design with a direct letter-sound experiment behind it [1], it is what the largest spacing and retrieval literatures imply [2-4], and a controlled flashcard study found that splitting material into several small stacks was worse than one large stack [3].
- A small number of new items per step is supported by working-memory limits and by drill-ratio research, but no study I could find tests the number of new kana (or any syllabary or abugida symbols) per session. Published practice ranges from one new letter per session with four per week [5] to ten kana per tutorial session in lab studies [6]; a faster-than-one-letter-per-week pace beat the usual slow pace in a natural experiment [7].
- Confusable items should be kept apart while each is being first acquired [1,8], then contrasted side by side once each is known, because discriminative contrast is what makes interleaving work [9-11]. The second half of that sequence is inference from category-learning work, not a tested kana result.
- No study compares learning a diacritic pair (カ/ガ) as base-plus-mark rule versus as two unrelated symbols. Indirect evidence says transparent, compositional graphs are learned better than opaque ones [12] and that children pick up orthographic regularities from exposure [13,14], while small marks are a known source of confusion [15,16].
- Singing helped foreign-language phrase learning in two experiments [17,18] but not lyric recall in another [19], and I found no experiment on learning symbol-to-sound mappings through songs.

### 1. Order of introduction: cumulative growth, disjoint subsets, blocked versus interleaved

#### 1.1 Findings

**Cumulative introduction in letter-sound teaching.** The founding experiment is Carnine (1976) [1]. Experiment 1 (42 first graders) put the similar-sounding letters e and i together or separated them by four other letters; the separated group made more correct responses during training, but posttest scores were low and did not differ. Experiment 2 (35 preschoolers, three groups) tested cumulative introduction, in which children were brought to criterion on each group of sounds before a new sound was added. The similar-separated plus cumulative group reached criterion significantly faster than both the similar-together group and a similar-separated group that had all sounds introduced simultaneously, and posttest scores were significantly higher for the two cumulative groups than for the simultaneous group. The sample is small and the paper is a single report from 1976, but it is the clearest direct test, and its design (criterion on a group, then add) is close to what a song-by-song curriculum does. Systematic phonics instruction in general has a moderate benefit over unsystematic instruction (d = 0.41 across 66 comparisons from 38 experiments, larger when begun early, d = 0.55 versus 0.27 after first grade) [20], and a whole-class 12-week programme of phoneme awareness plus phonics accelerated acquisition in 112 five-year-olds, 96 of them learning English as a second language [21]; neither isolates the introduction schedule.

**Interleaving versus blocking in category learning.** Kornell and Bjork (2008) found that studying paintings by different artists interleaved gave better identification of the artist of new paintings than studying each artist's paintings consecutively: .61 versus .35 correct in Experiment 1a and .59 versus .36 in 1b, 78 percent of participants did better with interleaving, yet 78 percent said massing was as good or better [22]. Kang and Pashler (2012) showed the benefit comes from discriminative contrast and not from temporal spacing as such: spacing a blocked sequence did no better than massing, while showing different artists' paintings simultaneously was as good as interleaving [9]. Birnbaum and colleagues (2013), with butterflies and birds, found that spacing harmed learning when it interrupted the juxtaposition of interleaved categories, but helped when it did not [10].

The meta-analysis by Brunmair and Richter (2019) pooled 59 studies (238 effect sizes in 158 samples) and found a moderate overall interleaving effect, Hedges' g = 0.42 [11]. It was largest for paintings (g = 0.67) and other visual material, small for mathematics (g = 0.34), absent for expository texts and tastes, and reversed for words (g = -0.39, blocking better). A meta-regression showed stronger interleaving effects when material was more similar between categories, less similar within categories, and more complex. The authors caution that the word result rests on few studies and may reflect task type rather than words as such; the analysis also supports the discriminative-contrast account, in that interleaving was effective only when items were presented in immediate succession without spacing. In the one directly relevant experiment series, Carpenter and Mueller (2013) taught English speakers French words that followed pronunciation rules (for example eau as a long o) either blocked by rule or interleaved, and blocking beat interleaving in all four experiments, whether there were 4 or 15 words per rule [23].

The moderators matter for symbols. Carvalho and Goldstone (2014) found interleaving better for categories with high within- and between-category similarity and blocking better for low-similarity categories [24]; the same group later showed the winner depends on whether study is active or passive [25] and that the interleaving benefit at a 24-hour delay is not mainly a spacing effect [26]. Zulkiply and Burt (2013) found interleaving advantageous for low-discriminability categories and massing at least as good for high-discriminability ones, although participants rated massing as more effective in both cases [27]. In classroom mathematics, interleaved practice produced d = 0.42 on an immediate and d = 0.79 on a 30-day test in 126 seventh graders [28], and 61 percent versus 38 percent (d = 0.83) in a cluster-randomized trial of 54 classes [29]. A broad review rated interleaved practice "moderate utility" because its generalisation was still being explored, versus "high utility" for practice testing and distributed practice [30].

**Spacing and retrieval practice.** Cepeda and colleagues' meta-analysis (839 assessments in 317 experiments) found that the inter-study gap that maximises retention grows with the retention interval [2]; in a study of more than 1,350 people the optimal gap fell from about 20 to 40 percent of a one-week test delay to about 5 to 10 percent of a one-year delay [31]. Kornell (2009) studied exactly the flashcard situation: in three experiments, one large stack beat four small stacks studied separately (the small stacks shrink the spacing between repetitions), and spacing beat cramming for about 90 percent of participants, although 72 percent believed massing had been more effective [3]. Pashler, Zarow and Triplett (2003) showed that longer lags between two tests hurt the second test but greatly improved a test one day or one week later, even for items that had produced errors [32]. Testing beats restudy [33,34]; the meta-analysis found larger benefits when the practice test was a recall test than a recognition test [34], a point relevant to a tap-the-glyph (recognition) task. When students learned vocabulary and a correctly recalled item was then only restudied, delayed recall did not improve, whereas continued testing produced a large benefit [4]. Letting learners drop items they think they know had small but consistently negative effects [35]. A prescriptive study of 533 students recommended practising to a criterion of three correct recalls and then relearning three times at widely spaced intervals [36]. Expanding schedules gave short-term benefits but equally spaced retrieval was better two days later; the key factor was delaying the first retrieval [37], and in second-language vocabulary the amount of spacing mattered more than expanding versus equal [38]. Spacing also helped three-year-olds in memory and category induction [39]. Schedulers fitted to large app datasets (half-life regression on Duolingo data reduced recall-prediction error by more than 45 percent and raised daily engagement 12 percent in an operational test [40]; an optimal-control schedule beat heuristic schedules in a natural experiment [41]) show that adaptive review scheduling is practical in a game setting.

**Part-task versus whole-task.** A meta-analysis of 37 transfer studies found that part-task training generally produced negative transfer when the parts had to be performed concurrently in the whole task, but not when the parts were performed in sequence, and that increasing-difficulty training worked when increases were adaptive and not when they came in fixed steps; experienced learners benefited less [42].

**Errorless learning and discrimination.** Terrace (1963) showed in pigeons that errors are not necessary for discrimination learning if the discriminative difference is progressively faded in, and errorless learners lacked the emotional responses seen after errorful learning [43]. In amnesic patients and elderly and young controls, errorless learning of word stems was beneficial, most strongly for amnesic participants [44], but a critical review concluded that benefits are not evident for all groups, some findings are equivocal and there are limitations [45]. In healthy learners the evidence points the other way for retrieval: unsuccessful retrieval attempts followed by feedback enhanced later learning [46], and errors did not outweigh the benefit of spacing [32].

#### 1.2 What this implies for introducing katakana

Three candidate designs were asked about.

(A) Linear growth of one cumulative set with cumulative review is what Carnine's criterion-then-add procedure, the large-stack flashcard result, the drop-item result and the retrieval-schedule literature all favour. It also fits a song game naturally: each new song adds a few glyphs and its practice mixes in glyphs from earlier songs. Keep every learned glyph in rotation, with review gaps that stretch as an item becomes stable.

(B) Learning small disjoint subsets separately and then merging is a form of part-task training. There is no letter-learning experiment on it. The nearest evidence is mildly against pure separation (small stacks gave less spacing and were worse [3]; parts practised in isolation did not transfer well when the whole task required them concurrently [42]) and mildly for merging early and adaptively. The one reason to keep subsets apart is to prevent confusable glyphs from being introduced together (Section 3), and that is better done by ordering within a cumulative set than by walling off subsets.

(C) Blocked versus interleaved depends on what is blocked. Repeating one glyph many times in a row is the weak, massed form [2,3]. Interleaving old and new glyphs within a session is supported for retention and is the default for a growing set. Interleaving matters most for confusable glyphs, because the mechanism is contrast between similar categories [9,11]; for visually dissimilar glyphs there is little to contrast, and the word-learning results (blocking at least as good, g = -0.39 [11]; blocking better for French pronunciation rules [23]) are a warning not to assume interleaving helps first acquisition of unrelated sound-symbol pairs. A sensible rule is block briefly for first exposure of a new item (a few trials), then interleave.

Because tapping is a recognition task and recall tests yield larger testing benefits [34], consider adding a production step (typing the romaji, or drawing the glyph) for items that are already stable. Bhide's Devanagari-like script study found testing did not help novices but copying did [12], so novices may need copying or tracing exposure before retrieval testing pays off.

#### 1.3 Strength of evidence

Spacing, retrieval practice and keeping known items in rotation: strong (meta-analyses, many replications). Interleaving for confusable items: moderate, mostly from visual category learning and mathematics. Interleaving for unrelated paired associates: weak and partly contradictory. Cumulative introduction for letter sounds: moderate to weak, essentially one 1976 study plus the logic of the spacing literature. Disjoint-subsets-then-merge: no direct evidence; reasoning by analogy only. Errorless learning for healthy adults: weak and only partly applicable (fading of foil similarity is the transferable idea).

### 2. How many new symbols per step

#### 2.1 Findings

**Meta-analysis.** Piasta and Wagner (2010) meta-analysed alphabet instruction: effects differed by outcome type and by content of instruction, school-based instruction beat home-based, small-group beat individual tutoring, and there was minimal evidence of transfer to phonological, reading or spelling skills [47]. I could not retrieve the effect-size tables or any pace-per-lesson moderator, so the abstract is all I can report. In a randomised experiment with 58 preschoolers, children taught both letter names and sounds learned the sounds best for letters whose names contain a cue to their sound [48]; children also use letter-name knowledge rather than memorising letter-sound links by rote [49]. Letter learning order is not random: in 339 four-year-olds, letters in the child's own name, letters early in the alphabet string, letters whose names carry their sound, and letters with early-acquired consonants were learned earlier [50].

**Pace in synthetic phonics.** The English national guidance Letters and Sounds, Phase Two, introduces letters one set per week, with each daily session beginning with practice of previously learned letters, teaching one new letter, practising, then applying it; the sets run s a t p, then i n m d, then g o c k, then ck e u r, then h b f ff l ll ss, so d arrives in week 2 and b in week 5 [5]. In Phase Five, new graphemes are taught at about four per week [5]. This is a policy document and not an experiment, but it fixes a widely used reference pace (about four per week, one per daily session, review first) and it keeps visually similar b and d four weeks apart. The Jolly Phonics group-one set is s, a, t, i, p, n, which the publisher says can build many simple words and give an early sense of success in reading and writing [51]; I could not verify its day-by-day pace. In Norway, one new letter a week is the most common approach, and a natural experiment found a faster pace gave significantly better letter knowledge, word reading and spelling, with the lowest-performing children benefiting more [7]; I could not obtain the paper's pace categories or effect sizes. A two-year exploratory study in 13 kindergarten classrooms combined more exposure and practice with extra focus on difficult letters through brief lessons and distributed cycles of review, and children acquired more alphabet knowledge [52].

**Working memory and the known-to-unknown ratio.** Working-memory capacity is about four chunks [53,54], which argues for introducing only a few new items at once and for using already-known items as the context. A meta-analysis of drill ratio research (55 effect sizes from 13 articles) found strong effects for drill with at least half the items known, a small to moderate effect when under half were known, and larger effects for acquisition tasks than proficiency tasks [55]. Taken together with the cumulative design this suggests each practice block should be mostly known material with a few new items.

**Studies on kana and other scripts.** Matsunaga (2003) had 66 beginning learners of Japanese learn 40 hiragana in four computer tutorial sessions of ten, each set taught with one of four methods (picture plus sound mnemonics, picture, sound, flash cards), with a delayed recall test two to five days later; picture-plus-sound mnemonics helped immediate recall only for learners whose first language used the Roman script, and not at delay for either group [6]. The follow-up on katakana (introduced after hiragana) found no short- or long-term benefit of conventional mnemonics, and only the Roman group's spatial ability correlated with immediate recall [56]. These studies use ten new kana per session but did not vary that number. In the opposite direction, embedded picture mnemonics (a letter shape drawn into a picture of an object whose name begins with its sound) in 36 preschoolers learning ten Hebrew letters needed fewer trials, produced fewer confusions between letters and were retained better after a week [57]; earlier work established pictorial mnemonics for phonics in the same spirit [58]. An adult classroom study of Korean Hangul found a mnemonics group outperformed a group taught through the script's design principles on both immediate and delayed tests [59]. Dunlosky and colleagues rated the verbal keyword mnemonic low utility for limited materials and short retention intervals [30]. For abugida and alphasyllabary scripts, Kannada children's akshara knowledge accumulated more slowly than letter knowledge does in alphabetic scripts [60], and adult English speakers learning 80 graphs of a Devanagari-modelled script learned transparent graphs (resembling their components) better than opaque ones and benefited from copying [12]. I found no controlled study of batch size for Chinese-character learners, Cherokee, Thai or Hangul; the commonly quoted "5 to 10 new characters per day" is practitioner folklore and is not cited here. Adult L2 learners show abstract cross-script kana representations early even with imperfect katakana name knowledge [61], consistent with katakana being the less well known script for such learners.

#### 2.2 What this implies for introducing katakana

With 46 base glyphs, the cumulative design implies a ramp of small steps. A defensible starting rule is three to five new glyphs per song or session, delivered inside a context in which most items are already known (drill-ratio evidence [55]) and capped at about four concurrent new items by working-memory limits [53], with a ceiling around ten per session because that is the largest size used in kana experiments [6]. This is inference from adjacent literatures, not a tested optimum. The Norwegian result [7] suggests that a very slow pace (one per week) is not obligatory when there is cumulative review, and the Letters and Sounds pace [5] gives four per week with daily review as a field-tested reference for children. The glyph-to-sound relation in katakana is essentially one-to-one at the mora level (a few homophones such as ジ and ヂ aside), so the extra step of mapping a letter name to a sound that complicates alphabetic letter learning [48,49] is absent; learners are not asked to learn names as well as sounds. Justice and colleagues found that familiar sequence position and sound-cue properties shape which letters are learned first [50], so gojūon order (the familiar a-i-u-e-o, ka-ki-ku-ke-ko sequence) is a plausible default for which the learner already holds a sequence. Whether to follow gojūon or to defer visually confusable members (Section 3) is the main trade-off.

#### 2.3 Strength of evidence

Small, mostly-known batches: moderate (drill-ratio meta-analysis, working-memory capacity, cumulative-introduction study). The specific number per step: weak; no kana, syllabary or abugida study varies it, and the letter-pace evidence comes from children learning alphabets in classrooms. Mnemonic aids for kana: mixed and small-sample [6,56].

### 3. Confusable symbols and diacritic pairs

#### 3.1 Findings on confusable symbols

**Separate or together?** Carnine's experiments found that separating similar-sounding letters (e and i) improved performance during training in first graders (Exp 1) and speed to criterion in preschoolers (Exp 2), although posttest scores in Experiment 1 did not differ [1]. For visually similar Chinese characters, 66 non-beginning learners of Chinese learned ten characters presented as visually similar pairs or as dissimilar pairs; those who learned dissimilar pairs outperformed those with similar pairs in immediate writing, but the advantage did not last to a one-week delayed test, and a verbal-plus-visual mnemonic was especially useful for the similar-pair condition [8]. In vocabulary learning, semantically related words learned together produced more interference errors than unrelated words, although posttest scores did not significantly differ [62]; semantic clustering was a hindrance in earlier work [63]. In category learning, contrast between adjacent exemplars from different categories is what drives interleaving [9,10], interleaving helps most when categories are similar to each other [11,24], and for hard-to-discriminate categories interleaving is better than massing [27].

The reconciliation, which is an inference and not a tested sequence, is that first acquisition (forming a stable sound-to-glyph association) is easier when look-alikes are separated, while discrimination (learning what distinguishes シ from ツ) is better achieved by juxtaposition once each member is individually known. Perceptual-learning theory names the second process differentiation, in which stimuli once indistinguishable become psychologically separated [64]. Progressive fading of foil difficulty is the transferable idea from errorless learning [43].

**How visual similarity is measured.** Higuchi and Kobayashi published a matrix of discrimination reaction times for 4,278 hiragana and katakana letter pairs, correlated with earlier similarity measures [65]; it is the natural quantitative source for choosing which glyph pairs to separate or contrast. In children's letter writing, shape statistics of the script shape what is easy to copy, so letters that violate a script's typical arrangement are harder [66]; in Arabic, where many letters differ only by dots, early spelling errors in 124 first graders included a significant share of visual-orthographic errors although phonological errors were most common [15], and letter knowledge mediated the link between visual attention and reading, consistent with complex letters taxing attention [67]. Adult L2 learners' cross-script priming for kana was equal for visually similar and dissimilar hiragana and katakana pairs [61], which concerns cross-script identity and not within-script confusion.

**Mnemonics as a confusion reducer.** Embedded picture mnemonics reduced confusions between Hebrew letters in preschoolers [57]; mixed results for conventional kana mnemonics are in Section 2 [6,56].

#### 3.2 Findings on diacritic pairs (カ/ガ)

I found no experiment comparing learning ガ as base-plus-dakuten versus as an unrelated symbol, nor any quantitative study of dakuten acquisition by learners. The nearest evidence:

- **Transparent, compositional graphs are easier.** In adults learning a semi-artificial Devanagari-like script, graphs that resemble their components were learned better than opaque graphs [12]. In Chinese, characters taught early are fewer-stroke and often less regular, and the properties of the 2,570 taught characters show a logic children can use [68]; children name phonologically regular characters more accurately than irregular ones and make phonetic-related errors [69]; and by late first grade some children are beginning to perceive characters in terms of component units [70].
- **Regularities are picked up from exposure.** Children's judgements of French orthographic regularities improved with grade and transferred to novel material with a decrement that did not fade, which the authors read as statistical learning and not abstract rule use [13]; in a later study, graphotactic regularities influenced spelling even when a morphological rule was available, again suggesting rules are not abstracted even after massive exposure [14]. Implication: many varied exemplars of the pairing matter more than stating the rule once.
- **Marks are perceptually small and less familiar.** In adult Hebrew readers, diacritics increased activity in orthography-to-phonology regions where vowel letters decreased it, interpreted as a familiarity cost [16]; the vowel-mark literature argues that diacritics add disambiguating information once learned [71]. Arabic dot pairs are a documented source of early confusion [15,67].
- **Kana are moraic.** Learning kana shifts Japanese children's speech segmentation from syllable-based toward mora-based [72], so a mora-level syllable cue is the natural unit for a sound-to-glyph task.

#### 3.3 What this implies for introducing katakana

Treat the dakuten pair as two jobs, a shape job and a sound job. Teach the base glyph (カ) first and stabilise it; then introduce ガ as "カ plus two ticks, voiced" using several base-voiced pairs in a short run (ガ, ザ, ダ, バ, パ) so the transform is available as a pattern, and test transfer to a pair that was not taught. This predicts faster acquisition of later voiced kana than treating each as new, but the prediction is untested for kana; it follows from compositional-graph and regularity-learning evidence [12,13]. Because カ/ガ differ only by a small mark, they are the diacritic analogue of Arabic dot pairs: expect shape confusions, and after both are known, contrast them in adjacent trials with the small mark made salient (for example, enlarged or colour-highlighted marks that fade). The ハ-row three-way ハ/バ/パ is not a single voicing rule (h to b through dakuten, h to p through handakuten), so teach it as an explicit three-member family. For the classic shape twins (シ/ツ, ソ/ン, ク/ケ), separate them in introduction order (the Letters and Sounds precedent keeps b and d four weeks apart [5]), then schedule contrast trials after each member reaches criterion, using the published similarity matrix to decide which pairs need this [65].

#### 3.4 Strength of evidence

Separating confusable sounds during early acquisition: weak to moderate (one 1976 study, one 2022 Chinese study, small samples). Contrast after acquisition: moderate for category learning in general, untested for kana. Diacritics as a rule: very weak and indirect; no direct test.

### 4. Song-based learning of symbol-sound mappings

#### 4.1 Findings

Sixty adults who learned Hungarian phrases by listen-and-sing outperformed those who spoke or rhythmically spoke them after 15 minutes, significantly on the two recall-and-produce tests (p < .05); the effect was not explained by age, mood, phonological working memory or musical training [17]. In Ecuadorian children learning an English passage for two weeks, the sung group outperformed the spoken group in verbatim recall, English vowel pronunciation and translation, and the advantage persisted after six months [18]. In an artificial language, sung sequences gave better learning (word segmentation) than spoken ones when linguistic and musical structure were consistently mapped [73]. Against these, 36 students learning an unfamiliar song recalled fewer words when singing than speaking, and sung versus spoken presentation did not affect lyric recall, which the authors attributed to text and melody being separate memory representations (singing as a dual task) [19]. A classic experiment on melody and recall of text is Wallace (1994) [74] (I verified its existence but did not read its results). A meta-analysis of 13 music-training studies (n = 901) found a small gain in phonological awareness (d = 0.2), larger with more training hours for rhyming, and no aggregate transfer to reading fluency [75]. For the alphabet song specifically, I found no verified experiment on its effect on letter or letter-sound knowledge; the Letters and Sounds guidance does include teaching an alphabet song daily over a week [5], and letter position in the alphabet string predicted which letters four-year-olds knew, which is consistent with, but does not demonstrate, an alphabet-song effect [50].

#### 4.2 What this implies for katakana

The positive song results involve verbatim phrase memory, segmentation and pronunciation of foreign language material, not mapping isolated sounds to printed shapes, so they support using songs as a motivating and attention-focusing context but do not show that songs speed glyph learning. The Racette and Peretz result is a caution: if the melody is the main thing being learned, the sound-to-glyph association may be learned less well than when it is practised directly. A practical design is to use the song as the sound source and context while the glyph-tapping loop (retrieval with feedback, spaced and cumulative) carries the learning, and to run an A/B comparison of sung versus spoken syllable cues on glyph accuracy at a delay.

#### 4.3 Strength of evidence

Singing benefits for foreign-language phrase learning: moderate to weak (two positive experiments, one contrary, small samples). Songs for symbol-sound mapping: no direct evidence found.

### 5. Open questions worth testing in the game

- Increments of 3, 4 and 5 new glyphs per song with identical cumulative review: accuracy at 1 day and 1 week.
- Confusable pairs: separated versus adjacent at first introduction, then contrast trials after criterion; measure confusion errors on シ/ツ and ソ/ン at a delay.
- Diacritics: rule-framed versus item-framed ガ/ザ/ダ introduction, then transfer to an untaught voiced kana.
- Recognition-only versus recognition-plus-production for stable items.
- Sung versus spoken syllable cues.

## Part II. Algorithms: choosing and ordering subsets that unlock words

Scope: the algorithmic part of the syllabary-curriculum research note. Every reference below was opened or resolved (Crossref record, arXiv page, publisher page or repository) during this search; where I could read only an abstract or a secondary description I say so. Statements marked "(derivation)" are my own reasoning from the cited definitions, not claims made by a cited paper. Statements marked "(expectation)" are untested predictions about our lexicon.

A correction to the brief first: the PLOS ONE paper on optimising the learning order of Chinese characters is Loach and Wang 2016 [76], not Yan et al. 2016. Yan et al. is the 2013 PLOS ONE paper that Loach and Wang benchmark against [77].

### Summary

- Problem (a) is the densest k-subhypergraph problem [78] (densest k-subgraph when every word has at most two distinct characters [79]). With character costs and a budget it is the set-union knapsack problem (SUKP) [80, 81]. It is NP-hard, has no PTAS under standard assumptions [82], and the best worst-case approximation ratios are polynomial in n [78, 83]. It is not submodular maximisation; the 1-1/e greedy guarantee [84] does not apply.
- Problem (b) in its nested form has an exact name in the literature: the minimum latency set cover problem (MLSC) [85], the "all required tools installed" member of the generalised min-sum set cover family [86, 87]. It is strongly NP-hard but, unlike (a), constant-factor approximable (factor 2, via single-machine scheduling with precedence constraints and Sidney decomposition) [85, 86, 88].
- Nobody has published this optimisation for a syllabary. The closest applied work is Loach and Wang's word-aware character ordering for Chinese [76] and the phonics tradition of choosing the first letters for word-blending potential [5, 89]. Both use heuristics, and neither claims optimality.
- At our size (about 90 characters, a few thousand words) problem (a) should be solved exactly by an off-the-shelf MIP solver, and (b) by Sidney-style decomposition plus local search, using the exact solver as a per-step subroutine and as a bound.

### 1. Problem (a): choosing k characters that spell the most words

#### 1.1 Names and equivalences

Setting: V is the set of characters (about 90). Each word w has a distinct-character set e_w, a subset of V, and a weight (1, or its frequency). Choose S, a subset of V, with |S| at most k (or with total cost at most B). Value f(S) = sum of weight_w over words with e_w a subset of S.

- Densest k-subhypergraph (DkSH): pick k vertices maximising the weight of hyperedges contained in the chosen set [78]. For hyperedges of size at most 2 (words using at most two distinct characters) this is the classical densest k-subgraph problem (DkS) [79]. Hassin and Levin introduced the hypergraph version under the name "densest k-sub-hyper-graph" in the course of their latency work and note it is at least as hard as DkS [85].
- Set-union knapsack problem (SUKP): items (words) have profits, elements (characters) have costs, and a selection of items costs the cost of the union of its elements; maximise profit under a budget [80]. Given a character set S, every word inside S can be added at no extra cost, so the SUKP optimum and the optimum of (a) with costs coincide (derivation). SUKP is NP-hard even in very restricted cases [80], and Taylor gives approximation ratios for SUKP and DkSH that depend on the maximum set size [81].
- Minimum k-union is the mirror image: choose k sets to minimise the size of their union [90]. Ours is the budget-on-union, maximise-the-number-of-sets version; the two are not interchangeable but share the hardness machinery.
- Complement view (derivation): let T = V minus S be the characters NOT taught. A word is spellable iff T misses it, so f(S) = total weight minus coverage(T), where coverage(T) is the weight of words that contain at least one character of T. Coverage is monotone submodular, so (a) is "minimise a monotone submodular function with a cardinality LOWER bound on T (|T| at least n-k)". That problem is hard to approximate in the value-oracle model (Svitkina and Fleischer prove sqrt(n/ln n) bounds for it) [91]. Their lower bound is an oracle-model result and does not transfer verbatim to explicit hypergraphs, so I cite it only for the structural point: the unconstrained problem is easy and the cardinality constraint is what makes it hard.
- I searched for the name "maximum k-subset intersection" as a label for this problem and did not find a source I could verify under that name; I do not use it.

#### 1.2 Why this is not maximum coverage, and why 1-1/e does not transfer

In maximum coverage and budgeted maximum coverage a word (set) is gained as soon as ANY of its elements is chosen [92]. The coverage function is monotone submodular, so greedy achieves 1-1/e [84], a knapsack-budgeted version also achieves 1-1/e with partial enumeration [92, 93], and 1-1/e is the best possible unless P = NP [94].

Our word is gained only when ALL of its characters are chosen. f is then monotone but supermodular: the marginal value of a character can only grow as more characters are taught (derivation: a word that needs c and is otherwise inside S is also otherwise inside any superset of S). Increasing returns break the greedy analysis: the first character added to an empty set completes no word (except one-character words), so marginal gains give no signal, and degree-style proxies mislead. Small counterexample (derivation): a hub character in 8 two-character words with 8 distinct leaves, plus a clique of 5 characters whose 10 pairs are all words. With k = 5 the hub has the highest word-count (8 against 4), and hub plus four leaves completes 4 words, while the clique completes 10.

Consequence: none of the 1-1/e results [84, 92-94] gives a guarantee for (a). The right comparison class is DkS-type hardness, not coverage-type hardness.

#### 1.3 Complexity and approximability

- NP-hard: with words of two distinct characters and k given, asking whether some k characters spell C(k,2) words is the clique problem.
- DkS has no PTAS under the assumption that NP does not have subexponential-time randomised algorithms (Khot) [82]. Under ETH the ratio n^(1/(log log n)^c) cannot be reached in polynomial time (Manurangsi) [95]. Upper bounds: n^(1/3-ε) for some small ε [79] then n^(1/4+ε) [83].
- Hypergraphs: Chlamtac et al. give a roughly n^0.70 ratio for hyperedges of size 3 and show both DkSH and the minimum p-union problem are solvable exactly on interval hypergraphs [78]; Taylor gives ratios as a function of the maximum hyperedge size [81]; for minimum k-union the n^(1/4+ε) ratio is tight under a hypergraph dense-versus-random conjecture [90]. Arulselvan notes that the budgeted-coverage greedy gives a constant factor for SUKP when every element occurs in a bounded number of sets, a regime that does not hold for frequent characters [96].
- Easy relatives (the reason an exact solution is realistic): without a cardinality or budget constraint, choosing characters to maximise words minus costs is a maximum-weight closure problem, solved by one min-cut [97]. The ratio version (maximise words per unit cost, i.e. densest sub-hypergraph) is solved by parametric min-cut/max-flow, which also yields the whole nested family of Lagrangian optima in the time of about one max-flow [98]; for graphs, the simple peeling algorithm gives a 2-approximation for the densest subgraph [99].

All the polynomial-in-n ratios above are worst-case statements about adversarial instances with large n. They say nothing about a 90-vertex instance with a Zipfian weight distribution.

#### 1.4 Practical methods

1. Preprocess. Merge words with identical character sets (weights add). Drop zero-weight words and unused characters. Both shrink the model a lot for a lexicon of a few thousand words over 90 characters (expectation).
2. Exact MIP (formulation below) with a branch-and-bound solver such as HiGHS [100] or CP-SAT. The LP relaxation of the disaggregated formulation equals the upper concave envelope of the optimum-versus-budget curve (derivation by LP duality: without the budget row the system is a closure LP and is integral; dualising the single budget row gives min over lambda of lambda*B plus the best Lagrangian closure). So the root bound is exactly as good as the parametric-flow breakpoints [97, 98] and is tightened by branching.
3. Greedy with lookahead. Plain marginal greedy fails (1.2). Useful variants: add the best SET of up to p characters by words completed (p = 2 or 3); add by "words completed per unit cost" over closures (the SUKP-greedy flavour used in [96]); and reverse greedy / peeling, which deletes the character whose removal loses the least weight, starting from the full alphabet [99].
4. Local search. 1-swap and 2-swap neighbourhoods with incremental scoring are the state of the art for SUKP in the heuristic literature, with tabu search and restarts reported on benchmark sets of hundreds to a few thousand items [101, 102]. Our instance is smaller than those benchmarks.
5. Beam search over prefixes of increasing size, scoring completed words plus an optimistic bound from the LP. Cheap to write, and it produces the whole k = 1..90 curve in one run.
6. Lagrangian / parametric min-cut [97, 98] for the nested chain of optimal closures (see section 2.5).

#### 1.5 ILP formulation of (a)

```
Data
  C            set of characters (about 90); W set of words
  e_w          distinct-character set of word w (a subset of C)
  weight_w     1, or word frequency, or a transformed frequency (see 4.3)
  cost_c       cost of teaching character c (1 by default)
  B            budget (B = k when every cost is 1)

Variables
  x_c  in {0,1}   for each c in C    (1 if character c is taught)
  y_w  in [0,1]   for each w in W    (1 if word w is usable; it may be left continuous, see note)

maximise     sum over w of  weight_w * y_w
subject to   y_w <= x_c                     for every word w and every c in e_w
             sum over c of  cost_c * x_c <= B
             x_c in {0,1}
```

Notes. (i) Because every weight is non-negative and each y_w only appears in the objective and in the upper-bound rows, an optimal solution sets y_w = 1 exactly when all x_c for c in e_w equal 1, so y_w can be declared continuous and integrality is automatic. (ii) Keep the disaggregated rows (one per (w, c) pair); the aggregated row |e_w| * y_w <= sum of x_c over e_w is weaker in the LP. (iii) Pairs (w, c) number the sum of |e_w| over distinct word types, a few ten thousand at most. (iv) A forced or forbidden character (for example a character that must be taught first) is a bound x_c = 1 or 0. (v) To require that a word list is covered (a "must be spellable" list), fix y_w = 1.

#### 1.6 What this implies for our lexicon (a few thousand words, about 90 characters)

- The model has about 90 binaries and one continuous variable per distinct character set among the words, fewer than the few thousand words after merging (expectation). An exact solve with a modern MIP solver for each k should be feasible; I did not run it. Plan: greedy-with-lookahead and swap local search first for an incumbent and a warm start, then HiGHS or CP-SAT to prove optimality, and fall back to the local-search answer with the LP/Lagrangian bound as a certificate if a particular k times out.
- Expect the answer to be driven by hub characters (the long-vowel mark and small tsu are the obvious candidates in katakana loanwords, plus the common moraic and consonant-vowel characters; expectation) and expect near-ties: the optimum at a given k is usually one of many solutions within a percent or two. Report the top few distinct optimal sets per k and break ties on pedagogical criteria (section 4).
- The weight scheme changes the answer more than the algorithm does. Compute the optimum under at least three weightings (type counts, raw frequency, log frequency) and show how much they disagree.
- Do not use character frequency or word count per character as the selection rule. Section 1.2 shows how it fails, and it is the rule keyboard-practice tools use [103].

### 2. Problem (b): ordering the characters (the "anytime" curve)

#### 2.1 The exact problem: minimum latency set cover

Hassin and Levin define the minimum latency set cover problem (MLSC): jobs (words) each need a subset of tools (characters); one tool can be installed per time unit; a job completes the instant its entire subset is installed; choose the installation order to minimise the weighted sum of job completion times [85]. This is problem (b) with a nested order, unit-size steps and the objective "area above the unlock curve". They prove it NP-hard in the strong sense and give an e-approximation; the construction starts from a densest k-sub-hypergraph subroutine (assumed solvable in their section 3, then removed in section 4), so (a) is literally the engine of (b) [85].

- Area under the curve versus sum of completion times (derivation): if U(t) is the weight unlocked after t characters, the sum of U(t) for t = 1..T equals the sum over words of weight_w * (T - t_w + 1), where t_w is the step at which word w is unlocked. Maximising the area is therefore exactly the same optimisation as minimising the sum of weight_w * t_w. The optimum is identical, but approximation ratios do not carry across because the two objectives differ by an additive constant.
- The factor-2 route: Hassin and Levin's own footnote observes that MLSC reduces to single-machine scheduling with precedence constraints and weighted completion times: each tool is a unit-time zero-weight job, each word is a zero-time job with its weight, and a word may run only after all its tools [85]. That problem has several 2-approximations [85, 88, 104, 105]; Azar, Gamzu and Yin state the improvement from e to 2 for the "non-decreasing profile" case that contains MLSC [86]. Chekuri and Motwani's algorithm computes the Sidney decomposition [106] by parametric max-flow and orders arbitrarily within blocks [105]; Margot, Queyranne and Wang show that every schedule consistent with the Sidney decomposition is within a factor 2 of optimal [88]; Correa and Schulz show that virtually all known 2-approximations are of this kind [107]. (These last two statements about the scheduling literature are from secondary summaries of the abstracts; I did not open the papers.)

#### 2.2 The min-sum set cover family

- Min-sum set cover (MSSC): order the sets so as to minimise the sum over elements of the time of the FIRST set containing them. Greedy is a 4-approximation, and 4-epsilon is NP-hard [108].
- Generalised MSSC (GMSSC): each element has a covering requirement k_e and is covered when k_e of its sets have appeared. MSSC is k_e = 1; MLSC is k_e = |e|, the case where all must have appeared [87]. Constant-factor approximations: 485 [87], 28 [109], 12.4 [110], 4.642 [111], and a 2026 preprint at 4.509 [112]. For general profiles Azar, Gamzu and Yin give O(log r), with r the largest hyperedge (our word length in characters, so a small constant) [86].
- Orientation (important): in these papers the ORDERED objects are the "vertices" and the covered objects are the "hyperedges". For us the ordered objects are characters and the hyperedges are words. Min-sum vertex cover is the special case of hyperedges of size 2 (words with two distinct characters) [108, 111].
- Semantics matter: MSSC's "first" semantics models a user who is satisfied by any relevant item. Our "last" semantics (every character needed) is the MLSC end of the family. Do not borrow MSSC's greedy or its 4-ratio.

#### 2.3 Submodular ranking and related orderings

- Submodular ranking: given monotone submodular functions f_j, order the ground set to minimise the weighted time at which each f_j reaches its cover value; O(log(1/epsilon)) approximation, matching an Omega(log) hardness, where epsilon is the smallest non-zero marginal [113]. Instantiation (derivation): define f_w(S) = |S intersect e_w| / |e_w|. It is monotone and modular (so submodular), and reaches 1 exactly when e_w is inside S. Our word-ordering problem is therefore a submodular ranking instance with epsilon at least 1/r, and the guarantee is O(log r), consistent with [86]. The trap is to model "word is usable" as the indicator [e_w inside S], which is supermodular and outside the theorem; the linear surrogate with a cover threshold is the correct encoding.
- Minimum latency submodular cover extends submodular ranking to path costs in a metric [114]; not needed here unless teaching a character has a position-dependent switching cost.
- Pipelined set cover orders filters so that covered (discarded) elements stop incurring cost; greedy and local search are 4-approximations via an LP analysis [115]. The semantics are those of MSSC (an element leaves after the first set that covers it), so it is related background rather than an applicable algorithm.
- Anytime and incremental views. Streeter and Golovin's online schedule maximisation gives near-optimal guarantees simultaneously for the fraction completed by a deadline and for average time to completion, but it assumes a monotone submodular objective [116]. Bernstein et al. study "incremental maximisation": a nested sequence of solutions of growing size judged against the best solution of each size, with a general 2.618-competitive algorithm for a class of problems with a relaxed submodularity condition and a 2.18 lower bound in general [117]. Our objective is supermodular, so these guarantees do not apply. The benchmark concept does: the best k-set for each k need not be nested (for supermodular f the optimal k-sets can differ completely), and the "price of nesting" can be measured exactly by comparing the nested curve against the independent optimum of (a) for each k (section 1.5).

#### 2.4 ILP formulation of (b), nested and with a per-step minimum

```
Data
  steps t = 1..T; step_budget_t = cost of characters newly taught at step t (for example 5 per lesson)
  m_t         optional minimum weight of words newly unlocked at step t

Variables
  x_{c,t} in {0,1}   character c is taught by the end of step t      (nested: x_{c,t} <= x_{c,t+1})
  y_{w,t} in [0,1]   word w is usable at the end of step t

maximise     sum over t, w of  weight_w * y_{w,t}          (area under the unlock curve)
subject to   y_{w,t} <= x_{c,t}                             for every w, c in e_w, and t
             x_{c,t} <= x_{c,t+1}                            for all c, and t < T
             sum over c of cost_c * (x_{c,t} - x_{c,t-1}) <= step_budget_t     with x_{c,0} = 0
             (optional lower bound on progress, needs y to be tight:)
             y_{w,t} >= sum over c in e_w of x_{c,t} - (|e_w| - 1)             for all w, t
             sum over w of weight_w * (y_{w,t} - y_{w,t-1}) >= m_t              with y_{w,0} = 0
```

Notes. Without the last two rows, y is a free upper bound and the model maximises the area. The minimum-new-words rows need the reverse linking row, so that y_{w,t} is forced to 1 when all characters are present; with it the model is feasible only if each step can really unlock m_t. Non-nested variants (a working-set limit with forgetting, or a window of K characters currently being drilled) drop the monotonicity row and add a cap on sum of x_{c,t}; I found no applied paper that needs this.

Size: about T (20 to 30 lessons) times (90 + the number of distinct word types) variables. That is large for exact solution; use it as a polishing step, or solve it only for the first few lessons, where the choice matters most.

#### 2.5 A practical algorithm for (b)

1. Compute the Sidney-style decomposition: find the set of characters (with all taught characters contracted) maximising unlocked weight per unit cost, which is a densest-sub-hypergraph or maximum-ratio closure problem solvable by parametric min-cut [97, 98, 105, 106]; teach it, contract, repeat. This is a factor-2 approximation of the sum-of-completion-times objective for any order consistent with the blocks [88]. If the whole alphabet turns out to be a single block the guarantee degenerates to "any order is within 2", which is too weak to guide teaching; hence steps 2 and 3.
2. Inside a block, order characters with the exact per-step subroutine of (a) (the best s characters to add to the current set, ILP in 1.5 with the taught set fixed), which is a receding-horizon, locally optimal choice.
3. Polish with local search on the permutation (adjacent swap and insertion moves, incremental scoring of the unlock curve), and certify against the LP/Lagrangian bound and, for small T, the ILP in 2.4.
4. Batch caveat: the cited results assume one character per time unit. Teaching s characters per lesson means a word's time is the lesson index of its last character; quantising a one-at-a-time order into lessons is a heuristic, and the lesson-indexed ILP in 2.4 is the exact statement.

#### 2.6 What this implies for our lexicon

- Treat (b) as MLSC with weights and lessons of 3 to 6 characters. Use the Sidney decomposition for a guaranteed-quality start, then local search on the lesson sequence; use the ILP in 2.4 on a rolling window to prove local optimality.
- The 2-approximation is worst-case. Report the ratio you actually achieve against the LP/Lagrangian lower bound and the nested-versus-independent gap from 2.3.
- "Each step unlocks enough new words" is a feasibility constraint, not part of the objective. Check early: in a mora-based script a handful of characters can already spell short words, but how many depends on the lexicon (expectation). If the first lesson cannot reach the minimum, the minimum for lesson 1 should be relaxed explicitly; do not let the solver hide an infeasible lesson.
- Keep word length in mind: the O(log r) guarantee improves with a shorter maximum word length, so truncating the lexicon to words of at most 6 or 7 distinct characters changes the theory very little and removes outliers (expectation).

### 3. Applied work on reading, scripts and curricula

I found no paper that formulates the character-selection or ordering problem for a syllabary (kana, or any script) as the optimisation problems above. The nearest work, with its evidence level:

#### 3.1 Character-order optimisation for logographic scripts

- Yan et al. (2013) rank Chinese characters by frequency-derived node weights in the network of structural (component) relations, and compare against textbook orders [77]. Their metric is cumulative usage coverage as a function of learning cost.
- Loach and Wang (2016) build the learning order from a centrality ranking that combines usage frequency with the cost of the components, then apply a topological sort that moves components ahead of the characters that need them while disturbing the frequency order as little as possible [76]. I read the arXiv HTML text: they compare orders by final and integral learning efficiency (cumulative usage coverage at a cost cap, and its average along the way), they do not discuss NP-hardness, they admit the order is "not necessarily the most efficient" and show a hypothetical network where it is suboptimal, and a final section adds multi-character words (the 10,000 most frequent from SUBTLEX-CH) so that word frequencies drive character acquisition [76]. The integral efficiency metric is the same shape as our area under the unlock curve. This is the most directly applicable prior work, and it is a heuristic with no optimality claim.
- TopoKanji applies a modified Kahn topological sort with frequency weights to kanji, with lists from several corpora; its coverage measure is kanji coverage of texts, not word coverage [118].
- Kana: the one study I could verify is Higuchi, Okumura and Kobayashi (2019), who regressed accuracy rankings of 4- to 5-year-olds on letter properties and found that picture-book letter frequency predicted both reading and writing of hiragana, and visual complexity predicted writing only [119] (abstract read; paper not opened). Nothing I found compares gojuon order, frequency order and optimised orders for katakana. The gojuon (row-by-row) order is a pedagogical convention rather than a result of optimisation (no source examined for or against it).

#### 3.2 Letter orders in typing tutors and phonics

- keybr.com starts with a small set of the most frequent letters and adds letters once the learner reaches a target speed on the current ones; this is a frequency order with a performance gate, not a word-driven choice (README read; the unlock code was not opened) [103].
- Phonics: the first group s, a, t, i, p, n in Jolly Phonics is described by the publisher as "chosen for high word-blending potential (e.g. sat, pin, tip)", with further aims of avoiding letter confusion (b and d separated) and supporting early handwriting [89]. Letters and Sounds (England, 2007) names the same starter letters s, a, t, p, i, n for Phase Two and builds its dictation word lists from them [5]. These are hand-designed, word-aware orders: the rationale is exactly the "words usable early" objective, but no optimisation is reported, and I found no study that tests whether the orders are optimal or even better than alternatives. Meta-analysis evidence on alphabet instruction concerns effect sizes by instruction type and content, not the optimal letter sequence [120] (abstract read).
- Decodable text research asks the converse question: given a letter-sound progression, how decodable are the texts? Juel and Roper/Schneider (1985), described in secondary sources as finding that children induced untaught letter-sound correspondences better from more decodable text [121]; Mesmer (2005) on the decodability of first-grade texts [122]; and Cheatham and Allor (2012), whose review, per secondary summaries, finds decodability mainly affects early decoding accuracy and recommends it as one of several criteria rather than the only one [123]. (For these three only the bibliographic records and secondary descriptions were checked.) This supports measuring "decodability" (share of text tokens spellable from the taught set) alongside unlocked word types, but it does not give an algorithm.

#### 3.3 Vocabulary coverage targets

- Hu and Nation (2000) propose that about 98 percent of running words should be known for unassisted reading comprehension [124]. Schmitt, Jiang and Grabe (2011), from 661 learners, found a roughly linear relationship between known-word percentage and comprehension with no sharp threshold, and judged 98 percent a more reasonable target than the earlier 95 percent for academic text [125] (abstract read). Nation (2006) estimates the vocabulary size needed to reach such coverage in written and spoken text [126], and Nation and Wang (1999) bear on graded-reader level design [127] (these two were verified as records only). They define the right evaluation measure for our unlock curve, token coverage of running text at each step, but they are about word knowledge, not script knowledge.

#### 3.4 Curriculum sequencing, spaced repetition and learning spaces

- Duolingo: I found no peer-reviewed Duolingo paper on sequencing new content; the company's own description says designers order objectives by CEFR level ([Duolingo blog](https://blog.duolingo.com/how-duolingo-experts-work-with-ai)). The published research is on review scheduling, not selection: half-life regression [40], and the optimal scheduling of spaced repetition by Reddy et al. [128]. These decide WHEN to re-show items already taught, which is orthogonal to which characters to teach next.
- Knowledge space theory formalises feasible orders of acquisition: a knowledge structure is a family of feasible knowledge states, and learning spaces are the well-graded, union-closed ones whose maximal chains are the feasible learning paths [129, 130]. Skill maps (conjunctive and disjunctive models) link items to the skills they need [131, 132]. Our setting is a conjunctive skill map in which each word (item) requires a set of characters (skills): the states "words I can read" induced by character sets are exactly the union-closed family such a map generates (derivation from the definitions). With prerequisite relations between characters (a voiced character after its base), the feasible character sets become the down-sets of a partial order, giving a concrete interface for constraints like x_ガ <= x_カ in section 4. Knowledge space theory supplies the vocabulary and the assessment machinery (outer fringes, next-step recommendation), not an optimiser for coverage.

#### 3.5 What this implies for our lexicon

- The note can claim novelty in one respect: an explicit optimisation of syllabary character order against a real word lexicon, with a certificate (LP or ILP bound), appears not to exist in the literature surveyed here. State that as "not found in this search", not as absence.
- Adopt Loach and Wang's evaluation shape: cumulative coverage versus learning cost, summarised by final and integral efficiency, and add token coverage of running text and the decodability measure from the phonics literature [76, 123].
- Use frequency order, gojuon order and the phonics-style order of "most words completed" as baselines. Of the three, only the first has any usage as a tutor default [103].
- Reading and writing may need different weights, since visual complexity matters for writing but not for reading in the one kana study found [119].

### 4. Costs: a cheaper voiced variant, as a budgeted problem

#### 4.1 Plain budget

Replace "k characters" by a budget: sum of cost_c * x_c <= B, which is the SUKP form in 1.1 [80] and is already in the ILP of 1.5. The 1-1/e result for budgeted coverage [92] still does not apply (section 1.2); SUKP heuristics [101, 102] and exact MIP are the tools.

#### 4.2 Three ways to say "ガ is cheaper once カ is known"

Model A, sibling discount (cost depends on whether the base is taught). For each derived character d with base b(d), full cost a_d and discounted cost a'_d < a_d:

```
variables   x_d in {0,1}, z_d in {0,1}   (z_d = 1 means d is bought at the discounted price)
            z_d <= x_d,   z_d <= x_{b(d)}
budget      sum over base characters c of a_c * x_c
          + sum over derived characters d of ( a_d * x_d  -  (a_d - a'_d) * z_d )   <=  B
```

Since cost is being minimised for a given set of words, the solver sets z_d = 1 whenever it is allowed. In an ordering model the discount applies only when the base was taught at an earlier or the same step: z_{d,t} <= x_{b(d),t}.

Model B, shared components (a SUKP with two levels). Decompose characters into components (ガ = カ + the voicing mark; パ = ハ + the half-voicing mark) with a cost per component:

```
variables   u_k in {0,1} for each component k
            x_c <= u_k   for every character c and every component k of c
budget      sum over k of  cost_k * u_k  <=  B
words       y_w <= x_c as before
```

Here the marks are bought once and then reused by every character that uses them, which is the set-union knapsack in its natural form (characters are items, components are elements) [80]. It matches the way Loach and Wang price Chinese characters by their new components [76]. A stronger reading is available: if knowing the base and the mark is enough to read the combination, drop x_c for derived characters and require only the components in y_w <= u_k. That is a pedagogical judgement, not a mathematical one, and it hides the work of attaching a new sound to a new shape, so I would make it an option and default to Model A.

Model C, prerequisites (a hard order constraint instead of a price). x_ガ <= x_カ, or in the ordered model x_{ガ,t} <= x_{カ,t}: the feasible character sets become the down-sets of a partial order, which is the quasi-ordinal learning-space structure in knowledge space theory [129, 130]. Loach and Wang's topological sort enforces precisely this kind of prerequisite (components before compounds) [76].

#### 4.3 Other terms worth putting in the same formulation

- Confusable pairs. Phonics practice separates easily confused letters across groups [89]. For katakana pairs such as シ and ツ, add a per-step conflict row: newly taught x_{シ,t} + newly taught x_{ツ,t} <= 1. This is a constraint, not a cost, and is one line in the ILP of 2.4.
- Learner-specific cost. A cost vector can come from visual complexity (stroke count; predictive of writing, not reading [119]) or from a measured per-character learning time; keep cost_c a column in the data, not a constant.
- Word weights. Raw frequency is heavy-tailed; a few hundred words may carry nearly all the weight and the optimiser will serve only them. Compare raw, log and rank-capped weights, and also report the unweighted count of types.
- Budgets measured in characters per lesson with mixed costs make the time step a knapsack, which the ILP in 2.4 already allows through step_budget_t.

#### 4.4 What this implies for our lexicon

- Voiced and half-voiced katakana (20 voiced and 5 half-voiced characters, plus the extra voiced vu), the small characters and the long-vowel mark are exactly where Model A or B matters, because they multiply the usable lexicon cheaply once the bases are known. Expect the budgeted optimum to schedule bases early and voiced forms in later lessons, with the exact order sensitive to the discount a'_d. That discount is a pedagogical parameter with no measurement behind it: run the optimiser at several values (for example a' = 0.25, 0.5, 0.75 of a) and report how the order moves; do not present one value as a finding.
- Model C is the cheapest to implement and defensible without calibration data; Model A is the minimal step beyond it; Model B is the principled one if component structure is adopted anyway for other reasons.

### Search record and gaps

Searched: densest k-subhypergraph, set-union knapsack, budgeted maximum coverage, min-sum and generalised min-sum set cover, minimum latency set cover, submodular ranking, pipelined set cover, incremental maximisation, Sidney decomposition and precedence-constrained scheduling, Chinese character and kanji learning order, kana acquisition order, keybr, phonics letter orders, decodable text, lexical coverage, Duolingo and spaced repetition, knowledge space theory.

Not found or not verified: any paper that optimises syllabary character order against a lexicon; peer-reviewed support that the s, a, t, i, p, n order is optimal (only publisher rationale); a Duolingo paper on sequencing new content; the Juel and Roper/Schneider, Mesmer, Nation (2006) and Nation and Wang (1999) full texts (records and abstracts or secondary descriptions only); the original Letters and Sounds rationale for set order beyond the starter letters; the proofs behind the scheduling-literature statements in 2.1 (abstract-level summaries only).

## Part III. Applied to katakana: what the data showed

**The lexicon.** 4,159 katakana loanwords from European languages: every all-katakana token with Zipf ≥ 3 in the Japanese list of [wordfreq](https://github.com/rspeer/wordfreq) (Speer, data CC-BY-SA 4.0), plus hand-curated and non-English European additions. Each token was annotated by an LLM (category, donor language, donor word, English meaning, confidence); names, native words written in katakana, onomatopoeia, fragments, vulgar terms, non-European donors and low-confidence rows were dropped. 3,195 come from English, 278 from French, 169 each from German and Italian, 89 from Spanish, 69 from Portuguese, 56 from Dutch, 54 from Russian. The analysis used the 3,726 with Zipf ≥ 3. A second table holds 85 sentence templates and 2,650 native word forms (particles, copula, auxiliaries, and frequent verbs and adjectives with every inflected form), each spelled in katakana as it is sung (は → ワ, を → オ, へ → エ).

**The cost model.** A new shape costs 1. A voiced form of a known shape costs 0.35, plus 0.3 once per mark (゛ and ゜), for learning the rule. A small kana whose full-size twin is known costs 0.35. ッ and ー cost 0.5 each. These numbers are parameters, not measurements; Part I explains why no study pins them down.

**Findings.**

- **Supermodularity is the dominant fact.** The best 3-glyph set spells 7 words, the best 6-glyph-cost set about 35, and the nested optimum then grows by 100 to 300 words per step of 3 cost units. Any small set learned on its own spells next to nothing.
- **The textbook order is far behind.** At a learning cost of 10, gojūon rows spell 14 words, most-used-glyph-first 112 and the optimised order 142; at 20, 109, 660 and 824; at 30, 191, 1,512 and 1,662. A frequency rule (most-used glyph first, voiced forms after their base) captures much of the benefit after the first few steps. The optimiser matters most at the start, where 0 and 7 words are the difference between a song and no song, and it lets constraints in: a fixed song, grammar, look-alikes.
- **Splitting, then merging, is free at the start and only at the start.** The optimiser's first two steps are disjoint on their own (クッルー, then ストリ). The existing seven-glyph song splits into two halves that spell 25 and 22 words and whose union spells 114, so 67 of its words need both halves. Later, a disjoint chunk spells almost nothing alone, so splitting stops paying.
- **Grammar has to be asked for.** Loanword coverage alone puts ワ (the topic particle は, sung "wa") at step 17, because few loanwords use it. Adding the sentence templates to the objective, weighted by grammatical level, brings ワ to step 8; weighting each core particle as well brings ワ and デス to step 5 and ノ to step 12, for about a quarter fewer loanwords at step 5 and almost none from step 9.
- **Keeping look-alikes apart is cheap.** Forbidding シ/ツ/ソ/ン, ク/ケ, ス/ヌ and similar pairs in the same or adjacent steps costs 7 to 9 % of the words at the two steps where it binds, and nothing from step 9 on.

**What this changes for learny.** The machinery generalises beyond katakana: a symbol inventory with costs and prerequisites (a voiced form after its base), a lexicon of items each needing a set of symbols, an all-or-nothing value, and a sequence search with vetoes. Hiragana, Hangul, Cyrillic for a Latin reader, or any decodable-text curriculum is the same problem. The ad hoc code is the starter of a learny component (filed as an issue); the decision itself lives with its first consumer, syllabary-songs (`docs/curriculum.md`).

## REFERENCES

1. Carnine DW. Similar sound separation and cumulative introduction in learning letter-sound correspondences. The Journal of Educational Research. 1976;69(10):368-372. [link](https://doi.org/10.1080/00220671.1976.10884928)
2. Cepeda NJ, Pashler H, Vul E, Wixted JT, Rohrer D. Distributed practice in verbal recall tasks: A review and quantitative synthesis. Psychological Bulletin. 2006;132(3):354-380. [link](https://doi.org/10.1037/0033-2909.132.3.354)
3. Kornell N. Optimising learning using flashcards: Spacing is more effective than cramming. Applied Cognitive Psychology. 2009;23(9):1297-1317. [link](https://doi.org/10.1002/acp.1537)
4. Karpicke JD, Roediger HL. The Critical Importance of Retrieval for Learning. Science. 2008;319(5865):966-968. [link](https://doi.org/10.1126/science.1152408)
5. Department for Education and Skills. Letters and Sounds: Principles and Practice of High Quality Phonics (DFES-00281-2007). London: DfES/Primary National Strategy; 2007. [link](https://assets.publishing.service.gov.uk/media/5a7aa7b6e5274a34770e630c/Letters_and_Sounds_-_DFES-00281-2007.pdf)
6. Matsunaga S. Effects of mnemonics on immediate and delayed recalls of hiragana by learners of Japanese as a foreign language. Japanese-Language Education around the Globe (Sekai no Nihongo Kyoiku). 2003;13:19-40. [link](https://jpf.repo.nii.ac.jp/record/337/files/Sekai13_matsunaga.pdf)
7. Sunde K, Furnes B, Lundetræ K. Does Introducing the Letters Faster Boost the Development of Children’s Letter Knowledge, Word Reading and Spelling in the First Year of School? Scientific Studies of Reading. 2020;24(2):141-158. [link](https://doi.org/10.1080/10888438.2019.1615491)
8. Chang LY, Tang YY, Lee CY, Chen HC. The Effect of Visual Mnemonics and the Presentation of Character Pairs on Learning Visually Similar Characters for Chinese-As-Second-Language Learners. Frontiers in Psychology. 2022;13:783898. [link](https://doi.org/10.3389/fpsyg.2022.783898)
9. Kang SHK, Pashler H. Learning painting styles: spacing is advantageous when it promotes discriminative contrast. Applied Cognitive Psychology. 2012;26(1):97-103. [link](https://doi.org/10.1002/acp.1801)
10. Birnbaum MS, Kornell N, Bjork EL, Bjork RA. Why interleaving enhances inductive learning: The roles of discrimination and retrieval. Memory & Cognition. 2013;41(3):392-402. [link](https://doi.org/10.3758/s13421-012-0272-7)
11. Brunmair M, Richter T. Similarity matters: A meta-analysis of interleaved learning and its moderators. Psychological Bulletin. 2019;145(11):1029-1052. [link](https://doi.org/10.1037/bul0000209)
12. Bhide A. Copying helps novice learners build orthographic knowledge: methods for teaching Devanagari akshara. Reading and Writing. 2018;31(1):1-33. [link](https://doi.org/10.1007/s11145-017-9767-8)
13. Pacton S, Perruchet P, Fayol M, Cleeremans A. Implicit learning out of the lab: The case of orthographic regularities. Journal of Experimental Psychology: General. 2001;130(3):401-426. [link](https://doi.org/10.1037/0096-3445.130.3.401)
14. Pacton S, Fayol M, Perruchet P. Children's Implicit Learning of Graphotactic and Morphological Regularities. Child Development. 2005;76(2):324-339. [link](https://doi.org/10.1111/j.1467-8624.2005.00848_a.x)
15. Yassin R, Shalhoub-Awwad Y. Characteristics of early spelling errors in Arabic: the impact of visual-orthographic features. Reading and Writing. 2026;39(7):2737-2761. [link](https://doi.org/10.1007/s11145-025-10731-y)
16. Weiss Y, Katzir T, Bitan T. Many ways to read your vowels—Neural processing of diacritics and vowel letters in Hebrew. NeuroImage. 2015;121:10-19. [link](https://doi.org/10.1016/j.neuroimage.2015.07.029)
17. Ludke KM, Ferreira F, Overy K. Singing can facilitate foreign language learning. Memory & Cognition. 2014;42(1):41-52. [link](https://doi.org/10.3758/s13421-013-0342-5)
18. Good AJ, Russo FA, Sullivan J. The efficacy of singing in foreign-language learning. Psychology of Music. 2015;43(5):627-640. [link](https://doi.org/10.1177/0305735614528833)
19. Racette A, Peretz I. Learning lyrics: To sing or not to sing? Memory & Cognition. 2007;35(2):242-253. [link](https://doi.org/10.3758/bf03193445)
20. Ehri LC, Nunes SR, Stahl SA, Willows DM. Systematic Phonics Instruction Helps Students Learn to Read: Evidence from the National Reading Panel’s Meta-Analysis. Review of Educational Research. 2001;71(3):393-447. [link](https://doi.org/10.3102/00346543071003393)
21. Stuart M. Getting ready for reading: Early phoneme awareness and phonics teaching improves reading and spelling in inner‐city second language learners. British Journal of Educational Psychology. 1999;69(4):587-605. [link](https://doi.org/10.1348/000709999157914)
22. Kornell N, Bjork RA. Learning concepts and categories: is spacing the "enemy of induction"? Psychological Science. 2008;19(6):585-592. [link](https://doi.org/10.1111/j.1467-9280.2008.02127.x)
23. Carpenter SK, Mueller FE. The effects of interleaving versus blocking on foreign language pronunciation learning. Memory & Cognition. 2013;41(5):671-682. [link](https://doi.org/10.3758/s13421-012-0291-4)
24. Carvalho PF, Goldstone RL. Putting category learning in order: Category structure and temporal arrangement affect the benefit of interleaved over blocked study. Memory & Cognition. 2014;42(3):481-495. [link](https://doi.org/10.3758/s13421-013-0371-0)
25. Carvalho PF, Goldstone RL. The benefits of interleaved and blocked study: Different tasks benefit from different schedules of study. Psychonomic Bulletin & Review. 2015;22(1):281-288. [link](https://doi.org/10.3758/s13423-014-0676-4)
26. Carvalho PF, Goldstone RL. Effects of interleaved and blocked study on delayed test of category learning generalization. Frontiers in Psychology. 2014;5. [link](https://doi.org/10.3389/fpsyg.2014.00936)
27. Zulkiply N, Burt JS. The exemplar interleaving effect in inductive learning: Moderation by the difficulty of category discriminations. Memory & Cognition. 2013;41(1):16-27. [link](https://doi.org/10.3758/s13421-012-0238-9)
28. Rohrer D, Dedrick RF, Stershic S. Interleaved practice improves mathematics learning. Journal of Educational Psychology. 2015;107(3):900-908. [link](https://doi.org/10.1037/edu0000001)
29. Rohrer D, Dedrick RF, Hartwig MK, Cheung CN. A randomized controlled trial of interleaved mathematics practice. Journal of Educational Psychology. 2020;112(1):40-52. [link](https://doi.org/10.1037/edu0000367)
30. Dunlosky J, Rawson KA, Marsh EJ, Nathan MJ, Willingham DT. Improving Students’ Learning With Effective Learning Techniques. Psychological Science in the Public Interest. 2013;14(1):4-58. [link](https://doi.org/10.1177/1529100612453266)
31. Cepeda NJ, Vul E, Rohrer D, Wixted JT, Pashler H. Spacing effects in learning: a temporal ridgeline of optimal retention. Psychological Science. 2008;19(11):1095-1102. [link](https://doi.org/10.1111/j.1467-9280.2008.02209.x)
32. Pashler H, Zarow G, Triplett B. Is Temporal Spacing of Tests Helpful Even When It Inflates Error Rates? Journal of Experimental Psychology: Learning, Memory, and Cognition. 2003;29(6):1051-1057. [link](https://doi.org/10.1037/0278-7393.29.6.1051)
33. Roediger HL, Karpicke JD. Test-Enhanced Learning. Psychological Science. 2006;17(3):249-255. [link](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
34. Rowland CA. The effect of testing versus restudy on retention: A meta-analytic review of the testing effect. Psychological Bulletin. 2014;140(6):1432-1463. [link](https://doi.org/10.1037/a0037559)
35. Kornell N, Bjork RA. Optimising self-regulated study: The benefits—and costs—of dropping flashcards. Memory. 2008;16(2):125-136. [link](https://doi.org/10.1080/09658210701763899)
36. Rawson KA, Dunlosky J. Optimizing schedules of retrieval practice for durable and efficient learning: How much is enough? Journal of Experimental Psychology: General. 2011;140(3):283-302. [link](https://doi.org/10.1037/a0023956)
37. Karpicke JD, Roediger HL. Expanding retrieval practice promotes short-term retention, but equally spaced retrieval enhances long-term retention. Journal of Experimental Psychology: Learning, Memory, and Cognition. 2007;33(4):704-719. [link](https://doi.org/10.1037/0278-7393.33.4.704)
38. Nakata T. Effects of expanding and equal spacing on second language vocabulary learning. Studies in Second Language Acquisition. 2015;37(4):677-711. [link](https://doi.org/10.1017/s0272263114000825)
39. Vlach HA, Sandhofer CM, Kornell N. The spacing effect in children’s memory and category induction. Cognition. 2008;109(1):163-167. [link](https://doi.org/10.1016/j.cognition.2008.07.013)
40. Settles B, Meeder B. A Trainable Spaced Repetition Model for Language Learning. Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 2016;1848-1858. [link](https://doi.org/10.18653/v1/p16-1174)
41. Tabibian B, Upadhyay U, De A, Zarezade A, Schölkopf B, Gomez-Rodriguez M. Enhancing human learning via spaced repetition optimization. Proceedings of the National Academy of Sciences. 2019;116(10):3988-3993. [link](https://doi.org/10.1073/pnas.1815156116)
42. Wickens CD, Hutchins S, Carolan T, Cumming J. Effectiveness of Part-Task Training and Increasing-Difficulty Training Strategies. Human Factors: The Journal of the Human Factors and Ergonomics Society. 2013;55(2):461-470. [link](https://doi.org/10.1177/0018720812451994)
43. Terrace HS. Discrimination learning with and without "errors". Journal of the Experimental Analysis of Behavior. 1963;6(1):1-27. [link](https://doi.org/10.1901/jeab.1963.6-1)
44. Baddeley A, Wilson BA. When implicit learning fails: Amnesia and the problem of error elimination. Neuropsychologia. 1994;32(1):53-68. [link](https://doi.org/10.1016/0028-3932(94)90068-x)
45. Clare L, Jones RSP. Errorless Learning in the Rehabilitation of Memory Impairment: A Critical Review. Neuropsychology Review. 2008;18(1):1-23. [link](https://doi.org/10.1007/s11065-008-9051-4)
46. Kornell N, Hays MJ, Bjork RA. Unsuccessful retrieval attempts enhance subsequent learning. Journal of Experimental Psychology: Learning, Memory, and Cognition. 2009;35(4):989-998. [link](https://doi.org/10.1037/a0015729)
47. Piasta SB, Wagner RK. Developing Early Literacy Skills: A Meta‐Analysis of Alphabet Learning and Instruction. Reading Research Quarterly. 2010;45(1):8-38. [link](https://doi.org/10.1598/rrq.45.1.2)
48. Piasta SB, Wagner RK. Learning letter names and sounds: Effects of instruction, letter type, and phonological processing skill. Journal of Experimental Child Psychology. 2010;105(4):324-344. [link](https://doi.org/10.1016/j.jecp.2009.12.008)
49. Treiman R, Weatherston S, Berch D. The role of letter names in children's learning of phoneme–grapheme relations. Applied Psycholinguistics. 1994;15(1):97-122. [link](https://doi.org/10.1017/s0142716400006998)
50. Justice LM, Pence K, Bowles RB, Wiggins A. An investigation of four hypotheses concerning the order by which 4-year-old children learn the alphabet letters. Early Childhood Research Quarterly. 2006;21(3):374-389. [link](https://doi.org/10.1016/j.ecresq.2006.07.010)
51. Jolly Learning. Jolly Phonics teacher's guide, Step 1: Group 1 sounds (s, a, t, i, p, n). Web page, accessed 2026-10-11. [link](https://jollylearning.com/resources/jolly-phonics/teachers-guide/group-1)
52. Jones CD, Reutzel DR. Enhanced Alphabet Knowledge Instruction: Exploring a Change of Frequency, Focus, and Distributed Cycles of Review. Reading Psychology. 2012;33(5):448-464. [link](https://doi.org/10.1080/02702711.2010.545260)
53. Cowan N. The magical number 4 in short-term memory: A reconsideration of mental storage capacity. Behavioral and Brain Sciences. 2001;24(1):87-114. [link](https://doi.org/10.1017/s0140525x01003922)
54. Cowan N. The magical mystery four: how is working memory capacity limited, and why? Current Directions in Psychological Science. 2010;19(1):51-57. [link](https://doi.org/10.1177/0963721409359277)
55. Burns MK. Empirical analysis of drill ratio research: refining the instructional level for drill tasks. Remedial and Special Education. 2004;25(3):167-173. [link](https://doi.org/10.1177/07419325040250030401)
56. Matsunaga S. Retention of katakana as foreign scripts: the effects of mnemonics and spatial ability. Journal of the National Council of Less Commonly Taught Languages. 2009;6:85-112. [link](https://doaj.org/article/af5ca5db2c014ed2aa0b0dbf67be6406)
57. Shmidman A, Ehri L. Embedded Picture Mnemonics to Learn Letters. Scientific Studies of Reading. 2010;14(2):159-182. [link](https://doi.org/10.1080/10888430903117492)
58. Ehri LC, Deffner ND, Wilce LS. Pictorial mnemonics for phonics. Journal of Educational Psychology. 1984;76(5):880-893. [link](https://doi.org/10.1037/0022-0663.76.5.880)
59. Brown L. The use of visual/verbal and physical mnemonics in the teaching of Korean Hangul in an authentic L2 classroom context. Writing Systems Research. 2012;4(1):72-90. [link](https://doi.org/10.1080/17586801.2011.635949)
60. Nag S. Early reading in Kannada: the pace of acquisition of orthographic knowledge and phonemic awareness. Journal of Research in Reading. 2007;30(1):7-22. [link](https://doi.org/10.1111/j.1467-9817.2006.00329.x)
61. Schubert T, Gawthrop R, Kinoshita S. Evidence for cross-script abstract identities in learners of Japanese kana. Memory & Cognition. 2018;46(6):1010-1021. [link](https://doi.org/10.3758/s13421-018-0818-4)
62. Nakata T, Suzuki Y. Effects of massing and spacing on the learning of semantically related and unrelated words. Studies in Second Language Acquisition. 2019;41(2):287-311. [link](https://doi.org/10.1017/s0272263118000219)
63. Tinkham T. The effects of semantic and thematic clustering on the learning of second language vocabulary. Second Language Research. 1997;13(2):138-163. [link](https://doi.org/10.1191/026765897672376469)
64. Goldstone RL. Perceptual learning. Annual Review of Psychology. 1998;49(1):585-612. [link](https://doi.org/10.1146/annurev.psych.49.1.585)
65. Higuchi H, Kobayashi T. Letter visual similarity of Japanese hiragana and katakana based on reaction times. Current Psychology. 2023;42(15):12835-12844. [link](https://doi.org/10.1007/s12144-021-02664-w)
66. Treiman R, Kessler B. Similarities among the shapes of writing and their effects on learning. Written Language & Literacy. 2011;14(1):39-57. [link](https://doi.org/10.1075/wll.14.1.03tre)
67. Ghandour A, Trouche E, Guillo D, Valdois S. The influence of visual attention on letter recognition and reading acquisition in Arabic. Frontiers in Psychology. 2025;16:1628051. [link](https://doi.org/10.3389/fpsyg.2025.1628051)
68. Shu H, Chen X, Anderson RC, Wu N, Xuan Y. Properties of School Chinese: Implications for Learning to Read. Child Development. 2003;74(1):27-47. [link](https://doi.org/10.1111/1467-8624.00519)
69. Ho CS, Bryant P. Learning to Read Chinese Beyond the Logographic Phase. Reading Research Quarterly. 1997;32(3):276-289. [link](https://doi.org/10.1598/rrq.32.3.3)
70. Anderson RC, Ku YM, Li W, Chen X, Wu X, Shu H. Learning to See the Patterns in Chinese Characters. Scientific Studies of Reading. 2013;17(1):41-56. [link](https://doi.org/10.1080/10888438.2012.689789)
71. Shimron J. The role of vowels in reading: A review of studies of English and Hebrew. Psychological Bulletin. 1993;114(1):52-67. [link](https://doi.org/10.1037/0033-2909.114.1.52)
72. Inagaki K, Hatano G, Otake T. The Effect of Kana Literacy Acquisition on the Speech Segmentation Unit Used by Japanese Young Children. Journal of Experimental Child Psychology. 2000;75(1):70-91. [link](https://doi.org/10.1006/jecp.1999.2523)
73. Schön D, Boyer M, Moreno S, Besson M, Peretz I, Kolinsky R. Songs as an aid for language acquisition. Cognition. 2008;106(2):975-983. [link](https://doi.org/10.1016/j.cognition.2007.03.005)
74. Wallace WT. Memory for music: Effect of melody on recall of text. Journal of Experimental Psychology: Learning, Memory, and Cognition. 1994;20(6):1471-1485. [link](https://doi.org/10.1037/0278-7393.20.6.1471)
75. Gordon RL, Fehd HM, McCandliss BD. Does Music Training Enhance Literacy Skills? A Meta-Analysis. Frontiers in Psychology. 2015;6. [link](https://doi.org/10.3389/fpsyg.2015.01777)
76. Loach JC, Wang J. 2016. Optimizing the learning order of Chinese characters using a novel topological sort algorithm. PLOS ONE 11(10):e0163623. [link](https://doi.org/10.1371/journal.pone.0163623) (preprint: [arXiv:1602.08742](https://arxiv.org/abs/1602.08742))
77. Yan X, Fan Y, Di Z, Havlin S, Wu J. 2013. Efficient learning strategy of Chinese characters based on network approach. PLOS ONE 8(8):e69745. [link](https://doi.org/10.1371/journal.pone.0069745) (preprint: [arXiv:1303.1599](https://arxiv.org/abs/1303.1599))
78. Chlamtac E, Dinitz M, Konrad C, Kortsarz G, Rabanca G. 2018. The densest k-subhypergraph problem. SIAM Journal on Discrete Mathematics 32(2):1458-1477. [link](https://doi.org/10.1137/16M1096402) (preprint: [arXiv:1605.04284](https://arxiv.org/abs/1605.04284))
79. Feige U, Kortsarz G, Peleg D. 2001. The dense k-subgraph problem. Algorithmica 29(3):410-421. [link](https://doi.org/10.1007/s004530010050)
80. Goldschmidt O, Nehme D, Yu G. 1994. Note: On the set-union knapsack problem. Naval Research Logistics 41(6):833-842. [link](https://ideas.repec.org/a/wly/navres/v41y1994i6p833-842.html)
81. Taylor R. 2016. Approximations of the densest k-subhypergraph and set union knapsack problems. arXiv:1610.04935 [cs.DS]. [link](https://arxiv.org/abs/1610.04935)
82. Khot S. 2006. Ruling out PTAS for graph min-bisection, dense k-subgraph, and bipartite clique. SIAM Journal on Computing 36:1025-1071. [link](https://doi.org/10.1137/S0097539705447037)
83. Bhaskara A, Charikar M, Chlamtac E, Feige U, Vijayaraghavan A. 2010. Detecting high log-densities: an O(n^1/4) approximation for densest k-subgraph. Proceedings of STOC 2010, pp. 201-210. [link](https://doi.org/10.1145/1806689.1806719) (preprint: [arXiv:1001.2891](https://arxiv.org/abs/1001.2891))
84. Nemhauser GL, Wolsey LA, Fisher ML. 1978. An analysis of approximations for maximizing submodular set functions - I. Mathematical Programming 14(1):265-294. [link](https://doi.org/10.1007/BF01588971)
85. Hassin R, Levin A. 2005. An approximation algorithm for the minimum latency set cover problem. In: Algorithms - ESA 2005, LNCS 3669, pp. 726-733. [link](https://doi.org/10.1007/11561071_64) ([author PDF](https://www.tau.ac.il/~hassin/minsum_sc.pdf))
86. Azar Y, Gamzu I, Yin X. 2009. Multiple intents re-ranking. Proceedings of STOC 2009, pp. 669-678. [link](https://doi.org/10.1145/1536414.1536505)
87. Bansal N, Gupta A, Krishnaswamy R. 2010. A constant factor approximation algorithm for generalized min-sum set cover. Proceedings of SODA 2010, pp. 1539-1545. [link](https://doi.org/10.1137/1.9781611973075.125)
88. Margot F, Queyranne M, Wang Y. 2003. Decompositions, network flows, and a precedence constrained single-machine scheduling problem. Operations Research 51(6). [link](https://doi.org/10.1287/opre.51.6.981.24912)
89. Jolly Learning. Letter sounds recognition (Jolly Phonics teacher's guide). [link](https://jollylearning.com/teachersguide/letter-sounds-recognition)
90. Chlamtac E, Dinitz M, Makarychev Y. 2017. Minimizing the union: tight approximations for small set bipartite vertex expansion. Proceedings of SODA 2017. [link](https://arxiv.org/abs/1611.07866)
91. Svitkina Z, Fleischer L. 2011. Submodular approximation: sampling-based algorithms and lower bounds. SIAM Journal on Computing. [link](https://doi.org/10.1137/100783352) (preprint: [arXiv:0805.1071](https://arxiv.org/abs/0805.1071))
92. Khuller S, Moss A, Naor J. 1999. The budgeted maximum coverage problem. Information Processing Letters 70(1):39-45. [link](https://doi.org/10.1016/S0020-0190(99)00031-9)
93. Sviridenko M. 2004. A note on maximizing a submodular set function subject to a knapsack constraint. Operations Research Letters 32(1):41-43. [link](https://doi.org/10.1016/S0167-6377(03)00062-2)
94. Feige U. 1998. A threshold of ln n for approximating set cover. Journal of the ACM 45(4):634-652. [link](https://doi.org/10.1145/285055.285059)
95. Manurangsi P. 2017. Almost-polynomial ratio ETH-hardness of approximating densest k-subgraph. Proceedings of STOC 2017, pp. 954-961. [link](https://doi.org/10.1145/3055399.3055412)
96. Arulselvan A. 2014. A note on the set union knapsack problem. Discrete Applied Mathematics 169:214-218. [link](https://doi.org/10.1016/j.dam.2013.12.015)
97. Picard JC. 1976. Maximal closure of a graph and applications to combinatorial problems. Management Science 22(11):1268-1272. [link](https://doi.org/10.1287/mnsc.22.11.1268)
98. Gallo G, Grigoriadis MD, Tarjan RE. 1989. A fast parametric maximum flow algorithm and applications. SIAM Journal on Computing 18(1):30-55. [link](https://doi.org/10.1137/0218003)
99. Charikar M. 2000. Greedy approximation algorithms for finding dense components in a graph. In: Approximation Algorithms for Combinatorial Optimization (APPROX 2000), LNCS 1913, pp. 84-95. [link](https://doi.org/10.1007/3-540-44436-X_10)
100. Huangfu Q, Hall JAJ. 2018. Parallelizing the dual revised simplex method (the standard citation for the HiGHS solver). Mathematical Programming Computation 10:119-142. [link](https://doi.org/10.1007/s12532-017-0130-5)
101. Wei Z, Hao JK. 2021. Multistart solution-based tabu search for the set-union knapsack problem. Applied Soft Computing 105:107260. [link](https://doi.org/10.1016/j.asoc.2021.107260)
102. Zhu W, Luo L. 2022. Efficient and effective local search for the set-union knapsack problem and budgeted maximum coverage problem. arXiv:2207.00749 [cs.DS]. [link](https://arxiv.org/abs/2207.00749)
103. aradzie (GitHub user). keybr.com: source repository and README (software, GitHub). [link](https://github.com/aradzie/keybr.com)
104. Chudak FA, Hochbaum DS. 1999. A half-integral linear programming relaxation for scheduling precedence-constrained jobs on a single machine. Operations Research Letters 25:199-204. [link](https://doi.org/10.1016/s0167-6377(99)00056-5)
105. Chekuri C, Motwani R. 1999. Precedence constrained scheduling to minimize sum of weighted completion times on a single machine. Discrete Applied Mathematics 98:29-38. [link](https://doi.org/10.1016/s0166-218x(98)00143-7)
106. Sidney JB. 1975. Decomposition algorithms for single-machine sequencing with precedence relations and deferral costs. Operations Research 23(2):283-298. [link](https://doi.org/10.1287/opre.23.2.283)
107. Correa JR, Schulz AS. 2005. Single-machine scheduling with precedence constraints. Mathematics of Operations Research 30(4):1005-1021. [link](https://doi.org/10.1287/moor.1050.0158)
108. Feige U, Lovasz L, Tetali P. 2004. Approximating min sum set cover. Algorithmica 40(4):219-234. [link](https://doi.org/10.1007/s00453-004-1110-5)
109. Skutella M, Williamson DP. 2011. A note on the generalized min-sum set cover problem. Operations Research Letters 39(6):433-436. [link](https://doi.org/10.1016/j.orl.2011.08.002) (preprint: [arXiv:1107.2033](https://arxiv.org/abs/1107.2033))
110. Im S, Sviridenko M, van der Zwaan R. 2014. Preemptive and non-preemptive generalized min sum set cover. Mathematical Programming 2014 (pp. 377-401). [link](https://doi.org/10.1007/s10107-013-0651-2)
111. Bansal N, Batra J, Farhadi M, Tetali P. 2023. On min sum vertex cover and generalized min sum set cover. SIAM Journal on Computing 52:327-357. [link](https://doi.org/10.1137/21m1434052) (conference version SODA 2021: [link](https://doi.org/10.1137/1.9781611976465.62); preprint: [arXiv:2007.09172](https://arxiv.org/abs/2007.09172))
112. Bhangale A, Zhang Y. 2026. A 4.509-approximation algorithm for generalized min sum set cover. arXiv:2605.10031 [cs.DS]. [link](https://arxiv.org/abs/2605.10031)
113. Azar Y, Gamzu I. 2011. Ranking with submodular valuations. Proceedings of SODA 2011, pp. 1070-1079. [link](https://doi.org/10.1137/1.9781611973082.81) (preprint: [arXiv:1007.2503](https://arxiv.org/abs/1007.2503))
114. Im S, Nagarajan V, van der Zwaan R. 2012. Minimum latency submodular cover. arXiv:1110.2207 [cs.DS]. [link](https://arxiv.org/abs/1110.2207)
115. Munagala K, Babu S, Motwani R, Widom J. 2005. The pipelined set cover problem. In: Database Theory - ICDT 2005, LNCS 3363, pp. 83-98. [link](https://doi.org/10.1007/978-3-540-30570-5_6)
116. Streeter M, Golovin D. 2008. An online algorithm for maximizing submodular functions. Advances in Neural Information Processing Systems 21 (NIPS 2008), pp. 1577-1584. [link](https://mlanthology.org/neurips/2008/streeter2008neurips-online)
117. Bernstein A, Disser Y, Gross M, Himburg S. 2022. General bounds for incremental maximization. Mathematical Programming 191(2):953-979. [link](https://doi.org/10.1007/s10107-020-01576-0) (conference version, ICALP 2017: [link](https://drops.dagstuhl.de/opus/volltexte/2017/7465))
118. scriptin. TopoKanji: topologically ordered lists of kanji for effective learning (software and data, GitHub). [link](https://github.com/scriptin/topokanji)
119. Higuchi H, Okumura Y, Kobayashi T. 2019. Influence of letter properties on Japanese hiragana reading and writing acquisition. The Japan Journal of Logopedics and Phoniatrics 60(2):113-120. [link](https://doi.org/10.5112/jjlp.60.113)
120. Piasta SB, Wagner RK. 2010. Developing early literacy skills: a meta-analysis of alphabet learning and instruction. Reading Research Quarterly 45(1). [link](https://pmc.ncbi.nlm.nih.gov/articles/PMC2910925)
121. Juel C, Roper/Schneider D. 1985. The influence of basal readers on first grade reading. Reading Research Quarterly 20(2):134-152. [link](https://doi.org/10.2307/747751)
122. Mesmer HAE. 2005. Text decodability and the first-grade reader. Reading & Writing Quarterly 21:61-86. [link](https://doi.org/10.1080/10573560590523667)
123. Cheatham JP, Allor JH. 2012. The influence of decodability in early reading text on reading achievement: a review of the evidence. Reading and Writing 25:2223-2246. [link](https://doi.org/10.1007/s11145-011-9355-2)
124. Hu HM, Nation P. 2000. Unknown vocabulary density and reading comprehension. Reading in a Foreign Language 13(1):403-430. [link](https://doi.org/10.64152/10125/66973)
125. Schmitt N, Jiang X, Grabe W. 2011. The percentage of words known in a text and reading comprehension. The Modern Language Journal 95(1):26-43. [link](https://doi.org/10.1111/j.1540-4781.2011.01146.x)
126. Nation ISP. 2006. How large a vocabulary is needed for reading and listening? The Canadian Modern Language Review 63(1):59-82. [link](https://doi.org/10.3138/cmlr.63.1.59)
127. Nation P, Wang MK. 1999. Graded readers and vocabulary. Reading in a Foreign Language 12. [link](https://doi.org/10.64152/10125/66966)
128. Reddy S, Labutov I, Banerjee S, Joachims T. 2016. Unbounded human learning. Proceedings of KDD 2016, pp. 1815-1824. [link](https://doi.org/10.1145/2939672.2939850)
129. Doignon JP, Falmagne JC. 1985. Spaces for the assessment of knowledge. International Journal of Man-Machine Studies 23(2):175-196. [link](https://doi.org/10.1016/S0020-7373(85)80031-6)
130. Falmagne JC, Doignon JP. 2011. Learning Spaces: Interdisciplinary Applied Mathematics. Springer. [link](https://doi.org/10.1007/978-3-642-01039-2)
131. Doignon JP. 1994. Knowledge spaces and skill assignments. In: Fischer GH, Laming D (eds), Contributions to Mathematical Psychology, Psychometrics, and Methodology. Springer. [link](https://doi.org/10.1007/978-1-4612-4308-3_8)
132. Duntsch I, Gediga G. 1995. Skills and knowledge structures. British Journal of Mathematical and Statistical Psychology 48(1):9-27. [link](https://doi.org/10.1111/j.2044-8317.1995.tb01047.x)
