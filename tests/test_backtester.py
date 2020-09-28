import unittest

from sklearn.metrics import mean_absolute_error, mean_squared_error

from soam.backtester import compute_metrics


def test_compute_metrics():
    metrics = {
        "mae": mean_absolute_error,
        "mse": mean_squared_error,
    }
    y_true = [3, -0.5, 2, 7]
    y_pred = [2.5, 0.0, 2, 8]
    expected_output = {'mae': 0.5, 'mse': 0.375}
    output = compute_metrics(y_true, y_pred, metrics)
    unittest.TestCase().assertDictEqual(expected_output, output)
