from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="./examples/MoshiVis.pdf",
    config_path="config.json",
    format_type="four-people-podcast",
    length="long",
    style="academic",
    # preference="Focus on the key technical aspects, this podcast should only be for Machine Learning researchers and engineers.",
    output_dir="./examples/test_output",
    # skip_to=3
)

if success:
        print(f"✅ Podcast generated at: {result}")
else:
    print(f"❌ Failed: {result}")