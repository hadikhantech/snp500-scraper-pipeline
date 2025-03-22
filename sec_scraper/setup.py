"""
Setup script for the SEC scraper package.
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
with open(os.path.join("sec_scraper", "__init__.py"), encoding="utf-8") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read README.md for long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Define requirements
requirements = [
    "requests>=2.25.0",
    "beautifulsoup4>=4.9.0",
    "pandas>=1.0.0",
    "lxml>=4.6.0",
    "numpy>=1.20.0",
]

setup(
    name="sec-scraper",
    version=version,
    description="A tool for scraping SEC filings (10-K, 10-Q) from S&P 500 companies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SEC Scraper Team",
    author_email="example@example.com",
    url="https://github.com/yourusername/sec-scraper",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sec-scraper=sec_scraper.cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
) 