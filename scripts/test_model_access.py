#!/usr/bin/env python3
"""
Test gpt-oss-20b and gpt-oss-120b access via Groq.

Usage:
    GROQ_API_KEY=your_key uv run python scripts/test_model_access.py
"""
import asyncio
import os
import sys
import time

try:
    from groq import AsyncGroq
except ImportError:
    print("❌ groq not installed. Run: uv sync")
    sys.exit(1)


MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

PROMPT = "Say exactly: 'gpt-oss is working!' — nothing else."


async def test_model(client: AsyncGroq, model: str) -> dict:
    print(f"\n🔄 Testing {model}...")
    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=32,
        )
        elapsed = time.time() - start
        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens
        tps = tokens / elapsed if elapsed > 0 else 0
        print(f"  ✅ Response: {content!r}")
        print(f"  ⚡ {tokens} tokens in {elapsed:.2f}s ({tps:.0f} tps)")
        return {"model": model, "status": "ok", "content": content, "tps": tps}
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"model": model, "status": "error", "error": str(e)}


async def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("❌ GROQ_API_KEY not set. Get one at https://console.groq.com")
        sys.exit(1)

    print("🚀 Testing gpt-oss model access via Groq")
    print(f"   API key: {api_key[:8]}...")

    client = AsyncGroq(api_key=api_key)
    results = []
    for model in MODELS:
        result = await test_model(client, model)
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 Summary:")
    for r in results:
        status = "✅" if r["status"] == "ok" else "❌"
        print(f"  {status} {r['model']}: {r.get('tps', 0):.0f} tps")

    all_ok = all(r["status"] == "ok" for r in results)
    if all_ok:
        print("\n✅ All models accessible! Ready to build.")
    else:
        print("\n⚠️  Some models failed. Check your GROQ_API_KEY and quota.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
