#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 23:44:28 2020

@author: ewa
"""

# main.py
from hashlib import sha256
from fastapi import FastAPI, Request, Cookie, Depends, HTTPException, status, Response 
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import RedirectResponse

app = FastAPI()
count = -1
patients = {}
security = HTTPBasic()
app.secret_key = "very constatn and random secret, best 64 characters"
app.tokens_list = []

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "trudnY")
    correct_password = secrets.compare_digest(credentials.password, "PaC13Nt")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credentials.username, credentials.password


class Patient(BaseModel):
    name: str
    surename: str 
@app.get("/")
def root():
    return {"message":  "Hello World during the coronavirus pandemic!"}

@app.post("/login")
def login(credentials_user = Depends(get_current_username)):
    user = credentials_user[0]
    password =  credentials_user[1]
    session_token = sha256(bytes(f"{user}{password}{app.secret_key}", encoding='utf8')).hexdigest()
    app.tokens_list.append(session_token)
    response = RedirectResponse(url = "/welcome")
    response.set_cookie(key="session_token", value=session_token)
    return response

   
@app.api_route("/welcome", methods=["GET", "POST"])
async def welcome():
    return {"message":"Welcome!"}

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

