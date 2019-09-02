from pathlib import Path

from setuptools import find_packages, setup

current_dir = Path(__file__).parent.resolve()

with open(current_dir / "README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mikro",
    version="0.2.1",
    py_modules=["mikro"],
    url="https://github.com/isidentical/mikro",
    description="A micro service tool built atop on python's http.server",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
