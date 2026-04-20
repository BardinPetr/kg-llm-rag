i am working for system that analyzes documents using uses knowledge graph with hybrid rag. 
the system takes different documents like pdf.
the task is to do Beneficial Owner identification, company ownership structure investigating and sanction checking.

i want to have some test documents (5 docs) that i would use for checking.data should be better in russian. 
i want to confirm that my system can merge diverse data from different documents into single navigable knowledge base (i am working now on entity and fact disambiguation/merging)

so i want that these docs represent one system with companies, people, stakes and so on, but split into different self-sufficient docs each should cover some parts of situation (with intersections and duplicates).
there should be 3-7 companies, 3-7 persons.
there should be different types and combinations of links between them.
also add suplementary entities and information to enrich graph. 

output only documents.
the last document (not from those 5) should be description of what was generated for me to read and understand,  also describe your concept in terms of entities and relationships.

format:

!DOC 0: <name>
<content here>
!END 0

!DOC 1: <name>
<content here>
!END 1
