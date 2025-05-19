import os
from volcenginesdkarkruntime import Ark
import re
from tqdm import tqdm

def extract_sections(markdown_text):
    """从markdown文本中提取二级标题及其内容"""
    sections = []
    current_section = None
    lines = markdown_text.split('\n')
    
    for line in lines:
        if line.startswith('## '):
            if current_section:
                sections.append(current_section)
            current_section = {'title': line[3:].strip(), 'content': []}
        elif current_section is not None and line.strip() and not line.startswith('# '):
            current_section['content'].append(line.strip())
    
    if current_section:
        sections.append(current_section)
    
    return sections

def generate_qa_pair(title, content):
    """使用大模型API生成问答对"""
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="08c545a7-214a-469a-99cf-8d741df7a5dc"
    )
    joined_content = '\n'.join(content)
    prompt = f""" 请将以下Markdown格式的笔记转换为"问题+答案"的形式：

标题：{title}
内容：{joined_content}

请按照以下格式输出：
问题：[基于标题生成的问题]
答案：[基于内容生成的答案] 

答案的输出需要使用markdown格式，并且需要保留原有的换行符。
"""
    
    completion = client.chat.completions.create(
        model="deepseek-v3-250324",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response = completion.choices[0].message.content
    
    # 记录API调用日志
    import json
    from datetime import datetime
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "response": response
    }
    with open('api_calls.json', 'a', encoding='utf-8') as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write('\n')
    
    # 提取问题和答案
    question_match = re.search(r'问题：([^\n]+)', response)
    answer_match = re.search(r'答案：([\s\S]+?)(?=\n\n问题：|$)', response)
    
    if question_match and answer_match:
        question = question_match.group(1).strip()
        answer = answer_match.group(1).strip()
        # 保持答案的原始markdown格式，包括换行符
        return question, answer
    return title, ' '.join(content)  # 如果提取失败，返回原始标题和内容

def main():
    # 读取markdown文件
    with open('./嵌入式笔记.md', 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # 提取所有二级标题及其内容
    sections = extract_sections(markdown_text)
    
    # 生成CSV文件
    with open('./anki.csv', 'w', encoding='utf-8', newline='') as f:
        f.write('问题,答案\n')  # CSV header
        
        # 显示进度条
        print('正在生成问答对...')
        for section in tqdm(sections, desc='处理进度'):
            question, answer = generate_qa_pair(section['title'], section['content'])
            # 处理CSV中的特殊字符
            question = question.replace('"', '""')
            answer = answer.replace('"', '""')
            f.write(f'"{question}","{answer}"\n')
        
        print(f'完成！已生成 {len(sections)} 个问答对。')

if __name__ == '__main__':
    main()