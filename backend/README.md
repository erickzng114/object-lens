# Object Lens backend

## Run

```
cd backend
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...        # never commit it; see ../.env.example
uvicorn app.main:app --reload
```

Then:

```
curl -X POST localhost:8000/v1/query -H 'content-type: application/json' -d '{"text": "ماگ سرامیکی سفید"}'
curl -N "localhost:8000/v1/search/<id from above>"
```

`/v1/search` streams Server-Sent Events: one `shop_results` per shop that returned products, then `ranked` (cheapest first).

## Test

```
pytest              # offline tests
pytest -m live      # hits Digikala and Torob for real (run from Iran)
python -m scripts.probe_shops "ماگ سرامیکی"
```
