import json
import os
from app_config import BASE_DIR
directory = rf"roboflow_config.json" 
directory2 = os.path.join(BASE_DIR, directory)
with open(directory2, 'r') as f:
    config = json.load(f)
    # print(f)
    ROBOFLOW_API_KEY = config["ROBOFLOW_API_KEY"]
    ROBOFLOW_MODEL = config["ROBOFLOW_MODEL"]
    ROBOFLOW_SIZE = config["ROBOFLOW_SIZE"]
    LOCAL_SERVER = config["LOCAL_SERVER"]
    DATASET_NAME = config["DATASET_NAME"]

    FRAMERATE = config["FRAMERATE"]
    BUFFER = config["BUFFER"]

# Local Server Link
infer_url = "".join([
    "https://detect.roboflow.com/" + ROBOFLOW_MODEL,
    "?api_key=" + ROBOFLOW_API_KEY,
    "&name=YOUR_IMAGE.jpg"
])
if not LOCAL_SERVER:
    pass
else:
    infer_url = "".join([
        "http://127.0.0.1:9001/" + ROBOFLOW_MODEL,
        "?api_key=" + ROBOFLOW_API_KEY,
        "&name=YOUR_IMAGE.jpg"
    ])