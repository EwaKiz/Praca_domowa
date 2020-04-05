#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 23:44:28 2020

@author: ewa
"""

# main.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()
count = -1
patients = {}

class Patient(BaseModel):
    name: str
    surename: str 


@app.get("/")
def root():
    return {"message":  "Hello World during the coronavirus pandemic!"}


@app.api_route("/method", methods=["GET", "POST", "DELETE", "PUT"])
async def method(request: Request):
    return {"method": request.method}


@app.post("/patient/")
async def set_patient(patient:Patient):
    global count, patients
    count += 1
    patients[count] = patient
    return {"id" : count ,"patient": patient}

    
@app.get("/patient/{pk}")
async def get_patient(pk:int):
    global patients
    if pk in patients.keys():
        return patients[pk]
    else:
        return JSONResponse(status_code=204, content={"message": "Patient not found"})

