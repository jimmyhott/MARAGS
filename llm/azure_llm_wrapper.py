class AzureLLMWrapper:
    def __init__(self, client, deployment):
        self.client = client
        self.deployment = deployment

    def invoke(self, prompt):
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}]
        )
        # Extract the text response (for OpenAI client >= 1.0.0)
        return response.choices[0].message.content
