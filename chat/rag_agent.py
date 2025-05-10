import os
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
from chat.models import Message  # adjust import if needed


# Load env variables
load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# import Django settings for BASE_DIR
from django.conf import settings

# Path setup based on BASE_DIR
BASE = settings.BASE_DIR / "PanduOne_Resources"
VECTOR_INDEX_PATH = BASE / "Chunks/pdf_index.faiss"
CHUNKS_PATH = BASE / "FAISS/doc_chunks.txt"
RULES_PATH = BASE / "rules.txt"

TOP_K = 8

class RAGConversationalAgent:
    def __init__(self, api_key, vector_index_path, chunks_path, rules_path, top_k=TOP_K):
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.vector_index = faiss.read_index(str(vector_index_path))
        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks = f.readlines()

        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel(model_name="gemini-2.0-pro-exp")

        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = f.read().strip()

        self.top_k = top_k
        # self.history = []

    def chat(self, user_prompt, chat_session=None):

        # 🧠 1. Combine recent conversation history
        history_str = ""
        if chat_session:
            recent_messages = (
                Message.objects
                .filter(chat=chat_session, sender__in=["patient", "bot"])
                .order_by("timestamp")
            )

            history_lines = []
            for msg in recent_messages:
                role = "User" if msg.sender == "patient" else "Assistant"
                history_lines.append(f"{role}: {msg.content}")

            history_str = "\n".join(history_lines)

        # 📦 2. Create embedding
        combined_text = f"{history_str}\n{user_prompt}" if history_str else user_prompt
        vector = self.embed_model.encode([combined_text])

        # 📚 3. Retrieve top-k context
        D, I = self.vector_index.search(vector, k=self.top_k)
        context_chunks = []
        for i in I[0]:
            line = self.chunks[i].strip()
            if "\t" in line:
                filename, chunk = line.split("\t", 1)
                context_chunks.append(f"[{filename}]: {chunk}")
            else:
                context_chunks.append(line)

        context_str = "\n".join(context_chunks)

        # 🧾 4. Build the final prompt
        prompt = (
            f"{self.rules}\n\n"
            f"Context:\n{context_str}\n\n"
            f"Conversation:\n{history_str}\n"
            f"User: {user_prompt}"
        )

        # 🤖 5. Generate Gemini response
        response = self.genai_model.generate_content(prompt).text

        return response


# Export single instance (like a service)
try:
    rag_agent = RAGConversationalAgent(
        api_key=GENAI_API_KEY,
        vector_index_path=VECTOR_INDEX_PATH,
        chunks_path=CHUNKS_PATH,
        rules_path=RULES_PATH
    )
except Exception as e:
    rag_agent = None
    print(f"[❌ RAG Init Error] {e}")