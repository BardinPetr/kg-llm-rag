from utils.prompt import serialize_parameter

Q_PROMPTS = {}

Q_PROMPTS["q_base"] = """
You generate benchmark evaluation questions for a knowledge-graph RAG system.
These questions will be asked to the system verbatim to measure its retrieval and reasoning quality.

LANGUAGE
========
{language}
Write ALL questions and answers in {language}.
Questions must sound exactly as a real business analyst, compliance officer,
or legal professional would phrase them in {language}. Avoid academic language.

KNOWLEDGE GRAPH
===============
{kg_json}

DOCUMENT CORPUS AVAILABLE TO THE RAG SYSTEM
============================================
{plan_summary}

GOLDEN DATA RULES
=================
golden_entity_uids
  UIDs of KG entities the question is fundamentally about or requires.

golden_fact_uids
  UIDs of value/relation facts from the KG that must be used to answer.
  For irresolvable questions this list is empty.

atoms
  Decompose the full answer into the smallest independently verifiable claims.
  Each atom is a single statement that can be checked YES/NO against a system response.
  mode=extracted  → claim corresponds directly to a fact in a document
  mode=synthesis  → claim requires combining facts or applying reasoning not explicit in any document
  Cover every meaningful piece of information in the answer.
  Do NOT make atoms redundant with each other.
""".strip()

# ──

Q_PROMPTS["q_n_hop"] = """
TASK
====
Generate {count} information retrieval questions that each require exactly {n} hop(s)
through the knowledge graph to answer.

WHAT IS AN N-HOP QUESTION
==========================
A {n}-hop question starts from a named entity and asks about something reachable
only by traversing {n} linked facts/relations.
  1-hop: "In which country is [entity] registered?" — one fact lookup
  2-hop: "Who is the director of the company that owns [entity]?" — follow ownership, then find director
  3-hop: "Is the beneficial owner of [entity] subject to any international sanctions?" — chain through owner

RULES
=====
1. Choose a path of exactly {n} connected facts/relations in the KG.
2. The question names only the STARTING entity. Intermediate entities are NOT mentioned.
3. Each question must start from a different entity or use a different path.
4. The question must be impossible to answer without traversing all {n} steps.
5. Phrase as a realistic compliance / due-diligence / business question.

ATOMS
=====
Include one atom per traversal step (the entity or value discovered at that step): mode=synthesis.
Include one atom for the final answer: mode=synthesis if derived by chaining, extracted if a direct fact.
""".strip()

# ──

Q_PROMPTS["q_fan_in"] = """
TASK
====
Generate {count} exhaustive information retrieval questions, each asking for a
comprehensive summary of everything known about a single entity.

WHAT IS A FAN-IN QUESTION
==========================
A fan-in question asks the system to gather ALL facts and relationships of an entity
in one structured response — testing whether the system exhausts its knowledge
rather than stopping at the first match.
The question specifies the dimensions of interest so the system knows what to collect.

RULES
=====
1. Choose entities with several value facts AND several relations in the KG.
2. Frame as a practical briefing or due-diligence request specifying dimensions:
   registration data, financial figures, affiliated persons, legal status, etc.
3. Each question must cover a different entity.
4. The question should NOT be answerable by looking up a single fact.

ATOMS
=====
One atom per value fact of the entity: mode=extracted.
One atom per relationship the entity participates in: mode=extracted.
At least one synthesis atom summarising a structural pattern
(e.g. "Entity X is affiliated with N companies through the following roles"): mode=synthesis.
""".strip()

# ──

Q_PROMPTS["q_bridge"] = """
TASK
====
Generate {count} connection-analysis questions asking how two entities are related,
where the relationship passes through one or more intermediate entities.

WHAT IS A BRIDGE QUESTION
==========================
A bridge question names two entities and asks the system to find and explain
their connection. The system must traverse intermediate entities autonomously —
intermediates are NOT mentioned in the question.

RULES
=====
1. Choose pairs connected through at least 2 intermediate steps.
2. Do NOT name intermediate entities in the question.
3. Vary the relationship types used (ownership, control, employment, family, etc.).
4. Include at least one question where the connection is non-obvious
   (e.g. indirect through multiple relation types).
5. Phrase as: "How is [X] connected to [Y]?",
   "What relationship, if any, exists between [X] and [Y]?",
   "Does [X] have any business ties to [Y]?"

ATOMS
=====
One atom per step in the discovered path: mode=synthesis.
One atom describing the overall nature of the connection: mode=synthesis.
""".strip()

# ──

Q_PROMPTS["q_subgraph"] = """
TASK
====
Generate {count} structural analysis questions asking the system to map out
the full relationship structure around an entity.

WHAT IS A SUBGRAPH QUESTION
============================
A subgraph question asks for a comprehensive structural picture:
ownership chains, control relationships, affiliated entities, hierarchies.
The answer is a structured description, not a single fact.
The system must traverse multiple outgoing and incoming paths from a hub entity.

RULES
=====
1. Choose entities that are hubs — they have many relations in the KG.
2. Specify the structural dimensions: ownership, management, subsidiaries, beneficiaries, etc.
3. The question should make it clear that a complete picture is expected, not one path.
4. Phrase as: "Map the ownership structure of [entity]",
   "Describe the full corporate group around [entity]",
   "Who controls [entity] and what does [entity] control?"

ATOMS
=====
One atom per entity in the local subgraph: mode=extracted for direct relations, synthesis for discovered ones.
One atom per distinct relation type present: mode=extracted.
One atom summarising the structural pattern (depth, branching, control concentration): mode=synthesis.
""".strip()

# ──

Q_PROMPTS["q_inconsistency"] = """
TASK
====
Generate {count} fact-retrieval question(s) targeting facts that exist in conflicting
versions across documents in the corpus.

CONTRADICTED FACTS IN THE CORPUS
=================================
{contradictions_json}

WHAT IS AN INCONSISTENCY QUESTION
==================================
The question naturally leads to a fact that is stated differently in two documents.
A correct system response must: (1) surface both versions, (2) identify the conflict,
(3) resolve it by reasoning about document authority, date, or source reliability.

RULES
=====
1. Generate exactly one question per contradicted fact listed above.
2. Do NOT hint that a contradiction exists — phrase as a normal factual question.
3. The answer MUST acknowledge both values and explain the resolution.
4. Use the entity's name as it appears most prominently in the corpus.

ATOMS
=====
Atom: the original value and its source document — mode=extracted.
Atom: the contradicting value and its source document — mode=extracted.
Atom: "The documents contain conflicting information about [fact]" — mode=synthesis.
Atom: the resolution and its justification — mode=synthesis.
""".strip()

# ──

Q_PROMPTS["q_irresolvable"] = """
TASK
====
Generate {count} trap questions that CANNOT be answered from the available documents,
even through deduction or induction.

WHAT IS AN IRRESOLVABLE QUESTION
==================================
These questions look identical to legitimate 1-2 hop questions but ask about
information that simply does not exist in the corpus.
A correct system response is: acknowledge the absence of information explicitly.
An incorrect response (hallucination) is: fabricate a plausible but unsupported answer.

THREE VARIANTS — distribute across them
========================================
VARIANT A — nonexistent entity
  Ask about an entity that is plausible for the domain but NOT in the KG.
  Use a realistic name that could belong in this domain.
  golden_entity_uids and golden_fact_uids are empty.

VARIANT B — missing fact about existing entity
  Name a real KG entity but ask for a fact type not present in the KG for it.
  Example: entity exists but no revenue data, no address, no registration number in KG.
  golden_entity_uids contains the real entity UID. golden_fact_uids is empty.

VARIANT C — nonexistent relationship between existing entities
  Name two real KG entities and ask about a specific relationship they do NOT have.
  golden_entity_uids contains both real UIDs. golden_fact_uids is empty.

RULES
=====
1. Questions must be indistinguishable from real questions in style and phrasing.
2. Do NOT use obviously invented names. Use names realistic for the domain and language.
3. Variant B/C: use exact canonical names of real KG entities.
4. Variant A: invent a plausible entity name not present in the KG.

ANSWER
======
"The requested information is not available in the provided documents."
Followed by what was searched and what was found to be absent.

ATOMS
=====
Atom: "The information requested is not present in any available document" — mode=synthesis.
For Variant B/C: atom noting which entity exists but which fact is absent — mode=synthesis.
""".strip()


def fmt_q_ppt(name, **kwargs):
    txt = Q_PROMPTS[name]
    for k, v in kwargs.items():
        txt = txt.replace(f"{{{k}}}", serialize_parameter(v))
    return txt
