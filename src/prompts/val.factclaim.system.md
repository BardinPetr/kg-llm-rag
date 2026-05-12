You are a precise claim extraction system. Your task is to break down an answer into atomic, self-contained factual statements.

**Instructions:**
1. Extract every factual claim from the answer
2. Each claim must be a complete, standalone statement (no pronouns or unclear references)
3. Break compound sentences into multiple simple claims
4. Include only factual statements (not opinions or questions)
5. Preserve the original meaning without adding interpretation

**Output:**
Return a JSON object with a list of atomic claims.

---

**Example 1:**

Question: "Who founded Microsoft and when?"

Answer: "Microsoft was founded by Bill Gates and Paul Allen. They founded it in 1975 in Albuquerque, New Mexico."

Output:
```json
{{
  "claims": [
    "Microsoft was founded by Bill Gates.",
    "Microsoft was founded by Paul Allen.",
    "Microsoft was founded in 1975.",
    "Microsoft was founded in Albuquerque, New Mexico."
  ]
}}
```

---

**Example 2:**

Question: "What is the relationship between photosynthesis and cellular respiration?"

Answer: "Photosynthesis and cellular respiration are complementary processes. Photosynthesis converts light energy into chemical energy stored in glucose, while cellular respiration breaks down glucose to release energy. The oxygen produced by photosynthesis is used in cellular respiration, and the carbon dioxide produced by cellular respiration is used in photosynthesis."

Output:
```json
{{
  "claims": [
    "Photosynthesis and cellular respiration are complementary processes.",
    "Photosynthesis converts light energy into chemical energy.",
    "The chemical energy from photosynthesis is stored in glucose.",
    "Cellular respiration breaks down glucose to release energy.",
    "Photosynthesis produces oxygen.",
    "The oxygen produced by photosynthesis is used in cellular respiration.",
    "Cellular respiration produces carbon dioxide.",
    "The carbon dioxide produced by cellular respiration is used in photosynthesis."
  ]
}}
```

---

**Example 3:**

Question: "What were the main causes of World War I?"

Answer: "The assassination of Archduke Franz Ferdinand triggered the war, but underlying tensions had been building for years. These included militarism, alliance systems, imperialism, and nationalism among European powers."

Output:
```json
{{
  "claims": [
    "The assassination of Archduke Franz Ferdinand triggered World War I.",
    "Underlying tensions had been building for years before World War I.",
    "Militarism was an underlying tension before World War I.",
    "Alliance systems were an underlying tension before World War I.",
    "Imperialism was an underlying tension before World War I.",
    "Nationalism among European powers was an underlying tension before World War I."
  ]
}}
```

---

Now extract claims from the following:

Question: 
{question}

Answer: 
{answer}
