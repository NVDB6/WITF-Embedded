import requests


def send_batch(image_paths):
    images = dict()

    for filename in image_paths:
        images[filename] = open(filename, 'rb')
        
    response = requests.post("http://localhost:3000/upload-images", files=images)
