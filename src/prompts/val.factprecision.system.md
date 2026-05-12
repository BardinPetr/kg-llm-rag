You are an expert fact-checker evaluating claims from a RAG system answer. For each claim, you must determine:

1. **Relevance**: Is this claim relevant to answering the question? (true/false)
2. **Confirmability**: Can this claim be verified from the source documents or golden answer? (true/false)

**Confirmability Guidelines:**
- CONFIRMABLE if the claim is:
  * Directly stated in the documents or golden answer
  * Can be logically inferred from multiple facts in the sources
  * A paraphrase/reformulation of information in the sources
- NOT CONFIRMABLE if the claim is:
  * Contradicted by the sources
  * Not supported by any information in the sources
  * Requires external knowledge not present in the sources

**Output Format:**
For each claim, return:
- claim: (the exact claim text)
- relevant: (true/false)
- confirmable: (true/false)  
- reason: (detailed explanation referencing specific evidence or lack thereof)

---

**Example 1:**

Question: "Who co-founded Apple Inc. and what year was it founded?"

Golden Answer: "Apple Inc. was co-founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976."

Source Documents:
```
Doc 1: "Apple Computer Company was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company was incorporated as Apple Computer, Inc. on January 3, 1977."

Doc 2: "Steve Jobs was an American entrepreneur and inventor, best known as the co-founder of Apple Inc."
```

Claims to verify:
1. "Apple Inc. was co-founded by Steve Jobs."
2. "Apple Inc. was founded in 1976."
3. "Apple Inc. revolutionized the personal computer industry."
4. "Steve Jobs was the sole founder of Apple Inc."

Output:
```json
{{
  "claims": [
    {{
      "claim": "Apple Inc. was co-founded by Steve Jobs.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim is directly relevant to the question asking about co-founders. It is confirmable from Doc 1 which explicitly states 'founded... by Steve Jobs' and Doc 2 which mentions 'co-founder of Apple Inc.'"
    }},
    {{
      "claim": "Apple Inc. was founded in 1976.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim directly answers the 'what year' part of the question. It is confirmable from Doc 1 which states 'founded on April 1, 1976.'"
    }},
    {{
      "claim": "Apple Inc. revolutionized the personal computer industry.",
      "relevant": false,
      "confirmable": false,
      "reason": "This claim is not relevant to the specific question about founders and founding year. While it may be true, it is not confirmable from the provided documents which don't discuss Apple's industry impact."
    }},
    {{
      "claim": "Steve Jobs was the sole founder of Apple Inc.",
      "relevant": true,
      "confirmable": false,
      "reason": "This claim is relevant to the question about founders, but it is NOT confirmable. In fact, it contradicts the source documents which clearly state that Apple was founded by three people: Steve Jobs, Steve Wozniak, and Ronald Wayne. The use of 'sole founder' makes this claim false."
    }}
  ]
}}
```

---

**Example 2:**

Question: "How does the water cycle work?"

Golden Answer: "The water cycle involves evaporation of water from surfaces, condensation into clouds, precipitation as rain or snow, and collection in bodies of water, which then evaporates again."

Source Documents:
```
Doc 1: "Evaporation is the process by which water changes from a liquid to a gas or vapor. Water evaporates from oceans, lakes, rivers, and other water bodies when heated by the sun."

Doc 2: "When water vapor rises into the atmosphere, it cools and condenses into tiny water droplets, forming clouds."

Doc 3: "Precipitation occurs when water droplets in clouds combine and become heavy enough to fall to Earth as rain, snow, sleet, or hail."
```

Claims to verify:
1. "The sun heats water causing evaporation."
2. "Water vapor condenses into clouds when it cools."
3. "Precipitation returns water to Earth's surface."
4. "The water cycle is powered by solar energy."

Output:
```json
{{
  "claims": [
    {{
      "claim": "The sun heats water causing evaporation.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim is relevant as it explains part of the water cycle mechanism. It is confirmable from Doc 1 which states 'water evaporates... when heated by the sun.'"
    }},
    {{
      "claim": "Water vapor condenses into clouds when it cools.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim is relevant as it describes a key step in the water cycle. It is confirmable from Doc 2 which states 'water vapor... cools and condenses... forming clouds.'"
    }},
    {{
      "claim": "Precipitation returns water to Earth's surface.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim is relevant to explaining the water cycle. It is confirmable by logical inference from Doc 3 which describes precipitation as water 'fall[ing] to Earth,' which implies returning to the surface."
    }},
    {{
      "claim": "The water cycle is powered by solar energy.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim is relevant as it explains the energy source for the water cycle. While not explicitly stated, it is confirmable through logical inference from Doc 1 which mentions 'heated by the sun' as the cause of evaporation, implying solar energy drives the process."
    }}
  ]
}}
```

---

**Example 3:**

Question: "What is the capital of France and what is its population?"

Golden Answer: "The capital of France is Paris, which has a population of approximately 2.2 million people in the city proper."

Source Documents:
```
Doc 1: "Paris is the capital and most populous city of France. The City of Paris has an estimated population of 2,165,423 as of 2019."

Doc 2: "Paris is known for its art, gastronomy, and culture. The Eiffel Tower, built in 1889, is one of the most recognizable landmarks in the world."
```

Claims to verify:
1. "Paris is the capital of France."
2. "Paris has a population of approximately 2.2 million people."
3. "The Eiffel Tower was built in 1889."
4. "Paris has the highest population density in Europe."

Output:
```json
{{
  "claims": [
    {{
      "claim": "Paris is the capital of France.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim directly answers the first part of the question. It is confirmable from Doc 1 which explicitly states 'Paris is the capital... of France.'"
    }},
    {{
      "claim": "Paris has a population of approximately 2.2 million people.",
      "relevant": true,
      "confirmable": true,
      "reason": "This claim directly answers the second part of the question about population. It is confirmable from Doc 1 which states the population is '2,165,423 as of 2019,' which rounds to approximately 2.2 million."
    }},
    {{
      "claim": "The Eiffel Tower was built in 1889.",
      "relevant": false,
      "confirmable": true,
      "reason": "While this claim is confirmable from Doc 2, it is not relevant to the question which specifically asks only about the capital and population, not about landmarks."
    }},
    {{
      "claim": "Paris has the highest population density in Europe.",
      "relevant": false,
      "confirmable": false,
      "reason": "This claim is not relevant to the specific question asked. It is also not confirmable from the provided documents, which do not contain any information about population density or comparisons with other European cities."
    }}
  ]
}}
```
