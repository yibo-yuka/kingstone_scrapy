from flask import Flask, render_template, request, redirect, url_for
import requests as rq
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

# 資料庫設置
DATABASE = 'kingstone_books.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        link TEXT NOT NULL,
        author TEXT NOT NULL,
        price TEXT NOT NULL,
        crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def crawl_kingstone(url):
    myhead = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"}
    try:
        bookstore = rq.get(url, headers=myhead).text
        tet = BeautifulSoup(bookstore, "html5lib")
        boxs = tet.find_all("li", "embla__slide")
        
        books_data = []
        for i in boxs:
            try:
                title = i.find("h3", "pdnamebox height2").a.text.strip()
                link = "https://www.kingstone.com.tw" + i.find("h3", "pdnamebox height2").a["href"]
                author = i.find("div", "author").a.text
                price = i.find("div", "priceset").find_all("span")[2].find_all("span")[0].text
                
                books_data.append({
                    'title': title,
                    'link': link,
                    'author': author,
                    'price': price
                })
            except:
                continue
                
        return books_data
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return []

def save_to_db(books_data):
    conn = get_db_connection()
    for book in books_data:
        conn.execute(
            'INSERT INTO books (title, link, author, price) VALUES (?, ?, ?, ?)',
            (book['title'], book['link'], book['author'], book['price'])
        )
    conn.commit()
    conn.close()
    return len(books_data)

def export_to_excel():
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT title as 書名, link as 連結, author as 作者, price as 價格 FROM books', conn)
    conn.close()
    
    if not df.empty:
        df.to_excel("金石堂書單.xlsx", index=False)
        return True
    return False

@app.route('/')
def index():
    # 獲取數據庫中的書籍列表
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books ORDER BY id DESC LIMIT 100').fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/crawl', methods=['POST'])
def crawl():
    url = request.form.get('url', "https://www.kingstone.com.tw/book/nnnn")
    books_data = crawl_kingstone(url)
    if books_data:
        count = save_to_db(books_data)
        return redirect(url_for('index'))
    return "爬蟲失敗，請檢查URL或網路連接", 400

@app.route('/export')
def export():
    if export_to_excel():
        return "數據已成功導出為Excel檔案", 200
    return "導出失敗，可能沒有數據", 400

@app.route('/clear_db')
def clear_db():
    conn = get_db_connection()
    conn.execute('DELETE FROM books')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/before_first_request')
def before_first_request():
    init_db()

# 創建templates目錄
if not os.path.exists('templates'):
    os.makedirs('templates')

# 創建templates/index.html檔案
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>金石堂書籍爬蟲</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        input[type="text"] { width: 70%; padding: 8px; }
        button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .actions { margin: 20px 0; }
        .actions button { margin-right: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>金石堂書籍爬蟲系統</h1>
        
        <div class="form-group">
            <form action="/crawl" method="POST">
                <input type="text" name="url" placeholder="請輸入金石堂書籍頁面URL" value="https://www.kingstone.com.tw/book/nnnn">
                <button type="submit">開始爬蟲</button>
            </form>
        </div>
        
        <div class="actions">
            <a href="/export"><button>導出Excel</button></a>
            <a href="/clear_db" onclick="return confirm('確定要清空所有數據嗎？');"><button style="background: #f44336;">清空數據</button></a>
        </div>
        
        <h2>書籍列表</h2>
        <table>
            <thead>
                <tr>
                    <th>編號</th>
                    <th>書名</th>
                    <th>作者</th>
                    <th>價格</th>
                    <th>爬蟲時間</th>
                </tr>
            </thead>
            <tbody>
                {% for book in books %}
                <tr>
                    <td>{{ book['id'] }}</td>
                    <td><a href="{{ book['link'] }}" target="_blank">{{ book['title'] }}</a></td>
                    <td>{{ book['author'] }}</td>
                    <td>{{ book['price'] }}</td>
                    <td>{{ book['crawl_date'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    #監聽所有
    app.run(host='0.0.0.0',port=8080)