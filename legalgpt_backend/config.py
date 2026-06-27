# import os
# from dataclasses import dataclass


# @dataclass(frozen=True)
# class Settings:
#     groq_api_key: str = os.getenv("GROQ_API_KEY", "")
#     groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
#     app_name: str = "LegalGPT"
#     max_context_chars: int = 14000


# settings = Settings()
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    app_name: str = "LegalGPT"
    max_context_chars: int = 14000

settings = Settings()