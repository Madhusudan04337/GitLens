import asyncio
from main import generate_card, GenerateRequest

async def debug_test():
    try:
        req = GenerateRequest(username="torvalds")
        print("Starting generate_card debug test...")
        result = await generate_card(req)
        print("Success!", result)
    except Exception as e:
        print("Caught Error:", e)

if __name__ == "__main__":
    asyncio.run(debug_test())
