from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def get_date():
    print(f"Date du jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

default_args = {
    'owner': 'airflow',
    'email_on_failure': False,
}

with DAG(
    dag_id='exercice_jour1',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule    =None,
    catchup=False,
    tags=['tp', 'jour1'],
) as dag:

    t1 = BashOperator(
        task_id='debut_workflow',
        bash_command='echo "Début du workflow"',
    )

    t2 = PythonOperator(
        task_id='date_du_jour',
        python_callable=get_date,
    )

    t3 = BashOperator(
        task_id='fin_workflow',
        bash_command='echo "Fin du workflow"',
    )

    t1 >> t2 >> t3