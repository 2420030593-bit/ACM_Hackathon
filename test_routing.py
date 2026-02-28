import asyncio
from services.llm_brain import process_with_llm

async def run_test():
    result = await process_with_llm("I want to get a bus ticket to vijaywada")
    print("----- RESULTS -----")
    print(f"Intent: {result.get('intent')}")
    print(f"Entities: {result.get('entities')}")
    print(f"All Intents: {result.get('all_intents')}")

if __name__ == "__main__":
    asyncio.run(run_test())
