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
    package_data={"soam": ["resources/*.html", "templates/*", "db_migrations"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["wheel"],
    install_requires=[
        "jinja2",
        "pandas>=1.0.0",
        "statsmodels<0.12,>=0.11",
        "Cython<0.29.18,>=0.29",
        "progressbar2",
        "sqlalchemy",
        "fbprophet",
        "u8darts",
        "alembic",
        "python-decouple",
        "prefect",
        "filelock",
        "click",
        "cookiecutter",
        "muttlib @ git+https://gitlab.com/mutt_data/muttlib#egg=muttlib"
    ],
    entry_points={'console_scripts': ['soam = soam.console:cli']},
)
# include python versions https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires