# Depth Map

A reflective-questioning tool in two parts. Depth asks specific, open questions and analyzes each answer. Map, which isn't built yet, will track the themes that recur across answers and link each one back to the entries it came from.

## Run it

Needs Python 3.11+. An Anthropic API key is optional.

```bash
python -m venv .venv
source .venv/bin/activate             # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=your-key     # PowerShell: $env:ANTHROPIC_API_KEY = "your-key"
python -m depthmap
```

It asks one question at a time until you type `q`, each one after a framing sentence. Entries are saved in `depthmap.db`, a SQLite file in the folder you run it from (`DEPTHMAP_DB_PATH` moves it), so they are still there the next time you start it. The next question is the one you've answered least among those the rules allow: never two `disclosure` questions in a row, never two from the same domain in a row, and none marked `clinician_gated`. Ties go to whichever comes first in `src/depthmap/data/questions.v2.json`. Pass `--question-id well-01` (or any other id in that file) to start with a different question.

The key can also go in a `.env` file in the folder you run it from. Without a key, or with `DEPTHMAP_PROVIDER=fake`, it runs offline on a fake provider that builds its reply from your answer; the first line it prints says which provider is active. `DEPTHMAP_MODEL` picks the model. `DEPTHMAP_QUESTION_BANK=v1` switches back to the first bank in `questions.json`, which has no framing sentences and only the least-answered rule.

The same loop is available over HTTP:

```bash
uvicorn depthmap.api:app
```

`GET /questions/next` returns the next question (add `?client_id=...` to pick for another client), `POST /entries` takes `{"question_id": "...", "response": "..."}` and returns the stored entry with its analysis, and `GET /entries` lists entries newest first. The interactive docs are at `http://127.0.0.1:8000/docs`. The server reads and writes the same `depthmap.db`.
