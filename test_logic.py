import requests

# Test cases
tests = [
    "do",    # Should find recipes with 'domates' (Menemen, etc.) - Valid start
    "avuc",  # Should NOT find 'havuç' (Mercimek Corbas) - Invalid start
]

for q in tests:
    try:
        url = f'http://127.0.0.1:5000/api/search?q={q}'
        response = requests.get(url)
        data = response.json()
        print(f"Query: '{q}' -> Found {len(data)} recipes")
        for r in data:
            print(f" - {r['name']}")
    except Exception as e:
        print(f"Error testing '{q}': {e}")
