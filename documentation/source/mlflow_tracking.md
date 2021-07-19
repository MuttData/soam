# Parameters log using Mlflow tracking

Mlflow tracking allows you to automatically track the input arguments, parameters, and metrics of the tasks in any
given flow and then visualize them on its intuitive UI.

You can enable tracking with Mlflow by setting `TRACKING_IS_ACTIVE` to *True* on `soam/cfg.py`.
MLflow runs can be recorded to local files, to a SQLAlchemy compatible database, or remotely to a tracking server.
By default, the MLflow Python API logs runs locally to files in an `mlruns` directory wherever you ran the script that
contains the flow you want to keep track of.
To log runs remotely, you can set the `TRACKING_URI` variable on `soam/cfg.py` to a tracking server’s URI (as shown in
the [official mlflow documentation](https://www.mlflow.org/docs/latest/tracking.html#logging-to-a-tracking-server)).
Keep in mind that if you use file tracking uri you should use a path with a directory that does not exist, as mlflow
will create it for you.

To visualize the logged runs just execute the script that contains the flow you are interested on tracking and run `mlflow ui`
in the same directory as your script, then go to http://localhost:5000 on your browser to view the logs (if the default settings
were used).

Follow [this notebook](../../notebook/examples/mlflow_log_test.ipynb) to see an example on how to use this feature!