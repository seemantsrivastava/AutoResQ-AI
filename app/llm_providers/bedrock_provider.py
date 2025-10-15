# llm_providers/bedrock_provider.py
import boto3, os, json

class BedrockProvider:
    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-west-2"))

    def get_embedding(self, text):
        body = json.dumps({"inputText": text})
        resp = self.client.invoke_model(modelId="amazon.titan-embed-text-v2:0", body=body)
        result = json.loads(resp["body"].read())
        return result["embedding"]

    def generate_text(self, prompt):
        body = json.dumps({"inputText": prompt, "temperature": 0.3})
        resp = self.client.invoke_model(modelId="amazon.titan-text-express-v1", body=body)
        result = json.loads(resp["body"].read())
        return result["results"][0]["outputText"]
