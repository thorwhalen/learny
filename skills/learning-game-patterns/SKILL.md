---
name: learning-game-patterns
description: >-
  A pattern language for games that teach symbols (characters of another script) and vocabulary: the ten learning families (match, produce, construct, order, discriminate, context, explore, encode, schedule, assess), the six matching patterns (pick-the-match, pair-off field, hidden pair, route the stream, find in a field, chain), nine pressure renderings (countdown bar, falling object, overflow container, time bank, and more), and which to use in which learning phase. Use when designing or choosing a mechanic for a language-learning, kana, kanji, alphabet or vocabulary game, when asked "what kinds of matching games are there", "how should the timer work", "which game form for look-alike characters", or when deciding what a game must log for the learner model.
metadata:
  audience: developers
  source: thorwhalen/learny docs/research/learning-game-patterns.md (2026-10-16)
---

# Learning-game patterns for symbols and vocabulary

Distilled from `docs/research/learning-game-patterns.md` in the learny repo, which has the evidence, caveats and references. Read that note before asserting any evidence claim: the catalogue is design hypotheses grounded in component evidence, because no study compares matching forms.

## The model: six axes, not a tree

A game is a point in: **family** (what the learner does) × **pattern** (layout of prompts and answers) × **pressure** (what the clock looks like) × **feedback** × **progression** × **wrapper** (the theme). Pressure, feedback and wrapper swap onto any pattern. Modality (glyph to sound, picture to word) and direction (recognise versus produce) are settings of the item set, not patterns.

Rule of thumb: **intrinsic integration**. The answer should be the move. Matching satisfies this; "answer a question to earn play time" does not.

## Matching: six patterns (k options, n pairs)

| ID | Pattern | Notes |
|---|---|---|
| M1 | Pick the match: one prompt, k options, one correct | the clean case; guess rate 1/k; distractors from a confusability table |
| M2 | Pair off in a visible field (mixed pile, two columns, connect, drag) | elimination inflates scores; random-pick guess about 1/(2n-1); weaker evidence per response |
| M3 | Hidden pair (concentration) | also trains spatial memory; poor for diagnosing symbol knowledge |
| M4 | Route the arriving item to one of k fixed targets | best fit for the fluency phase; easy to wrap as runner or tower defence |
| M5 | Find every target in a field | look-alike discrimination; log false alarms |
| M6 | Chain (the match is the next prompt; shiritori) | vocabulary, late phase |

The user's examples: multiple choice untimed = M1 + no pressure; the object that falls and must be popped = M1 + falling deadline; balloons in a box popped by matching pairs, overflowing if slow = M2 + capacity overflow.

## Other families (one line each)

Produce (type the answer, draw or trace, say it, self-graded flashcard). Construct (assemble a word from tiles, build a character from components, assemble a sentence, crossword). Order (put symbols in standard order, stroke order). Discriminate (odd one out, same or different, sort into bins, true or false). Context (cloze, listen and tap, read and respond). Explore and collect (find symbols in a scene, collections, build with earned symbols). Encode (mnemonic picture, song, component breakdown; before testing, not instead). Schedule (spaced repetition, mastery gate, daily review: every pattern should draw its items from one). Assess (placement, boss round, timed fluency probe).

## Pressure: nine renderings

none; countdown bar (per-item latency); falling deadline (latency shown as distance); capacity overflow (throughput); time bank (streak speed); chasing threat (sustained accuracy); round timer; opponent race; rhythm. Evidence is thin: timers seem to raise practice volume and speed more than accuracy. Defaults (design choices): start with none; add pressure once accuracy is stable; set the limit as a multiple of that learner's own median response time and adapt it; use overflow or falling pressure for the fluency phase.

## Phase ladder (an untested inference)

1 Encode (3 to 5 new symbols) → 2 Recognise (M1, k 2 to 4, untimed) → 3 Discriminate (M5, odd-one-out, look-alike distractors) → 4 Recall (type the answer) → 5 Fluency (M4, M2 with overflow, M1 with falling deadline, timed probe) → 6 Transfer (word building, cloze, listen and tap, chains).

## What every pattern must log

For the learner model (`learny.tracing`): the item, the outcome, the latency, **the options shown and the wrong choice** (confusions drive distractor choice), the pattern and pressure used, and a guess-like-play flag (a fast wrong answer on a symbol the model thinks is weak is guessing, not ignorance; downweight it). Pass the pattern's guess rate as `guess=`; it is a property of the pattern. Items come from the scheduler, never from the game.

## Open questions (do not assert as settled)

Whether falling or overflow pressure beats the same layout untimed; how much M2 elimination inflates scores; which distractor policy retains best; whether the six axes are exhaustive. The game's own logs (pattern, pressure, phase as fields) are the evidence to collect.
