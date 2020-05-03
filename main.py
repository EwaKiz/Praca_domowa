#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 23:44:28 2020

@author: ewa
"""

# main.py
import sqlite3 
from hashlib import sha256
from fastapi import FastAPI, Request, Cookie, Depends, HTTPException, status, Response 
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

app = FastAPI()
count = 1
patients = {}
security = HTTPBasic()
app.secret_key = "very constatn and random secret, best 64 characters"
app.tokens_list = []
templates = Jinja2Templates(directory="templates")


    
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "trudnY")
    correct_password = secrets.compare_digest(credentials.password, "PaC13Nt")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    session_token = sha256(bytes(f"{credentials.username}{credentials.password}{app.secret_key}", encoding='utf8')).hexdigest()
    app.tokens_list.append(session_token)
    print (app.tokens_list)
    return session_token

def check_token(token: str):
    if token not in app.tokens_list:
        raise HTTPException(status_code=401, detail="Unathorized")

class Patient(BaseModel):
    name: str
    surname: str
    
class Album(BaseModel):
    title: str
    artist_id: int
    
class Customer(BaseModel):
    company: str =None
    address: str =None
    city: str = None
    state: str= None
    country: str = None
    postalcode: str= None
    fax: str =None
    
@app.get("/")
def root():
    return {"message":  "Hello World during the coronavirus pandemic!"}

@app.post("/login")
def login(response: Response, session_token = Depends(get_current_username)):
    response = RedirectResponse(url = "/welcome")
    response.set_cookie(key="session_token", value=session_token)
    return response

   
@app.api_route("/welcome", methods=["GET", "POST"])
async def welcome(request: Request, session_token: str = Cookie(None)):
    check_token(session_token)
    return templates.TemplateResponse("welcome.html", {"request": request, "user": "trudnY"})

@app.api_route("/method", methods=["GET", "POST", "DELETE", "PUT"])
async def method(request: Request):
    return {"method": request.method}

@app.post("/logout")
def logout(session_token: str = Cookie(None)):
    check_token(session_token)
    app.tokens_list = [i for i in app.tokens_list if i != session_token]
    return RedirectResponse(url = "/")


@app.post("/patient/")
async def set_patient(patient:Patient, session_token: str = Cookie(None)):
    check_token(session_token)
    global count, patients
    count += 1
    patients[count] = patient
    return RedirectResponse(url = "/patient/{patient_id}".format(patient_id=count))


@app.get("/patient/")
async def get_all_patients(session_token: str = Cookie(None)):
    check_token(session_token)
    return JSONResponse(jsonable_encoder(patients))


@app.post("/patient/{pk}")
async def return_patient(pk:int, patient:Patient, session_token: str = Cookie(None)):
    """return after post"""
    check_token(session_token)
    global count, patients
    return JSONResponse(jsonable_encoder(patients[pk]))


@app.get("/patient/{pk}")
async def get_patient(pk:int, session_token: str = Cookie(None)):
    check_token(session_token)
    global patients
    if pk in patients.keys():
        return JSONResponse(jsonable_encoder(patients[pk]))
    else:
        return JSONResponse(status_code=404, content={"message": "Patient not found"})

@app.delete("/patient/{pk}")
async def delete_patient(pk:int, session_token: str = Cookie(None)):
    check_token(session_token)
    global count, patients
    if pk in patients.keys():
        del patients[pk]
        return JSONResponse(status_code=200, content={"message": "Patient {id} deleted!".format(id=pk)})
    else:
        return JSONResponse(status_code=404, content={"message": "Patient not found"})
    
    
@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()




@app.get("/tracks")
async def all_tracks(page:int=0, per_page:int=10):
    tracks = app.db_connection.execute("select * from tracks order by TrackId ASC ").fetchall()
    tracks = tracks[page*per_page:(page+1)*per_page]
    keys = ["TrackId",
        "Name",
        "AlbumId",
        "MediaTypeId",
        "GenreId",
        "Composer",
        "Milliseconds",
        "Bytes",
        "UnitPrice"]
    tracks = [dict(zip(keys, x)) for x in tracks]
    return tracks



@app.get("/tracks/composers")
async def composers(composer_name:str):
    #tracks = app.db_connection.execute("select Name from tracks where Composer LIKE ? order by Name ASC ", ('%'+composer_name+'%',)).fetchall()
    tracks = app.db_connection.execute("select Name from tracks where Composer = ? order by Name ASC ", (composer_name,)).fetchall()
    tracks = [x[0] for x in tracks]
    if tracks:
        return tracks
    else:
        resp= {'error': composer_name}
        return JSONResponse(status_code=404, content={'detail': resp})

@app.post("/albums")
async def albums_add(album: Album):
    artists = app.db_connection.execute(
        "SELECT ArtistId FROM artists WHERE ArtistId = ?", (album.artist_id,)
    ).fetchall()
    if artists:
        cursor = app.db_connection.execute(
            "INSERT INTO albums (Title, ArtistId) VALUES (?,?)", (album.title,album.artist_id)
        )
        app.db_connection.commit()
        new_album_id = cursor.lastrowid
        app.db_connection.row_factory = sqlite3.Row
        album = app.db_connection.execute(
            "SELECT *FROM albums WHERE AlbumId = ?",
            (new_album_id, )).fetchone()
        json_compatible_item_data = jsonable_encoder(album)
        return JSONResponse(status_code=201, content=json_compatible_item_data)
    else:
        return JSONResponse(status_code=404, content={'detail': {'error': "Artist not in database"}})


@app.get("/albums/{album_id}")
async def albums_get(album_id:int):
    app.db_connection.row_factory = sqlite3.Row
    album = app.db_connection.execute(
            "SELECT *FROM albums WHERE AlbumId = ?",
            (album_id, )).fetchone()
    json_compatible_item_data = jsonable_encoder(album)
    return JSONResponse(status_code=200, content=json_compatible_item_data)

@app.put("/customers/{customer_id}")
async def update_customer(customer_id: int,customer: Customer):
    cust_id = app.db_connection.execute(
        "SELECT CustomerId FROM Customers WHERE CustomerId = ?", (customer_id,)
    ).fetchall()
    if cust_id:
        dictionary =  customer.dict()
        columns = []
        vals = []
        for column in dictionary.keys():
            if dictionary[column] != None:
                columns.append(column)
                vals.append(dictionary[column])
        columns = [f"{x} = ? " for x in columns]
        query = "UPDATE customers SET "
        for i in range(len(columns)):
            query += columns[i]
            if i != len(columns)-1:
                query += ","
        query += "WHERE customerid = ?"
        print(query)
        vals.append(customer_id)
        vals = tuple(vals)
        cursor = app.db_connection.execute(
            query, vals
        )
        app.db_connection.commit()
        app.db_connection.row_factory = sqlite3.Row
        customer = app.db_connection.execute(
            """SELECT * 
             FROM customers WHERE customerid = ?""",
            (customer_id, )).fetchone()
    
        return customer
    else:
        return JSONResponse(status_code=404, content={'detail': {'error': "Customer not in database"}})

            
            
@app.get("/sales")
async def stats(category: str):
    if category == "customers":
        app.db_connection.row_factory = sqlite3.Row
        customers = app.db_connection.execute(
            """SELECT customerid,email, phone, ROUND(SUM(total),2) AS Sum 
            FROM invoices NATURAL JOIN customers group by customerid ORDER BY Sum DESC, customerid""").fetchall()
    
        return customers
    elif category == "genres":
        app.db_connection.row_factory = sqlite3.Row
        genres = app.db_connection.execute(
            """SELECT genres.Name , Sum(Quantity) AS Sum
            FROM (invoice_items NATURAL JOIN tracks) x INNER JOIN genres ON x.GenreId = genres.GenreId 
            GROUP BY genres.GenreId 
            ORDER BY sum DESC, genres.Name """).fetchall()
    
        return genres
    else:
        return JSONResponse(status_code=404, content={'detail': {'error': "Unknown category"}})
        
    













        
    

