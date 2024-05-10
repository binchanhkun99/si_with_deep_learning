import sqlite3
import pickle

# Đường dẫn đến tệp pkl và cơ sở dữ liệu SQLite
pkl_file_path = "../static/ds_facenet512_retinaface_v2.pkl"
sqlite_db_path = "image_database.db"

# Hàm để chèn dữ liệu từ tệp pkl vào cơ sở dữ liệu SQLite
def insert_pkl_to_sqlite():
    try:
        # Tạo kết nối đến cơ sở dữ liệu SQLite
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        # Tạo bảng trong cơ sở dữ liệu nếu chưa tồn tại
        cursor.execute('''CREATE TABLE IF NOT EXISTS pkl_data
                        (id INTEGER PRIMARY KEY,
                         pkl VARBINARY)''')

        # Đọc dữ liệu từ tệp pkl và chèn vào cơ sở dữ liệu SQLite
        with open(pkl_file_path, 'rb') as f:
            pkl_data = f.read()
            cursor.execute("INSERT INTO pkl_data (id, pkl) VALUES (?, ?)", (1, sqlite3.Binary(pkl_data)))

        # Commit và đóng kết nối
        conn.commit()
        conn.close()
        print("Data from pkl file inserted into SQLite database successfully.")

    except Exception as e:
        print(f"Error occurred while inserting pkl data into SQLite database: {e}")

# Hàm để đọc dữ liệu từ cơ sở dữ liệu SQLite và unpickle nó
def read_and_unpickle_from_sqlite():
    try:
        # Tạo kết nối đến cơ sở dữ liệu SQLite
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        # Đọc dữ liệu từ cơ sở dữ liệu SQLite
        cursor.execute("SELECT pkl FROM pkl_data WHERE id=1")
        pkl_data = cursor.fetchone()[0]

        # Unpickle dữ liệu
        unpickled_data = pickle.loads(pkl_data)

        # In dữ liệu unpickled
        print("Unpickled data from SQLite database:")
        print(unpickled_data)

        # Đóng kết nối
        conn.close()

    except Exception as e:
        print(f"Error occurred while reading and unpickling data from SQLite database: {e}")

# Hàm để chèn dữ liệu từ embedding vector vào cơ sở dữ liệu SQLite
def insert_embedding_to_sqlite(embedding_data):
    try:
        # Tạo kết nối đến cơ sở dữ liệu SQLite
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        # Tạo bảng trong cơ sở dữ liệu nếu chưa tồn tại
        cursor.execute('''CREATE TABLE IF NOT EXISTS embeddings
                        (id INTEGER PRIMARY KEY,
                         embedding TEXT)''')

        # Chuyển đổi embedding thành chuỗi và chèn vào cơ sở dữ liệu SQLite
        cursor.execute("INSERT INTO embeddings (embedding) VALUES (?)", (str(embedding_data),))

        # Commit và đóng kết nối
        conn.commit()
        conn.close()
        print("Embedding data inserted into SQLite database successfully.")

    except Exception as e:
        print(f"Error occurred while inserting embedding data into SQLite database: {e}")

# Gọi hàm để chèn dữ liệu từ tệp pkl vào cơ sở dữ liệu SQLite
insert_pkl_to_sqlite()

# Gọi hàm để đọc dữ liệu từ cơ sở dữ liệu SQLite và unpickle nó
read_and_unpickle_from_sqlite()
