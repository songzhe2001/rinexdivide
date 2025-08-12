import os
import json
import shutil
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue

def load_config(config_file="config.json"):
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        dict: 配置信息
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"错误：配置文件 {config_file} 不存在！")
        return None
    except json.JSONDecodeError:
        print(f"错误：配置文件 {config_file} 格式错误！")
        return None

def is_o_file(filename, patterns):
    """
    检查文件是否为 o 文件（观测文件）
    
    Args:
        filename: 文件名
        patterns: o 文件的模式列表
    
    Returns:
        bool: 是否为 o 文件
    """
    filename_lower = filename.lower()
    for pattern in patterns:
        if pattern.startswith("regex:"):
            # 使用正则表达式匹配
            regex_pattern = pattern[6:]  # 去掉 "regex:" 前缀
            if re.search(regex_pattern, filename_lower):
                return True
        else:
            # 使用简单的扩展名匹配
            if filename_lower.endswith(pattern.lower()):
                return True
    return False

def is_p_file(filename, patterns):
    """
    检查文件是否为 p 文件（导航文件）
    
    Args:
        filename: 文件名
        patterns: p 文件的模式列表
    
    Returns:
        bool: 是否为 p 文件
    """
    filename_lower = filename.lower()
    for pattern in patterns:
        if pattern.startswith("regex:"):
            # 使用正则表达式匹配
            regex_pattern = pattern[6:]  # 去掉 "regex:" 前缀
            if re.search(regex_pattern, filename_lower):
                return True
        else:
            # 使用简单的扩展名匹配
            if filename_lower.endswith(pattern.lower()):
                return True
    return False

def process_single_file(file_info):
    """
    处理单个文件的函数（用于多线程）
    
    Args:
        file_info: 包含文件信息的字典
    
    Returns:
        dict: 处理结果
    """
    file_path = file_info["file_path"]
    target_file = file_info["target_file"]
    file_type = file_info["file_type"]
    config = file_info["config"]
    
    result = {"file_type": file_type, "status": "ignored", "message": "", "filename": file_path.name}
    
    try:
        # 检查目标文件是否已存在
        if not target_file.exists():
            if config["copy_mode"]:
                shutil.copy2(str(file_path), str(target_file))
                action = "复制"
            else:
                shutil.move(str(file_path), str(target_file))
                action = "移动"
            
            result["status"] = "success"
            result["message"] = f"已{action}: {file_path.name} -> {target_file.parent.name}/"
        else:
            if config["skip_existing"]:
                result["status"] = "skipped"
                result["message"] = f"跳过 (已存在): {file_path.name}"
            else:
                # 重命名文件
                counter = 1
                original_target = target_file
                while target_file.exists():
                    name_parts = file_path.stem, counter, file_path.suffix
                    new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    target_file = original_target.parent / new_name
                    counter += 1
                
                if config["copy_mode"]:
                    shutil.copy2(str(file_path), str(target_file))
                    action = "复制"
                else:
                    shutil.move(str(file_path), str(target_file))
                    action = "移动"
                
                result["status"] = "success"
                result["message"] = f"已{action} (重命名): {file_path.name} -> {target_file.name}"
    
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"错误：处理文件 {file_path.name} 时出错: {e}"
    
    return result

def organize_files(config):
    """
    根据配置文件自动分类文件（多线程版本）
    
    Args:
        config: 配置信息字典
    """
    source_dir = config["source_directory"]
    o_target_dir = config["o_files_directory"]
    p_target_dir = config["p_files_directory"]
    o_patterns = config["file_extensions"]["o_files"]
    p_patterns = config["file_extensions"]["p_files"]
    max_workers = config.get("max_workers", 4)  # 默认4个线程
    
    source_path = Path(source_dir)
    o_path = Path(o_target_dir)
    p_path = Path(p_target_dir)
    
    # 验证源目录是否存在
    if not source_path.exists():
        print(f"错误：源文件夹 {source_dir} 不存在！")
        return
    
    # 创建目标目录
    o_path.mkdir(parents=True, exist_ok=True)
    p_path.mkdir(parents=True, exist_ok=True)
    
    print(f"开始处理文件夹: {source_dir}")
    print(f"o 文件目标目录: {o_target_dir}")
    print(f"p 文件目标目录: {p_target_dir}")
    print(f"o 文件匹配模式: {', '.join(o_patterns)}")
    print(f"p 文件匹配模式: {', '.join(p_patterns)}")
    print(f"使用线程数: {max_workers}")
    print("-" * 60)
    
    # 收集需要处理的文件
    files_to_process = []
    ignored_count = 0
    
    for file_path in source_path.iterdir():
        if file_path.is_file():
            filename = file_path.name
            
            # 判断文件类型
            if is_o_file(filename, o_patterns):
                target_dir = o_path
                file_type = "o_files"
            elif is_p_file(filename, p_patterns):
                target_dir = p_path
                file_type = "p_files"
            else:
                ignored_count += 1
                continue  # 跳过其他类型文件
            
            target_file = target_dir / file_path.name
            
            files_to_process.append({
                "file_path": file_path,
                "target_file": target_file,
                "file_type": file_type,
                "config": config
            })
    
    if not files_to_process:
        print("没有找到需要处理的文件。")
        return
    
    print(f"找到 {len(files_to_process)} 个文件需要处理...")
    
    # 使用线程池处理文件
    copied_count = {"o_files": 0, "p_files": 0, "skipped": 0, "ignored": ignored_count, "errors": 0}
    
    # 创建线程锁用于安全打印
    print_lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {executor.submit(process_single_file, file_info): file_info for file_info in files_to_process}
        
        # 处理完成的任务
        completed = 0
        for future in as_completed(future_to_file):
            result = future.result()
            completed += 1
            
            # 更新计数器
            if result["status"] == "success":
                copied_count[result["file_type"]] += 1
            elif result["status"] == "skipped":
                copied_count["skipped"] += 1
            elif result["status"] == "error":
                copied_count["errors"] += 1
            
            # 线程安全的打印
            with print_lock:
                print(f"[{completed}/{len(files_to_process)}] {result['message']}")
    
    print("-" * 60)
    print(f"处理完成！")
    print(f"o 文件处理: {copied_count['o_files']} 个")
    print(f"p 文件处理: {copied_count['p_files']} 个")
    print(f"跳过文件: {copied_count['skipped']} 个")
    print(f"忽略文件: {copied_count['ignored']} 个")
    print(f"错误文件: {copied_count['errors']} 个")

def main():
    """
    主函数
    """
    print("文件自动分类工具")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if config is None:
        return
    
    # 显示配置信息
    print("当前配置:")
    print(f"  源目录: {config['source_directory']}")
    print(f"  o文件目录: {config['o_files_directory']}")
    print(f"  p文件目录: {config['p_files_directory']}")
    print(f"  操作模式: {'复制' if config['copy_mode'] else '移动'}")
    print(f"  重复处理: {'跳过' if config['skip_existing'] else '重命名'}")
    print()
    
    # 确认执行
    confirm = input("是否开始处理？(y/n): ").strip().lower()
    if confirm in ['y', 'yes', '是']:
        organize_files(config)
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()