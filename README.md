# 文件自動分類工具

這個工具可以自動將 RINEX 觀測文件（O 文件）和導航文件（P 文件）分類到不同的目錄中。

## 目錄結構

```
rinexdivide/
├── bin/                    # 執行腳本目錄
│   ├── install_and_run.ps1      # 自動安裝並運行腳本
│   ├── run_file_organizer.bat   # 文件整理器運行腳本
│   ├── run_scheduler.ps1        # 定期運行腳本 (PowerShell)
│   └── setup_and_run.bat        # 設置並運行腳本
├── config/                 # 配置文件目錄
│   ├── config.ini          # INI 格式配置文件
│   ├── config.json         # JSON 格式配置文件
│   └── config.yaml         # YAML 格式配置文件
├── docs/                   # 文檔目錄
│   ├── README.md           # 原始說明文檔
│   ├── README_定期運行功能.md  # 定期運行功能說明
│   └── 使用說明.txt         # 使用說明文檔
├── examples/               # 配置範例目錄
│   ├── config_example.json      # JSON 配置範例
│   └── config_scheduler_example.yaml  # 定期運行配置範例
├── logs/                   # 日誌目錄（預留）
├── scripts/                # 輔助腳本目錄
│   └── auto_install_and_run.bat # 自動安裝運行腳本
├── services/               # 服務相關腳本目錄
│   ├── install_service.bat      # 服務安裝腳本 (Batch)
│   ├── install_service.ps1      # 服務安裝腳本 (PowerShell)
│   └── manage_service.bat       # 服務管理腳本
├── temp/                   # 臨時文件目錄（預留）
├── file_organizer.py       # 主程序文件
├── requirements.txt        # Python 依賴文件
└── README.md              # 本說明文檔
```

## 功能特點

- 支持多組路徑配置，可以一次處理多個數據源
- 支持正則表達式匹配文件名
- 多線程處理，提高效率
- 可選擇複製或移動文件
- 可設置是否跳過已存在的文件
- 支持定期自動運行功能
- **根據時間自動生成日誌文件**，詳細記錄處理過程

## 快速使用指南

### 1. 基本使用
```bash
# 直接運行主程序
python file_organizer.py

# 使用定期運行功能
.\bin\run_scheduler.ps1

# 使用批處理文件運行
.\bin\run_file_organizer.bat
```

### 2. 配置文件
- 主配置：`config/config.yaml` 或 `config/config.json`
- 參考範例：`examples/` 目錄下的範例文件
- 定期運行配置：`examples/config_scheduler_example.yaml`

### 3. 服務安裝
```bash
# 安裝為 Windows 服務
.\services\install_service.bat

# 管理服務
.\services\manage_service.bat
```

## 配置文件說明

程式支援三種配置文件格式，會按以下順序自動尋找：
1. `config/config.yaml` 或 `config/config.yml` (推薦)
2. `config/config.json`
3. `config/config.ini`

### YAML 格式配置 (推薦)

YAML 格式最直觀，支援註解，且不需要轉義反斜線：

```yaml
# 文件自動分類工具配置文件

# 文件匹配模式
file_extensions:
  o_files:
    - "regex:\\d{2}o$"
  p_files:
    - "regex:\\d{2}p$"

# 操作設置
copy_mode: true        # true=複製文件, false=移動文件
skip_existing: true    # true=跳過已存在文件, false=重命名
max_workers: 16        # 最大線程數

# 默認路徑配置
source_directory: "C:\\115"
o_files_directory: "C:\\115\\OBS"
p_files_directory: "C:\\115\\NAV"

# 多組路徑配置
path_groups:
  - source_directory: "C:\\115"
    o_files_directory: "C:\\115\\OBS"
    p_files_directory: "C:\\115\\NAV"
  
  - source_directory: "C:\\data\\ST02"
    o_files_directory: "C:\\data\\ST02\\OBS"
    p_files_directory: "C:\\data\\ST02\\NAV"
```

### JSON 格式配置

```json
{
    "file_extensions": {
        "o_files": ["regex:\\d{2}o$"],
        "p_files": ["regex:\\d{2}p$"]
    },
    "copy_mode": true,
    "skip_existing": true,
    "max_workers": 16,
    
    "source_directory": "C:\\115",
    "o_files_directory": "C:\\115\\OBS",
    "p_files_directory": "C:\\115\\NAV",
    
    "path_groups": [
        {
            "source_directory": "C:\\115",
            "o_files_directory": "C:\\115\\OBS",
            "p_files_directory": "C:\\115\\NAV"
        }
    ]
}
```

**注意：** JSON 格式中的反斜線需要雙重轉義（`\\` 表示一個反斜線）

### 參數說明

- `file_extensions`: 文件匹配模式
  - `o_files`: 觀測文件的匹配模式列表
  - `p_files`: 導航文件的匹配模式列表
- `copy_mode`: 設置為 `true` 表示複製文件，`false` 表示移動文件
- `skip_existing`: 設置為 `true` 表示跳過已存在的文件，`false` 表示重命名
- `max_workers`: 最大線程數
- `logging`: 日誌配置（可選）
  - `enabled`: 是否啟用日誌記錄
  - `log_directory`: 日誌文件目錄
  - `log_level`: 日誌級別（DEBUG, INFO, WARNING, ERROR）
  - `max_log_files`: 保留的日誌文件數量
  - `log_format`: 日誌格式（simple, detailed）
  - `console_output`: 是否同時輸出到控制台
- `source_directory`: 默認源目錄（當不使用 path_groups 時）
- `o_files_directory`: 默認觀測文件目標目錄（當不使用 path_groups 時）
- `p_files_directory`: 默認導航文件目標目錄（當不使用 path_groups 時）
- `path_groups`: 多組路徑配置，每組包含：
  - `source_directory`: 源目錄
  - `o_files_directory`: 觀測文件目標目錄
  - `p_files_directory`: 導航文件目標目錄

### 文件匹配模式

可以使用兩種方式指定文件匹配模式：

1. 直接指定文件擴展名，如 `.21o`
2. 使用正則表達式，格式為 `regex:表達式`，如 `regex:\\d{2}o$`

### 路徑格式支援

程式支援多種路徑格式：

**Windows 路徑：**
- `C:\115` (YAML 中可直接使用)
- `C:\\115` (YAML 中也可使用)
- `C:/115` (所有格式都支援)

**相對路徑和環境變數：**
- `~/Documents/data` (用戶主目錄)
- `%USERPROFILE%\Documents\data` (Windows 環境變數)
- `$HOME/Documents/data` (Unix 環境變數)

## 安裝要求

如果使用 YAML 配置格式，需要安裝 PyYAML：

```bash
pip install PyYAML
```

或者運行：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 選擇配置格式並編輯配置文件：
   - 推薦：創建 `config/config.yaml` 文件
   - 或者：編輯現有的 `config/config.json` 文件
2. 設置源目錄和目標目錄
3. 運行程式：
   - 直接運行：`python file_organizer.py`
   - 或使用批處理文件：`.\bin\run_file_organizer.bat`
4. 確認配置無誤後，輸入 `y` 開始處理

## 多組路徑配置

程式支援任意數量的路徑組，每組會依序處理。在 `path_groups` 中添加更多組即可：

```yaml
path_groups:
  - source_directory: "C:\\115"
    o_files_directory: "C:\\115\\OBS"
    p_files_directory: "C:\\115\\NAV"
  
  - source_directory: "D:\\data"
    o_files_directory: "D:\\data\\OBS"
    p_files_directory: "D:\\data\\NAV"
  
  # 可以添加更多組...
```

## 日誌功能

程式支援根據時間自動生成日誌文件，詳細記錄處理過程：

### 日誌配置範例

```yaml
# 日誌配置
logging:
  enabled: true                    # 啟用日誌記錄
  log_directory: "logs"            # 日誌文件目錄
  log_level: "INFO"                # 日誌級別：DEBUG, INFO, WARNING, ERROR
  max_log_files: 30                # 保留的日誌文件數量
  log_format: "detailed"           # 日誌格式：simple, detailed
  console_output: true             # 是否同時輸出到控制台
```

### 日誌功能特點

- **自動命名**：日誌文件按時間自動命名，格式為 `file_organizer_YYYYMMDD_HHMMSS.log`
- **詳細記錄**：記錄程序啟動、文件處理、錯誤信息、處理統計等
- **自動清理**：自動清理超過保留數量的舊日誌文件
- **多級別支援**：支援 DEBUG、INFO、WARNING、ERROR 四個日誌級別
- **雙重輸出**：可同時輸出到日誌文件和控制台
- **線程安全**：多線程環境下安全記錄日誌

### 日誌文件示例

```
2025-08-12 15:38:23 - INFO - setup_logging:149 - 日誌系統已初始化，日誌文件：logs\file_organizer_20250812_153823.log
2025-08-12 15:38:23 - INFO - main:754 - 程序啟動
2025-08-12 15:38:23 - INFO - run_file_organization:565 - === 開始執行文件整理任務 ===
2025-08-12 15:38:23 - INFO - organize_files:408 - 开始处理文件夹: temp
2025-08-12 15:38:23 - INFO - organize_files:498 - 文件處理成功: test01.21o -> 已复制: test01.21o -> OBS/
2025-08-12 15:38:23 - INFO - organize_files:522 - 處理統計 - o文件: 2個, p文件: 2個, 跳過: 0個, 忽略: 1個, 錯誤: 0個
2025-08-12 15:38:23 - INFO - run_file_organization:575 - === 文件整理任務完成，耗時: 0:00:00.007897 ===
```

## 注意事項

- 主程序 `file_organizer.py` 在根目錄，可直接執行
- 所有腳本已移至 `bin/` 目錄，執行時需要指定路徑
- 配置文件已整理至 `config/` 目錄，程序會自動尋找配置文件
- 如果程序找不到配置文件，請檢查 `config/` 目錄下的配置文件

## 版本資訊

整理完成於：2025年8月12日