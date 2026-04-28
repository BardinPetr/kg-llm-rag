i am working for system that analyzes documents using uses knowledge graph with hybrid rag. 
the system takes different documents like pdf.
the task is to do Beneficial Owner identification, company ownership structure investigating and sanction checking.

i want to have some test documents (2 docs) that i would use for checking.data should be better in russian. 
i want to confirm that my system can merge diverse data from different documents into single navigable knowledge base (i am working now on entity and fact disambiguation/merging)

so i want that these docs represent one system with companies, people, stakes and so on, but split into different self-sufficient docs each should cover some parts of situation (with intersections and duplicates).
there should be (in all docs in total) 2-3 companies, 3-7 persons.
there should be different types and combinations of links between them.
also add supplementary entities and information to enrich graph. 

output only documents.
also there should be description of what was generated for me to read and understand,  also describe your concept in terms of entities and relationships.
it must contain sections:
- short description what was those docs about
- what to check when doing verification of results
- entities must be found, each with its facts
- relations between entities that must be found

all in russian, except entity types and other code-like things.

YOU MUST ENSURE THAT KG WOULD NOT GET LARGE, MAKE DOCS VERY SHORT
DOCUMENTS COUNT SHOULD BE EXACTLY = 2


output format:

@DOC:0:`docuement_name_here`
<content here>
@END:0

@DOC:1:`docuement_name_here`
<content here>
@END:1

@DESC
<here description>
@END:DESC
