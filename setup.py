#!/usr/bin/env python3

from pathlib import Path
from setuptools import setup


ptr_params = {
    "disabled": True,
    "entry_point_module": "ssde",
    "test_suite": "ssde_tests",
    "test_suite_timeout": 10,
    "required_coverage": {"ssde.py": 25},
    "run_black": True,
    "run_mypy": True,
    "run_flake8": True,
}


def get_long_desc() -> str:
    repo_base = Path(__file__).parent
    long_desc = ""
    for info_file in (repo_base / "README.md", repo_base / "CHANGES.md"):
        with info_file.open("r", encoding="utf8") as ifp:
            long_desc += ifp.read()
        long_desc += "\n\n"

    return long_desc


setup(
    name=ptr_params["entry_point_module"],
    version="21.1.2",
    description=(
        "Schlage Door Lock Prometheus Exporters via Samsung Smartthings API"
    ),
    long_description=get_long_desc(),
    long_description_content_type="text/markdown",
    py_modules=["ssde"],
    url="http://github.com/cooperlees/smartthings_schlage_doorlock_exporter",
    author="Cooper Lees",
    author_email="me@cooperlees.com",
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
    install_requires=["prometheus_client", "pysmartthings"],
    entry_points={"console_scripts": ["ssde = ssde:main"]},
    test_suite=ptr_params["test_suite"],
)
