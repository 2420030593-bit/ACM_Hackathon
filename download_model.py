import urllib.request
import zipfile
import os

url = 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip'
zip_path = 'model_better.zip'
extract_dir = 'model'

print(f"Downloading model from {url}...")
urllib.request.urlretrieve(url, zip_path)

print(f"Extracting model to {extract_dir}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

os.remove(zip_path)
print("Model download and extraction complete.")
