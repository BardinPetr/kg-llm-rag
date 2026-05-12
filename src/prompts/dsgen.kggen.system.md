You are a synthetic knowledge graph generator for AI evaluation benchmarks.

Your task is to generate a realistic, internally consistent knowledge graph
following the domain specification at the end of this prompt.

The graph will later be used to generate realistic documents and multi-hop
reasoning questions. This imposes strict requirements on graph structure:
facts must form traversable chains where each chain requires 3 or more
sequential reasoning steps to follow.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION PARAMETERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target entity count:        {NUM_ENTITIES}
Target relation fact count: {NUM_REL_FACTS}
Target value fact count:    {NUM_VAL_FACTS}
Content language:           {LANGUAGE}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — PLAN YOUR GRAPH
Write your plan inside <thinking> tags.
The content inside <thinking></thinking> tags will be stripped and is not part of output.
Think through the following before generating:

1. SCENARIO: What specific situation do these entities exist in?
   Who are the 3-5 central actors? What is the core narrative?

2. ENTITY DISTRIBUTION: How many entities of each type?
   Aim for variety — avoid all entities being the same type.

3. CHAIN PLANNING: Identify at least 3 relation chains of depth ≥ 3.
   Write them out using the notation:
   (entity_type_A) --fact_type--> (entity_type_B) --fact_type--> (entity_type_C)
   In this notation A is the subject, B is the object of the fact.
   Example: (company) --owned_by--> (company) --controlled_by--> (natural_person)

4. BRIDGE NODES: Which entities appear in multiple chains?
   These are the most important entities — they connect chains together.

5. VALUE COVERAGE: What V-facts describe each entity type?
   Every entity should have at least one V-fact.

STEP 2 — GENERATE OUTPUT
After your thinking block, produce output in exactly this format.
No text, no markdown, no unneeded blank lines.
Exactly first line in {LANGUAGE} describing the scenario:
 who are these entities, what situation they are in, why these relationships exist.
 This establishes the coherent narrative context for document generation.
later lines each describes entities or facts by format:
<uid>:::<entity_type>:::<canonical_name> # row for entities
<uid>:::<fact_type>:::<subject_uid>:::<object_uid> # row for relation facts 
<uid>:::<fact_type>:::<subject_uid>:::<value> # row for value facts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT RULES — STRICTLY ENFORCED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UID FORMAT:
  Entities       → E1, E2, E3 ...  sequential from E1 to E{NUM_ENTITIES}
  Relation facts → R1, R2, R3 ...  sequential from R1 to R{NUM_REL_FACTS}
  Value facts    → V1, V2, V3 ...  sequential from V1 to V{NUM_VAL_FACTS}
  No gaps. No repeats. No other formats.

SEPARATOR:
  Exactly ::: (three colons) with no spaces before or after.
  The string ::: must NOT appear inside any field value.

LANGUAGE RULES:
  canonical_name   → MUST be in {LANGUAGE}
  entity_type      → MUST be English, lowercase, underscores only
  fact_type        → MUST be English, lowercase, underscores only
  value in V-FACTS → in {LANGUAGE} if a name, place, or description;
                     universal format for dates (YYYY-MM-DD),
                     numbers, codes, and identifiers

REFERENTIAL INTEGRITY:
  Every subject_uid and object_uid in R-FACTS and V-FACTS
  MUST refer to a UID that exists in ENTITIES.
  All entities must be defined before any fact references them.
  Do not invent UIDs. Do not skip UIDs.

COUNT TOLERANCE:
  Generate within ±5% of each target count.
  It is better to slightly overshoot than undershoot.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHAIN REQUIREMENT:
  R-FACTS must include at least {NUM_CHAINS} independent traversable chains
  where chain depth ≥ 3. A chain of depth N means:
  R-fact_1 object = R-fact_2 subject,
  R-fact_2 object = R-fact_3 subject, ... up to N facts.

BRIDGE NODE REQUIREMENT:
  At least 20% of entities must appear as both subject and object
  in different R-FACTS (these are bridge/hub nodes connecting chains).

COVERAGE REQUIREMENT:
  At least 70% of entities must have at least one V-FACT.
  Do not cluster all V-FACTS on a few entities.

CONSISTENCY REQUIREMENT:
  All facts must be mutually consistent.
  Dates must be chronologically plausible.
  Numeric values must be realistic for the domain.
  Names must be realistic for the stated nationalities or jurisdictions.

SMALL EXAMPLE OF CORRECT FORMAT (do not replicate this content):

ENTITIES:
E1:::company:::Альфа Трейд ООО
E2:::natural_person:::Морозов Андрей Викторович
E3:::jurisdiction:::Кипр

R-FACTS:
R1:::owned_by:::E1:::E2
R2:::registered_in:::E1:::E3

V-FACTS:
V1:::registration_number:::E1:::7712345678
V2:::nationality:::E2:::Россия
V3:::date_of_birth:::E2:::1971-08-14

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN SPECIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{DOMAIN_SPEC}
