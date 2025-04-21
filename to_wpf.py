from flask import Flask, render_template, request, jsonify
import requests as rq
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

def crawl_kingstone(url, user_agent=None):
    """爬取金石堂書籍資料，使用提供的 User-Agent 或默認值"""
    # 如果沒有提供 User-Agent，使用一個較為通用的瀏覽器 User-Agent
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    
    myhead = {"user-agent": user_agent}
    
    try:
        print(f"使用 User-Agent: {user_agent}")
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

@app.route('/')
def index():
    # 簡單主頁面
    return render_template('index.html')

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    # 從請求中獲取 User-Agent
    client_user_agent = request.headers.get("User-Agent")
    
    data = request.get_json()
    url = data.get('url', "https://www.kingstone.com.tw/book/nnnn") if data else request.form.get('url', "https://www.kingstone.com.tw/book/nnnn")
    
    # 使用客戶端的 User-Agent 進行爬蟲
    books_data = crawl_kingstone(url, client_user_agent)
    
    if books_data:
        return jsonify({
            "status": "success",
            "message": f"成功爬取 {len(books_data)} 筆書籍資料",
            "user_agent_used": client_user_agent,
            "data": books_data
        })
    return jsonify({
        "status": "error",
        "message": "爬蟲失敗，請檢查URL或網路連接",
        "user_agent_used": client_user_agent,
        "data": []
    }), 400

@app.route('/api/user-agent', methods=['GET'])
def get_user_agent():
    """返回當前客戶端的 User-Agent"""
    client_user_agent = request.headers.get("User-Agent", "未檢測到 User-Agent")
    return jsonify({
        "user-agent": client_user_agent
    })

# 創建templates目錄
if not os.path.exists('templates'):
    os.makedirs('templates')

# 創建templates/index.html檔案
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>金石堂書籍爬蟲API</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        input[type="text"] { width: 70%; padding: 8px; }
        button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        #result { margin-top: 20px; border: 1px solid #ddd; padding: 15px; background: #f9f9f9; border-radius: 5px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
        h2 { margin-top: 30px; }
        .api-info { background: #e9f7fe; padding: 15px; border-left: 4px solid #4CAF50; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .user-agent-info { background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 20px 0; }
        .copy-button { background: #007bff; color: white; border: none; border-radius: 3px; padding: 2px 5px; cursor: pointer; font-size: 12px; }
        .copy-button:hover { background: #0056b3; }
        .link-actions { display: flex; gap: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>金石堂書籍爬蟲API</h1>
        
        <div class="api-info">
            <h3>API 使用說明</h3>
            <p>端點：<code>/api/crawl</code> (POST)</p>
            <p>請求格式：JSON</p>
            <p>參數：<code>{"url": "金石堂書籍頁面URL"}</code></p>
            <p>回傳：JSON 格式書籍資料</p>
            <p><strong>注意：</strong> API 會使用您當前瀏覽器的 User-Agent 進行爬蟲</p>
        </div>
        
        <div class="user-agent-info">
            <h3>您的 User-Agent 資訊</h3>
            <p>爬蟲將使用您瀏覽器的 User-Agent:</p>
            <p id="current-ua">載入中...</p>
            <button onclick="checkUserAgent()" style="background: #ffc107; color: #000;">檢查 User-Agent</button>
        </div>
        
        <h2>API 測試工具</h2>
        <div class="form-group">
            <input type="text" id="urlInput" placeholder="請輸入金石堂書籍頁面URL" value="https://www.kingstone.com.tw/book/nnnn">
            <button onclick="testApi()">測試爬蟲API</button>
        </div>
        
        <div id="result" style="display: none;">
            <h3>API 回應結果</h3>
            <pre id="resultContent"></pre>
        </div>
        
        <div id="tableResult" style="display: none;">
            <h3>書籍資料表格</h3>
            <table id="booksTable">
                <thead>
                    <tr>
                        <th>書名</th>
                        <th>作者</th>
                        <th>價格</th>
                        <th>連結操作</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // 頁面載入時檢查 User-Agent
        window.onload = function() {
            checkUserAgent();
        }
        
        function checkUserAgent() {
            const uaSpan = document.getElementById('current-ua');
            uaSpan.textContent = '載入中...';
            
            fetch('/api/user-agent')
                .then(response => response.json())
                .then(data => {
                    uaSpan.textContent = data['user-agent'];
                })
                .catch(error => {
                    uaSpan.textContent = '無法獲取 User-Agent 資訊';
                });
        }
        
        
        // 在新視窗中開啟連結，並解決 referer 問題
        function openInNewTab(url) {
            // 創建一個表單進行提交，避免發送 referer
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = url;
            form.target = '_blank';
            form.style.display = 'none';
            
            // 關鍵：添加 noreferrer
            const linkRel = document.createElement('input');
            linkRel.name = 'rel';
            linkRel.value = 'noreferrer';
            form.appendChild(linkRel);
            
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }
        
        function testApi() {
            const url = document.getElementById('urlInput').value;
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            const tableResult = document.getElementById('tableResult');
            const tableBody = document.getElementById('tableBody');
            
            resultDiv.style.display = 'none';
            tableResult.style.display = 'none';
            resultContent.textContent = '處理中...';
            resultDiv.style.display = 'block';
            
            fetch('/api/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                resultContent.textContent = JSON.stringify(data, null, 2);
                
                if (data.status === 'success' && data.data.length > 0) {
                    // 顯示表格
                    tableBody.innerHTML = '';
                    data.data.forEach(book => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${book.title}</td>
                            <td>${book.author}</td>
                            <td>${book.price}</td>
                            <td class="link-actions">
                                <a href="${book.link}" target="_blank" rel="noreferrer noopener">查看</a>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                    tableResult.style.display = 'block';
                }
            })
            .catch(error => {
                resultContent.textContent = "發生錯誤: " + error;
            });
        }
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    # 監聽所有
    app.run(host='0.0.0.0', port=8001)