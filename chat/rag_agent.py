import os

import faiss
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from chat.models import Message  # adjust import if needed

from .profiles import PATIENT_PROFILES

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
    def __init__(
        self, api_key, vector_index_path, chunks_path, rules_path, top_k=TOP_K
    ):
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.vector_index = faiss.read_index(str(vector_index_path))
        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks = f.readlines()

        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")

        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = f.read().strip()

        self.top_k = top_k
        # self.history = []

    def chat(self, user_prompt, chat_session=None):
        N_TURNS = 4  # to limit the context

        # 🧠 1. Combine recent conversation history
        history_str = ""
        if chat_session:
            recent_messages = list(
                Message.objects.filter(
                    chat=chat_session, sender__in=["patient", "bot"]
                ).order_by("timestamp")
            )

            if len(recent_messages) > (N_TURNS * 2):

                history_cut = recent_messages[:-1]

                history = history_cut[-(N_TURNS * 2) :]
            elif len(recent_messages) > 1:
                history = recent_messages[:-1]
            else:
                history = []

            history_lines = []
            for msg in history:
                role = "User" if msg.sender == "patient" else "Assistant"
                history_lines.append(f"{role}: {msg.content}")

            history_str = "\n".join(history_lines)

        # 📄 2. Add patient profile context
        profile_context = ""
        if chat_session:
            patient_id = chat_session.patient_id  # e.g. 'patient_arif'
            profile_data = PATIENT_PROFILES.get(patient_id)
            if profile_data:
                profile_context = profile_data.get("profile_context", "")

        # 📦 3. Create embedding (for context retrieval)
        combined_text = f"{history_str}\n{user_prompt}" if history_str else user_prompt
        vector = self.embed_model.encode([combined_text])

        # 📚 4. Retrieve top-k context
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

        # 🧾 5. Build the final prompt
        prompt = (
            f"{self.rules}\n\n"
            f"---\n"
            f"Patient Profile:\n{profile_context}\n\n"
            f"---\n"
            f"Relevant Information:\n{context_str}\n\n"
            f"---\n"
            f"Conversation History:\n{history_str}\n\n"
            f"---\n"
            f"User Prompt:\n{user_prompt}"
        )

        # print(prompt)

        # 🤖 6. Generate Gemini response
        response = self.genai_model.generate_content(prompt).text

        return response


# Export single instance (like a service)
try:
    rag_agent = RAGConversationalAgent(
        api_key=GENAI_API_KEY,
        vector_index_path=VECTOR_INDEX_PATH,
        chunks_path=CHUNKS_PATH,
        rules_path=RULES_PATH,
    )
except Exception as e:
    rag_agent = None
    print(f"[❌ RAG Init Error] {e}")
