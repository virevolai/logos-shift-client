from setuptools import find_packages, setup
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="logos-shift-client",
    version="0.7.0",
    author="Saurabh Bhatnagar",
    author_email="saurabh@virevol.com",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "requests",
        "asyncio",
        "tenacity",
        "httpx",
    ],
    extras_require={"dev": ["pytest", "ruff>=0.1.2", "bump2version==1.0.1"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
