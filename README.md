# Depth Map

A reflective-questioning tool in two parts. Depth asks specific, open questions and analyzes each answer. Map, which isn't built yet, will track the themes that recur across answers and link each one back to the entries it came from.

## Run it

Needs Python 3.11+ and an Anthropic API key.

```bash
python -m venv .venv
source .venv/bin/activate             # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=your-key     # PowerShell: $env:ANTHROPIC_API_KEY = "your-key"
python -m depthmap
```

It asks one question at a time until you type `q`. The next question is always the one you've answered least in this run, and ties go to whichever comes first in `src/depthmap/data/questions.json`. Pass `--question-id desire-01` (or any other id in that file) to start with a different question.

The key can also go in a `.env` file at the repo root. Without a key, or with `DEPTHMAP_PROVIDER=fake`, it runs offline on a fake provider that builds its reply from your answer; the first line it prints says which provider is active. `DEPTHMAP_MODEL` picks the model.
