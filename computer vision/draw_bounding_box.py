
import cv2
import numpy as np
from config import*
import requests
import base64
import io
from PIL import Image

# ANNOTATION RECEIVED
data = [{"image": "elephant.jpg", 
         "annotations": [{"label": "Elephant", 
                          "coordinates": {"x": 712, "y": 303, "width": 381, "height": 287},
                          "confidence": 0.8}]}]
print(data)  
img = r'C:\Users\vinshen\Desktop\vinshen_workspace\Year_3_Project\Mobile_Connectivity\Codes\new_packet_structure\draw_box_roboflow\paper1.jpg'
img = cv2.imread(img)
def bounding_box_and_text(annotations, img):
    
    for box in annotations:
        label = box['label']
        x = box['coordinates']['x']
        y = box['coordinates']['y']
        w = box['coordinates']['width']
        h = box['coordinates']['height']
        confidence = box['confidence']
        # shift x & y as annotations was meant for roboflow
        x  -= w/2
        y  -= w/2
        x = int(x)
        y = int(y)
        # draw rectangle
        cv2.rectangle(img, (x, y), (x + w, h + y), color=(0, 255, 0), thickness=2)
        # Setting label to print about bounding box
        text_box = label + str(" (") + str(round(confidence*100,2)) +str("%)")

        # Get location of bounding box
        labelSize, baseLine = cv2.getTextSize(text_box, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size

        # Put text above bounding box
        cv2.rectangle(img, (x, y), (x+labelSize[0]+5, y+baseLine-30), (255, 255, 255), cv2.FILLED)
        cv2.putText(img, text_box, (x+10, y-7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 2)

    # cv2.imshow('cock', img)
    # cv2.waitKey(2000)
  

bounding_box_and_text(data[0]['annotations'],img)


# remember to remove confidence from the annotations before sending to roboflow api

for box in data[0]['annotations']:
    del box['confidence']

print(data)



# PROCEED TO ROBOFLOW API

# After all detections, Convert image
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
pilImage = Image.fromarray(img)

# Convert to JPEG Buffer
buffered = io.BytesIO()
pilImage.save(buffered, quality=90, format="JPEG")

# Base 64 Encode
img_str = base64.b64encode(buffered.getvalue())
img_str = img_str.decode("ascii")
print("decoded and ready to send!")


# Construct the URL
image_upload_url = "".join([
    "https://api.roboflow.com/dataset/", DATASET_NAME, "/upload",
    "?api_key=", ROBOFLOW_API_KEY,
    "&name=captured.jpg",
    "&split=train"
])

r = requests.post(image_upload_url, data=img_str, headers={
    "Content-Type": "application/x-www-form-urlencoded"
})

imageId = r.json()['id']
print(imageId)

# After all detections,
# Save to Json File
with open("activeLearning.json", 'w') as outfile:
    json.dump(data, outfile)

annotationFilename = "activeLearning.json"

# Read Annotation as String
annotationStr = open("activeLearning.json", "r").read()
print(annotationStr)

# Construct the URL
annotation_upload_url = "".join([
    "https://api.roboflow.com/dataset/", DATASET_NAME, "/annotate/", imageId,
    "?api_key=", ROBOFLOW_API_KEY,
    "&name=", annotationFilename
])
print(annotation_upload_url)
# POST to the API


r = requests.post(annotation_upload_url, data=annotationStr, headers={
    "Content-Type": "text/plain"
})

print(r.json()['success'])

print("Done Bossku")