from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def transform_content(self, content: str, source_platform: str, target_platform: str) -> str:
        prompt = f"""
        Transform the following {source_platform} content to be suitable for {target_platform}.
        Maintain the core message while adapting to the target platform's style and constraints.
        
        Content: {content}
        
        Target Platform: {target_platform}
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a social media expert who transforms content between platforms while maintaining the core message."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content 