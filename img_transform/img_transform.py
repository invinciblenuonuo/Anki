import re
import os

def extract_online_links(img_link_file):
    """从img_link.md文件中提取在线图片链接"""
    online_links = {}
    with open(img_link_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配markdown格式的图片链接
        pattern = r'!\[(.*?)\]\((https://obsidian-.*?\.(?:png|jpg|jpeg|gif|webp))\)'
        matches = re.finditer(pattern, content)
        for match in matches:
            img_name = match.group(1)
            online_url = match.group(2)
            online_links[img_name] = online_url
    return online_links

def replace_local_links(note_file, output_file, online_links):
    """替换markdown文件中的本地图片链接为在线链接"""
    with open(note_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 替换Markdown格式的图片链接
        md_pattern = r'!\[(.*?)\]\((.*?)\)'
        def replace_md_link(match):
            img_text = match.group(1)
            local_path = match.group(2)
            img_name = os.path.basename(local_path)
            if img_name in online_links:
                return f'![{img_name}]({online_links[img_name]})'
            return match.group(0)
        content = re.sub(md_pattern, replace_md_link, content)
        
        # 替换HTML格式的图片链接
        html_pattern = r'<img[^>]*?src="([^"]*?)"([^>]*?)>'
        def replace_html_link(match):
            local_path = match.group(1)
            other_attrs = match.group(2)
            img_name = os.path.basename(local_path)
            if img_name in online_links:
                return f'<img src="{online_links[img_name]}"{other_attrs}>'
            return match.group(0)
        content = re.sub(html_pattern, replace_html_link, content)
        
    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    # 文件路径
    img_link_file = 'img_link2.md'
    note_file = '嵌入式八股.md'
    output_file = '嵌入式八股_online.md'
    
    # 提取在线链接
    online_links = extract_online_links(img_link_file)
    print(f'从{img_link_file}中提取到{len(online_links)}个在线图片链接')
    
    # 替换本地链接
    replace_local_links(note_file, output_file, online_links)
    print(f'已将{note_file}中的本地图片链接替换为在线链接，并保存到{output_file}')

if __name__ == '__main__':
    main()