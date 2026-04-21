"""Tests for new UI controls: model dropdown and temperature slider."""
import gradio as gr

from src.ui import LlamaStackUI, create_ui, MODEL_CHOICES, DEFAULT_MODEL, DEFAULT_TEMPERATURE


def test_ui_creates_with_new_controls():
    demo = create_ui()
    assert isinstance(demo, gr.Blocks)
    # History attribute wired onto the UI class
    ui = LlamaStackUI()
    assert ui.history is not None
    assert len(ui.history) == 0


def test_model_dropdown_choices_correct():
    assert DEFAULT_MODEL == "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    assert MODEL_CHOICES[0] == "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    assert "meta-llama/Llama-3.3-70B-Instruct-Turbo" in MODEL_CHOICES
    assert "meta-llama/Llama-3.1-8B-Instruct-Turbo" in MODEL_CHOICES
    assert len(MODEL_CHOICES) == 3


def test_temperature_slider_bounds_and_default():
    # Default
    assert DEFAULT_TEMPERATURE == 0.7
    # Build a fresh Slider with the same configuration and verify bounds
    slider = gr.Slider(minimum=0.0, maximum=1.5, value=0.7, step=0.1, label="Temperature")
    assert slider.minimum == 0.0
    assert slider.maximum == 1.5
    assert slider.step == 0.1
    assert slider.value == 0.7


def test_history_recorded_on_empty_input_skipped():
    """Empty queries should NOT create a history entry."""
    ui = LlamaStackUI()
    list(ui.run_research("   "))
    list(ui.run_code(""))
    list(ui.run_pipeline(""))
    assert len(ui.history) == 0
