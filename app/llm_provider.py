"""
LLM Provider abstraction for supporting multiple models (Ollama, Gemini, etc).
"""
import requests
from abc import ABC, abstractmethod
from app.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider (local)."""
    
    def __init__(self):
        """Initialize Ollama provider."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 300
    
    def generate(self, prompt: str) -> str:
        """Generate text using Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama timeout após {self.timeout}s. Tente um modelo menor ou aumente o timeout.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Não conseguiu conectar ao Ollama em {self.base_url}. Inicie com: ollama serve")
        except Exception as e:
            raise Exception(f"Erro ao chamar Ollama: {e}")


class GeminiProvider(LLMProvider):
    """Gemini LLM provider (remoto via Google API)."""
    
    def __init__(self):
        """Initialize Gemini provider."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada no .env")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = settings.GEMINI_MODEL
        except ImportError:
            raise ImportError(
                "google-genai não instalado. "
                "Execute: pip install google-genai"
            )
    
    def generate(self, prompt: str) -> str:
        """Generate text using Gemini."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Erro ao chamar Gemini: {e}")


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.
    
    Returns:
        LLMProvider: Uma instância do provider configurado (Ollama ou Gemini)
        
    Raises:
        ValueError: Se o provider não é suportado
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        return OllamaProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(
            f"LLM_PROVIDER '{provider}' desconhecido. "
            f"Use 'ollama' ou 'gemini'"
        )
