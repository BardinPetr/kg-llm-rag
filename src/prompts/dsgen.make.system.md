You are generating a single realistic synthetic document as HTML.

═══════════════════════════════════════
DOCUMENT SPECIFICATION
═══════════════════════════════════════
{plan_json}

═══════════════════════════════════════
FULL KNOWLEDGE GRAPH (context only)
═══════════════════════════════════════
Use this to understand the full domain context.
Do NOT add facts from this graph that are not listed in the document specification above.
Do NOT accidentally introduce consistent information for facts marked as contradictions.

{kg_json}

═══════════════════════════════════════
GENERATION RULES
═══════════════════════════════════════

── ENTITY NAMES ─────────────────────────────────────────────────────
Use entity names EXACTLY as specified in entity_usages[].name_variant.
Do not use the canonical_name unless it matches the assigned name_variant.
Consistency within this document: use the same variant throughout.

── FACT INCLUSION ────────────────────────────────────────────────────
Every fact listed in fact_placements[] MUST appear in this document,
in the modality specified (text | table | image).

For TEXT facts: weave them naturally into the document narrative.
For TABLE facts: include in an appropriate HTML table. The fact value
  must appear as a cell value, not just as narrative.
For IMAGE facts: do not describe the image in text — insert an <img> tag
  using the specification from image_specs[]. The fact must be IN the image
  (via the vlm prompt), not described beside it in text.

── CONTRADICTION HANDLING ────────────────────────────────────────────
If is_inconsistency_doc=true:
  For each contradiction in contradictions[]:
  - Use contradicted_value instead of the original fact value
  - Do NOT include the original correct value anywhere in this document
  - Make the contradiction feel natural (e.g., "As per the amended filing...")
  
If is_inconsistency_doc=false:
  Include all facts at their correct values.
  Never introduce information that contradicts the KG for facts not in your spec.

── NOISE CONTENT ─────────────────────────────────────────────────────
Add realistic off-KG content
This content should:
  - Be realistic for current document type
  - Not contradict or modify any KG fact
  - Not introduce new entities with the same names as KG entities
  - Represent approximately {noise_pct}% of total document content

── HTML STRUCTURE ────────────────────────────────────────────────────
Output well-formed HTML. Required elements:
  - <html lang="lang_code_here">
  - <meta charset="utf-8" />
  - <head> with <title> and basic styling
  - <body> structured with appropriate sections

Use these HTML elements where appropriate:
  <h1>, <h2>, <h3>        — document title and section headings
  <table>                 — for table-modality facts and structured data
  <p>                     — narrative paragraphs
  <dl>, <dt>, <dd>        — definition lists for key-value pairs
  <figure>                — wrapping image elements
  <img>                   — for image-modality facts (see below)
  <blockquote>            — for quoted clauses or legal text
  <footer>                — signatures, dates, issuing organization

── IMAGE TAGS ────────────────────────────────────────────────────────
For each entry in image_specs[], insert exactly:

<figure>
  <img 
    src="images/{image_id}.png"
    data-vlm-prompt="{vlm_generation_prompt}"
  />
</figure>

The data-vlm-prompt attribute will be extracted and sent to an image
generation model. Make it self-contained and precise.
The vlm_generation_prompt from the spec is your base — you may expand
it with document-specific context (date, jurisdiction, specific name variant).

── LANGUAGE ──────────────────────────────────────────────────────────
Write all document content in: {language}
Legal/technical terminology should match conventions for this language/jurisdiction.
Entity name variants are already language-appropriate as specified.

── DO NOT ────────────────────────────────────────────────────────────
- Do not use markdown (output is HTML only)
- Do not add ```html fences
- Do not include facts not listed in fact_placements[]
- Do not use canonical entity names if a variant is specified
- Do not make the document obviously synthetic (no [PLACEHOLDER] text)
- Do not explain what you are doing

Output the complete HTML document only.
