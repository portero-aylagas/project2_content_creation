import gradio as gr

from llm_integration import get_summary_candidate_models


def save_model_settings(selected_model: str, temperature: float) -> str:
    """
    Receive the model and temperature selected in the Gradio UI.

    Args:
        selected_model:
            Model ID selected by the user.

        temperature:
            Temperature selected by the user.

    Returns:
        Confirmation text shown in the UI.

    Notes:
        This function does not call the LLM.
        It only receives the selected values so they are available to main.py.
        Later, these values can be passed to the real content-generation workflow.
    """
    # Keep the selected values together in one dictionary.
    # This can later be passed to another function, stored, or reused by the app.
    selected_settings = {
        "model": selected_model,
        "temperature": temperature,
    }

    # For now, print the values in the terminal so you can verify they arrived.
    print("Selected LLM settings:", selected_settings)

    # Return a visible confirmation to the Gradio UI.
    return (
        f"Selected model: {selected_model}\n"
        f"Selected temperature: {temperature}"
    )


def main():
    """
    Launch the local Gradio UI for selecting LLM settings.

    Current purpose:
        - Fetch models suitable for text editing/summarization
        - Let the user select one model
        - Let the user select a temperature
        - Make those values available inside main.py

    This does not run any LLM generation yet.
    """
    # Fetch only models that make sense for text editing/summarization.
    models = get_summary_candidate_models()

    # Avoid crashing if no usable model is found.
    default_model = models[0] if models else None

    with gr.Blocks() as demo:
        gr.Markdown("# LLM Settings")

        # Dropdown receives the model list generated from the user's OpenAI key.
        model_dropdown = gr.Dropdown(
            choices=models,
            value=default_model,
            label="Model",
            info="Only models suitable for text editing and summarization are shown.",
        )

        # Slider passes a float value to save_model_settings().
        # Gradio Slider inputs are passed to the function as float values. :contentReference[oaicite:0]{index=0}
        temperature_slider = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            step=0.1,
            value=0.3,
            label="Temperature",
            info="Lower = more deterministic. Higher = more creative.",
        )

        output_box = gr.Textbox(
            label="Selected settings",
            lines=3,
        )

        save_button = gr.Button("Save settings")

        # When clicked, Gradio sends the current dropdown and slider values
        # into save_model_settings(). Button click events are the standard
        # way to trigger functions in Gradio Blocks. :contentReference[oaicite:1]{index=1}
        save_button.click(
            fn=save_model_settings,
            inputs=[model_dropdown, temperature_slider],
            outputs=output_box,
        )

    # Launch the app locally.
    demo.launch()


if __name__ == "__main__":
    main()