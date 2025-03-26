import os
import uuid
import gradio as gr
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_notebooklm.processor import podcast_processor
from local_notebooklm.steps.helpers import LengthType, FormatType, StyleType

def process_podcast(pdf_file, config_file, format_type, length, style, language, additional_preference, output_dir):
    """
    Process the podcast generation based on user inputs
    """
    if pdf_file is None:
        return "Please upload a PDF file first.", None, "", ""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # In Gradio, pdf_file is a file path, not the file content
        if hasattr(pdf_file, 'name'):  # For UploadFile objects
            # For newer Gradio versions
            pdf_path = pdf_file.name
        else:
            # For older Gradio versions or direct file paths
            pdf_path = pdf_file
        
        # Use the provided config file or default
        if config_file is None:
            config_path = "/Users/gokdenizgulmez/Desktop/Local-NotebookLM/example_config.json"
        else:
            if hasattr(config_file, 'name'):
                config_path = config_file.name
            else:
                config_path = config_file
        
        # Call the podcast processor with the file paths
        success, result = podcast_processor(
            pdf_path=pdf_path,
            config_path=config_path,
            format_type=format_type,
            length=length,
            style=style,
            preference=additional_preference if additional_preference else None,
            output_dir=output_dir,
            language=language
        )
        
        if success:
            # Get paths to generated files
            podcast_audio_path = os.path.join(output_dir, "podcast.wav")
            
            # Read content of text files for display
            file_contents = {}
            generated_files = [
                "step1/extracted_text.txt",
                "step1/clean_extracted_text.txt",
                "step2/data.pkl",
                "step3/podcast_ready_data.pkl"
            ]
            
            for file in generated_files:
                full_path = os.path.join(output_dir, file)
                if os.path.exists(full_path) and file.endswith(".txt"):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            file_contents[file] = file_content[:1000] + "..." if len(file_content) > 1000 else file_content
                    except Exception as e:
                        file_contents[file] = f"Error reading file: {str(e)}"
            
            # Return the audio file path and success message
            return "Podcast Generated Successfully!", podcast_audio_path, file_contents.get("step1/extracted_text.txt", ""), file_contents.get("step1/clean_extracted_text.txt", "")
        else:
            return f"Failed to generate podcast: {result}", None, "", ""
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"An error occurred: {str(e)}\n\nDetails:\n{error_details}", None, "", ""

def create_gradio_ui():
    """
    Create a Gradio web UI for Local-NotebookLM
    """
    # Convert the Literal types to lists for Gradio dropdowns
    format_options = list(FormatType.__args__) if hasattr(FormatType, '__args__') else ["podcast"]
    length_options = list(LengthType.__args__) if hasattr(LengthType, '__args__') else ["medium"]
    style_options = list(StyleType.__args__) if hasattr(StyleType, '__args__') else ["conversational"]
    
    with gr.Blocks(title="Local-NotebookLM") as app:
        gr.Markdown("# 🎙️ Local-NotebookLM: PDF to Podcast Converter")
        
        with gr.Row():
            with gr.Column(scale=1):
                # Input components
                pdf_file = gr.File(label="Upload PDF", file_types=[".pdf"])
                config_file = gr.File(
                    label="Upload Config JSON (Optional)", 
                    file_types=[".json"],
                    info="Default: /Users/gokdenizgulmez/Desktop/Local-NotebookLM/example_config.json"
                )
                format_type = gr.Dropdown(choices=format_options, label="Select Format", value=format_options[0])
                length = gr.Dropdown(choices=length_options, label="Select Length", value=length_options[1] if len(length_options) > 1 else length_options[0])
                style = gr.Dropdown(choices=style_options, label="Select Style", value=style_options[0])
                language = gr.Dropdown(
                    choices=["english", "german", "french", "spanish", "italian", "portuguese"],
                    label="Select Language",
                    value="english"
                )
                additional_preference = gr.Textbox(
                    label="Additional Preferences (Optional)",
                    placeholder="Focus on key points, provide examples, etc."
                )
                output_dir = gr.Textbox(label="Output Directory", value="./output")
                generate_button = gr.Button("Generate Podcast")
            
            with gr.Column(scale=2):
                # Output components
                result_message = gr.Textbox(label="Status")
                audio_output = gr.Audio(label="Generated Podcast", type="filepath")
                
                with gr.Accordion("View Extracted Text", open=False):
                    extracted_text = gr.Textbox(label="Extracted Text", lines=10)
                
                with gr.Accordion("View Clean Extracted Text", open=False):
                    clean_text = gr.Textbox(label="Clean Extracted Text", lines=10)
        
        # Footer
        gr.Markdown("---")
        gr.Markdown("Local-NotebookLM by Gökdeniz Gülmez")
        gr.Markdown("[GitHub Repository](https://github.com/Goekdeniz-Guelmez/Local-NotebookLM)")
        
        # Set up event handler
        generate_button.click(
            fn=process_podcast,
            inputs=[pdf_file, config_file, format_type, length, style, language, additional_preference, output_dir],
            outputs=[result_message, audio_output, extracted_text, clean_text]
        )
    
    return app

def run_gradio_ui():
    """
    Entry point to run the Gradio web UI
    """
    app = create_gradio_ui()
    app.launch(share=False)

if __name__ == "__main__":
    run_gradio_ui()