# llm_providers/openai_provider.py
import os
from openai import OpenAI

class OpenAIProvider:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_embedding(self, text):
        resp = self.client.embeddings.create(model="text-embedding-3-large", input=text)
        return resp.data[0].embedding

    def generate_text(self, prompt):
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return resp.choices[0].message.content
