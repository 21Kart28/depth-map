# Depth Map

A reflective-questioning tool in two parts. Depth asks specific, open questions and analyzes each answer; Map tracks the themes that recur across answers and links each one back to the entries it came from.

## Run it

Needs Python 3.11+ and an Anthropic API key.

```bash
python -m venv .venv
source .venv/bin/activate             # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key     # PowerShell: $env:ANTHROPIC_API_KEY = "your-key"
python depthmap.py
```

It asks the first question in `questions.json`. Pass `--question-id desire-01` (or any other id in that file) to answer a different one.
