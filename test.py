from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="./examples/JOSIEv4o.pdf",
    config_path="config.json",
    format_type="three-people-podcast",
    length="medium",
    style="normal",
    # preference="Focus on the key technical aspects, this podcast shoudl only be for Machine Learning researchers and engineers.",
    output_dir="./examples/test_output",
    # skip_to=3
)

if success:
        print(f"✅ Podcast generated at: {result}")
else:
    print(f"❌ Failed: {result}")


# python -m local_notebooklm.start --pdf ./examples/JOSIEv4o.pdf --config config.json --format podcast --length medium --style normal --output-dir ./examples/test_output --skip-to 4