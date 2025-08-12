# 文件自動分類工具 - 定期運行功能說明

## 概述

本工具新增了定期運行功能，可以按照設定的時間間隔自動執行文件分類任務，支援三種運行模式：

1. **定期運行模式** - 在命令行中持續運行
2. **Windows 服務模式** - 作為系統服務在背景運行
3. **手動運行模式** - 原有的一次性執行模式

## 新增文件說明

### 核心文件
- `file_organizer.py` - 主程序（已更新，新增調度功能）
- `config.yaml` - 配置文件（已更新，新增 schedule 區塊）
- `config_scheduler_example.yaml` - 定期運行配置範例

### 定期運行模式
- `run_scheduler.bat` - 啟動定期運行模式
- `run_scheduler.ps1` - PowerShell 版本

### Windows 服務模式
- `install_service.bat` - 安裝為 Windows 服務
- `install_service.ps1` - PowerShell 版本服務安裝
- `manage_service.bat` - 服務管理工具
- `file_organizer_service.py` - 服務腳本（自動生成）

### 依賴文件
- `requirements.txt` - 已更新，新增 schedule 依賴

## 配置說明

### 基本調度配置

在 `config.yaml` 中添加 `schedule` 區塊：

```yaml
schedule:
  enabled: true        # 啟用定期運行
  run_on_start: false  # 啟動時是否立即執行一次
  
  # 調度類型選擇其一：
  type: "interval"     # 間隔執行
  interval: 30         # 間隔數值
  unit: "minutes"      # 時間單位
```

### 調度類型

#### 1. 間隔執行
```yaml
schedule:
  enabled: true
  type: "interval"
  interval: 30
  unit: "minutes"      # seconds, minutes, hours, days
```

#### 2. 每日執行
```yaml
schedule:
  enabled: true
  type: "daily"
  time: "02:00"        # 24小時制
```

#### 3. 每週執行
```yaml
schedule:
  enabled: true
  type: "weekly"
  day: "monday"        # monday, tuesday, ..., sunday
  time: "02:00"
```

## 使用方法

### 定期運行模式

1. 編輯 `config.yaml`，設置路徑和調度配置
2. 將 `schedule.enabled` 設為 `true`
3. 雙擊運行 `run_scheduler.bat`
4. 程序將按配置的時間間隔自動執行
5. 按 `Ctrl+C` 可停止定期運行

### Windows 服務模式（推薦用於伺服器）

#### 安裝服務
1. 編輯 `config.yaml`，設置路徑和調度配置
2. 將 `schedule.enabled` 設為 `true`
3. 右鍵以管理員身分運行 `install_service.bat`

#### 管理服務
使用 `manage_service.bat` 可以：
- 啟動服務
- 停止服務
- 重啟服務
- 查看服務狀態
- 移除服務
- 查看服務日誌

#### 命令行管理
```cmd
# 啟動服務
net start FileOrganizerService

# 停止服務
net stop FileOrganizerService

# 查看服務狀態
sc query FileOrganizerService
```

#### PowerShell 管理
```powershell
# 啟動服務
Start-Service FileOrganizerService

# 停止服務
Stop-Service FileOrganizerService

# 查看服務狀態
Get-Service FileOrganizerService
```

## 日誌和監控

### 定期運行模式
- 日誌直接顯示在命令行視窗
- 包含執行時間和處理結果

### Windows 服務模式
- 服務日誌保存在 `service.log` 文件
- Windows 事件日誌中也會記錄服務狀態
- 可通過事件檢視器查看：Windows 日誌 > 應用程式

## 依賴套件

新增依賴：
- `schedule>=1.2.0` - 任務調度
- `pywin32` - Windows 服務支援（僅服務模式需要）

安裝命令：
```cmd
pip install schedule PyYAML
# 服務模式額外需要
pip install pywin32
```

## 故障排除

### 常見問題

1. **服務安裝失敗**
   - 確保以管理員權限運行
   - 檢查 Python 是否正確安裝
   - 確認所有依賴套件已安裝

2. **調度不執行**
   - 檢查 `schedule.enabled` 是否為 `true`
   - 確認調度配置格式正確
   - 查看日誌文件中的錯誤信息

3. **路徑權限問題**
   - 確保服務帳戶有讀寫目標目錄的權限
   - Windows 服務默認以 SYSTEM 帳戶運行

### 日誌查看

#### 定期運行模式
直接在命令行視窗查看輸出

#### Windows 服務模式
```cmd
# 查看服務日誌文件
type service.log

# 查看 Windows 事件日誌
Get-EventLog -LogName Application -Source FileOrganizerService -Newest 10
```

## 效能考量

- 建議根據文件產生頻率設置合適的執行間隔
- 避免設置過短的間隔，以免影響系統效能
- 大量文件處理時，可調整 `max_workers` 參數
- Windows 服務模式比定期運行模式更穩定，適合長期運行

## 安全注意事項

- Windows 服務以 SYSTEM 權限運行，請確保配置文件安全
- 定期檢查日誌文件，避免佔用過多磁碟空間
- 建議定期備份重要文件，避免意外操作