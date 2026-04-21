"""
Llama Stack Showcase - HuggingFace Spaces Entry Point

This is the main entry point for the HuggingFace Spaces deployment.
It creates and launches the Gradio UI with live log streaming.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui import create_ui


def main():
    """Main entry point for the application."""
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 7860))
    
    # Create and launch the UI
    demo = create_ui()
    
    # Launch with HuggingFace Spaces compatible settings
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        theme=getattr(demo, "_theme", None),
    )


if __name__ == "__main__":
    main()
