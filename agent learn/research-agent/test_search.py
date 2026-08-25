from ddgs import DDGS

results = DDGS(timeout=15).text(
    "2026 AI Agent development trends",
    max_results=5,
    backend="bing",
)

for item in results:
    print(item)