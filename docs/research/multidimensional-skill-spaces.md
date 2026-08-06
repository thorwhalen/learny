# Multi-dimensional skill spaces with order structure: what the field calls it, and what is actually known

**Date: 2026-08-06**

## What this is / what it is not

**What it is.** A research report on the learning-science, psychometric and machine-learning literature that formalises *skill/knowledge spaces built from several ordered dimensions*, the partial order such a product induces, whether mastery propagates down that order, and whether it is pedagogically wise to temporarily reduce difficulty on one dimension while advancing another. It maps a specific informal model (stated below) onto established terminology, reports what the evidence supports, and flags where the literature is thin, contested, or negative.

**What it is not.** It is not about music, and no music-specific literature was consulted. It is not a systematic review — coverage is deliberately broad rather than exhaustive, and search was English-language and web-accessible only. Several key sources (ScienceDirect, Springer, ResearchGate PDFs) returned 403 and were reached only through abstracts, indexes, or citing works; those cases are marked **[abstract only]** or **[secondary]** in the text. Where I could not verify a claim I say so rather than asserting it.

**The model being mapped.** (1) Learning has several dimensions, each carrying a roughly total order (a difficulty ladder). (2) The product A×B inherits the *product order*: (a,b) ≤ (x,y) iff a ≤ x and b ≤ y. (3) That order should carry **mastery propagation** — mastering (x,y) implies mastering everything below it, so introducing a new dimension does not restart the others at the bottom. (4) The combinatorial explosion must be mitigated. (5) Counter-intuition: when stepping up on one dimension it may be better to *temporarily simplify the others* — having (10,1), reach (10,2) via (4,2), (6,2), (10,2). (6) All of this is suspected to depend heavily on subject and learner.

---

## 0. The short answer

Points 1–3 are a known formal object with a fifty-year literature: the model is a **quasi-ordinal knowledge space** [1] over a **product order** derived by **component-based construction** [11][12], and its polytomous (graded-item) form was worked out explicitly between 2019 and 2023 [13][14][15]. The same object appears in psychometrics as the permissible attribute space **A(E)** of a **Hierarchical Latent Attribute Model** [16] and as the reduced Q-matrix of the **Attribute Hierarchy Method** [17][18].

Point 4 has a clean mathematical answer that is better than expected: committing to the product order collapses the state space from 2^(m·n) to a binomial coefficient. Verified below.

Point 3 has a caveat the maintainer will not like: Doignon and Falmagne state explicitly that closure under intersection — which is exactly what "mastery propagates down a partial order" buys you — **"does not make good pedagogical sense"** [1, p. 10]. The mainstream KST position is that the maintainer's structure is *too strong*, not too weak.

Point 5 is the most interesting and the best-supported part of the intuition, but it has **no single established name**. It is covered, partially and under four different vocabularies, by the *simplifying conditions method* [19], the *isolated-elements effect* [20], *simplification* in the part-task-training taxonomy [21], and *separation* in variation theory [22]. The strongest single piece of evidence is a meta-analysis of 37 transfer studies [23] whose finding is sharply conditional: increasing-difficulty training worked **when the increases were adaptive and not when they were fixed steps**, and **experienced learners benefited less or were harmed**. Several well-evidenced effects (contextual interference, interleaving, desirable difficulties, productive failure) point the *other* way, and the reconciliation is not settled.

Point 6 — that it depends on subject and learner — is the one point on which the literature is unambiguous and unanimous.

---

## 1. Knowledge Space Theory and Learning Spaces: the spine

### 1.1 The objects

Knowledge Space Theory (KST) was introduced by Doignon and Falmagne in 1985 as a combinatorial rather than numerical approach to assessment [1]. A **knowledge structure** is a pair (Q, K) where Q is a domain of items and K is a family of subsets of Q — the **knowledge states** — always containing ∅ and Q. A student in state K can in principle solve exactly the items in K.

A **knowledge space** is a knowledge structure closed under union [1, Def. 5]. A **learning space** additionally satisfies two axioms [1, Def. 3]:

- **[L1] Learning smoothness.** For states K ⊂ L there is a chain K = K₀ ⊂ K₁ ⊂ … ⊂ K_p = L with |K_i \ K_{i−1}| = 1. *In words: the learner can reach L by mastering items one by one.*
- **[L2] Learning consistency.** For K ⊂ L, if K ∪ {q} is a state then L ∪ {q} is a state. *In words: knowing more does not prevent learning something new.*

Theorem 7 of [1] gives the key equivalence: **learning space ⟺ antimatroid ⟺ well-graded knowledge space**. Well-gradedness means any two states are joined by a path of single-item steps [1, Def. 5].

A **learning path** is a maximal chain of states; a path in which consecutive states differ by exactly one item is a **gradation** [4].

**The fringes.** The **outer fringe** of K is K^O = {q ∉ K : K ∪ {q} ∈ K}; the **inner fringe** is K^I = {q ∈ K : K \ {q} ∈ K} [1, Def. 20]. In a learning space every state is uniquely determined by the pair (K^I, K^O) [1, Thm 21]. The outer fringe is the formal operationalisation of "what the learner is ready to learn next" — a discrete, computable Zone of Proximal Development.

**This is not merely theoretical.** Doignon and Falmagne report that, estimated over hundreds of thousands of ALEKS assessments, the probability that a student succeeds in learning an item drawn from the outer fringe of their state is **about .93** [1, §6]. That is the single most directly relevant empirical number in this entire report for anyone building a next-item selector.

### 1.2 The surmise relation, Birkhoff, and why the maintainer's model is the *special* case

The **surmise relation** ⊑ on Q is the prerequisite relation: q ⊑ q′ means that from mastery of q′ one may surmise mastery of q [4]. Surmise relations are quasi-orders, and their whole point is that they "reduce the quantity of all possible solution patterns to a more manageable amount of knowledge states" [4].

The bridge is **Birkhoff's theorem** [3], stated in KST form as [1, Thm 10]:

> There is a one-to-one correspondence between the collection of all **quasi ordinal spaces** K on Q (knowledge spaces closed under *both* union and intersection) and the collection of all quasi orders on Q, via
> K ∈ K ⟺ (∀(q,r) ∈ Q : r ∈ K ⇒ q ∈ K).

That second line is *exactly* the maintainer's point 3: a state is a **downset** (order ideal) of the prerequisite order — mastering something implies mastering everything below it. **The maintainer has independently reconstructed the quasi-ordinal knowledge space.**

Now the caveat. Immediately after Theorem 10, Doignon and Falmagne write: *"Note in passing that the closure under intersection does not make good pedagogical sense."* [1, p. 10]. The reason is that intersection-closure forbids genuine alternative routes. If two learners can each be in a state, intersection-closure forces their common core to also be a legal state, which rules out "you need **either** A **or** B before C". The field's mainstream object is therefore the **union-closed-but-not-intersection-closed** knowledge space, whose combinatorial description is not a relation but a **surmise function** σ mapping each item to its family of **atoms** (alternative minimal prerequisite sets), via an extension of Birkhoff's theorem due to Doignon and Falmagne [1, Thm 18].

There is a further, practical warning from the same source. The QUERY procedure that elicits a structure from human experts asks only relation-level questions, whose transitive closure yields a quasi-ordinal space L₁; this L₁ "typically contains a possibly very large number of false states, which are due to the closure of intersection" [1, §on QUERY]. Their pragmatic verdict is that L₁ is nonetheless "sufficiently informative to be used in the schools and colleges", and is then refined against data. That is a fair description of the maintainer's likely trajectory: start with the product order because it is cheap and expressive; expect it to over-generate states; refine from data.

### 1.3 Competence-based KST: multiple attributes behind the items

Competence-based KST (CbKST) splits the model into a **performance level** (observable items) and a **competence level** (latent skills), linked by a **skill function** or **skill map** assigning a set of skills to each item, with a **problem function** in the other direction [5][6][secondary]. Korossy (1993, 1997, 1999) and Heller and colleagues are credited with introducing the competence level [5][secondary]. Two delineation modes are standard:

- **conjunctive** — all assigned skills are needed; the induced family is a *closure space*;
- **disjunctive** — at least one assigned skill suffices; the induced family is a *knowledge space* [6][7][secondary].

Extensions include **skill multimaps** (several alternative skill sets per item), **fuzzy skill maps** (graded proficiency per skill) and **fuzzy skill multimaps** [5][7][secondary]. There is also recent work on **master fringes** in CbKST for personalised learning [5][abstract only]. CbKST is the natural home for "an item requires level 6 of dimension A and level 2 of dimension B".

### 1.4 The direct hit: component-based construction of surmise relations

The closest thing in the literature to the maintainer's construction is **component-based knowledge space construction**, developed by Albert and Held and by Schrepp, Held and Albert. Problems are described by **components** (attributes); **ordering principles** are applied to the component values; and the surmise relation on problems is derived from those component orderings. Albert and Held's 1994 chapter is "Establishing knowledge spaces by systematical problem construction" and their 1999 chapter is "Component based knowledge spaces in problem solving and inductive reasoning"; Schrepp, Held and Albert (1999) applied it to chess problems, where the components are the tactical *motives* (subgoals) of the position [11][12][secondary — the primary PDFs returned 403; details are from citing indexes and the `pks` R package documentation]. The described construction uses formal principles of "set inclusion" and "sequence inclusion" over the components to build a surmise relation and hence a quasi-ordinal knowledge space [12][secondary].

I could not verify the exact algebra from the primary sources, so I state it carefully: **the component-based programme is the same idea as the maintainer's product order, applied domain by domain, and it is the literature to read first.** Whether any of those papers uses the phrase "product order" I could not confirm.

### 1.5 Polytomous KST: ordered levels per item, and the direct generalisation of Birkhoff

Classical KST is binary — an item is mastered or not. The maintainer's dimensions are graded. The generalisation exists and is recent:

- Schrepp (1997), "A generalization of knowledge space theory to problems with more than two answer alternatives" [13].
- Stefanutti, Anselmi, de Chiusole and Spoto (2020), "On the polytomous generalization of knowledge space theory", *J. Math. Psych.* 94:102306, which decomposes Schrepp's closure condition into necessary and sufficient properties that "allow for a straight generalization of Birkhoff's Theorem" [14][abstract only].
- Heller (2021), "Generalizing quasi-ordinal knowledge spaces to polytomous items", *J. Math. Psych.* 101:102515 [15][abstract only].
- Follow-ups: "Notes on the polytomous generalization of KST" (2022); "Well-graded polytomous knowledge structures" (2023); "CD-polytomous knowledge spaces and corresponding polytomous surmise systems" (2023); "Polytomous knowledge structures based on entail relations" (2024); "Discriminability around polytomous knowledge structures" (2025) [all abstract/title only].
- On the probabilistic side, Stefanutti, de Chiusole, Anselmi and Spoto extended the Basic Local Independence Model to polytomous data (PoLIM) [abstract only].

In the polytomous formulation a state is a *function* from items to ordered response levels rather than a subset, and the state family is ordered pointwise. **A pointwise order on functions into chains is exactly a product order.** So the polytomous KST literature of 2019–2024 is, formally, the literature on the maintainer's object — and it is active enough that the terminology is still settling. This is worth knowing: they are not late to a closed field.

### 1.6 What ALEKS actually shows at scale

ALEKS is the large deployed instance, used by "about four to five million students each year" across mathematics, chemistry, statistics and accounting [2]. Concrete facts from the ALEKS team's own account [2]:

- A typical course is **300–600 items**; an item is a granular topic instantiated by interchangeable **instances** designed to be equal in difficulty (this is a radicals/incidentals design, see §6.4).
- For one 314-item course, the number of knowledge states is **about 10²³**, against 2³¹⁴ ≈ 10⁹⁴ subsets [2]. The structure is a learning space [2, Def. A.1].
- Assessment: the outer fringe of the state from the initial assessment is the entry point to learning mode; the student picks an item from the outer fringe, practises instances, and on success the item is added and the fringe recomputed [2].
- Periodic **progress assessments** are described by the authors as delivering retrieval practice and enforcing **interleaving** on items previously learned by massed practice [2].
- Usage statistics reported: Sixth-Grade Math N = 99,482 students, mean 4.9 assessments, mean 128.2 items learned, mean 15.6 hours; Algebra I N = 63,097, 4.1 assessments, 104.3 items learned, 13.7 hours [2, Table 1]. The standard deviations are of the same order as the means, which is itself informative about learner heterogeneity.
- They report the aggregate success rate for learning an outer-fringe item "increases monotonically with the course grade" [2].

**On outcome evidence**, be careful. The ALEKS paper is explicit that it studies *internal* measures and points to a separate literature for external outcomes, listing Hagerty et al. (2010) and Mojarad et al. (2018) for college mathematics, Baxter and Thibodeau (2011) for accounting, Hickey et al. (2020) for college chemistry, Hu et al. (2007) for statistics, Huang et al. (2016) and Craig et al. (2011, 2013) for middle-school mathematics, Reddy and Harper (2013) for placement, and a meta-analysis by Fang et al. (2019) [2]. **I did not verify any of those outcome studies, and I found no What Works Clearinghouse intervention report for ALEKS.** Treat "ALEKS works" as an unverified claim in this report; treat "ALEKS is a working large-scale instantiation of a learning space, whose outer-fringe readiness prediction is ~.93 accurate" as verified [1][2].

---

## 2. The psychometric mirror: Q-matrices, DINA, and attribute hierarchies

### 2.1 The basic objects

Cognitive diagnostic models (CDMs) represent a learner as a binary **attribute profile** α ∈ {0,1}^K — a point in a discrete multi-attribute space — and an item by its row of the **Q-matrix**, which attributes it requires.

- **DINA** is *conjunctive*: a correct response requires **all** required attributes [8][secondary].
- **DINO** is *disjunctive/compensatory*: **at least one** required attribute suffices [8][secondary].
- **G-DINA** (de la Torre, 2011) is saturated: the success probability decomposes into an intercept plus main effects of the required attributes plus their interactions, and nests DINA, DINO, ACDM, R-RUM as constrained cases [8][secondary].

Empirical model comparisons do **not** find a single winner. In one reading-comprehension application, G-DINA fit best overall, ACDM/C-RUM/NC-RUM were close, and DINA and DINO were substantially worse at test level — but item-level comparison showed **DINA, DINO and ACDM each fitting different items**, leading the authors to argue that model choice should be made per item, and that "relationships among subskills might be a combination of compensatory and noncompensatory" [24][secondary]. That is a direct and important answer to the maintainer's mastery-propagation question: *in real data, the conjunctive/compensatory question does not have one answer even within a single test.*

### 2.2 Attribute hierarchies: the same object as a quasi-ordinal knowledge space

The **Attribute Hierarchy Method** (AHM) was developed by Leighton, Gierl and Hunka at the University of Alberta [17][18]. Its defining move, relative to Tatsuoka's Rule Space, is to assume *dependencies* among attributes: prerequisites must be mastered before dependents, so mastering a higher attribute implies mastering everything below it. This is operationalised by the **reduced incidence matrix Q_r**, which retains only hierarchy-consistent attribute-item combinations, and from it an **expected response matrix E** [17].

Gu and Xu formalise this as the **Hierarchical Latent Attribute Model (HLAM)**: a hierarchy E = {k → ℓ : k is prerequisite for ℓ} induces a DAG, which induces the set A(E) ⊆ {0,1}^K of **permissible** attribute patterns; patterns violating the hierarchy get population proportion exactly zero [16]. They are careful to note that this DAG "encodes hard constraints on what variable patterns are permissible/forbidden", unlike a Bayesian-network DAG which encodes conditional independence [16].

**A(E) is the set of downsets of the prerequisite order — i.e. precisely the quasi-ordinal knowledge space of §1.2.** The KST and CDM literatures have independently constructed the same lattice. Recognising that they are the same object is genuinely useful: the KST literature has the assessment algorithms and the fringe machinery; the CDM literature has the identifiability theory and the estimation machinery.

### 2.3 Identifiability: the combinatorial explosion in psychometric clothing

This is where the CDM literature earns its keep, because it has actually done the hard work on what breaks as K grows.

- Gu and Xu establish **sufficient and necessary identifiability conditions for HLAMs**, including for the case where the hierarchy and the Q-matrix are themselves unknown, and show that the hierarchy "necessarily leads to degenerate parameter space" — some proportion parameters are constrained to zero, which is exactly what makes the standard identifiability results inapplicable [16]. Their conditions "directly and sharply characterize the different impacts on identifiability cast by different attribute types in the graph" [16].
- Attributes that appear **only in conjunction with other attributes** are not separately identifiable in DINA — a long-known issue that is "ignored in practice" [25][secondary]. This is the formal version of "if dimension B is never varied while A is held fixed, you cannot tell them apart."
- Design recommendations reported in the literature include that the Q-matrix should contain at least two identity submatrices and each attribute be measured by more than one item [25][secondary].
- Non-identifiability in Q-matrix-based CDMs yields **equivalence classes** of parameters, with some attributes still individually classifiable even when the full model is not [26][abstract/title].

### 2.4 How many attributes can a real system carry?

Nájera, Abad and Sorrel (2021) reviewed applied CDM studies and report that **the most common number of attributes K in applied studies is 4**, with 5 the most usual value in simulation studies; practical applications typically use 4–6 [9]. As K grows, Q-matrix specification becomes harder, estimation becomes harder, and high attribute counts can mask redundant or highly correlated attributes [9]. Their recommended detection methods are parallel analysis (83% accuracy), a machine-learning "Factor Forest" (82%) and AIC-based model comparison (77%), with 97.6% accuracy when all three agree [9].

**Read this as a hard empirical constraint.** Deployed diagnostic assessment has converged on roughly 4–6 latent dimensions, not 20. If the maintainer's model needs many dimensions, the psychometric estimation machinery will not follow it there without a lot of data and a lot of structure.

### 2.5 Compensatory vs conjunctive in continuous form: MIRT

The same distinction exists with continuous abilities. **Compensatory MIRT** puts a linear combination a₁θ₁ + a₂θ₂ − d inside the logistic: high θ₁ can compensate for low θ₂. **Noncompensatory / partially compensatory MIRT** (Sympson, 1977) takes a **product of unidimensional probabilities**, so the success probability is limited by the examinee's *lowest* relevant ability [10][secondary]. Bolt and Lall (2003) compared estimation of both families by MCMC [10]. The terms "partially compensatory" and "noncompensatory" are used interchangeably in the literature and do not reliably denote different models [10][secondary].

The maintainer's product order is the *deterministic* limiting case of the noncompensatory family: you need enough of *both*. If they ever fit a probabilistic model over their dimensions, the noncompensatory/conjunctive family is the one that matches their stated semantics — and the empirical literature above warns that it may not be the family that fits their data.

---

## 3. Does the order actually propagate mastery? What is known and what is not

Three distinct claims are often conflated. Separating them matters.

1. **Structural claim**: harder-item states are downward-closed. This is the Birkhoff/quasi-ordinal assumption. It is *assumed*, not discovered, in almost every deployed system; it is what makes the state space tractable.
2. **Inferential claim**: observing success at (x,y) licenses inferring mastery at all (a,b) ≤ (x,y). This is what AHM's expected-response matrix does [17], and what HLAM's zero-proportion constraint does [16]. It is exactly as strong as the hierarchy is true, and the identifiability results say you *cannot* check it for attributes that never vary independently [25].
3. **Pedagogical claim**: therefore you need not re-practise the lower cells. This does **not** follow from 1 and 2, and is the weakest link. KST's [L2] says only that "knowing more does not prevent learning something new" [1] — a possibility claim, not a claim about optimal difficulty. Nothing in the formal theory says that going straight from (10,1) to (10,2) is as *efficient* as a graded route; the theory is silent on within-state difficulty.

Two further empirical facts complicate the propagation story:

- **Forgetting.** The ALEKS paper devotes a section to retention and forgetting of learned material and to the "layers" of a knowledge state [2]. In a system with forgetting, downward closure is not stable over time: a state that was a downset stops being one. Any implementation of mastery propagation needs a decay story or it will assert mastery it no longer has.
- **Guessing and slips.** All the probabilistic KST/CDM machinery exists because observed responses are noisy [1][2][8]. Deterministic propagation from a single observation is not defensible; propagation should be over a posterior, not over a certainty.

---

## 4. Prerequisite structures: authored, learned, and the case for scepticism

### 4.1 Inferring structure from data

There is an active literature on inducing prerequisite graphs from data rather than authoring them: data-driven induction of Prerequisite Structure Graphs from heterogeneous educational material and activity data (EDM 2016) [27]; **COMMAND**, which jointly infers a prerequisite graph and a student model as a Bayesian network in a two-stage process (EDM 2016) [28]; unsupervised multi-criteria approaches combining document, Wikipedia-hyperlink, graph and text features by voting [29]; and a 2025 ACM Computing Surveys review, "Prerequisite Relation Learning: A Survey and Outlook" [30][title/venue only]. Reported validation figures against expert-labelled ground truth in one such study were precision ≈ 0.83/0.74 and recall ≈ 0.81/0.76 across classifiers [29][secondary] — respectable, but note that the ground truth is *expert opinion*, not learning outcomes.

An asymmetry worth carrying into design, stated in this literature: **misleading a learner with an incorrect prerequisite is more harmful than omitting some prerequisites** [29][secondary]. A false edge blocks content forever; a missing edge merely costs one hard attempt.

### 4.2 The negative evidence — and it is substantial

The maintainer asked for scepticism. Here it is, and it is sharper than expected.

**Doroudi, Aleven and Brunskill (2019)** reviewed *all* empirical studies comparing RL-induced instructional policies to baselines [31]. Headline: of 36 studies, 21 found at least one RL-induced policy significantly better than all baselines, 4 found no overall difference but an aptitude–treatment interaction favouring low performers, 4 were mixed, 10 found no significant difference, and 1 found a baseline beating RL [31]. So "over half" is the optimistic reading. But three qualifications gut it:

1. **The cluster that matches the maintainer's problem is the one that fails.** Doroudi et al. classify studies into five clusters; the cluster called *sequencing interdependent content* — precisely the case where "a network specifying the relationship between different content areas or KCs (such as a prerequisite graph) must either be prespecified or automatically inferred from data" — is described as having "been the least successful, with **all of them resulting in either a mixed result or no significant difference** between policies" [31].
2. **Classrooms are much worse than labs.** "Only three out of 15 studies that were run in classroom settings found an RL-induced policy was significantly better than baselines" (four more found ATIs) [31].
3. **The baselines were often weak.** Among the 24 studies with a significant effect or ATI, 17 (71%) compared against a random policy or another RL policy not known to work; among the null studies, only 6 (35%) did [31]. Doroudi et al.'s own conclusion: this "does not give us insight into whether RL-based policies lead to substantially better instructional sequences than relying on learning theories and experts for sequencing" [31].

Their positive finding is worth as much as the negative one: RL "has been most successful in cases where it has been constrained with ideas and theories from cognitive psychology and the learning sciences" [31]. Structure helps; *learned* structure applied to *interdependent content* has not yet been shown to help.

**Rollinson and Brunskill (2015)** make the complementary methodological point: a model that predicts next-response well is not thereby a model that yields a good instructional policy, because policies require different properties from the student model than prediction does [32]. Do not read AUC improvements as pedagogical improvements.

**Koedinger et al. (2023, PNAS)** fit an individualised Additive Factors Model to 27 datasets — 1.3 million practice interactions, ~7,000 learners, across mathematics, language, science and computer science, elementary through college — and found an "astonishing regularity": students differ substantially in *initial* knowledge (roughly 55% vs 75% correct for lower and upper halves) but are remarkably similar in *learning rate*, typically about 0.1 log-odds or ~2.5% accuracy gain per opportunity [33]. This has a direct design consequence: **most of the personalisation value is in estimating where a learner starts, not in personalising how fast they climb.** (Note: this result is under active re-examination — at least two follow-ups probe the sensitivity of learning-rate estimates to practice-sequence length and to which observations are included [34][title/abstract only]. Treat it as strong but not closed.)

**Learning Factors Analysis / AFM** (Cen, Koedinger and Junker, 2006) is the standard tool for *evaluating and improving* a KC model against data by combining a statistical model, human expertise and combinatorial search [35]. Its follow-up (Cen et al., 2007) showed that better-calibrated KC-level mastery decisions reduced over-practice without hurting outcomes [35][secondary]. If the maintainer wants to know whether their dimensions are the right dimensions, AFM-style model comparison is the established method.

**Mastery learning**, the pedagogy that mastery propagation implies, has a contested evidence base. Kulik, Kulik and Bangert-Drowns (1990) meta-analysed 108 controlled evaluations and found positive effects, stronger for weaker students, varying by mastery procedure, design and content [36]. Slavin (1987) reached a much more negative conclusion, and the two camps disputed each other's inclusion criteria; on the ~11 studies both sides accept, effect sizes were around 0.36–0.45 on experimenter-made tests but about **0.09 on standardised tests** [36][secondary]. That gap — large on the aligned measure, near-zero on the transfer measure — is the honest summary of mastery learning and should temper any claim that mastery gating is self-evidently good.

---

## 5. Point 5: temporarily simplifying the other dimensions

This is the most substantive part of the maintainer's model and it deserves the most careful treatment.

### 5.1 There is no single name. There are four partial ones.

**(a) Simplifying Conditions Method (SCM)** — Reigeluth's revision of Elaboration Theory [19]. Two principles: *epitomising* (find the simplest version of the whole task that is still representative) and *elaborating* (teach increasingly complex versions by relaxing the simplifying conditions) [19][secondary]. The "simplifying conditions" *are* the other dimensions held at low values. This is the closest conceptual match to point 5 at the curriculum level. **Its evidence base is thin**: the standard citation is English and Reigeluth (1996), "Formative research on sequencing instruction with the elaboration theory", *ETR&D* 44(1):23–42 — formative research, i.e. design-improvement case study, not a controlled trial [19][secondary]. One secondary source reports a "30% performance improvement" [19][secondary]; I could not trace that to a primary study and would not rely on it.

**(b) The isolated-elements effect** — Pollock, Chandler and Sweller (2002), "Assimilating complex information", *Learning and Instruction* 12:61–86 [20]. A two-phase design: phase 1 **artificially reduces element interactivity** by presenting complex material as isolated elements processed serially; phase 2 presents everything integrated. Four experiments with Australian vocational students and apprentices found the isolated-then-interacting sequence superior for certain learner groups [20]. Crucially, a later study in an accountancy class found the effect **interacts with expertise**: lower-expertise students benefited from the isolated format, higher-expertise students learned more from the interacting format [37]. This is the cleanest cognitive-load-theoretic statement of point 5 — *temporarily suppress interaction between dimensions so working memory can process them serially* — and it comes with its own reversal condition.

**(c) "Simplification" in the part-task-training taxonomy** — Wightman and Lintern (1985), *Human Factors* 27:267–283, partition part-task methods into **segmentation** (split along spatial/temporal dimensions), **fractionation** (practise concurrent components separately) and **simplification** (reduce the difficulty of the whole task on some dimension) [21]. Note that *simplification* is explicitly the non-decomposing option: the task stays whole, one dimension is turned down. Their review, and reviews since, report that in the majority of cases part-training is **less efficient than whole-task training** [21][secondary].

**(d) "Separation" in Variation Theory** — Marton and colleagues [22]. To discern a critical aspect of a phenomenon, that aspect must **vary while other aspects remain invariant**; the four patterns are contrast, generalisation, separation and **fusion**, where fusion is the final stage in which all critical aspects vary simultaneously [22]. Explicitly: "to discern a dimension of variation that can take on different values, the other dimensions of variation need to be kept invariant or varying at a different rate" [22][secondary]. Variation theory therefore says *hold the other dimensions constant while varying the target one* — which is point 5's mechanism stated as a discernment principle rather than a load principle — and it also says you must eventually **fuse**, i.e. return to simultaneous variation. That "you must eventually fuse" clause is important and is missing from the maintainer's formulation.

A fifth, adjacent tradition: **Engelmann and Carnine's Theory of Instruction** (1982/1991) states the **difference principle** — "To show difference, juxtapose examples that are only minimally different and treat them differently" — alongside a set-up principle (juxtapose examples sharing the greatest possible number of features) [38][secondary]. Direct Instruction's "one difference at a time" is the same geometry at the level of individual example pairs.

And in motor learning, Newell's distinction between **task decomposition** (break into parts, decoupling perception from action) and **task simplification** (keep the task whole, manipulate constraints — equipment size, playing area — to reduce difficulty and degrees of freedom, then progressively restore them) [39][secondary]. Task simplification is point 5 for movement skills, and the ecological-dynamics camp argues it is preferable to decomposition precisely because it preserves the coupling between dimensions.

### 5.2 The best single piece of evidence, and its conditions

**Wickens, Hutchins, Carolan and Cumming (2013)**, "Effectiveness of part-task training and increasing-difficulty training strategies: a meta-analysis approach", *Human Factors* 55(2):461–470 — 37 transfer studies, two effect-size treatments (transfer ratios and Hedges' g) [23]. Findings:

- **Increasing-difficulty (ID) training succeeded when difficulty increases were implemented adaptively, and not when increased in fixed steps** [23]. Predetermined progression schedules failed.
- **Part-task training produced negative transfer when the parts had to be performed concurrently in the whole task**, and showed no negative effects when parts were sequential; variable-priority training of the whole task was the successful variant [23].
- **Both strategies showed that experienced learners benefited less, or suffered more** — an expertise reversal, which the authors read as confirming cognitive load theory [23].

This is as close to a direct test of point 5 as the literature offers, and its verdict is: **the intuition is right, but only in adaptive form, only for less experienced learners, and only when the dimensions are not so tightly coupled that suppressing one destroys the task.**

A recent supporting study: Marraffino et al. (2021) tested *within*-scenario adaptive difficulty against *between*-scenario adaptive difficulty and a fixed-difficulty control (N = 95). Within-adaptive beat control; **between-adaptive was worse than control**, apparently because it delivered lower average difficulty; higher average difficulty during training predicted better accuracy and faster responses [40]. Granularity of adaptation matters, and an adaptive scheme that accidentally makes practice easier can be worse than no adaptation.

The 85% rule is the other side of this. Wilson, Shenhav, Straccia and Cohen (2019), *Nature Communications* 10:4646, derive for a class of gradient-descent learners that the **optimal training error rate is ≈15.87%**, i.e. ≈85% accuracy, and demonstrate it for artificial and biologically plausible networks [41]. Read the scope honestly: this is a result about a class of learning algorithms and simple perceptual decision tasks, **not** a demonstrated result for complex human skill acquisition. It is nonetheless the most defensible available anchor for a difficulty-targeting controller.

### 5.3 The evidence that cuts the other way

Point 5, stated baldly, says: reduce difficulty on other dimensions, i.e. make practice more blocked, more constant, less variable. Four literatures say that hurts.

- **Contextual interference.** The hypothesis is that high CI (random practice) depresses acquisition but improves retention and transfer. Brady's (2004) meta-analysis found 139 effect sizes from 61 studies, overall d ≈ .38, but with **basic/laboratory research at .57 versus applied research at .19** [42]. The picture has since become worse for the effect: a 2023 systematic review and meta-analysis in sports practice is titled "The myth of contextual interference learning benefit in sports practice" [43][title/abstract], and a 2024 multilevel meta-analysis in *Educational Psychology Review* reported **no statistically significant difference in relatively permanent performance gains between high and low CI practice**, concluding that the recommendation to use high CI cannot be derived from present evidence [44][abstract]. Simultaneously, another 2024 meta-analysis in *Scientific Reports* concluded that high CI *does* improve retention [45][title], and a transfer-focused meta-analysis reported an overall SMD = 0.55 favouring random practice, split as 0.75 in laboratory and a non-significant 0.34 in applied settings [46][secondary]. **This literature is in open disagreement, and the disagreement tracks the lab/applied divide.** Do not treat "interleave everything" as established for real skills.
- **Interleaved practice in mathematics.** Rohrer, Dedrick, Hartwig and Cheung (2020), *J. Educational Psychology* 112(1):40–52, randomised 787 students in 54 classes across 5 schools; interleaved practice beat blocked on an unannounced delayed test, 61% vs 38%, **d = 0.83, 95% CI [0.68, 0.97]** [47]. This is a large, well-designed classroom trial and it is direct evidence *against* keeping a dimension constant across a practice block.
- **Desirable difficulties** (Bjork). The general claim — conditions that feel easiest produce the weakest long-term retention — is well established, but its own literature is explicit about boundaries: difficulty is desirable only when the learner has the foundational knowledge to eventually succeed, and "many failures to obtain desirable difficulty effects may occur under conditions where working memory is already stressed due to the use of high element interactivity information" [48][secondary]. That last sentence is the reconciliation clause: **element interactivity is the variable that decides whether adding difficulty helps or hurts.**
- **Productive failure.** Sinha and Kapur's (2021) meta-analysis of 53 studies and 166 comparisons found problem-solving-before-instruction beat instruction-first with **Hedges' g = 0.36 [0.20, 0.51]**, rising to 0.37–0.58 with high fidelity to Productive Failure principles [49]. Boundary conditions include learner characteristics, task domain, scaffolding of the exploration phase, and **age — effects were better for secondary school onwards** [49][secondary]. Deliberately letting learners fail at a hard combination is, sometimes, better than smoothing the path to it.

### 5.4 The reconciliation, insofar as one exists

The literatures are not as contradictory as they look, if you separate three variables:

1. **Acquisition vs retention/transfer.** Simplification reliably speeds *acquisition*. The interleaving/CI/desirable-difficulties camp is measuring *delayed retention and transfer*, where it reliably costs. Both can be true. Design systems that measure the delayed outcome, not the practice-session outcome — this is the single most transferable methodological point in the whole area.
2. **Expertise.** Every strand agrees on the direction: simplification, isolation, worked examples and scaffolding help novices and progressively hurt experts [20][23][37][50]. This is the **expertise reversal effect**, which Sweller and colleagues have argued is a special case of the **element interactivity effect** — both effects turn on relative levels of element interactivity, one because the material changes and the other because the learner does [50].
3. **Coupling between dimensions.** Naylor and Briggs' (1963) hypothesis — whole practice for tasks *high in organisation* (tightly interdependent components) and low in complexity, part practice otherwise — is the oldest statement of this and is still the textbook rule [51][secondary]. Wickens et al.'s finding that part-task training produces negative transfer specifically when the parts must be performed *concurrently* is the same thing measured [23]. **If dimension A and dimension B interact in the real task, suppressing A while training B trains a different skill.**

**The practical synthesis, which I state as a synthesis and not as a finding**: point 5 is best implemented as *adaptive*, *transient*, *novice-weighted* simplification, followed by an explicit **fusion** phase in Marton's sense — reintroduce simultaneous variation and verify at the target cell. The literature supports the "simplify" half and the "fuse" half separately; I found no study that tests the exact schedule the maintainer describes ((10,1) → (4,2) → (6,2) → (10,2)) against the direct route ((10,1) → (10,2)) with equated practice time. **That specific comparison appears to be unrun.** It is a cheap experiment for an adaptive system to run on itself.

### 5.5 The related scaffolding literature

Adjacent and better-evidenced: **worked-example fading**. Renkl, Atkinson and Maier's **backward fading** — first task fully worked, second omits the last step, third the last two, and so on — reliably improves near transfer relative to example–problem pairs, but the effect is **not reliable for far transfer** unless combined with self-explanation prompts [52]. The mechanism given is guidance fading avoiding redundancy for more experienced learners [52][secondary] — i.e. a scheduled expertise reversal.

This is worth noting because fading is *the same shape as point 5 on a different axis*: reduce support, not content difficulty. If the maintainer's system has both a difficulty-axis and a support-axis, the fading literature is more mature than the simplification literature and should be raided first.

Finally, the **assistance dilemma** (Koedinger and Aleven, 2007, *Educational Psychology Review*) names the general trade-off: withholding more information than needed causes frustration and wasted time; giving more than needed causes shallow learning [53]. Their honest conclusion is that "the optimal amount of assistance depends on learner characteristics" and that predicting it a priori remains open research [53][secondary]. Nineteen years later that is still the state of the art, which should calibrate expectations for any parameter the maintainer is tempted to hard-code.

---

## 6. Curriculum learning: the computational cousin, and its own negative results

Bengio, Louradour, Collobert and Weston (ICML 2009) formalised **curriculum learning** — order training examples easy-to-hard — hypothesising that it guides optimisation toward better local minima, and reported improved generalisation and faster convergence [54].

The result has not held up well at scale. Wu, Dyer and Neyshabur (ICLR 2021), "When do curricula work?", ran thousands of orderings across curriculum, anti-curriculum and random-curriculum conditions and found that **on standard benchmarks curricula have only marginal benefits, and randomly ordered samples perform as well or better**, with any apparent benefit attributable to the dynamic training-set size rather than the ordering [55]. Curricula *did* help under two specific conditions: a **limited training-time budget**, and **noisy data** — and anti-curricula did not [55]. Related theoretical work finds settings where curriculum is not optimal and anti-curriculum is not worst, which the authors offer as an explanation for the null empirical results [56][secondary].

Two branches remain live and are more relevant to the maintainer than vanilla curriculum learning:

- **Self-paced learning** and the difficulty-pacing problem: "two key challenges are arranging the training instances by a sensible measure of difficulty, and determining the pace" — too fast or too slow both fail [55][secondary]. Note the structural similarity to Wickens et al.'s adaptive-vs-fixed-step finding [23].
- **Automatic Curriculum Learning (ACL)** in RL: teacher algorithms that adapt the task-sampling distribution to the evolving student, typically by maximising **absolute learning progress**, e.g. ALP-GMM which clusters a *continuously parameterised* environment space and allocates training where competence changes fastest [57]. This is the closest computational analogue to point 5: the environment parameter space is a multi-dimensional difficulty space, and a learning-progress-maximising teacher will naturally *lower* one axis while *raising* another when that is where progress is fastest. It is not derived from education research and its transfer to human learners is unestablished — but the algorithmic template (sample where measured learning progress is highest, over a product-structured task space) is directly implementable and does not require the designer to hand-specify the simplification schedule.

The honest summary: **the ML literature is not evidence for human curriculum design.** Its value here is (a) as a cautionary tale — the intuitive "easy first" ordering repeatedly fails to reproduce, and (b) as a source of mechanisms — learning-progress-driven sampling over a parameterised task space.

---

## 7. Mitigating the combinatorial explosion

### 7.1 The mathematics is unusually favourable

If states are required to be **downsets** of the product order (the maintainer's point 3), the state space is not 2^(number of cells). By Birkhoff [3][1], the states are exactly the order ideals of the poset. For a poset that is a product of two chains of lengths m and n, **the order ideals are in bijection with monotone lattice paths, and there are exactly C(m+n, m) of them** — a standard enumerative-combinatorics result [58]. I verified this by brute-force enumeration for all m ≤ 3, n ≤ 4; the counts match C(m+n, m) exactly (e.g. 3×4 grid: 35 ideals, versus 2¹² = 4096 subsets).

Concretely:

| dimensions | cells | unconstrained 2^cells | downsets of the product order |
|---|---|---|---|
| 5 × 10 | 50 | 1.1 × 10¹⁵ | **3,003** |
| 10 × 10 | 100 | 1.3 × 10³⁰ | **184,756** |
| 5 × 5 × 5 | 125 | 4.3 × 10³⁷ | **267,227,532** |
| 10 × 10 × 10 | 1000 | ~10³⁰¹ | **≈ 9.3 × 10³³** |

For three chains the count is the number of plane partitions in a box, given by MacMahon's box formula ∏∏∏ (i+j+k−1)/(i+j+k−2); I verified this against brute force for several small boxes. For **four or more** dimensions no product formula is known — MacMahon's conjectured generalisation to solid partitions is known to be false — so beyond three dimensions you lose the closed form as well as the tractability.

**Three design consequences follow directly.**

1. **Two dimensions is nearly free; three is enumerable-ish; four is not.** This matches, independently, the CDM community's empirical convergence on 4–6 attributes [9]. Two disciplines, two arguments, same answer.
2. **Do not represent a state as a point.** There is a tempting simplification: represent the learner's state as a single cell (x,y) meaning "everything at or below". That collapses the space to m·n — very cheap — but it **cannot express the staircase states that point 5 requires**. After mastering (10,1) and then practising (4,2) and (6,2), the learner's state is exactly a staircase: mastered up to level 10 at B=1 and up to level 6 at B=2. The box representation cannot hold that. **The downset (staircase) representation is the minimum expressive power point 5 needs, and C(m+n,m) is its price.** This is the single most concrete structural recommendation in this report.
3. **The frontier is small.** The outer fringe of a downset in a two-dimensional grid is the set of minimal cells not yet mastered — at most min(m,n)+1 cells, and typically far fewer. Consistent with this, ALEKS reports that in real (much less structured) domains, a state with ~80 items typically has only ~9 fringe items [59][secondary], and adaptive assessment can locate a state in a 200–300 item domain in about 25–30 questions [59][secondary]. **You never need to enumerate the state space; you only need to enumerate the fringe.**

### 7.2 The other mitigations the literature offers

- **Hierarchies as constraints** (AHM's reduced Q-matrix [17]; HLAM's A(E) [16]) — the same trick as above, applied to unordered attribute DAGs rather than chains.
- **Factored response models.** G-DINA decomposes the item response function into main effects plus interactions [8]; dropping high-order interactions (ACDM, additive CDM) reduces parameters per item from 2^(Kj) to Kj+1, at the cost of assuming compensation. The empirical model-comparison result of §2.1 says this is often an acceptable trade [24].
- **Additive Factors Model.** AFM models the log-odds of success as a sum of student ability, KC difficulty and KC-specific learning-rate × opportunity count [35] — linear in the number of KCs regardless of how they combine. This is the standard scalable learner model and it is *deliberately* compensatory/additive. Its use as a model-*improvement* engine (LFA) is what lets you discover that two of your dimensions are really one [35].
- **Determining K empirically.** Nájera, Abad and Sorrel's triangulated procedure (parallel analysis + Factor Forest + AIC model comparison, 97.6% accurate when all three agree) is the established method for asking "how many dimensions does my data actually support?" [9].
- **Item templates instead of items.** Automatic item generation distinguishes **radicals** — structural features that drive item parameters, which define the item model / parent — from **incidentals**, surface features varied randomly within a family, producing **isomorphs** or clones [60]. This is exactly the ALEKS item/instance distinction [2]. The combinatorial object you schedule is the *template*; the thing you present is a freshly sampled sibling. This cuts the modelled object count by the sibling multiplicity for free, and it also solves the cold-start problem for new items, since a new sibling inherits its parent's parameters.
- **Granularity as a modelling choice.** The KLI framework treats knowledge components as existing at multiple granularities, and recommends focusing "on the component level at which the novice student makes errors" [61][secondary]. There is no principled granularity — it is chosen for the population, and it is legitimate to model coarsely and refine only where the data demand it (which is what LFA operationalises).

---

## 8. Terminology map: the maintainer's model → the field's

| Their term / idea | Established term(s) | Field | Key reference |
|---|---|---|---|
| Dimension with a difficulty ladder | **Component** / **attribute**; polytomous **item** with ordered response levels; **radical** in item design | KST; CDM; AIG | [11][12], [15], [60] |
| Level within a dimension | **Response level** in polytomous KST; **attribute level** in polytomous CDM | KST/CDM | [13][14][15] |
| The product order on A×B | **Surmise relation** derived by **component-based construction**; pointwise order on polytomous states; **attribute hierarchy** E (as DAG) | KST; CDM | [11][12], [15], [16][17] |
| A learner's mastery set | **Knowledge state** (KST); **attribute profile** α (CDM) | both | [1], [16] |
| Mastery propagates down the order | **Downward closure** ⇒ **quasi-ordinal knowledge space**; equivalently the permissible set **A(E)** of an HLAM; **Birkhoff correspondence** | KST; CDM | [1, Thm 10], [3], [16] |
| Set of all legal mastery sets | **Knowledge structure / knowledge space / learning space**; for the maintainer's model specifically, the **lattice of order ideals** | KST | [1] |
| "Knowing more doesn't block new learning" | **[L2] Learning consistency** | KST | [1, Def. 3] |
| "You can get anywhere one step at a time" | **[L1] Learning smoothness** / **well-gradedness** / antimatroid | KST | [1, Def. 3, Thm 7] |
| What to practise next | **Outer fringe** (formalised ZPD) | KST | [1, Def. 20] |
| A route through the space | **Learning path**; single-item-step path = **gradation** | KST | [4] |
| "You need both dimensions" | **Conjunctive** model (DINA); **noncompensatory / partially compensatory** MIRT | CDM; IRT | [8], [10] |
| "Dimensions can trade off" | **Compensatory / disjunctive** model (DINO, ACDM); compensatory MIRT | CDM; IRT | [8], [10] |
| Temporarily simplify other dimensions | **Simplifying conditions method**; **isolated-elements effect**; **simplification** (part-task taxonomy); **separation** (variation theory); **task simplification** (motor learning) | ID; CLT; HF; phenomenography; motor learning | [19], [20], [21], [22], [39] |
| ...and then restore them | **Fusion** (variation theory); the "interacting elements" phase | phenomenography; CLT | [22], [20] |
| Combinatorial explosion | **Latent class space 2^K**; **identifiability degeneracy**; **Q-matrix specification burden** | CDM | [9], [16], [25] |
| Reusable item with varied surface | **Item model / parent** + **incidentals** → **isomorphs**; ALEKS **item** vs **instance** | AIG; KST | [60], [2] |
| Adaptive difficulty targeting | **Increasing-difficulty (ID) training**; the **85% rule**; **assistance dilemma** | HF; comp. neuro; ITS | [23], [41], [53] |

**Where their model has no established equivalent.** (i) The specific *schedule* of point 5 — advance one dimension by first retreating on others and then re-climbing — has no name and, as far as I can find, no controlled test. (ii) "Mastery propagation across a *product* of ordered dimensions" as a design principle is not, to my knowledge, stated as such anywhere; the components exist (component-based construction, polytomous KST, HLAM) but the assembly is theirs. (iii) There is no established theory of *when a dimension should be introduced at all* — CbKST tells you how to structure competencies once chosen, not when to add one.

**Where their model differs subtly from a superficially similar concept.**
- Their point 3 is the **quasi-ordinal** (intersection-closed) case, which KST regards as a *simplification that is pedagogically suspect* [1, p.10], not as the general case. General knowledge spaces are union-closed only, and represent alternative prerequisite routes via surmise *functions* [1, Thm 18].
- **[L2] is not point 3.** [L2] says knowing more never *prevents* learning; point 3 says knowing a harder thing *implies* knowing easier things. These are different claims and [L2] is much weaker.
- Their product order is **conjunctive**; the field's default scalable learner model (AFM) is **additive/compensatory** [35]. Empirically, real tests contain both kinds of items [24].
- The "dimensions" of variation theory are dimensions of *discernment*, not of difficulty [22]. Superficially the same word; not the same object.

---

## 9. What this implies for a practical adaptive-practice system

**Design guidance that the research does support.**

1. **Represent state as a downset (staircase), not a point.** Required for point 5; costs C(m+n,m) instead of m·n; still trivially small for two dimensions. §7.1.
2. **Select next items from the outer fringe.** It is the formalised ZPD, it is what the deployed system does, and its readiness prediction is ~.93 accurate at scale [1][2]. Computing it for a product order is O(dimensions), not O(states).
3. **Cap the number of dimensions at about three or four, and justify each one.** The combinatorics degrades sharply past three [§7.1]; applied CDM has converged on 4–6 attributes [9]; unmeasured-in-isolation dimensions are formally non-identifiable [25]. Ensure every dimension varies independently in at least some items, or you will never be able to tell it apart from its neighbours.
4. **Schedule templates, sample siblings.** Radicals define the cell in the product order; incidentals are re-rolled per presentation [60][2]. This is standard practice and it makes cold-start tractable.
5. **Implement point 5 as an adaptive controller, not a fixed schedule.** Wickens et al. is unambiguous: increasing difficulty worked adaptively and failed in fixed steps [23]. Do not hard-code "(4,2) then (6,2) then (10,2)". Target a success-rate band — ~85% is the best-supported anchor available [41], with the caveat that it is derived for gradient-descent learners and simple decisions, not human skill acquisition — and let the retreat depth fall out.
6. **Weight simplification toward novices and withdraw it as competence grows.** Expertise reversal is the most reliably replicated moderator across all the strands here [20][23][37][50]. A simplification policy with no expertise term will actively harm your better learners.
7. **Always fuse.** Variation theory's fusion stage [22] and cognitive load theory's phase-2 "interacting elements" [20] agree: simplification must terminate in a verified performance at the *target* cell under simultaneous variation. Mastery of (10,2) is not established by success at (6,2).
8. **Measure delayed retention, not session accuracy.** Simplification helps acquisition and can hurt retention; the contextual-interference and interleaving literatures exist entirely because these dissociate [42][44][47]. If your only metric is within-session, you will systematically over-select simplification.
9. **Interleave across cells even while blocking within a cell.** Rohrer et al.'s d = 0.83 is a large, well-designed classroom effect [47], and ALEKS's designers explicitly cite the progress assessment's enforced interleaving as a benefit [2]. Point 5's "hold other dimensions constant" applies *within* an item's parameters, not to the session's item order. These are compatible; keep them distinct in the design.
10. **Treat your prerequisite structure as a hypothesis and refit it.** Use AFM/LFA-style model comparison to check whether your dimensions predict as separate dimensions [35], and re-derive whether the product order is over-constraining. Expect false states from intersection closure [1].
11. **Prefer omitting an edge to inventing one.** A wrong prerequisite blocks a learner indefinitely; a missing one costs one failed attempt [29][secondary].
12. **Model decay.** Downward closure is not stable under forgetting; ALEKS devotes a whole analysis to retention and forgetting within the state [2]. Propagate a posterior, not a certainty.

**Design decisions the research does not justify.**

- **The exact retreat schedule.** No study I found compares the graded route to the direct route with time equated. Instrument it and A/B it in-system; it is a cheap experiment and it would be a genuine contribution.
- **How far to retreat.** Nothing quantifies "drop dimension A from 10 to 4 versus to 6". Derive it from a success-rate target rather than from theory.
- **When to introduce a new dimension at all.** Not addressed by any literature I found.
- **Whether an authored product order beats a data-driven one for sequencing.** Doroudi et al.'s cluster analysis says the entire class of *sequencing interdependent content* studies produced only mixed or null results, and that only 3 of 15 classroom studies of RL sequencing beat their baselines [31]. This is the single strongest reason for humility: **the specific thing the maintainer wants to do is the thing the field has most consistently failed to demonstrate a benefit for.** That is not a reason not to build it — a well-structured system may still be better than no structure, and Doroudi et al. found that theory-constrained approaches did best [31] — but it is a reason not to promise gains and to compare against a strong, boring baseline (e.g. fringe-based selection with random tie-breaking) rather than a random one.
- **Whether mastery gating helps.** Mastery learning's effect drops from ~0.4 on aligned tests to ~0.09 on standardised tests even in the studies both sides of the Kulik/Slavin dispute accept [36][secondary].
- **The 85% target for skill practice.** Derived for a class of algorithms, not demonstrated for human complex-skill acquisition [41]. Use it as a starting parameter, not a finding.
- **Anything transferred from ML curriculum learning.** The flagship easy-to-hard result largely fails to replicate on standard benchmarks [55]; treat the ML literature as a source of mechanisms (learning-progress-driven sampling [57]), not of evidence about people.

---

## REFERENCES

1. Doignon J-P, Falmagne J-C. *Knowledge Spaces and Learning Spaces*. arXiv:1511.06757, 2015. [arxiv.org/abs/1511.06757](https://arxiv.org/abs/1511.06757) — full text obtained and quoted directly (Definitions 3, 5, 9, 20; Theorems 7, 10, 18, 21).
2. Cosyn E, Uzun H, Doble C, Matayoshi J. A practical perspective on knowledge space theory: ALEKS and its data. *Journal of Mathematical Psychology*; preprint dated October 2020. [jmatayoshi.github.io/publications/JMP2021_KST_ALEKS_preprint.pdf](https://jmatayoshi.github.io/publications/JMP2021_KST_ALEKS_preprint.pdf) — full text obtained.
3. Birkhoff G. Rings of sets. *Duke Mathematical Journal* 1937;3:443–454. (Cited from the bibliography of [1].)
4. Stahl C, Hockemeyer C. *Knowledge Space Theory* (R package `kst` vignette). CRAN. [cran.r-project.org/web/packages/kst/vignettes/kst.pdf](https://cran.r-project.org/web/packages/kst/vignettes/kst.pdf) — full text obtained.
5. Characterizing master fringes in competence-based knowledge space theory for personalized learning applications. *Journal of Mathematical Psychology*. [sciencedirect.com/science/article/abs/pii/S002224962400066X](https://www.sciencedirect.com/science/article/abs/pii/S002224962400066X) — **abstract only**.
6. On the assessment of learning in competence based knowledge space theory. *Journal of Mathematical Psychology*. [sciencedirect.com/science/article/abs/pii/S0022249617301694](https://www.sciencedirect.com/science/article/abs/pii/S0022249617301694) — **abstract only**.
7. Knowledge structures delineated by fuzzy skill maps. [sciencedirect.com/science/article/abs/pii/S016501142030381X](https://www.sciencedirect.com/science/article/abs/pii/S016501142030381X) — **abstract only**. See also `CbKST` R package: [cran.r-project.org/web/packages/CbKST/](https://cran.r-project.org/web/packages/CbKST/index.html).
8. Rajeb M (ed.). *Handout for Cognitive Diagnosis Modeling* — §3.5 The DINA model. [bookdown.org/mehdirajeb/CDM/the-dina-model.html](https://bookdown.org/mehdirajeb/CDM/the-dina-model.html). Primary source for G-DINA: de la Torre J. The generalized DINA model framework. *Psychometrika* 2011 — **not directly verified**.
9. Nájera P, Abad FJ, Sorrel MA. Determining the number of attributes in cognitive diagnosis modeling. *Frontiers in Psychology* 2021;12:614470. [frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.614470/full](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.614470/full)
10. Bolt DM, Lall VF. Estimation of compensatory and noncompensatory multidimensional item response models using Markov chain Monte Carlo. *Applied Psychological Measurement* 2003. [journals.sagepub.com/doi/10.1177/0146621603258350](https://journals.sagepub.com/doi/10.1177/0146621603258350). See also: Partially compensatory MIRT models: two alternate model forms. [ncbi.nlm.nih.gov/pmc/articles/PMC5965584](https://ncbi.nlm.nih.gov/pmc/articles/PMC5965584)
11. Albert D, Held T. Establishing knowledge spaces by systematical problem construction. In: Albert D (ed.), *Knowledge Structures*. Springer, 1994. Also Albert D, Held T. Component based knowledge spaces in problem solving and inductive reasoning. In: Albert D, Lukas J (eds.), *Knowledge Spaces: Theories, Empirical Research, Applications*. Erlbaum, 1999. — **secondary**, located via [kst.hockemeyer.at/kst-bib.html](https://kst.hockemeyer.at/kst-bib.html).
12. Schrepp M, Held T, Albert D. Component-based construction of surmise relations for chess problems. In: Albert D, Lukas J (eds.), *Knowledge Spaces: Theories, Empirical Research, Applications*. Erlbaum, 1999. — **secondary**; primary PDF returned 403. Data available in the R package `pks`: [search.r-project.org/CRAN/refmans/pks/html/chess.html](https://search.r-project.org/CRAN/refmans/pks/html/chess.html)
13. Schrepp M. A generalization of knowledge space theory to problems with more than two answer alternatives. *Journal of Mathematical Psychology* 1997. [pubmed.ncbi.nlm.nih.gov/9325119/](https://pubmed.ncbi.nlm.nih.gov/9325119/) — **title/venue only**.
14. Stefanutti L, Anselmi P, de Chiusole D, Spoto A. On the polytomous generalization of knowledge space theory. *Journal of Mathematical Psychology* 2020;94:102306. [sciencedirect.com/science/article/abs/pii/S0022249619301646](https://www.sciencedirect.com/science/article/abs/pii/S0022249619301646) — **abstract only**.
15. Heller J. Generalizing quasi-ordinal knowledge spaces to polytomous items. *Journal of Mathematical Psychology* 2021;101:102515. [sciencedirect.com/science/article/abs/pii/S0022249621000158](https://www.sciencedirect.com/science/article/abs/pii/S0022249621000158) — **abstract only**.
16. Gu Y, Xu G. *Identifiability of Hierarchical Latent Attribute Models*. arXiv:1906.07869v4, 2021. [arxiv.org/abs/1906.07869](https://arxiv.org/abs/1906.07869) — full text obtained.
17. Attribute hierarchy method. Wikipedia. [en.wikipedia.org/wiki/Attribute_hierarchy_method](https://en.wikipedia.org/wiki/Attribute_hierarchy_method) — tertiary source; primary is Leighton JP, Gierl MJ, Hunka SM, *Journal of Educational Measurement* 2004.
18. Gierl MJ. Using the attribute hierarchy method to identify and interpret cognitive skills that produce group differences. *Journal of Educational Measurement* 2008. [onlinelibrary.wiley.com/doi/10.1111/j.1745-3984.2007.00052.x](https://onlinelibrary.wiley.com/doi/10.1111/j.1745-3984.2007.00052.x); see also [files.eric.ed.gov/fulltext/EJ838616.pdf](https://files.eric.ed.gov/fulltext/EJ838616.pdf)
19. Reigeluth CM. Elaboration theory and the Simplifying Conditions Method. Overviews: [instructionaldesign.org/theories/elaboration-theory/](https://www.instructionaldesign.org/theories/elaboration-theory/), [edutechwiki.unige.ch/en/Elaboration_theory](https://edutechwiki.unige.ch/en/Elaboration_theory). Primary empirical citation: English RE, Reigeluth CM. Formative research on sequencing instruction with the elaboration theory. *ETR&D* 1996;44(1):23–42 — **not directly verified**. Formative research report: [files.eric.ed.gov/fulltext/ED397804.pdf](https://files.eric.ed.gov/fulltext/ED397804.pdf)
20. Pollock E, Chandler P, Sweller J. Assimilating complex information. *Learning and Instruction* 2002;12:61–86. [ro.uow.edu.au/edupapers/145/](https://ro.uow.edu.au/edupapers/145/), [eric.ed.gov/?id=EJ646442](https://eric.ed.gov/?id=EJ646442) — **abstract only**.
21. Wightman DC, Lintern G. Part-task training for tracking and manual control. *Human Factors* 1985;27(3):267–283. [journals.sagepub.com/doi/10.1177/001872088502700304](https://journals.sagepub.com/doi/10.1177/001872088502700304) — **abstract only**; taxonomy (segmentation/fractionation/simplification) confirmed via [reports.nlr.nl](https://reports.nlr.nl/server/api/core/bitstreams/df63d736-c6d7-4203-8afd-797f8eab2d53/content).
22. Marton F et al. Variation theory: contrast, generalisation, separation, fusion. Overviews: [kb.edu.hku.hk/approaches_variation_theory/](https://kb.edu.hku.hk/approaches_variation_theory/), [books.openbookpublishers.com/10.11647/obp.0431/ch9.xhtml](https://books.openbookpublishers.com/10.11647/obp.0431/ch9.xhtml), Kullberg, Kempe & Marton 2017: [variationtheory.com/.../What-is-made-possible-to-learn-when-using-the-variation-theory-Kullberg-Kempe-Marton-2017.pdf](https://variationtheory.com/wp-content/uploads/2018/07/What-is-made-possible-to-learn-when-using-the-variation-theory-Kullberg-Kempe-Marton-2017.pdf)
23. Wickens CD, Hutchins S, Carolan T, Cumming J. Effectiveness of part-task training and increasing-difficulty training strategies: a meta-analysis approach. *Human Factors* 2013;55(2):461–470. [pubmed.ncbi.nlm.nih.gov/23691838/](https://pubmed.ncbi.nlm.nih.gov/23691838/) — abstract obtained in full.
24. The selection of cognitive diagnostic models for a reading comprehension test. [michiganassessment.org/.../TheSelectionofCognitiveDiagnosticModelsforaReadingComprehensionTest.pdf](https://michiganassessment.org/wp-content/uploads/2020/02/20.02.pdf.Res_.TheSelectionofCognitiveDiagnosticModelsforaReadingComprehensionTest.pdf) — **secondary/summary**.
25. Gu Y, Xu G. Generic identifiability of the DINA model and blessing of latent dependence. *Psychometrika* 2022. [link.springer.com/article/10.1007/s11336-022-09886-2](https://link.springer.com/article/10.1007/s11336-022-09886-2); Xu G, Shang Z (2018) design recommendations — **secondary**. See also: The sufficient and necessary condition for the identifiability and estimability of the DINA model, arXiv:1711.03174. [arxiv.org/pdf/1711.03174](https://arxiv.org/pdf/1711.03174)
26. Non-identifiability, equivalence classes, and attribute-specific classification in Q-matrix based cognitive diagnosis models. arXiv:1303.0426. [arxiv.org/pdf/1303.0426](https://arxiv.org/pdf/1303.0426) — **title/abstract only**.
27. Data-driven automated induction of prerequisite structure graphs. EDM 2016. [eric.ed.gov/?id=ED592683](https://eric.ed.gov/?id=ED592683)
28. Joint discovery of skill prerequisite graphs and student models (COMMAND). EDM 2016. [eric.ed.gov/?id=ED592684](https://eric.ed.gov/?id=ED592684)
29. Inferring prerequisite knowledge concepts in educational knowledge graphs: a multi-criteria approach. arXiv:2509.05393. [arxiv.org/html/2509.05393](https://arxiv.org/html/2509.05393)
30. Prerequisite relation learning: a survey and outlook. *ACM Computing Surveys* 2025. [dl.acm.org/doi/10.1145/3733593](https://dl.acm.org/doi/10.1145/3733593) — **title/venue only**.
31. Doroudi S, Aleven V, Brunskill E. Where's the reward? A review of reinforcement learning for instructional sequencing. *International Journal of Artificial Intelligence in Education* 2019;29(4):568–620. Author version obtained in full: [bpb-us-e2.wpmucdn.com/faculty.sites.uci.edu/dist/f/847/files/2019/11/IJAIED-RL-Review-Author-Version.pdf](https://bpb-us-e2.wpmucdn.com/faculty.sites.uci.edu/dist/f/847/files/2019/11/IJAIED-RL-Review-Author-Version.pdf); [link.springer.com/article/10.1007/s40593-019-00187-x](https://link.springer.com/article/10.1007/s40593-019-00187-x)
32. Rollinson J, Brunskill E. From predictive models to instructional policies. EDM 2015. [files.eric.ed.gov/fulltext/ED560516.pdf](https://files.eric.ed.gov/fulltext/ED560516.pdf)
33. Koedinger KR et al. An astonishing regularity in student learning rate. *PNAS* 2023;120(13):e2221311120. [pnas.org/doi/10.1073/pnas.2221311120](https://www.pnas.org/doi/10.1073/pnas.2221311120)
34. Revisiting the regularity of student learning rate: sensitivity to which observations are included. arXiv:2605.01690. [arxiv.org/abs/2605.01690](https://arxiv.org/html/2605.01690v2); Replicating an "astonishing regularity in student learning rate", EDM 2024. [educationaldatamining.org/edm2024/proceedings/2024.EDM-short-papers.40/](https://educationaldatamining.org/edm2024/proceedings/2024.EDM-short-papers.40/index.html) — **titles/abstracts only**.
35. Cen H, Koedinger K, Junker B. Learning Factors Analysis — a general method for cognitive model evaluation and improvement. ITS 2006. [pact.cs.cmu.edu/pubs/Cen,%20Koedinger%20&%20Junker06.pdf](http://pact.cs.cmu.edu/pubs/Cen,%20Koedinger%20&%20Junker06.pdf). Follow-up: Cen, Koedinger & Junker (2007), Is over practice necessary? — **secondary**.
36. Kulik CC, Kulik JA, Bangert-Drowns RL. Effectiveness of mastery learning programs: a meta-analysis. *Review of Educational Research* 1990;60(2):265–299. [uky.edu/~gmswan3/575/kulik_kulik_Bangert-Drowns_1990.pdf](https://www.uky.edu/~gmswan3/575/kulik_kulik_Bangert-Drowns_1990.pdf). Kulik/Slavin dispute summary: [nintil.com/bloom-sigma/](https://nintil.com/bloom-sigma/) — **secondary**.
37. Interactions between the isolated–interactive elements effect and levels of learner expertise: experimental evidence from an accountancy class. *Instructional Science*. [link.springer.com/article/10.1007/s11251-009-9105-x](https://link.springer.com/article/10.1007/s11251-009-9105-x) — **abstract only**.
38. Engelmann S, Carnine D. *Theory of Instruction: Principles and Applications*. Irvington, 1982/1991. Juxtaposition principles summarised at [psych.athabascau.ca/open/engelmann/theory.php](https://psych.athabascau.ca/open/engelmann/theory.php) — **secondary**.
39. Newell KM, task decomposition vs task simplification; constraints-led approach. Overviews: [perceptionaction.com/simplification/](https://perceptionaction.com/simplification/), [eprints.qut.edu.au/198819/1/Constraints_Led_Learning_in_Practice...pdf](https://eprints.qut.edu.au/198819/1/Constraints_Led_Learning_in_Practice_Designing_effective_learning_environments_docx.pdf) — **secondary**. See also: The impact of task simplification in skill acquisition for young children. [sciencedirect.com/science/article/pii/S0001691825004561](https://www.sciencedirect.com/science/article/pii/S0001691825004561)
40. Marraffino MD et al. Adapting training in real time: an empirical test of adaptive difficulty schedules. 2021. [pmc.ncbi.nlm.nih.gov/articles/PMC10013456/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10013456/)
41. Wilson RC, Shenhav A, Straccia M, Cohen JD. The eighty five percent rule for optimal learning. *Nature Communications* 2019;10:4646. [nature.com/articles/s41467-019-12552-4](https://www.nature.com/articles/s41467-019-12552-4)
42. Brady F. Contextual interference: a meta-analytic study. *Perceptual and Motor Skills* 2004;99:116–126. [gwern.net/doc/psychology/spaced-repetition/2004-brady.pdf](https://gwern.net/doc/psychology/spaced-repetition/2004-brady.pdf)
43. The myth of contextual interference learning benefit in sports practice: a systematic review and meta-analysis. *Educational Research Review* 2023. [sciencedirect.com/science/article/abs/pii/S1747938X23000301](https://www.sciencedirect.com/science/article/abs/pii/S1747938X23000301) — **title/abstract only**.
44. The effects of contextual interference learning on the acquisition and relatively permanent gains in skilled performance: a critical systematic review with multilevel meta-analysis. *Educational Psychology Review* 2024. [link.springer.com/article/10.1007/s10648-024-09892-z](https://link.springer.com/article/10.1007/s10648-024-09892-z) — **abstract/summary only** (Springer redirect blocked full fetch). See also the 2025 methodological rejoinder: [link.springer.com/article/10.1007/s10648-025-10043-1](https://link.springer.com/article/10.1007/s10648-025-10043-1)
45. High contextual interference improves retention in motor learning: systematic review and meta-analysis. *Scientific Reports* 2024. [nature.com/articles/s41598-024-65753-3](https://www.nature.com/articles/s41598-024-65753-3) — **title only**.
46. The effect of contextual interference on transfer in motor learning — a systematic review and meta-analysis. [ncbi.nlm.nih.gov/pmc/articles/PMC11349744/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11349744/) — **secondary**.
47. Rohrer D, Dedrick RF, Hartwig MK, Cheung C-N. A randomized controlled trial of interleaved mathematics practice. *Journal of Educational Psychology* 2020;112(1):40–52. [gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf](https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
48. Bjork RA, Bjork EL. Desirable difficulties in theory and practice. 2020. [waddesdonschool.com/wp-content/uploads/2021/02/Desriable-Difficulties-in-theory-and-practice-Bjork-Bjork-2020.pdf](https://www.waddesdonschool.com/wp-content/uploads/2021/02/Desriable-Difficulties-in-theory-and-practice-Bjork-Bjork-2020.pdf). Element-interactivity boundary condition — **secondary**.
49. Sinha T, Kapur M. When problem solving followed by instruction works: evidence for productive failure. *Review of Educational Research* 2021;91(5):761–798. [janfasen.nl/wp-content/uploads/2023/05/Sinha-and-Kapur-PS-I.pdf](https://janfasen.nl/wp-content/uploads/2023/05/Sinha-and-Kapur-PS-I.pdf)
50. Chen O, Kalyuga S, Sweller J. The expertise reversal effect is a variant of the more general element interactivity effect. *Educational Psychology Review* 2017. [link.springer.com/article/10.1007/s10648-016-9359-1](https://link.springer.com/article/10.1007/s10648-016-9359-1); full text: [repository.lboro.ac.uk/.../22174806.pdf](https://repository.lboro.ac.uk/articles/The_expertise_reversal_effect_is_a_variant_of_the_more_general_element_interactivity_effect/12052695/files/22174806.pdf)
51. Naylor JC, Briggs GE. Effects of task complexity and task organization on the relative efficiency of part and whole training methods. *Journal of Experimental Psychology* 1963. [pubmed.ncbi.nlm.nih.gov/13937802](https://www.ncbi.nlm.nih.gov/pubmed/13937802) — **abstract/secondary**. Meta-analysis: Whole and part practice: a meta-analysis. [pubmed.ncbi.nlm.nih.gov/20038005/](https://pubmed.ncbi.nlm.nih.gov/20038005/) — **title only**.
52. Atkinson RK, Renkl A, Merrill MM. Transitioning from studying examples to solving problems: effects of self-explanation prompts and fading worked-out steps. [mrbartonmaths.com/resourcesnew/8.%20Research/Making%20the%20most%20of%20examples/Fading%20out%20and%20Prompts.pdf](https://mrbartonmaths.com/resourcesnew/8.%20Research/Making%20the%20most%20of%20examples/Fading%20out%20and%20Prompts.pdf); Renkl A, Atkinson RK. Structuring the transition from example study to problem solving. [mrbartonmaths.com/resourcesnew/8.%20Research/Explicit%20Instruction/Structuring%20the%20Transition%20From%20Example%20Study%20to%20Problem%20Solving.pdf](https://mrbartonmaths.com/resourcesnew/8.%20Research/Explicit%20Instruction/Structuring%20the%20Transition%20From%20Example%20Study%20to%20Problem%20Solving.pdf)
53. Koedinger KR, Aleven V. Exploring the assistance dilemma in experiments with Cognitive Tutors. *Educational Psychology Review* 2007. [pact.cs.cmu.edu/pubs/Koedinger%20Aleven%2007.pdf](https://pact.cs.cmu.edu/pubs/Koedinger%20Aleven%2007.pdf)
54. Bengio Y, Louradour J, Collobert R, Weston J. Curriculum learning. ICML 2009. [dblp.org/rec/conf/icml/BengioLCW09.html](https://dblp.org/rec/conf/icml/BengioLCW09.html); [semanticscholar.org/paper/Curriculum-learning-Bengio-Louradour/8de174ab5419b9d3127695405efd079808e956e8](https://www.semanticscholar.org/paper/Curriculum-learning-Bengio-Louradour/8de174ab5419b9d3127695405efd079808e956e8)
55. Wu X, Dyer E, Neyshabur B. When do curricula work? ICLR 2021. [openreview.net/pdf?id=tW4QEInpni](https://openreview.net/pdf?id=tW4QEInpni); [arxiv.org/abs/2012.03107](https://arxiv.org/abs/2012.03107); code: [github.com/google-research/understanding-curricula](https://github.com/google-research/understanding-curricula)
56. Saglietti L, Mannelli SS, Saxe A. An analytical theory of curriculum learning in teacher–student networks. NeurIPS 2022. [pmc.ncbi.nlm.nih.gov/articles/PMC10561397/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10561397/)
57. Portelas R, Colas C, Weng L, Hofmann K, Oudeyer P-Y. Automatic curriculum learning for deep RL: a short survey. IJCAI 2020. [ijcai.org/proceedings/2020/0671.pdf](https://www.ijcai.org/proceedings/2020/0671.pdf); code: [github.com/flowersteam/teachDeepRL](https://github.com/flowersteam/teachDeepRL)
58. Birkhoff's representation theorem and order ideals of a poset. Standard enumerative combinatorics (Stanley RP, *Enumerative Combinatorics* vol. 1, ch. 3); MacMahon's box formula for plane partitions. The counts C(m+n,m) for products of two chains and the box formula for three chains were **independently verified by brute-force enumeration for all cases up to 3×4 and up to 3×3×3 while preparing this report**. Background: [mathworld.wolfram.com/Antichain.html](https://mathworld.wolfram.com/Antichain.html)
59. ALEKS: knowledge space theory (vendor page). [aleks.com/about_aleks/knowledge_space_theory](https://www.aleks.com/about_aleks/knowledge_space_theory) — **vendor/secondary**; the ~9-item fringe and 25–30-question figures come from this and its citing summaries and were not independently confirmed against a peer-reviewed source.
60. Automatic item generation: radicals, incidentals, item models, isomorphs. Reviews: [mdpi.com/2079-3200/13/8/102](https://www.mdpi.com/2079-3200/13/8/102), [pmc.ncbi.nlm.nih.gov/articles/PMC12387605/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12387605/). Primary attributions to Bejar, Irvine and Kyllonen are **secondary** here.
61. Koedinger KR, Corbett AT, Perfetti C. The Knowledge-Learning-Instruction framework: bridging the science-practice chasm to enhance robust student learning. *Cognitive Science* 2012;36(5):757–798. [pact.cs.cmu.edu/pubs/Koedinger,%20Corbett,%20Perfetti%202012-KLI.pdf](http://pact.cs.cmu.edu/pubs/Koedinger,%20Corbett,%20Perfetti%202012-KLI.pdf)

---

### Verification notes

- **Directly obtained and read in full**: [1], [2], [4], [16], [31] (PDF text extraction), plus abstracts of [9], [17], [23], [40], [55].
- **Independently computed**: the order-ideal counts in §7.1 (brute-force enumeration against C(m+n,m) and MacMahon's box formula).
- **Could not verify**: any ALEKS *outcome* (external-measure) study; the "30% improvement" figure attributed to SCM; the exact algebra of component-based surmise construction in [11][12]; the primary Wightman & Lintern text; the primary Naylor & Briggs text; the 2024 contextual-interference meta-analysis full text (Springer paywall/redirect). Claims resting on these are marked in place.
- **Known open disagreement in the literature**: contextual interference (the 2024–2025 meta-analyses conflict); mastery learning (Kulik vs Slavin); curriculum learning in ML (2009 vs 2021); conjunctive vs compensatory CDM fit (varies by item within a single test).
