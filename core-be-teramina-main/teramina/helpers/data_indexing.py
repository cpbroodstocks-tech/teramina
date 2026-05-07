# pylint: disable=no-member, no-name-in-module, too-many-locals

import os

# import re
import dotenv

from langchain.vectorstores.faiss import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DataFrameLoader

from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class
from google.cloud import storage

dotenv.load_dotenv()

openai_api_key = os.getenv("open_ai_key")
BUCKET_NAME = os.getenv("GS_VDB_BUCKET_NAME")


def check_gcs_folder_exists(bucket_name, folder_path):
    """check wether the folder exist or not"""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    # List objects with a certain prefix (folder_path)
    blobs = bucket.list_blobs(prefix=folder_path)

    # If there are any blobs, then the "folder" exists
    for _ in blobs:
        return True

    return False


def delete_objects_with_prefix(bucket_name, prefix):
    """delete object from gcs"""
    # Initialize a client
    client = storage.Client()

    # Get the bucket
    bucket = client.get_bucket(bucket_name)

    # List objects in the bucket with the specified prefix
    blobs = bucket.list_blobs(prefix=prefix)

    # Delete each object with the specified prefix
    for blob in blobs:
        blob.delete()


def generate_vectordb(ndf):
    """generate vector db"""

    ndf["content"] = ndf.to_dict("records")
    ndf["content"] = ndf["content"].astype(str)
    ndf = ndf[["date", "doc", "cycle_name", "pond_name", "farm_name", "content"]]
    loader = DataFrameLoader(ndf, page_content_column="content")
    ndata = loader.load()

    embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectordb = FAISS.from_documents(documents=ndata, embedding=embedding)
    return vectordb


def download_file_from_bucket(source_blob_name, destination_file_path):
    """list bucket"""
    # Initialize a client
    client = storage.Client()

    # Get the bucket
    bucket = client.get_bucket(BUCKET_NAME)

    # Get the blob (file) from the bucket
    blob = bucket.blob(source_blob_name)

    # Create the necessary directories if they don't exist
    os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)

    # Download the file to a local destination
    blob.download_to_filename(destination_file_path)


def store_to_gcs(cycle_id, user_id, df):
    """store to gcs"""
    special_storage = get_storage_class("storages.backends.gcloud.GoogleCloudStorage")(
        bucket_name=BUCKET_NAME
    )
    folder_db_name = f"vdb_{cycle_id}"

    # generate vectordb
    vectordb = generate_vectordb(df)

    # Save the VDB
    vectordb.save_local(folder_db_name)

    summary_folder_path = f"{user_id}/vdb_summary"  # User's folder in GCS

    # Check if the "vdb_summary" folder exists in the user's folder
    if check_gcs_folder_exists(BUCKET_NAME, summary_folder_path):
        index_faiss = f"{user_id}/vdb_summary/index.faiss"
        index_pkl = f"{user_id}/vdb_summary/index.pkl"
        destination_path1 = index_faiss.replace(f"{user_id}/", "")
        destination_path2 = index_pkl.replace(f"{user_id}/", "")

        download_file_from_bucket(index_faiss, destination_path1)
        download_file_from_bucket(index_pkl, destination_path2)

        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        summary_vdb = FAISS.load_local("vdb_summary", embeddings=embedding)
        summary_vdb.merge_from(vectordb)

        summary_vdb.save_local("vdb_summary")
    else:
        vectordb.save_local("vdb_summary")

    # Save the local folder to Google Cloud Storage
    local_path_folder = os.path.join(folder_db_name)
    summary_path_folder = os.path.join("vdb_summary")

    # Save the local folder to Google Cloud Storage
    for local_folder_path in [local_path_folder, summary_path_folder]:
        for root, _, files in os.walk(local_folder_path):
            for file_name in files:
                local_path = os.path.join(root, file_name)

                # Read the content of the file
                with open(local_path, "rb") as file:
                    content = file.read()

                # Save the file to Google Cloud Storage
                relative_path = os.path.relpath(local_path, local_folder_path)
                gcs_path = os.path.join(f"{user_id}/{local_folder_path}", relative_path)
                special_storage.save(gcs_path, ContentFile(content))

                # Delete the local file after successfully storing in GCS
                os.remove(local_path)

    # Optionally, you can also delete the local folders after uploading all files
    os.rmdir(folder_db_name)
    os.rmdir("vdb_summary")


def delete_from_gcs(user_id, cycle_id):
    """delete from gcs"""
    prefix = f"{user_id}/vdb_{cycle_id}/"
    delete_objects_with_prefix(BUCKET_NAME, prefix)
