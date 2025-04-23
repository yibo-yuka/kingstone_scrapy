# kingstone_scrapy

##資料流
to_wpf.py：
Python flask站台，/api/crawl爬取金石堂新書推薦的書籍資訊的API，會回傳json格式

kingstone_new_book.exe：
WPF介面，可以打to_wpf.py的API去抓取書籍資訊，解析回傳的json內容，在介面上以表格的方式預覽資訊，也可以存入CSV檔。
