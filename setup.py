from setuptools import setup, find_packages

setup(
    name='logos-shift-client',
    version='0.2.0',
    author='Saurabh Bhatnagar',
    author_email='saurabh@virevol.com',
    packages=find_packages(),
    install_requires=[
        'pydantic',
        'requests',
        'asyncio',
        'tenacity',
    ],
    extras_require={
        'dev': [
            'pytest',
            'ruff==0.2.0'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
