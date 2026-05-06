# Believe Market Intelligence Report Generator

Gradio app that generates a Markdown market-intelligence report from local knowledge-base files, then supports iterative revision through user feedback.

## Quick Start (2-3 minutes)

1. Install dependencies.
2. Set `OPENAI_API_KEY` (env var or `.env` file).
3. Run `python src/main.py`.
4. Generate one report and apply one feedback iteration.
5. (Optional) Run tests with `python -m pytest -q`.

## What the App Does

- Loads markdown knowledge-base files from `knowledge_base/primary` and `knowledge_base/secondary`.
- Builds one combined context for selected sections, markets, and period.
- Builds a generation prompt from `templates/prompt_generation.json`.
- Calls OpenAI to generate report content.
- Rebuilds a feedback prompt using:
  - original generation prompt,
  - previous generated report,
  - general feedback,
  - section feedback.

## Current Behavior (Important)

- Report generation and feedback iteration are both working end-to-end.
- UI period options are static today:
  - months: `January`-`April`
  - year: `2026`
- The default month in the UI is currently hardcoded to `April`.
- The app prints compact step logs in the terminal (context build, prompt build, LLM call, preview).

## Architecture

Pipeline flow:

`src/main.py -> src/content_pipeline.py -> src/document_processor.py -> src/knowledge_base.py -> src/prompt_templates.py -> src/llm_integration.py`

File responsibilities:

- `src/main.py`: Gradio UI, request construction, feedback construction, download hooks.
- `src/content_pipeline.py`: orchestration for generation + feedback pipeline.
- `src/document_processor.py`: markdown KB loading/parsing.
- `src/knowledge_base.py`: context selection/assembly by section, date, market.
- `src/prompt_templates.py`: prompt template loading/formatting.
- `src/llm_integration.py`: OpenAI model discovery + generation + token/cost tracking.
- `templates/prompt_generation.json`: prompt templates (`market_analysis`, `feedback_prompt`).

## Setup

Prerequisites:

- Python 3.10+
- OpenAI API key

Install:

```bash
pip install -r requirements.txt
```

Or with repo-local Conda Python:

```bash
./.conda/bin/python -m pip install -r requirements.txt
```

Set API key (shell):

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Or create `.env` in repo root:

```env
OPENAI_API_KEY=your_api_key_here
```

Run:

```bash
python src/main.py
```

Or:

```bash
./.conda/bin/python src/main.py
```

## Usage

Generate report:

1. Pick period, markets, sections, depth, audience, style, model, temperature.
2. Click `Generate Report`.
3. Review:
   - `Pipeline Status`
   - `Generated Report`
   - `Original Report Request JSON`
   - `Content Pipeline JSON`
4. Optional: click `Download Report as .md`.

Apply feedback:

1. Add `General Feedback` and optional section-specific feedback.
2. Click `Apply Feedback`.
3. Review:
   - `Iterate Status`
   - `Revised Report`
   - `Iterate JSON`
4. Optional: click `Download Revised Report as .md`.

## Section and Market Mapping

Sections:

- `market_trends` -> `market_trends`
- `platform_updates` -> `platform_updates`
- `competitor_intelligence` -> `competition`
- `independent_artist_economy` -> `artist_economy`
- `market_opportunities` -> `opportunities`

Markets:

- `DE` -> `Germany`
- `UK` -> `UK`
- `FR` -> `France`

Date key used in KB lookup:

- `YYYY Month` (example: `2026 March`)

## Testing and Validation

Run tests:

```bash
python -m pytest -q
```

Or:

```bash
./.conda/bin/python -m pytest -q
```

Quick sanity checks:

```bash
python -m py_compile src/*.py
python -c "import json; json.load(open('templates/prompt_generation.json', encoding='utf-8'))"
```

## Troubleshooting

- `OPENAI_API_KEY is not set`
  - Set env var or `.env`, then restart.
- Date/market/section key issues
  - Confirm selected values exist in KB and mappings in `src/content_pipeline.py`.
- Feedback appears ignored
  - Check `Iterate JSON` and use explicit instructions (example: `Replace X with Y`).

## Known Limitations

- Period options are static in UI (`January`-`April`, `2026`).
- Knowledge-base parsing assumes consistent markdown heading hierarchy.
- OpenAI-only provider integration.

## Minimal Roadmap

- Derive months/years dynamically from KB metadata.
- Add deterministic post-processing for explicit replacement feedback.
- Expand integration tests for pipeline + mocked LLM.
