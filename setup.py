from pathlib import Path
from setuptools import find_packages, setup

# Get the project root directory
root_dir = Path(__file__).parent

# Read the requirements from requirements.txt
requirements_file = root_dir / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as fid:
        requirements = [l.strip() for l in fid.readlines()]
else:
    print("Warning: requirements.txt not found. Proceeding without dependencies.")
    requirements = []

# Import the version from the package
version = {}
try:
    with open("local_notebooklm/version.py") as f:
        exec(f.read(), version)
except FileNotFoundError:
    print("Warning: Could not find version.py in local_notebooklm/")
    try:
        with open("local_notebook/version.py") as f:
            exec(f.read(), version)
    except FileNotFoundError:
        print("Warning: Could not find version.py in local_notebook/ either. Using default version.")
        version["__version__"] = "0.1.0"  # Default version

version = version.get("__version__", "0.1.0")

# Setup configuration
setup(
    name="Local-NotebookLM",
    version=version,
    description="A Local-NotebookLM to convert PDFs into Audio.",
    long_description=open(root_dir / "README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Gökdeniz Gülmez",
    author_email="goekdenizguelmez@gmail.com",
    url="https://github.com/Goekdeniz-Guelmez/Local-NotebookLM",
    license="Apache-2.0",
    install_requires=requirements,
    packages=find_packages(),
    python_requires=">=3.12",
    classifiers=[
        "Programming Language :: Python :: 3.12"
    ],
)