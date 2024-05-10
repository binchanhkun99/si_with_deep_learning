import os

import sqlite3
from fastapi import HTTPException, Form
from pydantic import BaseModel
# Kiểm tra và tạo bảng events trong cơ sở dữ liệu nếu chưa tồn tại
def create_events_table():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS events
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name_event TEXT,
                      address TEXT,
                      folder TEXT,
                      banner TEXT,
                      limit_race INTEGER,
                      start_date TEXT,
                      number_date INTEGER)''')
    conn.commit()
    conn.close()
def get_all_events(limit=10, page=1):
    # Tính toán offset dựa trên trang và số lượng giới hạn
    offset = (page - 1) * limit

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Thực thi truy vấn để lấy các sự kiện với phân trang
    cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    events = cursor.fetchall()

    # Đóng kết nối đến cơ sở dữ liệu
    conn.close()

    # Format kết quả thành danh sách các từ điển
    formatted_events = []
    for event in events:
        formatted_event = {
            "id": event[0],
            "name_event": event[1],
            "address": event[2],
            "folder": event[3],
            "banner": event[4],
            "limit_race": event[5],
            "start_date": event[6],
            "number_date": event[7]
        }
        formatted_events.append(formatted_event)

    return formatted_events

# Kiểm tra và tạo cơ sở dữ liệu events.db nếu chưa tồn tại
def create_database():
    if not os.path.exists('events.db'):
        # Tạo mới cơ sở dữ liệu
        open('events.db', 'w').close()
        # Tạo bảng events trong cơ sở dữ liệu mới tạo
        create_events_table()