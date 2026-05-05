# Believe Market Intelligence Report Generator

Gradio application that generates a Markdown market-intelligence report from local knowledge-base markdown files, then supports iterative revision through user feedback.

## What It Does

- Ingests markdown files from `knowledge_base/primary` and `knowledge_base/secondary`.
- Builds one combined context string based on selected sections, markets, and period.
- Generates a report prompt from `templates/prompt_generation.json`.
- Calls OpenAI to generate report content.
- Applies feedback by rebuilding a feedback prompt with:
  - the original generation prompt,
  - the previous generated content,
  - general feedback,
  - section-specific feedback.

## Current Status

- Generation flow is connected end-to-end.
- Feedback iteration flow is connected end-to-end.
- Report and revised report are rendered as Markdown in document-style panels.
- Available months/years are currently static in UI (`January`-`April`, `2026`).

## Architecture

Pipeline flow:

`main.py` -> `content_pipeline.py` -> `document_processor.py` -> `knowledge_base.py` -> `prompt_templates.py` -> `llm_integration.py`

File responsibilities:

- `src/main.py`: Gradio UI and request/feedback payload construction.
- `src/content_pipeline.py`: Orchestration for initial generation and feedback iteration.
- `src/document_processor.py`: Reads and parses KB markdown into nested dictionaries.
- `src/knowledge_base.py`: Selects and concatenates context for requested sections.
- `src/prompt_templates.py`: Loads JSON templates and injects prompt variables.
- `src/llm_integration.py`: OpenAI model discovery, generation, and usage/cost accounting.
- `templates/prompt_generation.json`: Main generation and feedback prompt templates.

## Knowledge Base Layout

Expected structure:

- `knowledge_base/primary`
  - `believe_company_profile.md`
  - `believe_competitive_positioning.md`
  - `believe_strategic_priorities.md`
  - `believe_report_template.md`
- `knowledge_base/secondary`
  - `market_trends_DE_UK_FR.md`
  - `platform_policy_updates.md`
  - `streaming_platforms_landscape.md`
  - `competitor_intelligence.md`
  - `independent_music_industry.md`

## Section and Market Mapping

UI section keys -> internal KB keys:

- `market_trends` -> `market_trends`
- `platform_updates` -> `platform_updates`
- `competitor_intelligence` -> `competition`
- `independent_artist_economy` -> `artist_economy`
- `market_opportunities` -> `opportunities`

UI market codes -> internal KB labels:

- `DE` -> `Germany`
- `UK` -> `UK`
- `FR` -> `France`

Date key passed to KB:

- Format: `YYYY Month` (example: `2026 March`)

## Setup

Prerequisites:

- Python 3.10+ recommended
- OpenAI API key

Install:

```bash
pip install -r requirements.txt
```

Environment:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Run:

```bash
python src/main.py
```

## Usage

Generate report:

- Select period, markets, sections, report depth, audience, style, model, and temperature.
- Click `Generate Report`.
- Review:
  - `Pipeline Status`
  - `Generated Report`
  - `Content Pipeline JSON`

Apply feedback:

- Add `General Feedback` and optional per-section feedback.
- Optionally change model/temperature/report settings before feedback pass.
- Click `Apply Feedback`.
- Review:
  - `Iterate Status`
  - `Revised Report`
  - `Iterate JSON`

## Prompt Inputs

Main prompt (`market_analysis`) currently injects:

- `combined_context`
- `report_depth`
- `audience`
- `style_desc`
- `length_instruction`

Feedback prompt (`feedback_prompt`) currently injects:

- `original_prompt`
- `generated_content`
- `general_feedback`
- `section_feedback_block`
- `section_scope`
- `report_depth`
- `audience`
- `style_desc`
- `length_instruction`

## Output Payloads

`generate_report(...)` returns:

- `report.full_text`
- `report.word_count`
- `prompt`
- `combined_context`
- `llm_response`
- `metadata` (sections, markets, period, model, temperature, token/cost data)

`iterate_report(...)` returns:

- `report.full_text` (revised)
- `feedback_prompt`
- `llm_response`
- `metadata` (feedback, model, temperature, token/cost data)

## Troubleshooting

- `OPENAI_API_KEY is not set`:
  - Export env var before running.
- Key errors for date/market/section:
  - Verify UI selection exists in KB content.
  - Verify mapping keys in `content_pipeline.py`.
- Feedback seems ignored:
  - Check `Iterate JSON` to confirm feedback payload fields are populated.
  - Use explicit replacement wording in feedback (example: `Replace Spotify with spotifoo`).

## Testing and Validation

Current lightweight validation:

- Source compile check:
  - `python3 -m py_compile src/*.py`
- Prompt JSON validity:
  - `python3 -c "import json; json.load(open('templates/prompt_generation.json'))"`

## Roadmap

- Derive available report periods dynamically from KB metadata.
- Add deterministic post-processing for explicit replacement feedback rules.
- Add automated tests for:
  - markdown structure and date presence/format,
  - pipeline input validation,
  - integration happy path.
- Optional export automation to Notion.
