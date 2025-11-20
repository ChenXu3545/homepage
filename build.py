import re
from bs4 import BeautifulSoup
import os

# === 配置区域 ===
INPUT_FILE = 'bookmarks_2025_11_20.html'
OUTPUT_FILE = 'index.html'

# 网页模板 (保持不变，但内容会被新的解析逻辑填充)
HTML_HEADER = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的个人导航</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
    <style>
        :root { 
            --primary: #3b82f6; 
            --bg-page: #f3f4f6; 
            --bg-sidebar: #ffffff;
            --text-main: #1f2937;
            --text-muted: #6b7280;
        }
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: var(--bg-page); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }

        /* 侧边栏 */
        .sidebar { width: 240px; background: var(--bg-sidebar); border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; flex-shrink: 0; z-index: 20; }
        .logo { padding: 24px; font-size: 20px; font-weight: 800; color: var(--primary); display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f3f4f6; }
        .nav-scroll { flex: 1; overflow-y: auto; padding: 10px 0; }
        .nav-link { display: block; padding: 12px 24px; color: var(--text-main); text-decoration: none; transition: 0.2s; font-size: 15px; border-left: 3px solid transparent; }
        .nav-link:hover, .nav-link.active { background: #eff6ff; color: var(--primary); border-left-color: var(--primary); font-weight: 500; }

        /* 主内容区 */
        .main { flex: 1; overflow-y: auto; padding: 30px 40px; scroll-behavior: smooth; position: relative; }

        /* 搜索框 */
        .search-container { position: sticky; top: 0; z-index: 10; background: var(--bg-page); padding-bottom: 20px; margin-bottom: 20px; }
        .search-box { max-width: 600px; margin: 0 auto; position: relative; }
        .search-input { width: 100%; padding: 16px 24px; padding-left: 50px; border-radius: 12px; border: 1px solid #e5e7eb; font-size: 16px; outline: none; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); transition: 0.3s; box-sizing: border-box; background: white; }
        .search-input:focus { border-color: var(--primary); box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.1); }
        .search-icon { position: absolute; left: 18px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: 18px; }

        /* 分类内容 */
        .category { margin-bottom: 40px; scroll-margin-top: 100px; }
        .cat-head { margin-bottom: 20px; display: flex; align-items: center; padding-bottom: 10px; border-bottom: 1px dashed #e5e7eb; }
        .cat-title { font-size: 18px; font-weight: 600; color: var(--text-main); }
        .cat-count { margin-left: 10px; background: #e5e7eb; color: var(--text-muted); padding: 2px 8px; border-radius: 10px; font-size: 12px; }

        /* 卡片网格 */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
        .card { background: white; padding: 16px; border-radius: 12px; display: flex; align-items: center; text-decoration: none; transition: 0.3s; border: 1px solid transparent; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: #bfdbfe; }
        .card-icon { width: 36px; height: 36px; margin-right: 16px; border-radius: 8px; object-fit: contain; background: #f9fafb; padding: 4px; box-sizing: border-box; flex-shrink: 0; }
        .card-info { flex: 1; overflow: hidden; }
        .card-text { font-weight: 500; font-size: 15px; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
        .card-url { font-size: 12px; color: #9ca3af; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* 移动端适配 */
        @media (max-width: 768px) {
            body { flex-direction: column; overflow: auto; }
            .sidebar { width: 100%; height: auto; border-right: none; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; }
            .nav-scroll { display: none; /* 移动端暂隐藏侧边导航，简化布局 */ }
            .logo { justify-content: center; padding: 15px; }
            .main { padding: 20px; }
            .grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }
            .card { flex-direction: column; text-align: center; padding: 15px 10px; }
            .card-icon { margin-right: 0; margin-bottom: 10px; width: 40px; height: 40px; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            <span>🧭 导航站</span>
        </div>
        <div class="nav-scroll" id="nav-container">
            </div>
    </div>

    <div class="main">
        <div class="search-container">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" class="search-input" placeholder="输入关键词搜索书签，或回车搜索 Google..." id="searchInput">
            </div>
        </div>
        <div id="content-container">
            </div>

        <footer style="text-align: center; margin-top: 50px; color: #9ca3af; font-size: 13px; padding-bottom: 20px;">
            Generated by Python Script | Last Update: <span id="date-now"></span>
        </footer>
    </div>

    <script>
        // 设置日期
        document.getElementById('date-now').innerText = new Date().toLocaleDateString();

        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const cards = document.getElementsByClassName('card');

        searchInput.addEventListener('keyup', function(e) {
            const term = e.target.value.toLowerCase();

            // 回车跳转Google
            if (e.key === 'Enter' && term) {
                window.open('https://www.google.com/search?q=' + encodeURIComponent(term), '_blank');
                return;
            }

            // 本地过滤
            for (let card of cards) {
                const text = card.innerText.toLowerCase();
                const category = card.closest('.category');

                if (text.includes(term)) {
                    card.style.display = "flex";
                } else {
                    card.style.display = "none";
                }
            }

            // 隐藏空分类
            document.querySelectorAll('.category').forEach(cat => {
                const visibleCards = cat.querySelectorAll('.card[style="display: flex;"]');
                const allCards = cat.querySelectorAll('.card');
                const hasVisible = Array.from(allCards).some(c => c.style.display !== 'none');
                cat.style.display = hasVisible ? 'block' : 'none';
            });
        });

        // 激活侧边栏滚动高亮（简版）
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                document.getElementById(this.getAttribute('href').substring(1)).scrollIntoView();
            });
        });
    </script>
</body>
</html>
"""


def parse_bookmarks():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误：找不到文件 {INPUT_FILE}，请确保它在项目根目录下！")
        return

    # 1. 尝试使用不同的编码读取文件 (增强鲁棒性)
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

    # 2. 提取数据 - V3 逻辑：抓取根目录链接到“快捷访问”，并递归抓取文件夹

    # 查找最外层的 <DL>
    root_dl = soup.find('dl')
    if not root_dl: return {}

    # 找到 "书签栏" 对应的 <DT> 标签
    main_dt = root_dl.find('dt', recursive=False)

    # 如果找不到书签栏，就找第一个 <DL> 标签作为内容根目录
    if main_dt and main_dt.find('h3', string=re.compile("书签栏")):
        # 获取书签栏内部的 <DL> 标签，作为实际内容的根
        content_root_dl = main_dt.find('dl', recursive=False)
    else:
        # 如果不是标准格式，就用最外层的 <DL>
        content_root_dl = root_dl

    if not content_root_dl: return {}

    data = {}
    quick_links = []

    # 遍历内容根目录下的所有直接 <DT> 子项
    for dt in content_root_dl.find_all('dt', recursive=False):
        h3 = dt.find('h3', recursive=False)
        a = dt.find('a', recursive=False)

        if h3:
            # 这是一个文件夹，递归提取它内部的所有链接
            folder_name = h3.text.strip()

            # 注意：这里调用一个内部函数来递归获取所有链接，防止丢失嵌套文件夹的内容
            def extract_all_links(node):
                all_links = []
                # 查找当前节点下的所有 <A> 标签
                for link_tag in node.find_all('a'):
                    title = link_tag.text.strip()
                    if title:
                        all_links.append({
                            'title': title,
                            'url': link_tag.get('href', '#'),
                            'icon': link_tag.get('icon', '')
                        })
                return all_links

            # 从文件夹的紧邻 <DL> 标签开始提取
            sub_dl = h3.find_next_sibling('dl')
            if sub_dl:
                links = extract_all_links(sub_dl)
                if links:
                    data[folder_name] = links
                    print(
                        f"   📂 发现分类: {folder_name} (包含 {len(links)} 个链接)")

        elif a:
            # 这是一个直接放在根目录下的链接
            title = a.text.strip()
            if title:
                quick_links.append({
                    'title': title,
                    'url': a.get('href', '#'),
                    'icon': a.get('icon', '')
                })

    # 将快捷访问（根目录链接）放在最前面
    if quick_links:
        data = {"快捷访问": quick_links, **data}
        print(f"   ⚡ 发现快捷访问链接: {len(quick_links)} 个")

    return data


def generate_html(data):
    nav_html = ""
    content_html = ""

    # ... (HTML generation logic remains the same)
    for idx, (category, links) in enumerate(data.items()):
        cat_id = f"cat-{idx}"
        nav_html += f'<a href="#{cat_id}" class="nav-link">{category}</a>\n'

        content_html += f'''
        <div id="{cat_id}" class="category">
            <div class="cat-head">
                <span class="cat-title">{category}</span>
                <span class="cat-count">{len(links)}</span>
            </div>
            <div class="grid">
        '''

        for link in links:
            icon_src = link['icon']
            if not icon_src:
                icon_src = f"https://ui-avatars.com/api/?background=random&color=fff&name={link['title'][0]}&size=64"

            content_html += f'''
                <a href="{link['url']}" target="_blank" class="card" title="{link['title']}">
                    <img src="{icon_src}" class="card-icon" loading="lazy" onerror="this.src='https://ui-avatars.com/api/?background=random&name={link['title'][0]}'">
                    <div class="card-info">
                        <div class="card-text">{link['title']}</div>
                        <div class="card-url">{link['url']}</div>
                    </div>
                </a>
            '''
        content_html += '</div></div>\n'

    # 组合最终HTML
    final_html = HTML_HEADER.replace('', nav_html) \
        .replace('', content_html)

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