"""main"""
#!/usr/bin/env python3

from darts import models
import pandas as pd
from soam.forecaster import Forecaster


def main():
    url = "https://raw.githubusercontent.com/facebook/prophet/master/examples/example_retail_sales.csv"
    df = pd.read_csv(url)
    my_model = models.Prophet(weekly_seasonality=False, daily_seasonality=False)
    forecaster = Forecaster(my_model)
    predictions = forecaster.run(raw_series=df, output_length=7)
    print(predictions)


if __name__ == "__main__":
    main()
