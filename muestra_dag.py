import pandas as pd
from google.cloud import storage
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import datetime

bucket_name            = 'pruebadags'
file                   = 'definitions.csv'
nameDAG                = 'nombredeldag' 
project                = 'vocal-byte-4548601' #id del proyecto de gcp
owner                  = 'Nombre' # tu nombre se verá reflejado en el tag
email                  = 'muestra@correo.com' #introduce tu correo electronico aca, esto solo es necesario para los casos en los que tienes el servicio de monitoreo premium


def download_data(file_name):
    # Inicializa el cliente de almacenamiento de Google Cloud.
    storage_client = storage.Client()
    # Accede al bucket y al archivo.
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Descarga el archivo a una ubicación temporal.
    destination_file = '/tmp/{}'.format(file_name)
    blob.download_to_filename(destination_file)
    #devuelve la ubicacion en la que dejo el archivo
    return destination_file


def upload_data(file_name, destination_file): # recibe el nombre del archivo que va a subir y la ruta  donde esta almacenado
    # Inicializa el cliente de almacenamiento de Google Cloud.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Accede al archivo.
    blob2= bucket.blob(file_name)
    
    # reemplaza el archivo en el bucket con el archivo en la destination file
    blob2.upload_from_filename(destination_file)


def drop_column(df,column_name):
    df.drop(columns=column_name)
    return df

def add_column():

    destination = download_data(file)
    df = pd.read_csv(destination)
    df['nueva_columna'] = 'hola'
    df = drop_column(df, 'nueva_columna')
    df.to_csv(destination, index=False)
    file_name = 'actualizado_hola'
    upload_data(file_name, destination)
    return file_name

def print_file_name(**kwargs):
    ti = kwargs['ti']
    file_name = ti.xcom_pull(task_ids = 'task_add_column')
    print(file_name)

default_args = {
    'owner': owner,                  # dueño de la tarea.
    'depends_on_past': True,         # si la tarea deberia o no depender de las tareas anteriores.              
    'start_date': datetime.datetime(2023, 10, 13),
    'retries': 1,                    # reintenta una vez antes de dar la tarea por fallida.
    'retry_delay': datetime.timedelta(minutes=.5),  # tiempo entre los intentos
    'project_id': project,           # Cloud Composer project ID.
}

with DAG(nameDAG,
         default_args = default_args,
         catchup = False,  # ejecucion de tareas pasadas
         max_active_runs = 1,
         schedule_interval ='0 3 * * 0') as dag: # schedule_interval = None en caso de que no haya intervalo de ejecucion
    

    t_begin = DummyOperator(task_id="begin")
    

    task_add_column = PythonOperator(task_id='task_add_column',
                                 provide_context=True,
                                 python_callable=add_column,
                                 depends_on_past=True,

                                    dag=dag

                                 )
    
    task_print_file_name = PythonOperator(task_id='task_print_file_name',
                                 provide_context=True,
                                 python_callable=print_file_name,
                                 depends_on_past=True,

                                    dag=dag

                                 )
    
    t_end = DummyOperator(task_id="end")

    #############################################################
    t_begin >> task_add_column >> task_print_file_name >> t_end