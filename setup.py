from setuptools import find_packages, setup
from pathlib import Path

# read contents of README.md to include it in package metadata
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text("utf-8")

setup(
    name="mkdocs-minify-plugin",
    version="0.7.1",
    description="An MkDocs plugin to minify HTML, JS or CSS files prior to being written to disk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mkdocs minify publishing documentation html css",
    url="https://github.com/byrnereese/mkdocs-minify-plugin",
    author="Byrne Reese, Lars Wilhelmer",
    author_email="byrne@majordojo.com",
    license="MIT",
    python_requires=">=3.7",
    install_requires=[
        "mkdocs>=1.4.1",
        "htmlmin2>=0.1.13",
        "jsmin>=3.0.1",
        "csscompressor>=0.9.5",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "minify = mkdocs_minify_plugin.plugin:MinifyPlugin",
        ],
    },
)
