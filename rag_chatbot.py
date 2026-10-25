import os
import json
import hashlib
from dataclasses import asdict, is_dataclass

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

load_dotenv()


class RAGChatbot:

    def __init__(self, top_k=5):

        self.top_k = top_k
        self.vectorstore = None
        self.retriever = None
        self.state_hash = None

        # 1. Embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 2. OpenAI LLM
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key or not model:
            raise ValueError(
                "Set OPENAI_API_KEY and OPENAI_MODEL in your .env file"
            )

        llm_config = {
            "model": model,
            "api_key": api_key,
            "temperature": 0.2,
        }

        if base_url:
            llm_config["base_url"] = base_url

        self.llm = ChatOpenAI(**llm_config)

        # 3. Document splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )

        # 4. Rewrite follow-up questions using chat history
        self.rewrite_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Rewrite the user's latest question as a standalone "
                "question using conversation history when needed. "
                "Preserve Jira issue keys exactly. Do not answer "
                "the question."
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{question}"),
        ])

        self.rewrite_chain = (
            self.rewrite_prompt
            | self.llm
            | StrOutputParser()
        )

        # 5. Final RAG prompt
        self.rag_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an AI Scrum Master assistant. "
                "Answer using the retrieved AgentState context. "
                "Do not invent Jira issues, statuses, metrics, "
                "team members, or recommendations. "
                "If the answer is not supported by the context, "
                "clearly state that the available data is insufficient. "
                "Use chat history to understand follow-up questions, "
                "but do not treat earlier assistant answers as proof "
                "of sprint facts. Cite source identifiers when useful.\n\n"
                "Retrieved context:\n{context}"
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{question}"),
        ])

        self.rag_chain = (
            self.rag_prompt
            | self.llm
            | StrOutputParser()
        )

    # ==================================================
    # 1. AGENTSTATE -> DOCUMENTS
    # ==================================================

    def _build_documents(self, state):

        if is_dataclass(state) and not isinstance(state, type):
            state_data = asdict(state)
        elif hasattr(state, "model_dump"):
            state_data = state.model_dump()
        elif isinstance(state, dict):
            state_data = state
        else:
            state_data = vars(state)

        documents = []

        # Create a document for each state section.
        # The report field is excluded because AgentState itself
        # should be the knowledge source, not a generated report.
        for key, value in state_data.items():

            if key in ("issues", "report"):
                continue

            if value is None or value == "" or value == [] or value == {}:
                continue

            documents.append(
                Document(
                    page_content=(
                        f"{key.replace('_', ' ').title()}:\n"
                        f"{json.dumps(value, indent=2, default=str)}"
                    ),
                    metadata={
                        "source": f"AgentState.{key}"
                    },
                )
            )

        # Create a separate document for every Jira issue.
        for issue in state_data.get("issues", []):

            issue_key = issue.get("key", "Unknown")

            documents.append(
                Document(
                    page_content=(
                        f"Jira Issue: {issue_key}\n"
                        f"{json.dumps(issue, indent=2, default=str)}"
                    ),
                    metadata={
                        "source": f"AgentState.issue.{issue_key}",
                        "issue_key": issue_key,
                    },
                )
            )

        return documents

    # ==================================================
    # 2. DOCUMENTS -> CHUNKS -> FAISS VECTOR STORE
    # ==================================================

    def _build_vectorstore(self, state):

        documents = self._build_documents(state)

        if not documents:
            self.vectorstore = None
            self.retriever = None
            self.state_hash = None
            return

        # Check whether the source state has changed.
        state_content = json.dumps(
            [doc.model_dump() for doc in documents],
            sort_keys=True,
            default=str,
        )

        current_hash = hashlib.sha256(
            state_content.encode("utf-8")
        ).hexdigest()

        # Reuse existing vectors if the state has not changed.
        if (
            self.vectorstore is not None
            and current_hash == self.state_hash
        ):
            return

        # Split documents into smaller chunks.
        chunks = self.text_splitter.split_documents(documents)

        # VECTOR DATABASE: FAISS
        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings,
        )

        # Save the index locally.
        self.vectorstore.save_local("faiss_index")

        # Retrieve the three most similar chunks.
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )

        self.state_hash = current_hash

    # ==================================================
    # 3. CHAT HISTORY
    # ==================================================

    @staticmethod
    def _format_history(history):

        messages = []

        for item in (history or [])[-8:]:

            if not isinstance(item, dict):
                continue

            content = item.get("content", "")
            role = item.get("role")

            if not content:
                continue

            if role == "user":
                messages.append(HumanMessage(content=str(content)))

            elif role == "assistant":
                messages.append(AIMessage(content=str(content)))

        return messages

    # ==================================================
    # 4. USER QUERY -> VECTOR SEARCH -> TOP 3 CHUNKS
    # ==================================================

    def answer(self, state, question, history=None):

        question = question.strip()

        if not question:
            return "Please enter a question about the sprint."

        try:
            # Build or reuse the vector store.
            self._build_vectorstore(state)

            if self.retriever is None:
                return "No usable information was found in AgentState."

            # Prepare recent conversation history.
            chat_history = self._format_history(history)

            # Rewrite follow-up questions before retrieval.
            search_query = question

            if chat_history:
                search_query = self.rewrite_chain.invoke({
                    "chat_history": chat_history,
                    "question": question,
                })

            # LangChain embeds the query and searches FAISS.
            # Only the top 3 relevant chunks are retrieved.
            retrieved_docs = self.retriever.invoke(search_query)

            if not retrieved_docs:
                return "No relevant information was retrieved."

            # Prepare retrieved context for OpenAI.
            context = "\n\n".join(
                (
                    f"Source: {doc.metadata.get('source', 'AgentState')}\n"
                    f"{doc.page_content}"
                )
                for doc in retrieved_docs
            )

            # Generate the final response through LangChain.
            response = self.rag_chain.invoke({
                "context": context,
                "question": question,
                "chat_history": chat_history,
            })

            # Show the answer and the sources used.
            sources = list(dict.fromkeys(
                doc.metadata.get("source", "AgentState")
                for doc in retrieved_docs
            ))

            return (
                f"{response}\n\n"
                f"Sources: {', '.join(sources)}"
            )

        except Exception as exc:
            return (
                "RAG processing failed. Check your dependencies, "
                "embedding model, and LLM configuration. "
                f"Error: {type(exc).__name__}: {exc}"
            )