import requests


def send_batch(image_paths):
    images = dict()

    for filename in image_paths:
        print(filename)
        images[filename] = open(filename, 'rb')
    
    try:
        requests.post("http://localhost:3000/upload-images", files=images)
    except Exception as e:
        print(e)
