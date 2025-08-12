# 文件自動分類工具

這個工具可以自動將 RINEX 觀測文件（O 文件）和導航文件（P 文件）分類到不同的目錄中。

## 功能特點

- 支持多組路徑配置，可以一次處理多個數據源
- 支持正則表達式匹配文件名
- 多線程處理，提高效率
- 可選擇複製或移動文件
- 可設置是否跳過已存在的文件

## 配置文件說明

程式支援三種配置文件格式，會按以下順序自動尋找：
1. `config.yaml` 或 `config.yml` (推薦)
2. `config.json`

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
   - 推薦：創建 `config.yaml` 文件
   - 或者：編輯現有的 `config.json` 文件
2. 設置源目錄和目標目錄
3. 運行程式：
   - 直接運行：`python file_organizer.py`
   - 或使用批處理文件：`run_file_organizer.bat`
4. 確認配置無誤後，輸入 `y` 開始處理

## 批處理文件

- `run_file_organizer.bat`: 直接運行文件分類工具
- `setup_and_run.bat`: 安裝依賴並運行文件分類工具

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
