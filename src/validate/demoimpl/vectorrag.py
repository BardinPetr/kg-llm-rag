from pathlib import Path
from textwrap import dedent
from typing import List

from langchain_core.globals import set_llm_cache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_docling.loader import DoclingLoader
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.aimodel import load_llm_lc
from utils.file import do_hash
from db.store.cacheservice import cache_iget, cache_iput
from validate.demoimpl.testsuite import RAGTestSuite


embeddings = load_llm_lc("test-embeddings")
llm = load_llm_lc("test-llm")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

prompt = PromptTemplate(
    template=dedent("""
        Human: You are an AI assistant, and provides answers to questions by using fact based and statistical information when possible.
        Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        <context>
        {context}
        </context>
        
        <question>
        {question}
        </question>
        
        The response should be specific and use statistics or numbers when possible.
        
        Assistant:
    """),
    input_variables=["context", "question"]
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class VectorRAG(RAGTestSuite):

    def __init__(self):
        self.retriever = None

    async def load(self, documents: List[Path]):
        paths = [str(i) for i in documents]
        doc_hash = self.batch_hash(documents)
        if (documents := cache_iget(doc_hash, "test-vector-rag")) is None:
            documents = DoclingLoader(file_path=paths).load_and_split(text_splitter)
            cache_iput(doc_hash, documents, "test-vector-rag")
        vectorstore = Milvus.from_documents(
            documents=documents,
            embedding=embeddings,
            connection_args=dict(uri="./milvus_demo.db"),
            drop_old=False
        )
        self.retriever = vectorstore.as_retriever(k=10)

    async def ask(self, question: str) -> str:
        rag_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
        )
        return rag_chain.invoke(question)
