from llm.azure_llm_wrapper import AzureLLMWrapper
from openai import AzureOpenAI

from llm.azure_secrets import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT


def get_azure_llm():

    subscription_key = AZURE_OPENAI_API_KEY
    endpoint = AZURE_OPENAI_ENDPOINT
    deployment = "gpt-4o-mini"
    api_version = "2024-12-01-preview"

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    return AzureLLMWrapper(client, deployment)





