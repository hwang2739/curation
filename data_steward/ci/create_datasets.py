import os

from google.oauth2 import service_account
from google.cloud import bigquery

from utils import bq

CLIENT = None


def get_client(project_id, app_creds):
    """
    Ensure only one client is created and reused
    :param project_id:  project to get a client for                                                                 
    :returns: a big query client object
    """
    global CLIENT
    if not CLIENT:
        credentials = service_account.Credentials.from_service_account_file(
            app_creds)
        CLIENT = bigquery.Client(project=project_id, credentials=credentials)

    return CLIENT


def create_dataset(project, dataset_id, description, tags, app_creds):
    # Construct a full Dataset object to send to the API.
    dataset = bq.define_dataset(project, dataset_id, description, tags)

    client = get_client(project, app_creds)
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Created dataset {project}.{dataset_id}")


def create_datasets(project, config, datasets):
    username = config.get('USERNAME', 'default')
    for dataset in datasets:
        dataset_name = dataset.split('_')[0]
        description = f"Test {dataset_name} dataset for {username}"
        dataset_id = config.get(dataset)
        create_dataset(project, dataset_id, description, {'automated_test': ''},
                       config.get('GOOGLE_APPLICATION_CREDENTIALS'))


def remove_datasets(project, creds_path, config, datasets):
    client = get_client(project, creds_path)
    for dataset in datasets:
        dataset_id = config.get(dataset)
        fq_dataset_id = f'{project}.{dataset_id}'
        client.delete_dataset(fq_dataset_id,
                              delete_contents=True,
                              not_found_ok=True)
        print(f"Deleted dataset '{fq_dataset_id}'")


def copy_vocab_tables(vocab_dataset, dest_prefix):
    client = get_client(None, None)
    tables = client.list_tables(vocab_dataset)
    for table in tables:
        vocab_table = f"{vocab_dataset}.{table.table_id}"
        dest_table = f"{dest_prefix}.{table.table_id}"
        client.copy_table(vocab_table, dest_table)
        print(f"copied '{vocab_table}' to '{dest_table}'")


def create_test_datasets(config, datasets):
    project = config.get('APPLICATION_ID')
    remove_datasets(project, config.get('GOOGLE_APPLICATION_CREDENTIALS'),
                    config, datasets)
    create_datasets(project, config, datasets)
    vocab_dataset = f"{project}.{config.get('VOCABULARY_DATASET')}"
    dest_prefix = f"{project}.{config.get('BIGQUERY_DATASET_ID')}"
    copy_vocab_tables(vocab_dataset, dest_prefix)


if __name__ == "__main__":
    # only import this if this is running as a standalone module
    from ci.setup import get_environment_config, DATASET_NAMES

    config = get_environment_config()
    create_test_datasets(config, DATASET_NAMES)
