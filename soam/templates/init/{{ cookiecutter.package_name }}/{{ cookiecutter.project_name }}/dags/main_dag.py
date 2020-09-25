from airflow import DAG
from airflow.operators.docker_operator import DockerOperator

dag_version = "0.1"

with DAG(dag_id=f"main_{dag_version}") as dag:
    main_task = DockerOperator(task_id="main_task", command="python main.py",)
