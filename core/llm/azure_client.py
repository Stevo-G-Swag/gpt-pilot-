"""
AzureClient module integrates with Azure's OpenAI service, handling API interactions
and configurations specific to the Azure deployment.
"""

from httpx import Timeout
from openai import AsyncAzureOpenAI

from core.config import LLMProvider
from core.llm.openai_client import OpenAIClient
from core.log import get_logger

log = get_logger(__name__)


class AzureClient(OpenAIClient):
    """
    AzureClient integrates with Azure's OpenAI service, handling API interactions
    and configurations specific to the Azure deployment.
    """
    provider = LLMProvider.AZURE
    stream_options = None
    def _init_client(self):
        extra: dict = self.config.extra or {}
        azure_deployment = extra.get("azure_deployment")
        api_version = extra.get("api_version")

        if self.config.base_url is None:
            raise ValueError("Azure endpoint URL (base_url) is not set")

        print(f"Using Azure API key: {self.config.api_key}")  # New line added
        self.client = AsyncAzureOpenAI(
            api_key=self.config.api_key,
            azure_endpoint=self.config.base_url,
            azure_deployment=azure_deployment,
            api_version=api_version,
            timeout=Timeout(
                max(self.config.connect_timeout, self.config.read_timeout),
                connect=self.config.connect_timeout,
                read=self.config.read_timeout,
            ),
        )
