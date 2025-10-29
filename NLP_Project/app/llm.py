import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class Ollama:
    def __init__(self):
        self.url = os.getenv('OLLAMA_URL')
        self.model = os.getenv('OLLAMA_MODEL')
    
    async def run(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Ollama returned error: {error_text}",
                        headers=response.headers
                    )
    
    async def clean_text(self, text: str) -> str:
        prompt = f"""
        You are a text cleaning assistant.
        Clean the following legal text by:
        - Removing headers, footers, page numbers, repeated dashes, underscores or bullet points
        - Removing irrelevant formatting, and text from other language than english
        - Keeping meaningful legal content intact
        - Preserving sections, subsections, clauses, and punctuation
        - remove any text which seems out of context from the given point
        - just return the cleaned text without any additional commentary

        Return as a single paragraph, without any new line characters.

        Text:
        {text}
        """
        return await self.run(prompt)


ollama_client = Ollama() 
