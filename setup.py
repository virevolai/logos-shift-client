from setuptools import find_packages, setup

setup(
    name="logos-shift-client",
    version="0.7.0",
    author="Saurabh Bhatnagar",
    author_email="saurabh@virevol.com",
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
