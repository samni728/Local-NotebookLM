from processor import podcast_processor

success, result = podcast_processor(
    pdf_path="examples/JOSIEv4o.pdf",
    config_path="config.json",
    format_type="interview",
    length="long",
    style="professional",
    preference="Focus on the key technical aspects",
    output_dir="./test_output"
)

if success:
    print(f"Successfully generated podcast: {result}")
else:
    print(f"Failed to generate podcast: {result}")