from flask import Flask, request, redirect, url_for, render_template, Response
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import os
import zipfile

app = Flask(__name__)

# Azure blob storage settings
AZURE_CONNECTION_STRING ="DefaultEndpointsProtocol=https;AccountName=mystorageacc123123;AccountKey=7hnTQSiYzV87WwXZgGEZL2xTBJj1KfJtnN8JeHmirIxwHV8wCCttJWIma7tegvOsJrui8l9gTtkX+AStO5EMbg==;EndpointSuffix=core.windows.net"
UPLOAD_CONTAINER = "datafiles"
DOWNLOAD_CONTAINER = "media"
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

def save_blob(file_path, container_name):
    blob_client = blob_service_client.get_blob_client(container_name, file_path)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)

def compress_and_upload(file_path, original_filename):
    zip_file_path = original_filename + ".zip"
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path)
    save_blob(zip_file_path, DOWNLOAD_CONTAINER)
    os.remove(zip_file_path)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        file_path = os.path.join(os.getcwd(), filename)
        file.save(file_path)  # Save the file temporarily in the current directory
        save_blob(file_path, UPLOAD_CONTAINER)
        compress_and_upload(file_path, filename)
        os.remove(file_path)  # Remove the original file
        return redirect(url_for('download_file', filename=filename + ".zip"))
    return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
    blob_client = blob_service_client.get_blob_client(DOWNLOAD_CONTAINER, filename)
    download_stream = blob_client.download_blob().readall()
    return Response(
        download_stream,
        mimetype="application/zip",
        headers={"Content-disposition": 'attachment; filename=' + filename}
    )

if __name__ == '__main__':
    app.run(debug=True)
