from datetime import date

import gradio as gr

from llm_integration import get_summary_candidate_models


MARKET_OPTIONS = ["DE", "UK", "FR"]
MONTH_OPTIONS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
YEAR_OPTIONS = [str(year) for year in range(2024, 2031)]

SECTION_OPTIONS = [
    "executive_summary",
    "market_trends",
    "platform_updates",
    "competitor_intelligence",
    "independent_artist_economy",
    "market_opportunities",
    "data_sources_used",
]


def build_report_request(
    year: str,
    month_name: str,
    markets: list[str],
    sections: list[str],
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
        "model": selected_model,
        "temperature": temperature,
    }

    print("Generated report request:", report_request)

    return report_request


def submit_report_request(
    year: str,
    month_name: str,
    markets: list[str],
    sections: list[str],
    selected_model: str,
    temperature: float,
) -> None:
    """
    Temporary submit handler so the UI remains fully interactive while the
    pipeline integration is still being developed.
    """
    build_report_request(
        year,
        month_name,
        markets,
        sections,
        selected_model,
        temperature,
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
    default_month = MONTH_OPTIONS[current_date.month - 1]

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

            generate_button = gr.Button("Generate Report")

        generate_button.click(
            fn=submit_report_request,
            inputs=[
                year_dropdown,
                month_dropdown,
                market_selector,
                section_selector,
                model_dropdown,
                temperature_slider,
            ],
            outputs=None,
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
