# Importing the required libraries
import cv2
import numpy as np
import os
import time
import os
import datetime

# Setting Thresholds
thres = 0.6
nms_threshold = 0.4

# Setup for class names
classNames= []
classFile = 'coco.names'
with open(classFile,'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Weights and config path
weightsPath = 'frozen_inference_graph.pb'
configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'

# Setting SSD 
net = cv2.dnn_DetectionModel(weightsPath,configPath)
net.setInputSize(320,320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# --------------------------------------------------------------------------
# Setting up pi camera 
from picamera.array import PiRGBArray
from picamera import PiCamera

camera = PiCamera()
camera.rotation = 180
camera.resolution = (640, 480)

# -------------------------------------------------------------------------
# Settting up GPIO Pins
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.IN)

import cv2
import requests

from config import *

import os
from PIL import Image
import base64
import io

# -------------------------------------------------------------------------

def performML():
    
    img = []
    confidence_array = []
    classIds = []
    confidence = []
    bbox = []
    
    # Capture 3 images
    for i in range(0,3):
        rawCapture = PiRGBArray(camera)
        camera.capture(rawCapture, format = "bgr")
        img.append(rawCapture.array)
    
    t0 = time.time()
    print("PIR DETECTED SOMETHING!!!")
    
    os.chdir('/home/pi/Desktop/4_ComputerVision/SSD/Captured')
                
    for index in range(0,3):

        cv2.imshow("Input Image", img[index])
        cv2.waitKey(2000)
        
        text = str(index) + str('.jpg')
        image = cv2.imwrite(text, img[index])
        
        # Perform network detection
        detect = net.detect(img[index], confThreshold=thres)
        
        a = []
        
        print("length of detect[1] is ",len(detect[1]))
        
        # If no detections have been made, append 0 confidence 
        if len(detect[1]) == 0:
            a = [0]
            confidence.append(a)
            
        else:
            confidence.append(detect[1])
        
        # Append class ID and bounding box location
        classIds.append(detect[0])
        bbox.append(detect[2])
        
        confidence_array.append(confidence[index])
        print("Confidence level is ", confidence[index])
    
    os.chdir('/home/pi/Desktop/4_ComputerVision/SSD')
    
    confidence_array = list(confidence_array)
    confidence_array = [list(i) for i in confidence_array]
    print("confidence array is ", confidence_array)
    
    max_value = max(confidence_array, key=max)
    print("The max_value is ", max_value)
    
    max_index = confidence_array.index(max_value)
    print("The max_index (The clearest photo) is photo number ", max_index+1)
        
    cv2.imshow("Clearest Output", img[max_index])
    cv2.waitKey(2000)
    
    bbox = list(bbox[max_index])
    confs = list(np.array(confidence[max_index]).reshape(1, -1)[0])
    confs = list(map(float, confidence[max_index]))
    
    try:
        indices = cv2.dnn.NMSBoxes(bbox, confs, thres, nms_threshold)
        print(indices)
        print("The number of detected objects are ", len(indices))
    
    except:
        print("No objects detected")
        quit()
    
    # Issue image, classIds and confidence
    img = img[max_index]
    classIds = classIds[max_index]
    confidence = confidence[max_index]
    
    print("classIds is ", classIds)
    
    # Set counting to zeros
    count_elephant = 0
    count_human = 0
    count_others = 0
    
    currenttime = str(datetime.datetime.now().strftime('%d_%m_%Y_%H-%M-%S')) + str('.jpg')
    
    # Desired dimension
    dim_x = 400
    dim_y = 300
    
    # After running detection, declare annotations for collection
    data = []
    annotations = []
    
    # resize image
    img = cv2.resize(img, (dim_x, dim_y), interpolation=cv2.INTER_AREA)
    
    print("number of detected objects are ", len(indices))
    
    # If there is a detection of an object
    if len(indices) > 0:
        for i in indices:
            # Get the rectangular box coordinates
            box = bbox[i]
            x, y, w, h = box[0], box[1], box[2], box[3]
            
            # After each detection, perform annotation reformation
            resize_x = dim_x/640
            resize_y = dim_y/480

            x = round(resize_x * x)
            w = round(resize_x * w)
            y = round(resize_y * y)
            h = round(resize_y * h)
            
            # Append annotations
            annotations.append({"label": classNames[classIds[i]-1].lower(),
                                "coordinates":{
                                    "x":x+w/2,
                                    "y":y+h/2,
                                    "width":w,
                                    "height":h
                                    }
                                })
            
            data.append({
                "image": "captured.jpg",
                "annotations": annotations
                })
            
            print("data is ", data)
            
            # Draw rectangle
            #cv2.rectangle(img, (x, y), (x + w, h + y), color=(0, 255, 0), thickness=2)
            
            # Setting label to print about bounding box
            label = classNames[classIds[i]-1].upper() + str(" (") + str(round(confidence[0]*100,2)) +str("%)")
            
            # Get location of bounding box
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
            
            # Put text above bounding box
            #cv2.rectangle(img, (x, y), (x+labelSize[0]+5, y+baseLine-30), (255, 255, 255), cv2.FILLED)
            #cv2.putText(img, label, (x+10, y-7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 2)
            
            # After performing ML, resize the image
            height, width, channel = img.shape
            print(width)
            print(height)
            
            # If the class detected is elephant 
            if classNames[classIds[i]-1].upper() == "ELEPHANT":
                count_elephant += 1
                print("Detected: Elephant!!!!!")
                
                # Number of elephants label
                number_label = "The number of detected " + classNames[classIds[i]-1] + " are " + str(count_elephant)
                
                # Put the number of elephants label on top
                #cv2.rectangle(img, (5,25), (5+labelSize[0], baseLine-20), (255, 255, 255), cv2.FILLED)
                #cv2.putText(img, number_label, (5,20), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 2)
                
                # Change and save elephant picture to folders
                os.chdir('/home/pi/Desktop/4_ComputerVision/SSD/Images/Elephant')
                image = cv2.imwrite(currenttime, img)
                os.chdir('..')
                
                # Show detected output
                cv2.imshow("Elephant!!!", img)
                cv2.waitKey(3000)
                
                cv2.destroyAllWindows()
                
                #return 1
            
            # If the class detected is person
            elif classNames[classIds[i]-1].upper() == "PERSON":
                count_human +=1
                print("Detected: Poacher!!!!!")
                
                # Number of human label
                number_label = "The number of detected " + classNames[classIds[i]-1] + " are " + str(count_human)
                
                # Put the number of human label on top
                labelSize, baseLine = cv2.getTextSize(number_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
                #cv2.rectangle(img, (5,25), (5+labelSize[0], baseLine-20), (255, 255, 255), cv2.FILLED)
                #cv2.putText(img, number_label, (5,20), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 2)
                
                # Change and save human picture to folders
                os.chdir('/home/pi/Desktop/4_ComputerVision/SSD/Images/Poacher')
                image = cv2.imwrite(currenttime, img)
                os.chdir('..')
                
                cv2.imshow("Poachers!!!", img)
                cv2.waitKey(3000)
                
                cv2.destroyAllWindows()
                
                #return 0 
                
            # If detected some other class objects
            else:
                count_others +=1
                print("Animal Detected: But not Elephant nor Poacher")
                
                os.chdir('/home/pi/Desktop/4_ComputerVision/SSD/Images/Others')
                image = cv2.imwrite(currenttime, img)
                os.chdir('..')
                
                # Change and save other object picture to folders
                cv2.imshow("Detected Others", img)
                cv2.waitKey(3000)
                
                cv2.destroyAllWindows()
        
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
        with open('/home/pi/Desktop/4_ComputerVision/SSD/activeLearning.json', 'w') as outfile:
            json.dump(data, outfile)
        
        annotationFilename = "activeLearning.json"
        
        # Read Annotation as String
        annotationStr = open('/home/pi/Desktop/4_ComputerVision/SSD/activeLearning.json', "r").read()
        print(annotationStr)
        
        # Construct the URL
        annotation_upload_url = "".join([
            "https://api.roboflow.com/dataset/", DATASET_NAME, "/annotate/", imageId,
            "?api_key=", ROBOFLOW_API_KEY,
            "&name=", annotationFilename
        ])

        # POST to the API
        r = requests.post(annotation_upload_url, data=annotationStr, headers={
            "Content-Type": "text/plain"
        })
        
        print("Done Bossku")
        
        # if confidence of detecteed object is below 0.6, send detected object to ROBOFLOW for active learning
    
    # If there is no detection of object
    else:
        os.chdir('/home/pi/Desktop/4_ComputerVision/SSD/Images/Undetected')
        image = cv2.imwrite(currenttime, img)
        os.chdir('..')
        
        cv2.imshow("No detection", img)
        cv2.waitKey(3000)
        
        cv2.destroyAllWindows()
        
        return 0
        
    cv2.destroyAllWindows()
    t1 = time.time()

    total = t1-t0
    print("The total time taken is", total)

if __name__ == '__main__':
    while True:
        
        val = GPIO.input(32)

        if (val == True):
            performML()
            #print("Elephant Presence: " + str(elephant))
                
        else:
            #print("Nothing Here!")
            pass

