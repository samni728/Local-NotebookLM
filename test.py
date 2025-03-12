from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="./examples/JOSIEv4o.pdf",
    config_path="config.json",
    format_type="summary",
    length="short",
    style="normal",
    # preference="Focus on the key technical aspects, this podcast shoudl only be for Machine Learning researchers and engineers.",
    output_dir="./examples/test_output",
    skip_to=4
)

if success:
        print(f"✅ Podcast generated at: {result}")
else:
    print(f"❌ Failed: {result}")