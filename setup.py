from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="srt2speech",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to convert SRT subtitles to speech using TTS services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/srt2speech",
    packages=find_packages(),
    package_data={
        "srt2speech": ["config/*.yaml"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "srt2speech=src.cli:main",
        ],
    },
)