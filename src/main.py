import json
from datetime import date

import gradio as gr

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
    "short: 200-300 words",
    "standard: 500-700 words",
    "detailed: 2500-3000 words",
]
AUDIENCE_OPTIONS = [
    "strategy",
    "artist_solutions",
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
    """
    Build the report-generation request object from the Gradio inputs.

    For now this returns the structured payload so the UI contract is aligned
    with the future content_pipeline.py integration.
    """
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

    print("Generated report request:", report_request, flush=True)

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
    """
    Submit the report request to the real content pipeline.
    """
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
            f"Report generation failed: {exc}",
            json.dumps(report_request, indent=2),
            "",
            "",
        )

    status_message = (
        "Report generated through the content pipeline. "
        f"Sections: {pipeline_response['metadata'].get('sections_generated', 0)}."
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
    general_feedback_text: str,
    *section_feedback_values: str,
) -> tuple[str, str, str]:
    """
    Send the generated report, original inputs, and user feedback to the
    iterate stage in content_pipeline.py.
    """
    if not generated_report_text.strip():
        return (
            "WARNING: Generate the mock report before applying feedback.",
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

    original_inputs = json.loads(report_request_json)
    feedback_parts = []

    if general_feedback_text:
        feedback_parts.append(f"General feedback:\n{general_feedback_text}")

    for section_name, feedback_text in section_feedback.items():
        feedback_parts.append(
            f"Section feedback for {section_name}:\n{feedback_text}"
        )

    feedback_scope = "full_report"
    feedback_target_section = ""
    if len(section_feedback) == 1 and not general_feedback_text:
        feedback_scope = "single_section"
        feedback_target_section = next(iter(section_feedback))

    feedback_request = {
        "original_report_text": generated_report_text,
        "original_inputs": original_inputs,
        "feedback_text": "\n\n".join(feedback_parts),
        "scope": feedback_scope,
        "target_section": feedback_target_section,
        "general_feedback": general_feedback_text,
        "section_feedback": section_feedback,
    }

    print("Generated feedback request:", feedback_request, flush=True)

    try:
        revised_response = iterate_report(feedback_request)
    except Exception as exc:
        return (
            f"Feedback iteration failed: {exc}",
            "",
            "",
        )

    status_message = "Feedback applied through the iterate pipeline."

    return (
        status_message,
        revised_response["report"]["full_text"],
        json.dumps(revised_response, indent=2),
    )


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
    """
    Launch the Gradio UI for selecting report-generation inputs.

    Current purpose:
    - Fetch models suitable for text generation
    - Collect report metadata and section selection
    - Prepare the UI contract for the pipeline layer
    """
    models = get_summary_candidate_models()
    default_model = models[0] if models else None
    current_date = date.today()
    default_year = str(current_date.year)
    default_month = "April" # ToDO read dynamically based on current_date.month

    with gr.Blocks() as demo:
        gr.Markdown("# Believe Market Intelligence Report Generator")
        gr.Markdown(
            "Choose the report month, markets, sections, and LLM settings."
        )

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

            market_selector = gr.CheckboxGroup(
                choices=MARKET_OPTIONS,
                value=MARKET_OPTIONS,
                label="Markets",
                info="Select one or more markets to include in the report.",
                interactive=True,
            )

            with gr.Row():
                select_all_button = gr.Button("Select All", size="sm")
                deselect_all_button = gr.Button("Deselect All", size="sm")

            section_selector = gr.CheckboxGroup(
                choices=SECTION_OPTIONS,
                value=SECTION_OPTIONS,
                label="Report Sections",
                info="Select one, several, or all sections.",
                interactive=True,
            )

            with gr.Row():
                report_depth_dropdown = gr.Dropdown(
                    choices=REPORT_DEPTH_OPTIONS,
                    value="standard: 500-700 words",
                    label="Report Depth",
                    info="Controls the intended output length and level of detail.",
                    interactive=True,
                )

                audience_dropdown = gr.Dropdown(
                    choices=AUDIENCE_OPTIONS,
                    value="strategy",
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

            generate_button = gr.Button("Generate Report")

        warning_output = gr.Textbox(
            label="Pipeline Status",
            interactive=False,
        )
        report_request_output = gr.Code(
            label="Original Report Request JSON",
            language="json",
            interactive=False,
        )
        report_output = gr.Textbox(
            label="Generated Report",
            lines=24,
            max_lines=40,
            interactive=False,
        )
        json_output = gr.Code(
            label="Content Pipeline JSON",
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

            apply_feedback_button = gr.Button("Apply Feedback")

        feedback_warning_output = gr.Textbox(
            label="Iterate Status",
            interactive=False,
        )
        revised_report_output = gr.Textbox(
            label="Revised Report",
            lines=24,
            max_lines=40,
            interactive=False,
        )
        revised_json_output = gr.Code(
            label="Iterate JSON",
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
                general_feedback_textbox,
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

    demo.launch()


if __name__ == "__main__":
    main()
