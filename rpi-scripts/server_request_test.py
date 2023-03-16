import os
import requests

directory = '../resources/upload_images/'
images = dict()
path = ""
for filename in os.listdir(directory):
    path = os.path.join(directory, filename)
    images[filename] = open(path, 'rb')
print(images)
response = requests.post("http://localhost:3000/upload-images", files=images)