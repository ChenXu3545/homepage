import re
from bs4 import BeautifulSoup
import os

# === 配置区域 ===
# 请确保这个文件名和你项目左侧的文件名一模一样！
INPUT_FILE = 'bookmarks_2025_11_20.html'
OUTPUT_FILE = 'index.html'

# 网页模板
HTML_HEADER = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的导航站</title>
    <style>
        :root { --primary: #3b82f6; --bg: #f3f4f6; --text: #1f2937; }
        body { margin: 0; font-family: sans-serif; background: var(--bg); color: var(--text); display: flex; height: 100vh; }
        .sidebar { width: 240px; background: white; border-right: 1px solid #e5e7eb; overflow-y: auto; flex-shrink: 0; }
        .logo { padding: 20px; font-size: 18px; font-weight: bold; color: var(--primary); border-bottom: 1px solid #eee; }
        .nav-link { display: block; padding: 12px 20px; color: #4b5563; text-decoration: none; transition: .2s; }
        .nav-link:hover { background: #eff6ff; color: var(--primary); border-left: 3px solid var(--primary); }
        .main { flex: 1; overflow-y: auto; padding: 30px; }
        .search-box { max-width: 600px; margin: 0 auto 40px; }
        .search-input { width: 100%; padding: 15px 20px; border-radius: 50px; border: 1px solid #d1d5db; outline: none; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .category { margin-bottom: 40px; }
        .cat-title { font-size: 20px; font-weight: 600; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px dashed #ccc; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; }
        .card { background: white; padding: 15px; border-radius: 10px; display: flex; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: .2s; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .icon { width: 32px; height: 32px; margin-right: 12px; border-radius: 50%; background: #f9fafb; object-fit: cover; }
        .info { overflow: hidden; }
        .title { font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .url { font-size: 12px; color: #9ca3af; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">我的导航</div>
        <div id="nav-links"></div>
    </div>
    <div class="main">
        <div class="search-box">
            <input type="text" class="search-input" placeholder="搜索..." onkeydown="if(event.key==='Enter') window.open('https://www.google.com/search?q='+this.value)">
        </div>
        <div id="content-area"></div>
    </div>
</body>
</html>
"""


def parse_bookmarks():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误：找不到文件 {INPUT_FILE}")
        return

    # 1. 尝试使用不同的编码读取文件
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
        print("❌ 无法读取文件，请检查文件编码")
        return

    soup = BeautifulSoup(content, 'html.parser')

    # 2. 提取数据 - 增强鲁棒性
    data = {}

    # 尝试找到所有 H3 (文件夹标题)
    # 不再局限于第一层，也不强求"书签栏"
    all_folders = soup.find_all('h3')

    print(f"🔍 扫描到 {len(all_folders)} 个文件夹标签...")

    for h3 in all_folders:
        folder_name = h3.text.strip()

        # 跳过书签栏本身，只看它里面的子文件夹
        if folder_name in ["书签栏", "Bookmarks bar", "Bookmarks"]:
            continue

        # 找到该标题对应的列表 (通常是紧接着的 DL 或 UL)
        next_element = h3.find_next_sibling()
        if next_element and next_element.name in ['dl', 'ul', 'p']:
            # 有些浏览器导出时会在DL外面包一层P
            if next_element.name == 'p':
                next_element = next_element.find('dl')

        if not next_element: continue

        # 提取链接
        links = []
        for a in next_element.find_all('a'):
            # 简单的过滤：如果链接就在H3的同一层级（不包含子文件夹的链接），这取决于你的需求
            # 这里我们做简单的去重：如果这个链接已经被算在子文件夹里了，可能会重复，但作为导航站宁可重复不可遗漏
            links.append({
                'title': a.text.strip(),
                'url': a.get('href', '#'),
                'icon': a.get('icon', '')
            })

        # 只有当文件夹里有链接时才添加
        if len(links) > 0:
            print(f"   📂 发现分类: {folder_name} (包含 {len(links)} 个链接)")
            data[folder_name] = links

    if not data:
        print("⚠️ 警告：没有解析到任何链接！可能是文件结构非常特殊。")

    return data


def generate_html(data):
    nav_html = ""
    content_html = ""

    for idx, (category, links) in enumerate(data.items()):
        cat_id = f"cat-{idx}"
        nav_html += f'<a href="#{cat_id}" class="nav-link">{category}</a>\n'

        content_html += f'<div id="{cat_id}" class="category"><div class="cat-title">{category}</div><div class="grid">'
        for link in links:
            # 默认图标逻辑
            icon_src = link['icon']
            if not icon_src:
                icon_src = f"https://ui-avatars.com/api/?background=random&name={link['title'][0]}"

            content_html += f'''
            <a href="{link['url']}" target="_blank" class="card">
                <img src="{icon_src}" class="icon">
                <div class="info">
                    <div class="title" title="{link['title']}">{link['title']}</div>
                    <div class="url">{link['url']}</div>
                </div>
            </a>
            '''
        content_html += '</div></div>\n'

    final_html = HTML_HEADER.replace('<div id="nav-links"></div>', nav_html) \
        .replace('<div id="content-area"></div>', content_html)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"🎉 网页生成完毕！请查看: {OUTPUT_FILE}")


if __name__ == '__main__':
    # 安装依赖提示
    try:
        bookmarks_data = parse_bookmarks()
        if bookmarks_data:
            generate_html(bookmarks_data)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()