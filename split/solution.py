import os
from volcenginesdkarkruntime import Ark
import re
from tqdm import tqdm
import queue
from multiprocessing.pool import ThreadPool
from datetime import datetime

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

def worker(worker_id, client, requests, results, task_status):
    """处理API请求的工作线程"""
    print(f"工作线程 {worker_id} 已启动并开始处理任务...")
    task_count = 0
    while True:
        try:
            task = requests.get(timeout=30)  # 设置30秒超时
            if task is None:
                requests.put(None)  # 为其他工作线程放回信号
                break

            title, content = task
            task_count += 1
            print(f"工作线程 {worker_id} 正在处理第 {task_count} 个任务：{title}")
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
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "response": response
            }
            with open('api_calls.json', 'a', encoding='utf-8') as f:
                import json
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')

            # 提取问题和答案
            question_match = re.search(r'问题：([^\n]+)', response)
            answer_match = re.search(r'答案：([\s\S]+?)(?=\n\n问题：|$)', response)

            if question_match and answer_match:
                question = question_match.group(1).strip()
                answer = answer_match.group(1).strip()
            else:
                question, answer = title, ' '.join(content)

            results.put((question, answer))
            task_status[title] = "完成"
            print(f"工作线程 {worker_id} 已完成第 {task_count} 个任务的处理：{title}")

        except queue.Empty:
            print(f"工作线程 {worker_id} 等待任务超时，退出线程")
            break
        except Exception as e:
            print(f"工作线程 {worker_id} 在处理任务时遇到错误：{e}")
            print(f"错误详情：\n标题：{title}\n内容：{joined_content}")
            task_status[title] = "失败"
        finally:
            if task is not None:
                requests.task_done()

def process_markdown_file(file_path, client, max_concurrent_tasks):
    """处理单个markdown文件并生成对应的CSV文件"""
    print(f'\n开始处理文件：{file_path}')
    start = datetime.now()
    task_status = {}  # 用于跟踪任务状态

    # 读取markdown文件
    print('正在读取markdown文件...')
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    print('文件读取完成！')

    # 提取所有二级标题及其内容
    print('正在解析文件中的二级标题和内容...')
    sections = extract_sections(markdown_text)
    print(f'共找到 {len(sections)} 个二级标题')

    if not sections:
        print('警告：未找到任何二级标题，跳过处理')
        return

    # 创建请求队列和结果队列
    requests = queue.Queue()
    results = queue.Queue()

    # 将任务放入请求队列
    print('正在准备任务队列...')
    for section in sections:
        requests.put((section['title'], section['content']))
    print(f'已将 {len(sections)} 个任务添加到队列')

    # 添加结束信号
    requests.put(None)

    # 创建线程池处理请求
    print(f'正在启动 {max_concurrent_tasks} 个工作线程处理问答对生成任务...')
    with ThreadPool(max_concurrent_tasks) as pool:
        workers = []
        for i in range(max_concurrent_tasks):
            worker_thread = pool.apply_async(worker, args=(i, client, requests, results, task_status))
            workers.append(worker_thread)
        pool.close()

        # 等待所有请求处理完成，同时显示任务状态
        try:
            while not all(worker.ready() for worker in workers):
                completed = sum(1 for status in task_status.values() if status == "完成")
                failed = sum(1 for status in task_status.values() if status == "失败")
                total = len(sections)
                print(f"\r当前进度：完成 {completed}/{total} 个任务，失败 {failed} 个任务", end="")
                import time
                time.sleep(1)
            requests.join(timeout=30)
        except queue.Empty:
            print("\n任务队列等待超时，程序将继续处理已完成的任务")
        except Exception as e:
            print(f"\n等待任务完成时发生错误：{e}")

    # 确保output目录存在
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)

    # 生成CSV文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    csv_path = os.path.join(output_dir, f'{base_name}.csv')

    # 生成CSV文件
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write('问题,答案\n')  # CSV header

        # 处理结果
        processed_count = 0
        with tqdm(total=len(sections), desc='保存进度') as pbar:
            while processed_count < len(sections):
                question, answer = results.get()
                # 处理CSV中的特殊字符
                question = question.replace('"', '""')
                answer = answer.replace('"', '""')
                f.write(f'"{question}","{answer}"\n')
                processed_count += 1
                pbar.update(1)

    end = datetime.now()
    print(f'\n文件处理完成：{file_path}')
    print(f'输出文件：{csv_path}')
    print(f'处理情况统计：')
    print(f'- 总共处理的二级标题数量：{len(sections)}')
    print(f'- 生成的问答对数量：{len(sections)}')
    print(f'- 处理耗时：{end - start}')

def main():
    start = datetime.now()
    max_concurrent_tasks = 20  # 设置合理的并发数

    # 创建API客户端
    print('正在初始化API客户端...')
    client = Ark(
        #base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="a4fea1b4-5e95-469b-8e0f-646ab46287f6"
    )
    print('API客户端初始化完成！')

    # 获取当前目录下的所有markdown文件
    markdown_files = [f for f in os.listdir('.') if f.endswith('.md')]
    
    if not markdown_files:
        print('错误：当前目录下未找到任何markdown文件')
        return

    print(f'找到 {len(markdown_files)} 个markdown文件：')
    for file in markdown_files:
        print(f'- {file}')

    # 处理每个markdown文件
    for file in markdown_files:
        process_markdown_file(file, client, max_concurrent_tasks)

    end = datetime.now()
    print(f'\n所有文件处理完成！')
    print(f'总耗时：{end - start}')

    client.close()

if __name__ == '__main__':
    main()