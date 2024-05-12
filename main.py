from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from deepface import DeepFace
from module.login import register_user, UserRegistration, login_user
from module.events import create_database, get_all_events
import logging

from deepface.models.FacialRecognition import FacialRecognition
import numpy as np
import easyocr
import base64
import cv2
import os
import sqlite3

import json
app = FastAPI()
folder_search = "search"
folder_data_search = "static"
backend = "retinaface"
model = "Facenet512"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



static_path = os.path.join(os.path.dirname(__file__), folder_data_search)

app.mount("/static", StaticFiles(directory=static_path), name="static")
app.mount("/banner", StaticFiles(directory="banner"), name="banner")



@app.get("/")
def read_root():
    return {"message": "home page"}


@app.get("/image")
def get_images(folder_data_search: str = Query(..., description="Folder containing images")):
    if not os.path.exists(folder_data_search):
        raise HTTPException(status_code=404, detail="Folder not found")

    jpg_files = []
    for filename in os.listdir(folder_data_search):
        if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
            jpg_files.append(os.path.join(folder_data_search, filename))
    return jpg_files

# folder_data_search = "static"
class Image(BaseModel):
    type: str
    base64_string: str
    folder_data_search: str
@app.post("/search")
async def search_image(image: Image):
    img_path = ""
    matching_images = []
    try:

        image_data = base64.b64decode(image.base64_string)
        if image.type.lower() not in ["jpeg", "jpg", "png"]:
            raise HTTPException(status_code=400, detail="Unsupported image format")

        image_name = os.urandom(24).hex() + "." + image.type
        img_path = folder_search + "/" + image_name
        with open(img_path, "wb") as f:
            f.write(image_data)

        for result in DeepFace.find(img_path=img_path, db_path=folder_data_search, detector_backend=backend, model_name=model): #thay db_path thành đường dẫn đến folder muốn phân tích
            for img in result.iloc[:,0]:
                matching_images.append(img)
    except FileNotFoundError as e:
        # Xử lý lỗi nếu tập tin hình ảnh không tồn tại
        print(f"File not found: {e}")
        return {"error": "Image file not found."}
    except Exception as e:
        # Xử lý các lỗi khác có thể xảy ra
        print(f"Error occurred: {e}")
        return {"error": f"Error occurred: {str(e)}"}
    finally:
        print("ccc")
        # Xóa tập tin hình ảnh sau khi hoàn thành
        if os.path.exists(img_path):
            os.remove(img_path)
    return list(dict.fromkeys(matching_images))



data_file = "ocr_data.json"

def read_and_store_ocr_data_first():
    try:
        # Kiểm tra xem tệp ocr_data.json đã tồn tại hay chưa
        if os.path.exists(data_file):
            try:
                # Nếu tệp tồn tại, đọc dữ liệu đã lưu trữ
                with open(data_file, 'r') as f:
                    ocr_data = json.load(f)
            except json.decoder.JSONDecodeError:
                # Xử lý ngoại lệ nếu dữ liệu không phải là JSON hợp lệ
                print("Lỗi: Dữ liệu trong tệp không phải là JSON hợp lệ.")
                ocr_data = {}
        else:
            ocr_data = {}

        reader = easyocr.Reader(["en"], gpu=True)
        print(f"Data pkl: {os.listdir(folder_data_search)}")
        for filename in os.listdir(folder_data_search):
            if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
                img_path = os.path.join(folder_data_search, filename)

                if filename in ocr_data:
                    text = ocr_data[filename]
                else:
                    img = cv2.imread(img_path)
                    text = reader.readtext(img)
                    text = [t[1] for t in text]
                    ocr_data[filename] = text

        with open(data_file, 'w') as f:
            json.dump(ocr_data, f)

    except Exception as e:
        print(e)



# Đường dẫn đến tệp SQLite
db_file = "static.db"

# Thiết lập kết nối tới cơ sở dữ liệu
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

# Tạo bảng trong cơ sở dữ liệu
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_data (
                filename TEXT PRIMARY KEY,
                text TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(e)

# Đọc và lưu dữ liệu OCR
def read_and_store_ocr_data(folder_data_search):
    try:
        # folder_data_search = 'G:/dala-2024'
        # Kiểm tra xem tệp ocr_data.json đã tồn tại hay chưa
        data_file = f"{folder_data_search}.json"  # Tạo tên file dựa trên folder_data_search
        if os.path.exists(data_file):
            try:
                # Nếu tệp tồn tại, đọc dữ liệu đã lưu trữ
                with open(data_file, 'r') as f:
                    ocr_data = json.load(f)
            except json.decoder.JSONDecodeError:
                # Xử lý ngoại lệ nếu dữ liệu không phải là JSON hợp lệ
                print("Lỗi: Dữ liệu trong tệp không phải là JSON hợp lệ.")
                ocr_data = {}
        else:
            ocr_data = {}

        conn = create_connection()
        if conn is None:
            print("Lỗi: Không thể kết nối tới cơ sở dữ liệu.")
            return

        # Nếu cơ sở dữ liệu không tồn tại, tạo mới và tạo bảng
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{folder_data_search}'")
        if not cursor.fetchone():
            # Thực hiện tạo bảng bằng câu truy vấn SQL
            create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_data_search} (filename TEXT, text TEXT)"
            cursor.execute(create_table_query)

            # Tạo ra dữ liệu OCR nếu không tồn tại
            reader = easyocr.Reader(["en"], gpu=True)
            for filename in os.listdir(folder_data_search): #Thay folder_data_search thành đường dẫn đén foler ảnh cần phân tích
                if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
                    img_path = os.path.join(folder_data_search, filename)
                    if filename in ocr_data:
                        text = ocr_data[filename]
                    else:
                        img = cv2.imread(img_path)
                        text = reader.readtext(img)
                        text = [t[1] for t in text]
                        ocr_data[filename] = text
                    cursor.execute(f"INSERT INTO {folder_data_search} (filename, text) VALUES (?, ?)", (filename, json.dumps(text)))  # Sử dụng folder_data_search trong truy vấn
            conn.commit()

        conn.close()

        # Lưu dữ liệu OCR vào tệp
        with open(data_file, 'w') as f:
            json.dump(ocr_data, f)

    except Exception as e:
        print(e)


# Thực hiện tìm kiếm bằng LIKE trong cơ sở dữ liệu
@app.get("/search/{input_text}/{folder_data_search}")
async def search_text(input_text: str, folder_data_search: str, q: str = ""):
    try:
        # Đảm bảo rằng dữ liệu OCR đã được đọc và lưu trữ
        read_and_store_ocr_data(folder_data_search)
        conn = create_connection()
        matching_images = []
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(f"SELECT filename FROM {folder_data_search} WHERE text LIKE ?", ('%' + input_text.lower() + '%',))  # Sử dụng folder_data_search trong truy vấn
            rows = cursor.fetchall()
            matching_images = [os.path.join(folder_data_search, row[0]) for row in rows]
            conn.close()
        return matching_images
    except Exception as e:
        print(e)
        return {"error": f"Error occurred: {str(e)}"}

def clear_data(folder):
    try:
        # Xoá tệp ocr_data.json nếu tồn tại
        if os.path.exists(data_file):
            os.remove(data_file)

        # Xoá dữ liệu trong cơ sở dữ liệu
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {folder}")
            conn.commit()
            conn.close()
    except Exception as e:
        print(e)


@app.get("/training_text/{folder}")
async def training_text(folder: str, q: str = ""):
    try:
        # Xoá dữ liệu
        clear_data(folder)

        # Đọc và lưu dữ liệu OCR từ đầu
        read_and_store_ocr_data(folder)

        return {"message": "Training completed successfully."}
    except Exception as e:
        print(e)
        return {"error": f"Error occurred: {str(e)}"}
@app.post("/register/")
async def register_user_endpoint(username: str = Form(...), password: str = Form(...)):
    return register_user(username, password)
@app.post("/login/")
async def login_user_endpoint(username: str = Form(...), password: str = Form(...)):
    return login_user(username, password)


#Thêm mới và chỉnh sửa events
BANNER_DIR = "banner"

# Hàm lưu hình ảnh banner vào thư mục banner và trả về đường dẫn của hình ảnh
def save_banner(image_base64, file_ext):
    if not os.path.exists(BANNER_DIR):
        os.makedirs(BANNER_DIR)

    image_data = base64.b64decode(image_base64)
    banner_path = os.path.join(BANNER_DIR, "image{}.{}".format(len(os.listdir(BANNER_DIR)) + 1, file_ext))

    with open(banner_path, "wb") as f:
        f.write(image_data)

    return banner_path


@app.post("/create_event/")
async def create_event(name_event: str = Form(...), address: str = Form(...),
                       folder: str = Form(...),
                       typeFile: str = Form(...),
                       start_date: str = Form(...), number_date: int = Form(...),
                       image_base64: str = Form(...)):
    # Kiểm tra và tạo cơ sở dữ liệu events.db nếu chưa tồn tại
    create_database()

    # Lưu hình ảnh banner vào thư mục banner và lấy đường dẫn của hình ảnh
    banner_path = save_banner(image_base64, file_ext=typeFile)

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Thêm thông tin sự kiện vào cơ sở dữ liệu
    cursor.execute("INSERT INTO events (name_event, address, banner, start_date, folder, limit_race, number_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (name_event, address, banner_path, start_date, folder, 30, number_date))
    conn.commit()
    conn.close()

    # Trả về thông báo cho người dùng
    return {"message": "Event created successfully"}

@app.post("/edit_event/{event_id}")
async def edit_event(event_id: int, name_event: str = Form(None), address: str = Form(None),
                     folder: str = Form(None), typeFile: str = Form(None),
                     start_date: str = Form(None), number_date: int = Form(None),
                     image_base64: str = Form(None)):
    # Kiểm tra xem có dữ liệu được gửi lên không
    if name_event is None and address is None and folder is None and typeFile is None and start_date is None and number_date is None and image_base64 is None:
        return {"message": "No data sent for updating"}

    # Kiểm tra và tạo cơ sở dữ liệu events.db nếu chưa tồn tại
    create_database()

    # Khởi tạo danh sách các trường và giá trị mới
    fields_to_update = []
    new_values = []

    # Kiểm tra từng trường và giá trị tương ứng
    if name_event is not None:
        fields_to_update.append("name_event")
        new_values.append(name_event)
    if address is not None:
        fields_to_update.append("address")
        new_values.append(address)
    if folder is not None:
        fields_to_update.append("folder")
        new_values.append(folder)
    if typeFile is not None:
        fields_to_update.append("banner")
        banner_path = save_banner(image_base64, file_ext=typeFile)
        new_values.append(banner_path)
    if start_date is not None:
        fields_to_update.append("start_date")
        new_values.append(start_date)
    if number_date is not None:
        fields_to_update.append("number_date")
        new_values.append(number_date)

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Cập nhật thông tin sự kiện trong cơ sở dữ liệu
    set_clause = ", ".join([f"{field} = ?" for field in fields_to_update])
    query = f"UPDATE events SET {set_clause} WHERE id = ?"
    cursor.execute(query, (*new_values, event_id))
    conn.commit()
    conn.close()

    # Trả về thông báo cho người dùng
    return {"message": f"Event with id {event_id} has been updated successfully"}


@app.post("/delete_event/{event_id}")
async def delete_event(event_id: int):
    # Kiểm tra và tạo cơ sở dữ liệu events.db nếu chưa tồn tại
    create_database()

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Kiểm tra xem sự kiện có tồn tại không
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    if event is None:
        conn.close()
        return {"message": f"Event with id {event_id} not found"}

    # Xóa sự kiện khỏi cơ sở dữ liệu
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    # Trả về thông báo cho người dùng
    return {"message": f"Event with id {event_id} has been deleted successfully"}

@app.get("/events/")
async def read_events(limit: int = 10, page: int = 1):
    # Gọi hàm get_all_events() để lấy các sự kiện với phân trang
    events = get_all_events(limit=limit, page=page)
    if not events:
        raise HTTPException(status_code=404, detail="No events found")
    return {"events": events}

@app.get("/events_by_id")
def get_event(event_id: int):
    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Thực hiện truy vấn để lấy thông tin của sự kiện dựa trên ID
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    # Đóng kết nối đến cơ sở dữ liệu
    conn.close()

    # Kiểm tra xem sự kiện có tồn tại không
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # Format thông tin của sự kiện thành một từ điển
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

    return formatted_event




@app.post("/update_event_limit_race/")
async def update_event_limit_race(event_id: int = Form(...), limit_race: int = Form(...)):
    try:
        # Kết nối đến cơ sở dữ liệu
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()

        # Thực hiện câu lệnh SQL để cập nhật trường limit_race
        cursor.execute("UPDATE events SET limit_race = ? WHERE id = ?",
                       (limit_race, event_id))
        conn.commit()

        # Đóng kết nối đến cơ sở dữ liệu
        conn.close()

        # Trả về thông báo cho người dùng
        return {"message": f"Event with id {event_id} updated successfully"}

    except Exception as e:
        return {"error": str(e)}
def create_contact_table_if_not_exists():
    conn = sqlite3.connect('contact')
    cursor = conn.cursor()

    # Kiểm tra xem bảng contact đã tồn tại chưa
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact'")
    table_exists = cursor.fetchone()

    # Nếu bảng không tồn tại, tạo mới
    if not table_exists:
        cursor.execute('''CREATE TABLE contact (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            company_name TEXT,
                            address_company TEXT,
                            phone TEXT,
                            email TEXT
                        )''')
        conn.commit()

    conn.close()





@app.post("/add_contact/")
async def add_contact(company_name: str = Form(...), address_company: str = Form(...),
                      phone: str = Form(...), email: str = Form(...)):
    create_contact_table_if_not_exists()
    conn = sqlite3.connect('contact')
    cursor = conn.cursor()

    # Thêm thông tin liên hệ mới vào bảng contact
    cursor.execute("INSERT INTO contact (company_name, address_company, phone, email) VALUES (?, ?, ?, ?)",
                   (company_name, address_company, phone, email))
    conn.commit()
    conn.close()

    return {"message": "Contact added successfully"}
@app.post("/update_contact")
async def update_contact(contact_id: int = Form(None), company_name: str = Form(None),
                         address_company: str = Form(None), phone: str = Form(None),
                         email: str = Form(None)):
    # Kiểm tra xem có cung cấp ID của contact không
    if contact_id is None:
        raise HTTPException(status_code=400, detail="Contact ID is required")

    conn = sqlite3.connect('contact')
    cursor = conn.cursor()

    # Kiểm tra xem contact có tồn tại không
    cursor.execute("SELECT * FROM contact WHERE id=?", (contact_id,))
    existing_contact = cursor.fetchone()

    if existing_contact:
        # Nếu contact đã tồn tại, thực hiện cập nhật thông tin
        cursor.execute("UPDATE contact SET company_name=?, address_company=?, phone=?, email=? WHERE id=?",
                       (company_name, address_company, phone, email, contact_id))
        conn.commit()
        conn.close()
        return {"message": "Contact updated successfully"}
    else:
        # Nếu contact không tồn tại, thực hiện thêm mới
        cursor.execute("INSERT INTO contact (company_name, address_company, phone, email) VALUES (?, ?, ?, ?)",
                       (company_name, address_company, phone, email))
        conn.commit()
        conn.close()
        return {"message": "Contact added successfully"}

@app.get("/get_contact/{contact_id}")
async def get_contact(contact_id: int):
    # Kiểm tra xem contact_id có hợp lệ không (không âm)
    if contact_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid contact ID")

    conn = sqlite3.connect('contact')
    cursor = conn.cursor()

    # Thực hiện truy vấn để lấy thông tin của contact có ID tương ứng
    cursor.execute("SELECT * FROM contact WHERE id=?", (contact_id,))
    contact = cursor.fetchone()

    conn.close()

    # Kiểm tra xem contact có tồn tại không
    if contact:
        return {
            "id": contact[0],
            "company_name": contact[1],
            "address_company": contact[2],
            "phone": contact[3],
            "email": contact[4]
        }
    else:
        raise HTTPException(status_code=404, detail="Contact not found")
# Thiết lập cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    try:
        logger.info("Starting the application...")

        # Khởi chạy ứng dụng bằng uvicorn
        uvicorn.run(app, host="0.0.0.0", port=2053)

    except Exception as e:
        logger.error(f"An error occurred while running the application: {e}")
