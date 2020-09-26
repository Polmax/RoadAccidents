from tensorflow.keras.models import load_model
import json
import requests
import cv2 
import numpy as np

def predict_risk_img(img,model):
  predictions = model.predict(np.array([img]))
  return np.argmax(predictions)

def acess_risk_img(img,model1,model2,accuracy="detailed"):
    
    danger = dict()
    if accuracy == "low":
        danger["low accuracy"] =  str(predict_risk_img(img,model1))

    else:
        danger["low accuracy"] = str(predict_risk_img(img,model1))
        if danger["low accuracy"] == "1":
            danger["detailed accuracy"]  = str(predict_risk_img(img,model2))
        else:
            danger["detailed accuracy"] = "0"

        
    return danger
  

def getImageBing(latitude,longitude):
    key = "Aqk4d8d5q_eWvI3oGYPNI-NdIuS5fEt3U-AnDWxNAzyM2Dn_v2vn2BbgD_8F-jIh"
    link = f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{latitude},{longitude}/19?mapSize=500,500&key={key}"
    buffer = requests.get(link).content
    img = cv2.imdecode(np.frombuffer(buffer, np.uint8), cv2.IMREAD_UNCHANGED)
    
    return img

def preprocess_image(img):
    img = img[:475]
    img = cv2.resize(img,(128,128))
    img = img / 255

    return img

def get_image(latitude,longitude,accuracy="detailed"):
    img = getImageBing(latitude,longitude)
    img = preprocess_image(img)
    return img

def acess_risk_location(latitude,longitude,model1,model2,accuracy):
    img = get_image(latitude,longitude)
    danger = acess_risk_img(img,model1,model2,accuracy)
    return danger
    