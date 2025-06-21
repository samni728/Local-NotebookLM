import os
import gradio as gr
import argparse
from local_notebooklm.processor import podcast_processor
from local_notebooklm.steps.helpers import LengthType, FormatType, StyleType, SkipToOptions

LABELS = {
    "English": {
        "title": "# \U0001F399\ufe0f Local-NotebookLM: PDF to Audio Converter",
        "config_info": "*Upload Config JSON (Optional) - Default: ./example_config.json*",
        "upload_pdf": "Upload PDF",
        "config_json": "Config JSON",
        "select_format": "Select Format",
        "select_length": "Select Length",
        "select_style": "Select Style",
        "select_language": "Select Language",
        "additional_preferences": "Additional Preferences (Optional)",
        "additional_placeholder": "Focus on key points, provide examples, etc.",
        "output_dir": "Output Directory",
        "output_placeholder": "Enter the path where output files will be saved",
        "skip_to_step": "Skip to Step (Optional)",
        "skip_info": "Select a step to start from if you want to skip earlier steps",
        "generate_button": "Generate Podcast",
        "status": "Status",
        "generated_podcast": "Generated Podcast",
        "view_extracted": "View Extracted Text",
        "extracted_text": "Extracted Text",
        "view_clean": "View Clean Extracted Text",
        "clean_text": "Clean Extracted Text",
        "view_script": "View Podcast Script",
        "podcast_script": "Podcast Script",
        "footer_title": "Local-NotebookLM by G\u00f6kdeniz G\u00fclmez",
        "github": "[GitHub Repository](https://github.com/Goekdeniz-Guelmez/Local-NotebookLM)",
        "ui_language": "UI Language"
    },
    "\u4e2d\u6587": {
        "title": "# \U0001F399\ufe0f Local-NotebookLM\uff1aPDF \u8f6c\u97f3\u9891\u8f6c\u6362\u5668",
        "config_info": "*\u4e0a\u4f20\u914d\u7f6e JSON\uff08\u53ef\u9009\uff09 - \u9ed8\u8ba4\uff1a./example_config.json*",
        "upload_pdf": "\u4e0a\u4f20 PDF",
        "config_json": "\u914d\u7f6e JSON",
        "select_format": "\u9009\u62e9\u683c\u5f0f",
        "select_length": "\u9009\u62e9\u957f\u5ea6",
        "select_style": "\u9009\u62e9\u98ce\u683c",
        "select_language": "\u9009\u62e9\u8bed\u8a00",
        "additional_preferences": "\u9644\u52a0\u504f\u597d\uff08\u53ef\u9009\uff09",
        "additional_placeholder": "\u5173\u6ce8\u8981\u70b9\uff0c\u63d0\u4f9b\u793a\u4f8b\u7b49",
        "output_dir": "\u8f93\u51fa\u76ee\u5f55",
        "output_placeholder": "\u8f93\u5165\u4fdd\u5b58\u8f93\u51fa\u6587\u4ef6\u7684\u8def\u5f84",
        "skip_to_step": "\u8df3\u8fc7\u5230\u6b65\u9aa4\uff08\u53ef\u9009\uff09",
        "skip_info": "\u5982\u9700\u8df3\u8fc7\u4ee5\u524d\u6b65\u9aa4\uff0c\u9009\u62e9\u4ece\u54ea\u4e2a\u6b65\u9aa4\u5f00\u59cb",
        "generate_button": "\u751f\u6210\u64ad\u5ba2",
        "status": "\u72b6\u6001",
        "generated_podcast": "\u751f\u6210\u7684\u64ad\u5ba2",
        "view_extracted": "\u67e5\u770b\u63d0\u53d6\u7684\u6587\u672c",
        "extracted_text": "\u63d0\u53d6\u7684\u6587\u672c",
        "view_clean": "\u67e5\u770b\u6e05\u7406\u540e\u7684\u6587\u672c",
        "clean_text": "\u6e05\u7406\u540e\u7684\u6587\u672c",
        "view_script": "\u67e5\u770b\u64ad\u5ba2\u811a\u672c",
        "podcast_script": "\u64ad\u5ba2\u811a\u672c",
        "footer_title": "G\u00f6kdeniz G\u00fclmez \u5f00\u53d1\u7684 Local-NotebookLM",
        "github": "[GitHub \u4ed3\u5e93](https://github.com/Goekdeniz-Guelmez/Local-NotebookLM)",
        "ui_language": "\u754c\u9762\u8bed\u8a00"
    }
}


def process_podcast(pdf_file, config_file, format_type, length, style, language, additional_preference, output_dir, skip_to):
    if pdf_file is None and (skip_to is None or skip_to == 1):
        return "Please upload a PDF file first.", None, "", "", ""
    
    if not output_dir:
        output_dir = "./local_notebooklm/web_ui/output"
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    except Exception as e:
        return f"Failed to create output directory: {str(e)}", None, "", "", ""
    
    try:
        if hasattr(pdf_file, 'name'):
            pdf_path = pdf_file.name
        else:
            pdf_path = pdf_file
        
        if config_file is None:
            config_path = "./example_config.json"
        else:
            if hasattr(config_file, 'name'):
                config_path = config_file.name
            else:
                config_path = config_file
        
        print(f"Processing with output_dir: {output_dir}")
        
        success, result = podcast_processor(
            pdf_path=pdf_path,
            config_path=config_path,
            format_type=format_type,
            length=length,
            style=style,
            preference=additional_preference if additional_preference else None,
            output_dir=output_dir,
            language=language,
            skip_to=skip_to
        )
        
        if success:
            audio_path = os.path.join(output_dir, "podcast.wav")
            file_contents = {}
            generated_files = [
                "step1/extracted_text.txt",
                "step1/clean_extracted_text.txt",
                "step2/data.pkl",
                "step3/podcast_ready_data.pkl",
                "step3/podcast_ready_data.txt"
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
            
            return "Audio Generated Successfully!", audio_path, file_contents.get("step1/extracted_text.txt", ""), file_contents.get("step1/clean_extracted_text.txt", ""), file_contents.get("step3/podcast_ready_data.txt", "")
        else:
            return f"Failed to generate audio: {result}", None, "", "", ""
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"An error occurred: {str(e)}\n\nDetails:\n{error_details}", None, "", "", ""

def create_gradio_ui():
    format_options = list(FormatType.__args__) if hasattr(FormatType, "__args__") else ["podcast"]
    length_options = list(LengthType.__args__) if hasattr(LengthType, "__args__") else ["medium"]
    style_options = list(StyleType.__args__) if hasattr(StyleType, "__args__") else ["conversational"]

    labels = LABELS["English"]

    with gr.Blocks(title="Local-NotebookLM") as app:
        ui_language = gr.Dropdown(["English", "\u4e2d\u6587"], value="English", label=labels["ui_language"])
        title_md = gr.Markdown(labels["title"])
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_file = gr.File(label=labels["upload_pdf"], file_types=[".pdf"])
                config_info = gr.Markdown(labels["config_info"])
                config_file = gr.File(label=labels["config_json"], file_types=[".json"])
                format_type = gr.Dropdown(choices=format_options, label=labels["select_format"], value=format_options[0])
                length = gr.Dropdown(choices=length_options, label=labels["select_length"], value=length_options[1] if len(length_options) > 1 else length_options[0])
                style = gr.Dropdown(choices=style_options, label=labels["select_style"], value=style_options[0])
                language = gr.Dropdown(
                    choices=["english", "german", "french", "spanish", "italian", "portuguese"],
                    label=labels["select_language"],
                    value="english"
                )
                additional_preference = gr.Textbox(
                    label=labels["additional_preferences"],
                    placeholder=labels["additional_placeholder"]
                )
                output_dir = gr.Textbox(
                    label=labels["output_dir"],
                    value="./local_notebooklm/web_ui/output",
                    placeholder=labels["output_placeholder"]
                )
                skip_to = gr.Dropdown(
                    choices=SkipToOptions,
                    label=labels["skip_to_step"],
                    value=None,
                    info=labels["skip_info"]
                )
                generate_button = gr.Button(labels["generate_button"])
            with gr.Column(scale=2):
                result_message = gr.Textbox(label=labels["status"])
                audio_output = gr.Audio(label=labels["generated_podcast"], type="filepath")

                with gr.Accordion(labels["view_extracted"], open=False) as acc1:
                    extracted_text = gr.Textbox(label=labels["extracted_text"], lines=10)

                with gr.Accordion(labels["view_clean"], open=False) as acc2:
                    clean_text = gr.Textbox(label=labels["clean_text"], lines=10)

                with gr.Accordion(labels["view_script"], open=False) as acc3:
                    audio_script = gr.Textbox(label=labels["podcast_script"], lines=15)
        
        gr.Markdown("---")
        footer_md = gr.Markdown(labels["footer_title"])
        repo_md = gr.Markdown(labels["github"])
        
        generate_button.click(
            fn=process_podcast,
            inputs=[pdf_file, config_file, format_type, length, style, language, additional_preference, output_dir, skip_to],
            outputs=[result_message, audio_output, extracted_text, clean_text, audio_script]
        )

        def change_language(choice):
            l = LABELS.get(choice, LABELS["English"])
            return [
                gr.update(label=l["ui_language"]),
                gr.update(value=l["title"]),
                gr.update(label=l["upload_pdf"]),
                gr.update(value=l["config_info"]),
                gr.update(label=l["config_json"]),
                gr.update(label=l["select_format"]),
                gr.update(label=l["select_length"]),
                gr.update(label=l["select_style"]),
                gr.update(label=l["select_language"]),
                gr.update(label=l["additional_preferences"], placeholder=l["additional_placeholder"]),
                gr.update(label=l["output_dir"], placeholder=l["output_placeholder"]),
                gr.update(label=l["skip_to_step"], info=l["skip_info"]),
                gr.update(value=l["generate_button"]),
                gr.update(label=l["status"]),
                gr.update(label=l["generated_podcast"]),
                gr.update(label=l["extracted_text"]),
                gr.update(label=l["clean_text"]),
                gr.update(label=l["podcast_script"]),
                gr.update(label=l["view_extracted"]),
                gr.update(label=l["view_clean"]),
                gr.update(label=l["view_script"]),
                gr.update(value=l["footer_title"]),
                gr.update(value=l["github"])
            ]

        ui_language.change(
            fn=change_language,
            inputs=ui_language,
            outputs=[
                ui_language,
                title_md,
                pdf_file,
                config_info,
                config_file,
                format_type,
                length,
                style,
                language,
                additional_preference,
                output_dir,
                skip_to,
                generate_button,
                result_message,
                audio_output,
                extracted_text,
                clean_text,
                audio_script,
                acc1,
                acc2,
                acc3,
                footer_md,
                repo_md,
            ]
        )

    return app

def run_gradio_ui(share=False, port=7860):
    app = create_gradio_ui()
    app.launch(
        share=share,
        server_port=port,
        server_name="0.0.0.0"
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Local-NotebookLM web UI")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--port", type=int, default=None, help="Port to run the interface on")
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    run_gradio_ui(share=args.share, port=args.port if args.port else 7860)

if __name__ == "__main__" or __name__ == "local_notebooklm.web_ui":
    main()