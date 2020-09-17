# Darts insights
Darts base all the library on the TimeSeries Class, a Class created by them with datetime type as index.
You can create a TimeSeries from a pandas df or other sources.

* It supports using uni-variate and multivariate features, but the multivariate capability is still under active development.

* Because the datetime is the index and must be unique you cant have more than one entity per model.

* Contains many classical statistical models (ARIMA, Theta, ...), Prophet and some deep learning models (RNN and TCN), not all models can use multivariate data, deep learning models and Prophet (adding holidays)

* By default the TimeSeries class will add the missing date with nan as value.
There is a function in utils to `fillna` with pandas interpolation methods.

* Has some backtesting methods, as well as a grid search function.

* Has the basic forecasting error metrics, you can easily create a custom one with a decorator.

* For preprocessing has some functions, normalize data between [0,1], interpolate `nan` values.

* add features attributes

Note: the data for the notebooks is on GoogleDrive