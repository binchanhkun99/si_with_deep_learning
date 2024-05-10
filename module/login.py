# login.py

import sqlite3
from fastapi import HTTPException, Form
from pydantic import BaseModel
import jwt


class UserRegistration(BaseModel):
    username: str
    password: str


def register_user(username: str = Form(...), password: str = Form(...)):
    user_data = UserRegistration(username=username, password=password)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      password TEXT)''')
    conn.commit()

    username = user_data.username
    password = user_data.password

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

    return {"message": "User registered successfully"}

def generate_token(username: str):

    return jwt.encode({"username": username}, "duytrapboy", algorithm="HS256")
def login_user(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    stored_password = user[2]  # Lấy mật khẩu đã lưu trong cơ sở dữ liệu
    if password != stored_password:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Trả về thông tin người dùng và token
    token = generate_token(username)  # Hàm generate_token() chưa được định nghĩa
    return {"username": username, "token": token}


def create_events_table():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS events
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name_event TEXT,
                      address TEXT,
                      banner TEXT,
                      start_date TEXT,
                      number_date INTEGER)''')
    conn.commit()
    conn.close()