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
        "sqlalchemy_utils",
        "fbprophet",
        "u8darts",
        "alembic",
        "python-decouple",
        "prefect",
        "filelock",
        "click",
        "cookiecutter",
        "slackclient",
        "muttlib @ git+https://gitlab.com/mutt_data/muttlib#egg=muttlib",
    ],
    extras_require={
        'dev': [
            'flake8-bugbear',
            'flake8-docstrings',
            'bump',
            'sphinx',
            'sphinx_rtd_theme',
            'm2r2',
            'pre-commit==2.5.0',
            'isort==4.3.21',
            'black==19.10b0',
            'mypy==0.782',
            'pylint==2.4.4',
            'nox',
        ],
        'test': [
            'nox',
            'pytest',
            'pytest-mpl',
            'pytest-xdist',
            'pytest-cov',
            'pytest-html',
            'hypothesis',
            'psycopg2',
        ],
    },
    python_requires="~=3.6",
    entry_points={'console_scripts': ['soam = soam.console:cli']},
)
# TODO: check why 'python setup.py develop' is failing to obtain muttlib, but 'pip install -e .' is working
