You are designing a synthetic document corpus for testing a knowledge graph RAG system.
Your output will be used to generate realistic documents. You must plan them carefully.

═══════════════════════════════════════
GOLDEN KNOWLEDGE GRAPH
═══════════════════════════════════════
{kg_json}

═══════════════════════════════════════
GENERATION PARAMETERS
═══════════════════════════════════════
- Standard documents to produce: {num_standard_documents}
- Include inconsistency document: {include_inconsistency}
- Language: {language}
- Fact modality distribution: text={text_pct}%, table={table_pct}%, image={image_pct}%
- Entity reuse probability: {entity_reuse_prob}%
- Noise level: {noise_level}% (0%=minimal off knowledge graph content, 100%=heavy)
- Minimum documents needed to answer any key question: {min_docs_per_chain}

═══════════════════════════════════════
YOUR TASK
═══════════════════════════════════════

Design a CorpusPlan. Follow ALL rules below precisely.

── DOCUMENT TYPE SELECTION ───────────────────────────────────────────
Choose document types realistic for the given domain.
Each document must be a type that would plausibly exist in this domain.
Examples depending on domain:
  Financial/corporate: shareholder register, annual report, trust deed,
    articles of association, board minutes, UBO declaration, KYC form,
    regulatory filing, power of attorney, sanctions list excerpt
  Medical: clinical trial report, patient intake form, prescription record
  Legal: contract, court filing, affidavit
  Real estate: property deed, lease agreement, valuation report
Match document types to what your chosen entities/facts would realistically appear in.

── FACT DISTRIBUTION RULES (CRITICAL) ───────────────────────────────
These rules ensure the corpus forces multi-document analysis:

RULE 1 — CHAIN SPLITTING:
  Identify all chains of related facts (where output of one fact is
  input of another). Facts forming a chain MUST be spread across
  DIFFERENT documents. No chain should be fully contained in one document.
  Minimum {min_docs_per_chain} documents must be required to reconstruct any chain.

RULE 2 — NO ISOLATED BLOCKS:
  Do not create documents that are completely self-contained islands.
  Every document must share at least one entity with at least two other documents.
  This forces cross-document entity resolution.

RULE 3 — ENTITY REUSE:
  Entities should appear in multiple documents with probability {entity_reuse_prob}%.
  When an entity is reused, apply alias with probability {alias_prob}% using
  one of these transformations: {alias_types}.
  Assign the exact name_variant string for each document explicitly.
  Important: aliases must be RECOVERABLE (human or system can still identify the entity).

RULE 4 — CONNECTOR ENTITIES:
  Entities that appear in relation facts connecting two chains should appear
  in documents from BOTH chains. These "connector" entities are the bridge
  a system must identify to link information.

── MODALITY ASSIGNMENT ──────────────────────────────────────────────
Distribute facts across modalities respecting the distribution:
  {text_pct}% in text narrative, {table_pct}% in tables, {image_pct}% in images.

Good candidates for each modality:
  TEXT: narrative facts (control relationships, contextual statements,
    qualitative descriptions, references to other entities)
  TABLE: structured data (ownership percentages, financial figures,
    lists of directors, dates, addresses, registration numbers)
  IMAGE: visual facts (org charts for ownership structure,
    ID cards showing person identity, stamps showing registration,
    signature blocks, photographs of property/assets)

For each image fact, you MUST provide a detailed vlm_generation_prompt that:
  - Describes exactly what should appear in the image
  - Names the entities using their document-specific name_variant
  - Specifies the visual style (formal corporate, government ID, etc.)
  - Is specific enough that a text-to-image model produces a useful, readable image

── INCONSISTENCY DOCUMENT ───────────────────────────────────────────
If include_inconsistency=true, plan one additional document that:
  - Looks like a legitimate document in this domain
  - Contradicts exactly {num_contradicted_facts} facts from the main corpus
  - Contradiction types to use: {contradiction_types}
  - For each contradicted fact, specify:
    * original_fact_uid: which fact is contradicted
    * contradiction_type: from the allowed types
    * contradicted_value: what incorrect value this document claims
    * rationale: why a real document might say this (e.g., outdated version,
      different source, amended filing, mistake in original)
  - This document should NOT contradict facts that are NOT in your plan
    (don't invent new contradictions outside the provided KG)

── NOISE CONTENT ────────────────────────────────────────────────────
Each document should contain realistic off-KG content.
Noise level means approximately {noise_level}% of document
content should be realistic but not present in the KG.
Examples: other entities and relations not from kg, 
any content may be present in real document of such type,
contact information, irrelevant financial information, standard clauses,
boilerplate legal text, standard disclaimers, signatory blocks,
List 2-10 specific noise_topics per document.

── OUTPUT SELF-VALIDATION ───────────────────────────────────────────
Before producing your JSON, verify:
1. Every relation fact appears in at least one document
2. Every value fact appears in at least one document  
3. No chain is contained within a single document
4. Every entity appears in at least one document
5. Image specs reference valid fact_uids
6. name_variant for each entity_usage is consistent with alias rules

You must produce not less than {num_standard_documents} documents!

In multi_hop_guarantee, explicitly list example questions that span multiple
documents and which documents are required to answer each.

═══════════════════════════════════════
OUTPUT
═══════════════════════════════════════
Output valid JSON conforming to this schema. No markdown, no explanation outside JSON.

