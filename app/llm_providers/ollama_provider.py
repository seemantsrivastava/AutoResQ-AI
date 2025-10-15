# llm_providers/ollama_provider.py
import os, requests

class OllamaProvider:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def get_embedding(self, text):
        payload = {"model": "nomic-embed-text", "input": text}
        resp = requests.post("http://localhost:11434/api/embeddings", json=payload)
        return resp.json()["embedding"]

    def generate_text(self, prompt):
        payload = {"model": self.model, "prompt": prompt}
        resp = requests.post("http://localhost:11434/api/generate", json=payload, stream=False)
        return resp.json().get("response", "")
