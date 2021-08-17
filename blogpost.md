# SoaM Public Release Blogpost

## What is SoaM?
SoaM is a library created by [Mutt](https://muttdata.ai/). It’s goal is to create a forecasting and anomaly detection framework, this tool is developed with conjunctions of experience on previous projects, there comes the name: Son of a Mutt = SoaM.

We developed this library because we were encountering the need of a strong and clear framework for forecasting projects and we didn’t find an open source solution that fitted our needs. As Mutter’s, one of our core values is Efficient Execution, upon this: we always seek ways to optimize our time. We understood that by developing this we wouldn't need to think and code the same thing on different projects and we could leverage its power and replicate it around all of them when needed.

### How can you use it?
You can download it directly from [PyPI](https://pypi.org/project/soam/).

### How are we using it today?
Of course, SoaM is present in lot’s of our projects. As an example, on one of them where we are building a DataOps platform to improve data pipeline creation we are leveraging SoaM modules to extract a time series from Redshift, make a forecast of it, detect anomalies, plot the results and send a report to our Slack channel. This really facilitates our workload and structures our code the Mutt way.
TODO: Business value/Benefits added of using soam

## The beginnings and the road to this public release
This long road started back then in April of 2020. When a couple Mutter’s had the bright idea to start developing this library and merged the first version of SoaM the 21st of April of 2020.

Since then, we have continually pivoted and iterated on the scope of the project but the main goal was always the same: to be the best open source framework for forecasting time-series data products.

### How we contribute to this library
We contribute to this project by setting ambitious goals for each Sprint and then dividing the workload among the Mutter’s involved in the SoaM development. We usually meet twice a week, Fridays are for sync and Mondays are for live-coding, and we fully dedicate these hours to this project. Then, during the week, our priority is always the external projects but from time to time we find some periods we can dedicate to contribute and commit some code to this library. At the same time, we usually incentivize new hires to solve a couple of SoaM issues so they can learn our methodologies and work scheme and most importantly: meet new colleagues!

## Main Features
This library pipeline supports any data source. The process is structured in different stages:
- Extraction: manages the granularity and aggregation of the input data.
- Preprocessing: lets select among out of the box tools to perform standard tasks as normalization or fill nan values.
- Forecasting: fits a model and predicts results.
- Post Processing: modifies the results based on business/real information or create analysis with the predicted values, such as an anomaly detection.

### Extraction
Time Series Extractor

### Preprocessing
- Transformer
- Merge Concat?
- Slicer?

### Forecasting
- Exponential Smoothing
- Orbit DLT Full
- Prophet
- SARIMAX
- Custom

### Post Processing
- Store
- Anomalies
- Backtester
- Plotting
- Reporting

## Documentation
- Sphinx docs.
- Quickstar I and II.
- Notebooks with examples.
- Documents with examples.
- End2end product using Soam and Airflow.

## Continuous Integration and Continuous Deployment
- Deployment practices.
- Contributing.
- Tests.
- Changelog.
- Version Control.
- Pre commit and Code linting (black, pylint).
- Deployment of updated docs on sphinx.
- Docstrings control.
- Deployment of version to git registry.

## Next Steps
Plans and possible future releases.

## Our Team
List of the team responsible for this library.