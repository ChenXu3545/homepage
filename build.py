import re
from bs4 import BeautifulSoup
import os

# === 配置区域 ===
INPUT_FILE = 'bookmarks_2025_11_20.html'
OUTPUT_FILE = 'index.html'

# 网页模板 (保持美观的样式)
HTML_HEADER = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的个人导航</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
    <style>
        :root { --primary: #3b82f6; --bg-page: #f3f4f6; --bg-sidebar: #ffffff; --text-main: #1f2937; }
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg-page); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 240px; background: var(--bg-sidebar); border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; flex-shrink: 0; }
        .logo { padding: 20px; font-size: 20px; font-weight: 800; color: var(--primary); border-bottom: 1px solid #f3f4f6; text-align: center; }
        .nav-scroll { flex: 1; overflow-y: auto; padding: 10px 0; }
        .nav-link { display: block; padding: 10px 20px; color: #4b5563; text-decoration: none; transition: 0.2s; font-size: 14px; border-left: 3px solid transparent; }
        .nav-link:hover, .nav-link.active { background: #eff6ff; color: var(--primary); border-left-color: var(--primary); font-weight: 500; }
        .main { flex: 1; overflow-y: auto; padding: 30px 40px; position: relative; }
        .search-box { max-width: 600px; margin: 0 auto 30px; }
        .search-input { width: 100%; padding: 15px 20px; border-radius: 50px; border: 1px solid #e5e7eb; outline: none; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .category { margin-bottom: 40px; }
        .cat-head { font-size: 18px; font-weight: 600; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 1px dashed #ccc; color: #374151; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; }
        .card { background: white; padding: 12px; border-radius: 8px; display: flex; align-items: center; text-decoration: none; transition: 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid transparent; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); border-color: var(--primary); }
        .card-icon { width: 32px; height: 32px; margin-right: 12px; border-radius: 50%; background: #f3f4f6; object-fit: cover; flex-shrink: 0; }
        .card-info { overflow: hidden; }
        .card-text { font-size: 14px; font-weight: 500; color: #111; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
        .card-url { font-size: 12px; color: #9ca3af; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">我的导航</div>
        <div class="nav-scroll" id="nav-container"></div>
    </div>
    <div class="main">
        <div class="search-box">
            <input type="text" class="search-input" placeholder="搜索..." onkeydown="if(event.key==='Enter') window.open('https://www.google.com/search?q='+this.value)">
        </div>
        <div id="content-container"></div>
    </div>
    <script>
        // 简单的滚动监听
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                document.getElementById(this.getAttribute('href').substring(1)).scrollIntoView({ behavior: 'smooth' });
            });
        });
    </script>
</body>
</html>
"""


def parse_bookmarks():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误：找不到文件 {INPUT_FILE}")
        return {}

    # 1. 读取文件
    content = ""
    for encoding in ['utf-8', 'gb18030', 'gbk']:
        try:
            with open(INPUT_FILE, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ 成功使用 {encoding} 编码读取文件")
            break
        except UnicodeDecodeError:
            continue

    if not content:
        print("❌ 无法读取文件内容")
        return {}

    soup = BeautifulSoup(content, 'html.parser')

    # V8 策略：直接查找所有链接，不再关心 DL/DT 嵌套结构
    all_links = soup.find_all('a')
    print(f"🔍 调试：共扫描到 {len(all_links)} 个链接标签")

    if not all_links:
        print("❌ 严重错误：未找到任何链接，请确认文件是 HTML 书签格式。")
        return {}

    data = {}
    count = 0

    for link in all_links:
        title = link.text.strip()
        url = link.get('href')
        if not url: continue

        # 处理图标 (忽略 Base64 以防内存溢出)
        icon = f"https://ui-avatars.com/api/?background=random&color=fff&name={title[0] if title else 'X'}&size=64"

        # 查找分类：向上找最近的一个 H3 标签
        category = "快捷访问"
        prev_header = link.find_previous('h3')
        if prev_header:
            cat_text = prev_header.text.strip()
            # 如果标题不是“书签栏”，则使用该标题作为分类
            if cat_text not in ["书签栏", "Bookmarks bar", "Bookmarks"]:
                category = cat_text

        # 添加到数据字典
        if category not in data:
            data[category] = []

        data[category].append({
            'title': title,
            'url': url,
            'icon': icon
        })
        count += 1

    print(f"🎉 解析成功：共整理出 {len(data)} 个分类，{count} 个链接。")
    return data


def generate_html(data):
    nav_html = ""
    content_html = ""

    # 排序：确保“快捷访问”排在前面，其他按原顺序
    categories = list(data.keys())
    if "快捷访问" in categories:
        categories.remove("快捷访问")
        categories.insert(0, "快捷访问")

    for idx, category in enumerate(categories):
        links = data[category]
        if not links: continue

        cat_id = f"cat-{idx}"
        nav_html += f'<a href="#{cat_id}" class="nav-link">{category}</a>\n'

        content_html += f'''
        <div id="{cat_id}" class="category">
            <div class="cat-head">{category} <span style="font-size:12px;color:#999">({len(links)})</span></div>
            <div class="grid">
        '''

        for link in links:
            content_html += f'''
                <a href="{link['url']}" target="_blank" class="card" title="{link['title']}">
                    <img src="{link['icon']}" class="card-icon">
                    <div class="card-info">
                        <div class="card-text">{link['title']}</div>
                        <div class="card-url">{link['url']}</div>
                    </div>
                </a>
            '''
        content_html += '</div></div>\n'

    final_html = HTML_HEADER.replace(
        '<div class="nav-scroll" id="nav-container"></div>',
        f'<div class="nav-scroll" id="nav-container">\n{nav_html}</div>') \
        .replace('<div id="content-container"></div>',
                 f'<div id="content-container">\n{content_html}</div>')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"🚀 网页文件 {OUTPUT_FILE} 已生成！")


if __name__ == '__main__':
    try:
        d = parse_bookmarks()
        if d:
            generate_html(d)
    except Exception as e:
        print(f"❌ 程序出错: {e}")
        import traceback

        traceback.print_exc()