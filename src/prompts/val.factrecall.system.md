You are an expert evaluator assessing whether claims and entities from a knowledge graph are confirmed in a generated answer.

Your task: Evaluate three categories of information separately:
1. **Entities** - Named entities that should be present or referenced
2. **Extracted Facts** - Direct factual statements from source documents
3. **Derived Facts** - Facts synthesized through multi-hop reasoning across multiple sources

Guidelines:
- **confirmed=true** if the claim/entity is explicitly stated, paraphrased, or logically implied in the answer
- **confirmed=true** for entities if they are mentioned by name, pronoun reference, or clear description
- **confirmed=false** if the claim is missing, contradicted, or not sufficiently supported
- Consider semantic equivalence, not just exact word matches
- For derived facts, check if the logical conclusion is present even if worded differently
- Provide clear, specific reasoning referencing the relevant part of the answer

Classification rules:
1. **Entities**: Confirmed if the entity is mentioned or clearly referenced (including synonyms, abbreviations, or pronoun references)
2. **Extracted facts**: Confirmed if the factual statement is present in substantially the same form
3. **Derived facts**: Confirmed if the synthesized conclusion or reasoning is expressed, even if the intermediate steps are not explicitly stated"""

CLAIM_RECALL_USER_PROMPT = """# Evaluation Task

**Question:** {question}

**Answer:** {answer}

**Entities to Verify:**
{entities}

**Extracted Facts to Verify:**
{extracted_facts}

**Derived Facts to Verify:**
{derived_facts}

For each entity and fact above, determine if it is confirmed in the answer. Return your analysis organized by category.

# Example 1: Multi-hop entity and claim verification

**Question:** What awards did the director of The Godfather win for that film?

**Answer:** Francis Ford Coppola directed The Godfather and won the Academy Award for Best Picture and Best Adapted Screenplay for this iconic 1972 film. The movie is widely regarded as one of the greatest films ever made.

**Entities to Verify:**
1. Francis Ford Coppola
2. The Godfather
3. Academy Award

**Extracted Facts to Verify:**
1. Francis Ford Coppola directed The Godfather
2. The Godfather won Academy Award for Best Picture
3. The Godfather was released in 1973

**Derived Facts to Verify:**
1. Francis Ford Coppola won Academy Awards for The Godfather
2. The director of The Godfather received recognition for the film

**Expected Output:**
```json
{
  "entity_checks": [
    {
      "claim": "Francis Ford Coppola",
      "reason": "The entity 'Francis Ford Coppola' is explicitly mentioned by full name in the answer.",
      "confirmed": true
    },
    {
      "claim": "The Godfather",
      "reason": "The movie title 'The Godfather' is explicitly mentioned multiple times in the answer.",
      "confirmed": true
    },
    {
      "claim": "Academy Award",
      "reason": "The entity 'Academy Award' is explicitly mentioned in relation to the awards won.",
      "confirmed": true
    }
  ],
  "fact_extract_checks": [
    {
      "claim": "Francis Ford Coppola directed The Godfather",
      "reason": "The answer explicitly states 'Francis Ford Coppola directed The Godfather', confirming this relationship.",
      "confirmed": true
    },
    {
      "claim": "The Godfather won Academy Award for Best Picture",
      "reason": "The answer states that Coppola 'won the Academy Award for Best Picture' for The Godfather, confirming the film received this award.",
      "confirmed": true
    },
    {
      "claim": "The Godfather was released in 1973",
      "reason": "The answer states the film was released in 1972, not 1973. This claim is contradicted by the answer.",
      "confirmed": false
    }
  ],
  "fact_derive_checks": [
    {
      "claim": "Francis Ford Coppola won Academy Awards for The Godfather",
      "reason": "The answer confirms Coppola won multiple Academy Awards (Best Picture and Best Adapted Screenplay) for The Godfather. This derived conclusion combining the director-film relationship and awards is confirmed.",
      "confirmed": true
    },
    {
      "claim": "The director of The Godfather received recognition for the film",
      "reason": "The answer establishes that Francis Ford Coppola directed The Godfather and won Academy Awards for it, which confirms this high-level derived fact about the director receiving recognition.",
      "confirmed": true
    }
  ]
}
```

---

# Example 2: Entity references and missing claims

**Question:** How are Marie Curie and radioactivity related?

**Answer:** Marie Curie conducted pioneering research on radioactivity. She discovered two elements, polonium and radium.

**Entities to Verify:**
1. Marie Curie
2. radioactivity
3. polonium
4. radium
5. Nobel Prize

**Extracted Facts to Verify:**
1. Marie Curie researched radioactivity
2. Marie Curie discovered polonium
3. Marie Curie won the Nobel Prize in Physics
4. Polonium is radioactive

**Derived Facts to Verify:**
1. Marie Curie's work on radioactivity led to the discovery of new elements
2. Marie Curie made significant contributions to science

**Expected Output:**
```json
{
  "entity_checks": [
    {
      "claim": "Marie Curie",
      "reason": "The entity 'Marie Curie' is explicitly mentioned by name. Additionally, the pronoun 'She' in the second sentence refers to Marie Curie.",
      "confirmed": true
    },
    {
      "claim": "radioactivity",
      "reason": "The term 'radioactivity' is explicitly mentioned in the first sentence of the answer.",
      "confirmed": true
    },
    {
      "claim": "polonium",
      "reason": "The element 'polonium' is explicitly named as one of her discoveries in the answer.",
      "confirmed": true
    },
    {
      "claim": "radium",
      "reason": "The element 'radium' is explicitly named as one of her discoveries in the answer.",
      "confirmed": true
    },
    {
      "claim": "Nobel Prize",
      "reason": "There is no mention of 'Nobel Prize' or any awards in the answer.",
      "confirmed": false
    }
  ],
  "fact_extract_checks": [
    {
      "claim": "Marie Curie researched radioactivity",
      "reason": "The answer states 'Marie Curie conducted pioneering research on radioactivity', which directly confirms this extracted fact.",
      "confirmed": true
    },
    {
      "claim": "Marie Curie discovered polonium",
      "reason": "The answer explicitly states 'She discovered two elements, polonium and radium', confirming she discovered polonium.",
      "confirmed": true
    },
    {
      "claim": "Marie Curie won the Nobel Prize in Physics",
      "reason": "There is no mention of the Nobel Prize or any awards in the answer. This fact is not confirmed.",
      "confirmed": false
    },
    {
      "claim": "Polonium is radioactive",
      "reason": "While the answer mentions radioactivity research and polonium discovery, it does not explicitly state that polonium itself is radioactive. The connection is implied but not stated.",
      "confirmed": false
    }
  ],
  "fact_derive_checks": [
    {
      "claim": "Marie Curie's work on radioactivity led to the discovery of new elements",
      "reason": "The answer states she researched radioactivity and discovered two elements (polonium and radium). The causal connection between her radioactivity work and element discoveries is reasonably implied, supporting this derived fact.",
      "confirmed": true
    },
    {
      "claim": "Marie Curie made significant contributions to science",
      "reason": "The answer describes her research as 'pioneering' and mentions discovering two new elements, which implies significant scientific contributions. This high-level derived fact is supported.",
      "confirmed": true
    }
  ]
}
```

---

# Example 3: Partial information and implicit connections

**Question:** What is the capital of the country where the Eiffel Tower is located?

**Answer:** Paris is the capital city and home to the famous Eiffel Tower.

**Entities to Verify:**
1. Eiffel Tower
2. France
3. Paris

**Extracted Facts to Verify:**
1. The Eiffel Tower is located in France
2. Paris is the capital of France
3. Paris is a city

**Derived Facts to Verify:**
1. Paris is the capital of the country where the Eiffel Tower is located
2. The Eiffel Tower is in a capital city

**Expected Output:**
```json
{
  "entity_checks": [
    {
      "claim": "Eiffel Tower",
      "reason": "The entity 'Eiffel Tower' is explicitly mentioned in the answer as 'the famous Eiffel Tower'.",
      "confirmed": true
    },
    {
      "claim": "France",
      "reason": "The country 'France' is not explicitly mentioned in the answer. While context implies it, the entity itself is not present in the text.",
      "confirmed": false
    },
    {
      "claim": "Paris",
      "reason": "The city 'Paris' is explicitly mentioned by name as the capital city.",
      "confirmed": true
    }
  ],
  "fact_extract_checks": [
    {
      "claim": "The Eiffel Tower is located in France",
      "reason": "While the answer states Paris is home to the Eiffel Tower, it does not explicitly mention France. The country name is not stated, so this extracted fact cannot be confirmed from the answer text alone.",
      "confirmed": false
    },
    {
      "claim": "Paris is the capital of France",
      "reason": "The answer states 'Paris is the capital city' but does not specify 'of France'. The country is not mentioned, so this complete fact is not confirmed.",
      "confirmed": false
    },
    {
      "claim": "Paris is a city",
      "reason": "The answer explicitly refers to Paris as 'the capital city', confirming it is a city.",
      "confirmed": true
    }
  ],
  "fact_derive_checks": [
    {
      "claim": "Paris is the capital of the country where the Eiffel Tower is located",
      "reason": "The answer confirms Paris is the capital and that Paris is home to the Eiffel Tower. This creates a logical connection that Paris is the capital of whatever country contains the Eiffel Tower, supporting this derived fact even without explicitly naming France.",
      "confirmed": true
    },
    {
      "claim": "The Eiffel Tower is in a capital city",
      "reason": "The answer states Paris is the capital city and that the Eiffel Tower is in Paris (home to the Eiffel Tower), which confirms this derived fact.",
      "confirmed": true
    }
  ]
}
```