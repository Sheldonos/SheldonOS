---
name: master-comedian-joke-writer
description: A framework for writing, analyzing, and structuring one-liner and two-liner jokes using the techniques of master comedians (Seinfeld, Hedberg, Carlin, Wright). Use when a user asks to write jokes, analyze comedy structure, punch up existing material, or generate stand-up comedy one-liners.
license: Complete terms in LICENSE.txt
---

# Master Comedian Joke Writer

This skill provides a rigorous, structural framework for writing and analyzing one-liner and two-liner jokes. It moves beyond "trying to be funny" and instead treats joke writing as an act of linguistic engineering, cognitive misdirection, and precise timing, based on the techniques of master comedians.

## Core Philosophy

A joke is not a random funny thought. It is a two-part structure built on cognitive misdirection:
1. **Setup:** Creates a false expectation (the Target Assumption) in the listener's mind. It must sound factual and not inherently funny.
2. **Punchline:** Shatters the expectation by revealing an alternative, unexpected meaning (the Reinterpretation) that was always latent in the setup.

## The 5-Mechanism Joke Structure (Greg Dean Model)

When writing or analyzing a joke, always break it down into these five mechanisms:

1. **1st Story:** The mental scene the audience constructs from the setup.
2. **Target Assumption:** The specific false belief the audience holds about the setup's meaning.
3. **Connector:** The ambiguous element (word, phrase, or concept) in the setup that has at least two valid interpretations. This is the pivot point of the joke.
4. **Reinterpretation:** The unexpected, alternative meaning of the Connector, revealed by the punchline.
5. **2nd Story:** The new, true, humorous reality the audience constructs after the punchline.

*Example:* "I've been getting into astronomy, so I installed a skylight. The people who live above me are furious."
*   **Connector:** "Above me" (sky vs. upstairs neighbor).
*   **Target Assumption:** He lives in a house looking at the sky.
*   **Reinterpretation:** He lives in an apartment and cut a hole in his neighbor's floor.

## Master Comedian Techniques

When generating jokes, adopt the specific structural techniques of these masters:

### 1. Jerry Seinfeld: Economy and Parallelism
*   **Economy:** Ruthlessly edit. Remove every unnecessary word or syllable. The shorter the path from setup to punchline, the harder it hits.
*   **Parallelism:** Use repeating sentence structures to create a rhythm, then break that rhythm with the punchline.
*   **Observational Minutiae:** Ground the setup in hyper-specific, universally relatable everyday details.

### 2. Mitch Hedberg: The Compressed Twist
*   **Compression:** Fuse the setup and punchline into a single, dense sentence. (e.g., "I haven't slept for ten days, because that would be too long.")
*   **Wittgensteinian Wordplay:** Exploit the gap between what a phrase *literally* means and what it *conventionally implies*. (e.g., "I used to do drugs. I still do, but I used to, too.")

### 3. George Carlin: Escalation and Deconstruction
*   **Double-Meanings:** Build jokes around words with multiple interpretations to expose the absurdity of common idioms.
*   **Escalating Premise:** Start with a simple observation and systematically push it to its logical, extreme conclusion through a series of mini-punchlines.

### 4. Steven Wright: Deadpan Misdirection
*   **The Non-Sequitur Illusion:** Write jokes that appear to be random thoughts but are actually highly structured incongruities.

## The Golden Rules of Delivery & Formatting

When outputting jokes for the user, you MUST adhere to these rules:

1. **The "Last Word" Rule:** The punch word (the word that triggers the reinterpretation) MUST be the absolute last word in the sentence. Anything after the punch word is wasted and ruins the timing.
   *   *Wrong:* "I had eggs for breakfast. They were Cadbury, which was delicious."
   *   *Right:* "I had eggs for breakfast. They were fresh, they were delicious, they were Cadbury."
2. **Indicate Pauses:** When providing jokes for a user to perform, use ellipses (...) or bracketed notes `[pause]` to indicate where the pre-punchline and post-punchline pauses should occur.

## Workflow: How to Write a Joke

When a user asks you to write a joke on a specific topic, follow this workflow:

1. **Identify the Topic:** Start with a factual, truthful piece of information about the topic. Do not try to be funny yet.
2. **List Assumptions:** Generate a list of normal assumptions a person would make upon hearing that factual statement.
3. **Find the Connector:** Identify a word, phrase, or concept in the setup that can be interpreted in more than one way.
4. **Create the Reinterpretation:** Choose an unexpected but logically valid alternative meaning for the Connector.
5. **Draft the Punchline:** Write the reveal based on the Reinterpretation.
6. **Edit for Economy and Placement:** Cut all fat. Ensure the punch word is the absolute last word.

## Workflow: How to Analyze/Punch Up a Joke

When a user provides a joke that isn't working:

1. Identify the **Connector**. If there isn't one, it's not a joke; it's just a statement. Find a Connector.
2. Check the **Target Assumption**. Is the setup effectively misdirecting the audience? If it's too obvious, rewrite the setup to be more mundane.
3. Check the **Last Word Rule**. Is the punch word buried in the middle of the sentence? Move it to the end.
4. Check for **Economy**. Remove any words that do not serve the setup or the punchline.
