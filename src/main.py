"""Gradio UI for report generation and feedback-based iteration."""

import json
from datetime import date

import gradio as gr
import tempfile

from content_pipeline import generate_report, iterate_report
from llm_integration import get_summary_candidate_models


MARKET_OPTIONS = ["DE", "UK", "FR"]

MONTH_OPTIONS = [
    "January",
    "February",
    "March",
    "April",
]

YEAR_OPTIONS = ["2026"]

REPORT_DEPTH_OPTIONS = [
    "standard: 500-700 words",
    "short: 200-300 words",
    "detailed: 2500-3000 words",
]

AUDIENCE_OPTIONS = [
    "casual music fan",
    "fan with industry knowledge",
    "artist manager",
    "artist",
    "executive",
]

SECTION_OPTIONS = [
    "market_trends",
    "platform_updates",
    "competitor_intelligence",
    "independent_artist_economy",
    "market_opportunities"
]

STYLES = {
    "thought_leadership": "insightful, expert-level, opinionated",
    "storytelling": "emotional, narrative-driven, engaging",
    "educational": "clear, structured, value-driven",
    "contrarian": "challenging assumptions, bold perspective",
    "minimalist": "concise, sharp, high-signal"
}

DOCUMENT_FRAME_CSS = """
.report-document {
  border: 1px solid #d5d9e0;
  border-radius: 10px;
  background: #ffffff;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
  max-height: 640px;
  overflow-y: auto;
}

/* Disable inner scrolling from Gradio */
.report-document .prose {
  max-height: none !important;
  overflow: visible !important;
}

.report-document p,
.report-document li {
  line-height: 1.7;
}

.orange-btn {
    background-color: darkorange !important;
    color: white !important;
    border: none !important;
}

.orange-btn:hover {
    background-color: orange !important;
}
"""


def build_report_request(
    year: str,
    month_name: str,
    markets: list[str],
    sections: list[str],
    report_depth: str,
    audience: str,
    style: str,
    selected_model: str,
    temperature: float,
) -> dict[str, object]:
    """Build the report-generation payload from current UI values."""
    report_request = {
        "month": month_name,
        "year": year,
        "report_period": f"{month_name} {year}",
        "markets": markets,
        "sections": sections,
        "report_depth": report_depth,
        "audience": audience,
        "style": style,
        "model": selected_model,
        "temperature": temperature,
    }

    return report_request


def submit_report_request(
    year: str,
    month_name: str,
    markets: list[str],
    sections: list[str],
    report_depth: str,
    audience: str,
    style: str,
    selected_model: str,
    temperature: float,
) -> tuple[str, str, str, str]:
    """Generate a report and return status, request JSON, markdown, and payload."""
    report_request = build_report_request(
        year,
        month_name,
        markets,
        sections,
        report_depth,
        audience,
        style,
        selected_model,
        temperature,
    )

    try:
        pipeline_response = generate_report(report_request)
    except Exception as exc:
        return (
            f"Report generation failed ({type(exc).__name__}): {exc}",
            json.dumps(report_request, indent=2),
            "",
            "",
        )

    status_message = (
        "Report generated through the content pipeline and LLM integration. "
        f"Model: {pipeline_response['metadata'].get('model_used', 'unknown')}."
    )

    return (
        status_message,
        json.dumps(report_request, indent=2),
        pipeline_response["report"]["full_text"],
        json.dumps(pipeline_response, indent=2),
    )


def submit_feedback_request(
    generated_report_text: str,
    report_request_json: str,
    pipeline_response_json: str,
    general_feedback_text: str,
    report_depth: str,
    audience: str,
    style: str,
    selected_model: str,
    temperature: float,
    *section_feedback_values: str,
) -> tuple[str, str, str]:
    """Run feedback iteration and return status, revised markdown, and payload."""
    if not generated_report_text.strip():
        return (
            "WARNING: Generate the report before applying feedback.",
            "",
            "",
        )

    section_feedback = {
        section_name: feedback_text.strip()
        for section_name, feedback_text in zip(
            SECTION_OPTIONS, section_feedback_values
        )
        if feedback_text.strip()
    }

    general_feedback_text = general_feedback_text.strip()

    if not general_feedback_text and not section_feedback:
        return (
            "WARNING: Enter feedback before applying the iterate step.",
            "",
            "",
        )

    try:
        original_inputs = json.loads(report_request_json)
        pipeline_response = json.loads(pipeline_response_json)
    except (json.JSONDecodeError, TypeError) as exc:
        return (
            f"Feedback iteration failed ({type(exc).__name__}): "
            f"invalid feedback JSON payload: {exc}",
            "",
            "",
        )
    # Reuse the exact prompt from the first generation pass for revision context.
    original_prompt = str(
        pipeline_response.get("prompt", {}).get("prompt", "")
    )
    feedback_parts = []

    if general_feedback_text:
        feedback_parts.append(f"General feedback:\n{general_feedback_text}")

    for section_name, feedback_text in section_feedback.items():
        feedback_parts.append(
            f"Section feedback for {section_name}:\n{feedback_text}"
        )

    feedback_request = {
        "original_report_text": generated_report_text,
        "original_prompt": original_prompt,
        "original_inputs": original_inputs,
        "feedback_text": "\n\n".join(feedback_parts),
        "general_feedback": general_feedback_text,
        "section_feedback": section_feedback,
        "report_depth": report_depth,
        "audience": audience,
        "style": style,
        "model": selected_model,
        "temperature": temperature,
    }

    try:
        revised_response = iterate_report(feedback_request)
    except Exception as exc:
        return (
            f"Feedback iteration failed ({type(exc).__name__}): {exc}",
            "",
            "",
        )

    status_message = (
        "Feedback applied through the iterate pipeline and LLM integration. "
        f"Model: {revised_response['metadata'].get('model_used', 'unknown')}."
    )

    return (
        status_message,
        revised_response["report"]["full_text"],
        json.dumps(revised_response, indent=2),
    )


def prepare_report_download(report_text: str) -> str:
    """Prepare the report text for download as a Markdown file."""
    if not report_text.strip():
        raise ValueError("No report content available to download.")
    
    # Create a temporary file with the report content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write(report_text)
        temp_file_path = temp_file.name
    
    return temp_file_path


def select_all_sections() -> list[str]:
    """
    Select every report section in the checkbox group.
    """
    return SECTION_OPTIONS


def deselect_all_sections() -> list[str]:
    """
    Clear every report section in the checkbox group.
    """
    return []


def get_style_preview(style_key: str) -> str:
    """
    Return the description for the selected style key.
    """
    style_description = STYLES.get(style_key, "")
    return f"**Style Description:** {style_description}"


def get_section_label(section_name: str) -> str:
    """
    Convert a section key into a readable label.
    """
    return section_name.replace("_", " ").title()


def main():
    """Launch the Gradio app for generation + feedback workflows."""
    models = get_summary_candidate_models()
    default_model = models[0] if models else None
    current_date = date.today()
    default_year = str(current_date.year)
    default_month = "April" # ToDO read dynamically based on current_date.month

    with gr.Blocks(css=DOCUMENT_FRAME_CSS) as demo:
        gr.Markdown("# Believe Market Intelligence Report Generator")
        gr.Markdown("This application generates customized market intelligence reports on the independent music industry using a local knowledge base.\n\n" \
        "The UI allows users to configure report generation by selecting a time period, target markets, the sections in the report, report length, target audience, and writing style.\n\n" \
        "Users can also choose the OpenAI model, adjust temperature for creativity control, download generated reports, and iteratively refine reports through general and section-specific feedback.")
        # gr.Markdown(
        #     "# Choose the report month, markets, sections, and LLM settings."
        # )

        with gr.Group():
            gr.Markdown("## LLM Configuration")

            model_dropdown = gr.Dropdown(
                choices=models,
                value=default_model,
                label="Model",
                info="Only models suitable for text generation are shown.",
                interactive=True,
            )

            temperature_slider = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                step=0.1,
                value=0.3,
                label="Temperature",
                info="Lower = more deterministic. Higher = more creative.",
                interactive=True,
            )

        with gr.Group():
            gr.Markdown("## Report Settings")

            with gr.Row():
                year_dropdown = gr.Dropdown(
                    choices=YEAR_OPTIONS,
                    value=default_year,
                    label="Year",
                    info="Initialized to the current year.",
                    interactive=True,
                )

                month_dropdown = gr.Dropdown(
                    choices=MONTH_OPTIONS,
                    value=default_month,
                    label="Month",
                    info="Initialized to the current month.",
                    interactive=True,
                )     

            section_selector = gr.CheckboxGroup(
                choices=SECTION_OPTIONS,
                value=SECTION_OPTIONS,
                label="Report Sections",
                info="Select one, several, or all sections.",
                interactive=True,
            )

            with gr.Row():
                select_all_button = gr.Button("Select All Sections", size="sm")
                deselect_all_button = gr.Button("Deselect All", size="sm")

            market_selector = gr.CheckboxGroup(
                choices=MARKET_OPTIONS,
                value=MARKET_OPTIONS,
                label="Markets",
                info="Select one or more countries to include in reports about market trends.",
                interactive=True,
            )

            with gr.Row():
                report_depth_dropdown = gr.Dropdown(
                    choices=REPORT_DEPTH_OPTIONS,
                    value=REPORT_DEPTH_OPTIONS[0],
                    label="Report Depth",
                    info="Controls the intended output length and level of detail.",
                    interactive=True,
                )

                audience_dropdown = gr.Dropdown(
                    choices=AUDIENCE_OPTIONS,
                    value=AUDIENCE_OPTIONS[0],
                    label="Audience",
                    info="Controls the framing of the output for the target reader.",
                    interactive=True,
                )

            style_selector = gr.Radio(
                choices=list(STYLES.keys()),
                value="thought_leadership",
                label="Report Style",
                info="Choose one writing style for the report output.",
                interactive=True,
            )
            style_preview = gr.Markdown(
                get_style_preview("thought_leadership")
            )

            generate_button = gr.Button("Generate Report", elem_classes="orange-btn")

        warning_output = gr.Textbox(
            label="Pipeline Status",
            interactive=False,
        )
        with gr.Accordion("Original Report Request JSON (click to expand/collapse)", open=False):
            report_request_output = gr.Code(
                language="json",
                interactive=False,
            )
        report_output = gr.Markdown(
            label="Generated Report",
            elem_classes=["report-document"],
        )
        
        # Download components for the report
        download_file = gr.File(label="Download Report", interactive=False, scale=0)
        download_button = gr.Button("Download Report as .md", elem_classes="orange-btn")
        
        with gr.Accordion("Content Pipeline JSON (click to expand/collapse)", open=False):
            json_output = gr.Code(
                language="json",
                interactive=False,
            )

        with gr.Group():
            gr.Markdown("## Iterate / Feedback")
            gr.Markdown(
                "Add general feedback for the whole report and optional "
                "section-specific feedback where needed."
            )

            general_feedback_textbox = gr.Textbox(
                label="General Feedback",
                lines=4,
                placeholder="Example: Make every section a bit longer and more data-driven.",
                interactive=True,
            )

            section_feedback_boxes = []
            for section_name in SECTION_OPTIONS:
                feedback_box = gr.Textbox(
                    label=f"{get_section_label(section_name)} Feedback",
                    lines=3,
                    placeholder=(
                        f"Optional feedback for {get_section_label(section_name)}."
                    ),
                    interactive=True,
                )
                section_feedback_boxes.append(feedback_box)

            apply_feedback_button = gr.Button("Apply Feedback", elem_classes="orange-btn")

        feedback_warning_output = gr.Textbox(
            label="Iterate Status",
            interactive=False,
        )
        revised_report_output = gr.Markdown(
            label="Revised Report",
            elem_classes=["report-document"],
        )
        with gr.Accordion("Iterate JSON (click to expand/collapse)", open=False):
            revised_json_output = gr.Code(
                language="json",
                interactive=False,
            )

        generate_button.click(
            fn=submit_report_request,
            inputs=[
                year_dropdown,
                month_dropdown,
                market_selector,
                section_selector,
                report_depth_dropdown,
                audience_dropdown,
                style_selector,
                model_dropdown,
                temperature_slider,
            ],
            outputs=[
                warning_output,
                report_request_output,
                report_output,
                json_output,
            ],
        )

        style_selector.change(
            fn=get_style_preview,
            inputs=style_selector,
            outputs=style_preview,
        )

        apply_feedback_button.click(
            fn=submit_feedback_request,
            inputs=[
                report_output,
                report_request_output,
                json_output,
                general_feedback_textbox,
                report_depth_dropdown,
                audience_dropdown,
                style_selector,
                model_dropdown,
                temperature_slider,
                *section_feedback_boxes,
            ],
            outputs=[
                feedback_warning_output,
                revised_report_output,
                revised_json_output,
            ],
        )

        select_all_button.click(
            fn=select_all_sections,
            inputs=None,
            outputs=section_selector,
        )

        deselect_all_button.click(
            fn=deselect_all_sections,
            inputs=None,
            outputs=section_selector,
        )

        download_button.click(
            fn=prepare_report_download,
            inputs=[report_output],
            outputs=[download_file],
        )

    demo.launch()


if __name__ == "__main__":
    main()
