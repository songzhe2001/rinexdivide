# 文件自动分类工具

这个工具可以根据文件扩展名自动将 o 文件和 p 文件分别复制到指定的目录中。

## 功能特点

- 根据配置文件自动分类文件
- 支持复制或移动模式
- 避免覆盖已存在的文件
- 支持多种文件扩展名
- **多线程并行处理，显著提升处理速度**
- 详细的处理日志和进度显示

## 环境要求

- Python 3.6 或更高版本
- 无需安装额外的第三方库（使用 Python 标准库）

## 使用方法

1. **检查 Python 环境**
   
   确保你的系统已安装 Python：
   ```bash
   python --version
   ```
   或
   ```bash
   python3 --version
   ```

2. **配置设置**
   
   编辑 `config.json` 文件，设置你的路径和参数：
   
   ```json
   {
       "source_directory": "C:/source_folder",        
       "o_files_directory": "D:/o_files_storage",     
       "p_files_directory": "D:/p_files_storage",     
       "file_extensions": {
           "o_files": [".o"],                         
           "p_files": [".p"]                          
       },
       "copy_mode": true,                             
       "skip_existing": true                          
   }
   ```

3. **运行工具**
   
   在命令行中进入工具所在目录，然后运行：
   ```bash
   python file_organizer.py
   ```
   
   如果系统中 Python 3 需要使用 python3 命令：
   ```bash
   python3 file_organizer.py
   ```

4. **确认执行**
   
   工具会显示当前配置，确认后开始处理文件。

## 快速开始

### 方法一：双击运行（推荐）

1. 下载所有文件到一个文件夹
2. 修改 `config.json` 中的路径设置
3. **首次使用**：双击 `setup_and_run.bat` 进行环境检查和配置确认
4. **日常使用**：双击 `run_file_organizer.bat` 快速运行

### 方法二：命令行运行

1. 下载所有文件到一个文件夹
2. 修改 `config.json` 中的路径设置
3. 在终端运行 `python file_organizer.py`
4. 按提示确认执行

## 文件说明

- `file_organizer.py` - 主程序文件
- `config.json` - 配置文件
- `run_file_organizer.bat` - 快速运行脚本（双击即可）
- `setup_and_run.bat` - 首次设置脚本（检查环境和配置）
- `README.md` - 使用说明

## 配置说明

- `source_directory`: 要处理的源文件夹路径
- `o_files_directory`: o 文件的目标存储目录
- `p_files_directory`: p 文件的目标存储目录
- `file_extensions`: 定义文件类型的匹配模式
  - `o_files`: o 文件的匹配模式列表，支持：
    - 简单扩展名：如 [".o", ".obs"]
    - 正则表达式：如 ["regex:\\d{2}o$"] 匹配年份+o结尾的文件（如 .25o, .24o）
  - `p_files`: p 文件的匹配模式列表，支持：
    - 简单扩展名：如 [".p", ".nav"]
    - 正则表达式：如 ["regex:\\d{2}p$"] 匹配年份+p结尾的文件（如 .25p, .24p）
- `copy_mode`: 
  - `true`: 复制文件（保留原文件）
  - `false`: 移动文件（删除原文件）
- `skip_existing`:
  - `true`: 跳过已存在的文件
  - `false`: 重命名文件（添加数字后缀）
- `max_workers`: 多线程处理的线程数量（默认4，建议根据CPU核心数调整）
  - 推荐设置：CPU核心数 × 2（如4核CPU设置为8）
  - 过高的线程数可能不会带来性能提升，反而增加系统负担

## 示例

### RINEX 文件示例

假设你的源文件夹中有以下 RINEX 文件：
```
source_folder/
├── ST0100.25o    (2025年观测文件)
├── ST0100.25p    (2025年导航文件)
├── ST0200.24o    (2024年观测文件)
├── ST0200.24p    (2024年导航文件)
├── document.txt  (其他文件)
└── ST0100.25o    (在目标目录已存在)
```

使用配置：
```json
{
    "file_extensions": {
        "o_files": ["regex:\\d{2}o$"],
        "p_files": ["regex:\\d{2}p$"]
    },
    "max_workers": 8
}
```

运行工具后：
- `ST0100.25o`, `ST0200.24o` 会被复制到 OBS 目录（观测文件）
- `ST0100.25p`, `ST0200.24p` 会被复制到 NAV 目录（导航文件）
- `document.txt` 会被忽略
- 如果目标目录已存在同名文件，会根据配置跳过或重命名
- **使用8个线程并行处理，显著提升处理速度**

### 多线程性能示例

处理1000个文件的性能对比：
- **单线程模式**：约需要 60 秒
- **8线程模式**：约需要 15 秒（提升约4倍速度）

实际性能提升取决于：
- 文件大小
- 磁盘I/O性能
- CPU核心数
- 网络存储速度（如果目标目录在网络驱动器上）

### 其他文件类型示例

如果你需要处理其他类型的文件，可以这样配置：
```json
{
    "file_extensions": {
        "o_files": [".o", ".obs", "regex:\\d{2}o$"],
        "p_files": [".p", ".nav", "regex:\\d{2}p$"]
    }
}
```

## 注意事项

- 请确保配置文件中的路径存在且有写入权限
- 工具会自动创建不存在的目标目录
- 建议先在测试环境中运行，确认效果后再处理重要文件