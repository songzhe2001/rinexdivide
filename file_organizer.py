import os
import json
import shutil
import re
import threading
import time
import signal
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue
from datetime import datetime, timedelta

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

try:
    import configparser
    INI_AVAILABLE = True
except ImportError:
    INI_AVAILABLE = False

def convert_ini_to_dict(ini_config):
    """
    將 INI 格式的配置轉換為標準字典格式
    
    Args:
        ini_config: 從 INI 文件讀取的配置字典
    
    Returns:
        dict: 轉換後的配置字典
    """
    config = {}
    
    # 處理基本設置
    if 'settings' in ini_config:
        settings = ini_config['settings']
        config['copy_mode'] = settings.get('copy_mode', 'true').lower() == 'true'
        config['skip_existing'] = settings.get('skip_existing', 'true').lower() == 'true'
        config['max_workers'] = int(settings.get('max_workers', '4'))
    
    # 處理文件擴展名
    if 'file_extensions' in ini_config:
        ext_config = ini_config['file_extensions']
        config['file_extensions'] = {
            'o_files': [ext.strip() for ext in ext_config.get('o_files', '').split(',') if ext.strip()],
            'p_files': [ext.strip() for ext in ext_config.get('p_files', '').split(',') if ext.strip()]
        }
    
    # 處理默認路徑
    if 'paths' in ini_config:
        paths = ini_config['paths']
        config['source_directory'] = paths.get('source_directory', '')
        config['o_files_directory'] = paths.get('o_files_directory', '')
        config['p_files_directory'] = paths.get('p_files_directory', '')
    
    # 處理調度配置
    if 'schedule' in ini_config:
        schedule_config = ini_config['schedule']
        config['schedule'] = {
            'enabled': schedule_config.get('enabled', 'false').lower() == 'true',
            'type': schedule_config.get('type', 'interval'),
            'interval': int(schedule_config.get('interval', '60')),
            'unit': schedule_config.get('unit', 'minutes'),
            'time': schedule_config.get('time', '00:00'),
            'day': schedule_config.get('day', 'monday'),
            'run_on_start': schedule_config.get('run_on_start', 'false').lower() == 'true'
        }
    
    # 處理日誌配置
    if 'logging' in ini_config:
        logging_config = ini_config['logging']
        config['logging'] = {
            'enabled': logging_config.get('enabled', 'false').lower() == 'true',
            'log_directory': logging_config.get('log_directory', 'logs'),
            'log_level': logging_config.get('log_level', 'INFO'),
            'max_log_files': int(logging_config.get('max_log_files', '30')),
            'log_format': logging_config.get('log_format', 'detailed'),
            'console_output': logging_config.get('console_output', 'true').lower() == 'true'
        }
    
    return config

def setup_logging(config):
    """
    設置日誌系統
    
    Args:
        config: 配置信息字典
    """
    logging_config = config.get('logging', {})
    
    if not logging_config.get('enabled', False):
        return
    
    # 創建日誌目錄
    log_dir = normalize_path(logging_config.get('log_directory', 'logs'))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成日誌文件名（基於當前時間）
    current_time = datetime.now()
    log_filename = f"file_organizer_{current_time.strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = Path(log_dir) / log_filename
    
    # 設置日誌級別
    log_level = getattr(logging, logging_config.get('log_level', 'INFO').upper(), logging.INFO)
    
    # 設置日誌格式
    log_format = logging_config.get('log_format', 'detailed')
    if log_format == 'simple':
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    else:  # detailed
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 清除現有的處理器
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(log_level)
    
    # 文件處理器
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台處理器（如果啟用）
    if logging_config.get('console_output', True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 清理舊日誌文件
    cleanup_old_logs(log_dir, logging_config.get('max_log_files', 30))
    
    logging.info(f"日誌系統已初始化，日誌文件：{log_filepath}")

def cleanup_old_logs(log_dir, max_files):
    """
    清理舊的日誌文件
    
    Args:
        log_dir: 日誌目錄
        max_files: 保留的最大文件數
    """
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return
        
        # 獲取所有日誌文件並按修改時間排序
        log_files = [f for f in log_path.glob("file_organizer_*.log") if f.is_file()]
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 刪除超出數量限制的舊文件
        if len(log_files) > max_files:
            for old_file in log_files[max_files:]:
                try:
                    old_file.unlink()
                    logging.info(f"已刪除舊日誌文件：{old_file.name}")
                except Exception as e:
                    logging.warning(f"無法刪除舊日誌文件 {old_file.name}：{e}")
    
    except Exception as e:
        logging.warning(f"清理舊日誌文件時出錯：{e}")

def normalize_path(p):
    """
    正規化路徑，支持 Windows 與 Unix 風格，並展開環境變數與 ~
    """
    if p is None:
        return None
    if not isinstance(p, str):
        return str(p)
    p = os.path.expandvars(p)
    p = os.path.expanduser(p)
    return str(Path(p))

def load_config(config_file=None):
    """
    加载配置文件，支持 YAML 和 JSON 格式
    
    Args:
        config_file: 配置文件路径，如果為 None 則自動尋找
    
    Returns:
        dict: 配置信息
    """
    # 如果沒有指定配置文件，按優先順序尋找
    if config_file is None:
        # 首先在 config/ 目錄下尋找
        config_dir_files = [
            "config/config.yaml", 
            "config/config.yml", 
            "config/config.json",
            "config/config.ini"
        ]
        # 然後在根目錄尋找（向後兼容）
        root_dir_files = ["config.yaml", "config.yml", "config.json"]
        
        possible_configs = config_dir_files + root_dir_files
        
        for possible_config in possible_configs:
            if os.path.exists(possible_config):
                config_file = possible_config
                break
        else:
            print("錯誤：找不到配置文件！")
            print("請在 config/ 目錄下創建以下任一配置文件：")
            print("  - config/config.yaml (推薦)")
            print("  - config/config.json")
            print("  - config/config.ini")
            return None
    
    try:
        if config_file.endswith(('.yaml', '.yml')):
            if not YAML_AVAILABLE:
                print("錯誤：需要安裝 PyYAML 來讀取 YAML 配置文件")
                print("請運行：pip install PyYAML")
                return None
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif config_file.endswith('.ini'):
            if not INI_AVAILABLE:
                print("錯誤：需要 configparser 來讀取 INI 配置文件")
                return None
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file, encoding='utf-8')
            # 將 INI 格式轉換為字典格式
            config = {}
            for section in config_parser.sections():
                config[section] = dict(config_parser[section])
            # 處理特殊的配置結構
            config = convert_ini_to_dict(config)
        else:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        print(f"已加載配置文件：{config_file}")
        return config
        
    except FileNotFoundError:
        print(f"錯誤：配置文件 {config_file} 不存在！")
        return None
    except (json.JSONDecodeError, yaml.YAMLError, configparser.Error) as e:
        print(f"錯誤：配置文件 {config_file} 格式錯誤：{e}")
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

def organize_files(config, path_group=None):
    """
    根据配置文件自动分类文件（多线程版本）
    
    Args:
        config: 配置信息字典
        path_group: 路径组配置，如果为None则使用默认路径
    """
    # 如果提供了特定的路径组，则使用该组的配置，否则使用默认配置
    if path_group:
        source_dir = normalize_path(path_group["source_directory"])
        o_target_dir = normalize_path(path_group["o_files_directory"])
        p_target_dir = normalize_path(path_group["p_files_directory"])
    else:
        source_dir = normalize_path(config["source_directory"])
        o_target_dir = normalize_path(config["o_files_directory"])
        p_target_dir = normalize_path(config["p_files_directory"])
    
    o_patterns = config["file_extensions"]["o_files"]
    p_patterns = config["file_extensions"]["p_files"]
    max_workers = config.get("max_workers", 4)  # 默认4个线程
    
    source_path = Path(source_dir)
    o_path = Path(o_target_dir)
    p_path = Path(p_target_dir)
    
    # 验证源目录是否存在
    if not source_path.exists():
        error_msg = f"错误：源文件夹 {source_dir} 不存在！"
        print(error_msg)
        logging.error(error_msg)
        return False
    
    # 创建目标目录
    o_path.mkdir(parents=True, exist_ok=True)
    p_path.mkdir(parents=True, exist_ok=True)
    
    info_msg = f"开始处理文件夹: {source_dir}"
    print(info_msg)
    logging.info(info_msg)
    
    print(f"o 文件目标目录: {o_target_dir}")
    print(f"p 文件目标目录: {p_target_dir}")
    print(f"o 文件匹配模式: {', '.join(o_patterns)}")
    print(f"p 文件匹配模式: {', '.join(p_patterns)}")
    print(f"使用线程数: {max_workers}")
    print("-" * 60)
    
    logging.info(f"o 文件目标目录: {o_target_dir}")
    logging.info(f"p 文件目标目录: {p_target_dir}")
    logging.info(f"o 文件匹配模式: {', '.join(o_patterns)}")
    logging.info(f"p 文件匹配模式: {', '.join(p_patterns)}")
    logging.info(f"使用线程数: {max_workers}")
    
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
            
            # 创建一个配置副本，确保每个文件使用正确的目标路径
            file_config = config.copy()
            if path_group:
                file_config["o_files_directory"] = o_target_dir
                file_config["p_files_directory"] = p_target_dir
            
            files_to_process.append({
                "file_path": file_path,
                "target_file": target_file,
                "file_type": file_type,
                "config": file_config
            })
    
    if not files_to_process:
        msg = "没有找到需要处理的文件。"
        print(msg)
        logging.info(msg)
        return True
    
    msg = f"找到 {len(files_to_process)} 个文件需要处理..."
    print(msg)
    logging.info(msg)
    
    # 使用线程池处理文件
    copied_count = {"o_files": 0, "p_files": 0, "skipped": 0, "ignored": ignored_count, "errors": 0}
    
    # 创建线程锁用于安全打印和日志记录
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
            
            # 线程安全的打印和日志记录
            with print_lock:
                progress_msg = f"[{completed}/{len(files_to_process)}] {result['message']}"
                print(progress_msg)
                
                # 根據結果狀態記錄不同級別的日誌
                if result["status"] == "success":
                    logging.info(f"文件處理成功: {result['filename']} -> {result['message']}")
                elif result["status"] == "skipped":
                    logging.info(f"文件跳過: {result['filename']} - {result['message']}")
                elif result["status"] == "error":
                    logging.error(f"文件處理錯誤: {result['filename']} - {result['message']}")
    
    print("-" * 60)
    summary_msg = f"处理完成！"
    print(summary_msg)
    logging.info(summary_msg)
    
    # 記錄處理統計
    stats_msg = (f"處理統計 - o文件: {copied_count['o_files']}個, "
                f"p文件: {copied_count['p_files']}個, "
                f"跳過: {copied_count['skipped']}個, "
                f"忽略: {copied_count['ignored']}個, "
                f"錯誤: {copied_count['errors']}個")
    
    print(f"o 文件处理: {copied_count['o_files']} 个")
    print(f"p 文件处理: {copied_count['p_files']} 个")
    print(f"跳过文件: {copied_count['skipped']} 个")
    print(f"忽略文件: {copied_count['ignored']} 个")
    print(f"错误文件: {copied_count['errors']} 个")
    
    logging.info(stats_msg)
    
    return True

def process_path_groups(config):
    """
    处理多组路径配置
    
    Args:
        config: 配置信息字典
    
    Returns:
        bool: 是否全部处理成功
    """
    # 检查是否有多组路径配置
    path_groups = config.get("path_groups", [])
    
    if not path_groups:
        # 如果没有多组路径配置，使用默认配置处理单个路径
        return organize_files(config)
    
    # 处理每组路径
    all_success = True
    for i, path_group in enumerate(path_groups):
        print(f"\n处理路径组 {i+1}/{len(path_groups)}")
        print("=" * 60)
        success = organize_files(config, path_group)
        if not success:
            all_success = False
    
    return all_success

def run_file_organization(config):
    """
    執行文件整理任務
    
    Args:
        config: 配置信息字典
    """
    start_time = datetime.now()
    start_msg = f"開始執行文件整理任務"
    print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] {start_msg}")
    print("=" * 60)
    logging.info(f"=== {start_msg} ===")
    
    try:
        success = process_path_groups(config)
        end_time = datetime.now()
        duration = end_time - start_time
        
        if success:
            success_msg = f"文件整理任務完成，耗時: {duration}"
            print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] 文件整理任務完成")
            logging.info(f"=== 文件整理任務完成，耗時: {duration} ===")
        else:
            error_msg = f"文件整理任務執行時出現錯誤，耗時: {duration}"
            print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] 文件整理任務執行時出現錯誤")
            logging.error(f"=== {error_msg} ===")
    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        error_msg = f"文件整理任務執行失敗: {e}，耗時: {duration}"
        print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] 文件整理任務執行失敗: {e}")
        logging.error(f"=== {error_msg} ===")
        logging.exception("詳細錯誤信息:")

def parse_schedule_config(schedule_config):
    """
    解析調度配置
    
    Args:
        schedule_config: 調度配置字典
    
    Returns:
        bool: 是否成功解析配置
    """
    if not SCHEDULE_AVAILABLE:
        error_msg = "錯誤：需要安裝 schedule 庫來使用定期運行功能"
        print(error_msg)
        print("請運行：pip install schedule")
        logging.error(error_msg)
        return False
    
    schedule_type = schedule_config.get("type", "").lower()
    logging.info(f"解析調度配置，類型: {schedule_type}")
    
    if schedule_type == "interval":
        # 間隔執行
        interval = schedule_config.get("interval", 60)
        unit = schedule_config.get("unit", "minutes").lower()
        
        if unit == "seconds":
            schedule.every(interval).seconds.do(lambda: run_file_organization(config))
        elif unit == "minutes":
            schedule.every(interval).minutes.do(lambda: run_file_organization(config))
        elif unit == "hours":
            schedule.every(interval).hours.do(lambda: run_file_organization(config))
        elif unit == "days":
            schedule.every(interval).days.do(lambda: run_file_organization(config))
        else:
            error_msg = f"錯誤：不支援的時間單位 '{unit}'"
            print(error_msg)
            logging.error(error_msg)
            return False
        
        success_msg = f"已設置間隔執行：每 {interval} {unit} 執行一次"
        print(success_msg)
        logging.info(success_msg)
        
    elif schedule_type == "daily":
        # 每日執行
        time_str = schedule_config.get("time", "00:00")
        try:
            schedule.every().day.at(time_str).do(lambda: run_file_organization(config))
            success_msg = f"已設置每日執行：每天 {time_str} 執行"
            print(success_msg)
            logging.info(success_msg)
        except Exception as e:
            error_msg = f"錯誤：無效的時間格式 '{time_str}': {e}"
            print(error_msg)
            logging.error(error_msg)
            return False
            
    elif schedule_type == "weekly":
        # 每週執行
        day = schedule_config.get("day", "monday").lower()
        time_str = schedule_config.get("time", "00:00")
        
        try:
            if day == "monday":
                schedule.every().monday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "tuesday":
                schedule.every().tuesday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "wednesday":
                schedule.every().wednesday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "thursday":
                schedule.every().thursday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "friday":
                schedule.every().friday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "saturday":
                schedule.every().saturday.at(time_str).do(lambda: run_file_organization(config))
            elif day == "sunday":
                schedule.every().sunday.at(time_str).do(lambda: run_file_organization(config))
            else:
                error_msg = f"錯誤：不支援的星期 '{day}'"
                print(error_msg)
                logging.error(error_msg)
                return False
            
            success_msg = f"已設置每週執行：每週{day} {time_str} 執行"
            print(success_msg)
            logging.info(success_msg)
        except Exception as e:
            error_msg = f"錯誤：無效的時間格式 '{time_str}': {e}"
            print(error_msg)
            logging.error(error_msg)
            return False
    else:
        error_msg = f"錯誤：不支援的調度類型 '{schedule_type}'"
        print(error_msg)
        print("支援的類型：interval, daily, weekly")
        logging.error(f"{error_msg}，支援的類型：interval, daily, weekly")
        return False
    
    return True

def signal_handler(signum, frame):
    """
    信號處理器，用於優雅地停止程序
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收到停止信號，正在退出...")
    sys.exit(0)

def run_scheduler(config):
    """
    運行調度器
    
    Args:
        config: 配置信息字典
    """
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    schedule_config = config.get("schedule", {})
    
    if not schedule_config.get("enabled", False):
        msg = "定期運行功能未啟用"
        print(msg)
        logging.warning(msg)
        return False
    
    # 解析調度配置
    if not parse_schedule_config(schedule_config):
        logging.error("調度配置解析失敗")
        return False
    
    # 是否在啟動時立即執行一次
    if schedule_config.get("run_on_start", False):
        msg = "啟動時立即執行一次..."
        print(msg)
        logging.info(msg)
        run_file_organization(config)
    
    start_msg = "調度器已啟動，按 Ctrl+C 停止"
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {start_msg}")
    print("=" * 60)
    logging.info(f"=== {start_msg} ===")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        stop_msg = "調度器已停止"
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {stop_msg}")
        logging.info(f"=== {stop_msg} ===")

def main():
    """
    主函数
    """
    print("文件自動分類工具")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if config is None:
        return
    
    # 初始化日誌系統
    setup_logging(config)
    logging.info("程序啟動")
    
    # 检查是否启用了定期运行
    schedule_config = config.get("schedule", {})
    if schedule_config.get("enabled", False):
        print("檢測到定期運行配置，啟動調度器模式...")
        logging.info("啟動調度器模式")
        run_scheduler(config)
        return
    
    # 检查是否有多组路径配置
    path_groups = config.get("path_groups", [])
    
    # 显示配置信息
    print("當前配置:")
    if path_groups:
        print(f"  路徑組數量: {len(path_groups)}")
        for i, group in enumerate(path_groups):
            print(f"  路徑組 {i+1}:")
            print(f"    源目錄: {group['source_directory']}")
            print(f"    o文件目錄: {group['o_files_directory']}")
            print(f"    p文件目錄: {group['p_files_directory']}")
    else:
        print(f"  源目錄: {config['source_directory']}")
        print(f"  o文件目錄: {config['o_files_directory']}")
        print(f"  p文件目錄: {config['p_files_directory']}")
    
    print(f"  操作模式: {'複製' if config['copy_mode'] else '移動'}")
    print(f"  重複處理: {'跳過' if config['skip_existing'] else '重命名'}")
    print()
    
    # 确认执行
    confirm = input("是否開始處理？(y/n): ").strip().lower()
    if confirm in ['y', 'yes', '是']:
        run_file_organization(config)
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()