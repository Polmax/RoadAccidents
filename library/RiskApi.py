from flask import Flask
from flask_restful import Resource,Api
from RiskLocation import acess_risk_location
from tensorflow.keras.models import load_model
import tensorflow as tf
import json
import os

app = Flask("__accident_risk_api__")
api = Api(app)


def read_settings(f):
    with open(f) as fp:
        settings = json.load(fp)['settings']
    model1 = settings['model1']
    model2 = settings['model2']
    cell_x = settings["cell_size_x"]
    cell_y = settings["cell_size_y"]

    model1 = load_model(model1)
    model2 = load_model(model2)

    return (model1,model2,cell_x,cell_y)

class PredictRisk(Resource):
    def get(self,latitude,longitude,accuracy="detailed"):
        latitude = float(latitude)
        longitude = float(longitude)
        danger = acess_risk_location(latitude,longitude,model1,model2,accuracy)
        print(f"lat: {latitude},lon: {longitude},acc: {accuracy}")
        return danger

api.add_resource(PredictRisk, '/risk_prediction_lat=<latitude>_lon=<longitude>')

key = "Aqk4d8d5q_eWvI3oGYPNI-NdIuS5fEt3U-AnDWxNAzyM2Dn_v2vn2BbgD_8F-jIh"
model1,model2,_,_ = read_settings("settings.json")

os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'


if __name__ == "__main__":    
    print("loaded model")
    app.run(debug=False)

