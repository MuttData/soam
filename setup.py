"""SOAM setup file"""

import setuptools

import soam

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="soam",
    version=soam.__version__,
    author="Mutt Data",
    home_page="https://gitlab.com/mutt_data/soam/",
    keywords="anomalies forecasting reporting",
    author_email="info@muttdata.ai",
    description="Tools for time series analysis, plotting and reporting.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    packages=["soam"],
    package_data={"soam": ["resources/*.html"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["wheel"],
    install_requires=[
        "jinja2",
        "pandas>=1.0.0",
        "progressbar2",
        "sqlalchemy",
        "fbprophet",
        "darts",
        "alembic",
        "python-decouple",
    ],
    dependency_links=["git+https://gitlab.com/mutt_data/muttlib"],
)
