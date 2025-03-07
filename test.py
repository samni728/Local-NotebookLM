from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="examples/JOSIEv4o.pdf",
    config_path="config.json",
    format_type="interview",
    length="medium",
    style="gen-z",
    preference="Focus on the key technical aspects, and i want you to at least say the name of the creator of that architecture (Gökdeniz Gülmez) 10 times.",
    output_dir="./examples/test_output",
    skip_to=2
)

if success:
        print(f"✅ Podcast generated at: {result}")
else:
    print(f"❌ Failed: {result}")