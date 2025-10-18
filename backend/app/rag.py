import os
import random
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .utils import ensure_dir
from .security import sanitize_text, is_in_domain

load_dotenv()

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./storage/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

SYSTEM_PROMPT = (
    "You are an expert vehicle IoT diagnostics assistant. "
    "Analyze logs and device telemetry to detect anomalies, explain possible causes, and suggest actions. "
    "Only answer about motor vehicle IoT, sensors, telemetry, DTC codes, and related diagnostics."
)

class RAGAgent:
    def __init__(self):
        ensure_dir(VECTOR_DB_PATH)
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        # lazy initialize vector store if path exists
        self.vs = Chroma(persist_directory=VECTOR_DB_PATH, embedding_function=self.embeddings)
        self.llm = ChatOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            model=OPENROUTER_MODEL,
            temperature=0.2,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "IoT Diagnostics Agent",
            },
        )
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)

    # ---------- Synthetic dataset generation ----------
    def build_and_ingest_synthetic_dataset(self, n: int = 300) -> int:
        docs = self._generate_synthetic_vehicle_dataset(n)
        chunks: List[Document] = []
        for d in docs:
            for ch in self.splitter.split_text(d):
                chunks.append(Document(page_content=ch, metadata={"source": "synthetic"}))
        if chunks:
            self.vs.add_documents(chunks)
            self.vs.persist()
        return len(chunks)

    def _generate_synthetic_vehicle_dataset(self, n: int) -> List[str]:
        vehicles = [f"VIN{1000+i:05d}" for i in range(80)]
        engines = ["I4", "V6", "V8", "Electric"]
        fuels = ["gasoline", "diesel", "electric"]
        statuses = []
        for i in range(n):
            vin = random.choice(vehicles)
            engine = random.choice(engines)
            fuel = random.choice(fuels)
            rpm = random.randint(650, 5200)
            coolant = random.randint(70, 115)
            oil = random.randint(20, 120)
            voltage = round(random.uniform(11.5, 14.8), 2)
            speed = random.randint(0, 160)
            dtc = random.choice([
                "P0300 random/multiple cylinder misfire detected",
                "P0420 catalyst system efficiency below threshold",
                "U0100 lost communication with ECM/PCM",
                "B0001 driver airbag deployed",
                "C0035 left front wheel speed sensor",
                "NONE",
            ])
            note = random.choice([
                "No anomalies detected. Heartbeat normal.",
                "Intermittent misfire observed under load.",
                "Catalyst efficiency trending low; monitor.",
                "Wheel speed sensor noisy; ABS alerts possible.",
                "Battery voltage low at idle; alternator check recommended.",
            ])
            text = (
                f"Vehicle {vin} with {engine} engine ({fuel}) reports telemetry:\n"
                f"RPM={rpm}; Coolant={coolant}C; OilPressure={oil}kPa; Voltage={voltage}V; Speed={speed}km/h.\n"
                f"Active DTC: {dtc}. {note}\n"
                f"If misfire persists, inspect spark plugs, coils, fuel trims, and compression."
            )
            statuses.append(text)
        return statuses

    # ---------- Sample log generation ----------
    def generate_sample_logs(self, count: int = 5) -> List[Dict[str, Any]]:
        items = []
        for i in range(count):
            log = (
                f"[log-{i}] RPM={random.randint(700, 4800)} Coolant={random.randint(75, 110)}C "
                f"Voltage={round(random.uniform(11.8, 14.5),2)}V Speed={random.randint(0,120)}km/h "
                f"DTC={random.choice(['NONE','P0301','P0420','C0035'])}"
            )
            items.append({"filename": f"sample_{i}.txt", "content": log})
        return items

    # ---------- Answering ----------
    def answer(self, question: str, context_docs: List[str] | None = None) -> str:
        # Guardrails pre-retrieval
        q = sanitize_text(question)
        if not is_in_domain(q):
            return (
                "Your query seems outside vehicle IoT diagnostics. Provide motor vehicle IoT logs or status questions."
            )

        retrieved = []
        if self.vs is not None:
            retr = self.vs.as_retriever(search_kwargs={"k": 6})
            retrieved_docs = retr.get_relevant_documents(q)
            for d in retrieved_docs:
                retrieved.append(d.page_content)

        # Include uploaded context (sanitized and filtered)
        if context_docs:
            for c in context_docs:
                c2 = sanitize_text(c)
                if is_in_domain(c2):
                    for ch in self.splitter.split_text(c2):
                        retrieved.append(ch)

        # Guardrails on retrieved content
        filtered = [r for r in retrieved if is_in_domain(r)]

        prompt = self._compose_prompt(q, filtered)

        try:
            resp = self.llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            answer = resp.content if hasattr(resp, "content") else str(resp)
        except Exception as e:
            answer = f"LLM error: {e}"

        # Post-generation guardrails: remove hallucinated instructions
        answer = sanitize_text(answer)
        if not is_in_domain(answer):
            return (
                "The generated content went out of scope. Please provide specific vehicle logs or metrics (RPM, temp, DTC)."
            )
        return answer

    def _compose_prompt(self, question: str, contexts: List[str]) -> str:
        context_text = "\n---\n".join(contexts[:12]) if contexts else ""
        guide = (
            "Task: Analyze vehicle IoT logs and status to detect anomalies, explain causes, and suggest next actions.\n"
            "- Flag abnormal ranges (e.g., coolant > 105C, low voltage < 12V at idle, misfire DTCs).\n"
            "- Explain likely root causes and confidence.\n"
            "- Provide safety implications and recommended diagnostics.\n"
            "- If input is unrelated, politely refuse and ask for relevant logs.\n"
            "Return: Clear bullet points with Status, Anomalies, Explanations, and Recommended Actions."
        )
        return f"{guide}\n\nContext from knowledge base and uploaded logs:\n{context_text}\n\nUser question or logs:\n{question}\n\nAnswer:"
