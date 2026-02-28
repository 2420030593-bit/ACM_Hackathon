import time
from services.automation import _call_llm

print("Testing LLM call (should use Groq)...")
prompt = '''You are a browser automation agent. Goal: Book a cab from 'Hyderabad' to 'Airport'.
Page: Uber (https://m.uber.com/go/pickup)
Previous actions: None yet
Interactive elements:
[0] INPUT "Where to?"

Reply with ONLY a JSON object for the NEXT action:
- Click: {"action":"click","element":<num>,"reason":"why"}
- Type: {"action":"type","element":<num>,"text":"value","reason":"why"}
'''

t0 = time.time()
res = _call_llm(prompt)
elapsed = time.time() - t0

print(f"Response: {res}")
print(f"Time: {elapsed:.2f}s")
