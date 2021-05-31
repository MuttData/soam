"""SOAM setup file"""

import setuptools

import soam

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

#  define 'extra_dependencies'
extra_dependencies = {
    'dev': [
        'flake8-bugbear',
        'flake8-docstrings',
        'bump2version',
        'docutils>=0.12,<0.17',
        'sphinx',
        'sphinx_rtd_theme',
        'm2r2',
        'pre-commit==2.5.0',
        'isort==4.3.21',
        'black==19.10b0',
        'mypy==0.782',
        'pylint==2.4.4',
        'nox',
        'wrapt==1.11.*',
    ],
    'test': [
        'interrogate',
        'nox',
        'pytest',
        'pytest-mpl',
        'pytest-xdist',
        'pytest-cov',
        'pytest-html',
        'pytest-mock',
        'hypothesis',
        'psycopg2-binary',
        'nbval',
        'pdftotext==2.1.5',
    ],
    'slack': ["slackclient",],
    'orbit': ['orbit-ml==1.0.13'],
    'prophet': ["pystan==2.19.1.1", "fbprophet==0.6",],
    'pdf_report': ["jupytext==1.10.2", "papermill==2.3.2", "nbconvert==5.6",],
    'gsheets_report': ["muttlib[gsheets]>=1.0,<2"],
    'statsmodels': ["statsmodels<0.12,>=0.11"],
}

# create 'all' and 'report' extras
all_extras = []
report_extras = []
for key, extra_dep in extra_dependencies.items():
    if not extra_dep in all_extras:
        all_extras += extra_dep
    if key == 'slack' or 'report' in key and not extra_dep in report_extras:
        report_extras += extra_dep
extra_dependencies.update({'report': report_extras})
extra_dependencies.update({'all': all_extras})

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
    packages=setuptools.find_packages(),
    package_data={
        "soam": ["resources/*.html", "templates/*", "db_migrations", "resources/*.tpl"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["pytest-runner", "wheel"],
    tests_require=["pytest", "pytest-cov", "pytest-html", "betamax"],
    test_suite='test',
    install_requires=[
        "jinja2",
        "pandas>=1.0.0",
        "Cython<0.29.18,>=0.29",
        "sqlalchemy<1.4.0,>=1.3.0",
        "sqlalchemy_utils",
        "alembic",
        "python-decouple",
        "prefect==0.14.17",
        "filelock",
        "click",
        "cookiecutter",
        "wheel",
        "muttlib>=1.1.2,<2",
        "numpy>=1.19,<1.20",
        "matplotlib==3.3.4",
    ],
    extras_require=extra_dependencies,
    python_requires="~=3.6",
    entry_points={'console_scripts': ['soam = soam.console:cli']},
)
# TODO: check why 'python setup.py develop' is failing to obtain muttlib, but 'pip install -e .' is working
