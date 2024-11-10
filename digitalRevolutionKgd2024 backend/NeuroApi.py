import os
from openai import OpenAI

client = OpenAI(
    api_key=f"{os.getenv('PROXY_API_KEY', default='sk-M7qrVHSqQ8jrddL1srsXTon9oZAlIRFq')}",
    base_url="https://api.proxyapi.ru/openai/v1"
)

def sendRequest(prompt: str) -> str:
    answer = ""

    # Define the system message
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            prompt
        )
    }

    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_message, user_message],
        max_tokens=5000
    )

    return chat_completion.choices[0].message.content.strip()

print(sendRequest("расскажи факт про кошек"))