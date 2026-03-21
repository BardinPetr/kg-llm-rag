from typing import Optional, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from ray import serve
from ray.serve.handle import DeploymentHandle

from src.document.docling.docling_processor import PDFProcessorDocling
from document.model.model import DocumentTables
from src.utils.aimodel import load_llm_lc


def _create_chain(llm):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an expert at analyzing and merging HTML tables from document parsing.

Your task:
1. Analyze two HTML representations of the same document
2. Identify tables that span multiple pages (split tables with similar headers/structure)
3. Merge split tables into complete, coherent tables
4. Extract ONLY the tables, removing all other content
5. Preserve table structure, headers, and data integrity

Rules:
- Merge tables with identical or very similar headers
- Maintain chronological/logical order when merging
- Remove duplicate headers from merged tables
- Keep only <table> elements with their content
- Output valid HTML with proper table structure
- If tables conflict, prefer the more complete version
- Preserve all data, don't summarize or truncate

Output format: Clean HTML document containing only <table> elements."""),
        ("human", """
Document representations to analyze:

{outputs}

Analyze both representations, merge split tables, and output HTML with ONLY the merged tables.
""")
    ])
    return prompt | llm | StrOutputParser()


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class DocumentTableProcessor:
    def __init__(self, docling: DeploymentHandle[PDFProcessorDocling]):
        self._docling = docling
        self._llm = load_llm_lc("gemini3")
        self._chain = _create_chain(self._llm)

    async def __call__(self, preprocessed_html: List[str]) -> Optional[DocumentTables]:
        outputs = "".join([f"===OUTPUT_{i}===\n{v}\n===END_OUTPUT_{i}\n" for i, v in enumerate(preprocessed_html)])
        try:
            result_html = self._chain.invoke(dict(outputs=outputs))
        except Exception as e:
            print(f"Error extracting tables {e}")
            result_html = preprocessed_html[0]

        result_html = result_html.replace("```html", "").replace("```", "").strip()
        res = await self._docling.load_html.remote(result_html)
        return DocumentTables(doc=res)
