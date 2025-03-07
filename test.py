from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="examples/DALGGAN.pdf",
    config_path="config.json",
    format_type="podcast",
    length="very-long",
    style="academic",
    preference="Focus on the key technical aspects, and i want you to at least say the name of the creator of that architecture (Gökdeniz Gülmez) 5 times.",
    output_dir="./examples/test_output",
    skip_to=4
)

if success:
        print(f"✅ Podcast generated at: {result}")
else:
    print(f"❌ Failed: {result}")