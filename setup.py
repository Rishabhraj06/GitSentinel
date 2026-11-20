from setuptools import setup, find_packages

setup(
    name="gitsentinel",
    version="1.0.0",
    author="Rishabh Raj",
    author_email="rishabhraj74918@gmail.com",
    description="Autonomous Pre-Flight Security Scanner & AI Git Copilot for Developers",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rishabhraj06/GitSentinel",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "ai": ["google-genai>=0.1.0"],
        "dev": ["pytest>=8.0.0"],
    },
    entry_points={
        "console_scripts": [
            "gitsentinel=gitsentinel.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Security",
    ],
)
