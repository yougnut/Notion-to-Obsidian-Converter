# Notion to Obsidian Bulk Converter (v2.0)

這是一個專為 Notion 使用者設計的 Python 自動化工具，能將 Notion 匯出的 Markdown & CSV 檔案進行深度清理與格式轉換，使其完美相容於 Obsidian。

## ✨ 主要功能 (Features)

### 核心修復

  * **🛡️ 檔名亂碼清洗**：保留中文/日文檔名，僅移除 Notion 產生的 32 碼 ID。
  * **🔗 連結完美修復**：自動修正內部連結路徑，並處理 `about:blank` 無效連結。
  * **📊 表格斷行修復**：自動偵測並修復 Notion 表格因換行導致的 Markdown 破碎問題（支援排除 Math/Code Block）。
  * **🏷️ 標籤轉換**：將 `Tags: A, B` 自動轉換為 Obsidian 的 `tags: [A, B]` 或行內 `#A #B`。

### v2.0 新增功能

  * **🎛️ GUI 設定精靈**：啟動時提供圖形化介面，讓您自訂是否要「自動壓縮」、「開啟資料夾」等，並自動記憶上次設定。
  * **💎 YAML Frontmatter 支援**：將 Notion 的 Page Properties 自動轉換為 Obsidian 頂部的 YAML Metadata（如 `Date`, `Status`, `Author` 等），便於 Dataview 插件使用。
  * **🔻 Toggle 列表還原**：將 Notion 的 Toggle List 轉換為 HTML `<details><summary>` 語法，在 Obsidian 中也能完美摺疊/展開。
  * **📂 CSV 智慧合併**：自動偵測 Database 匯出的 `_all.csv` 變體，保留資料最完整的版本並轉換為 Markdown 索引頁。
  * **📝 錯誤日誌輸出**：轉換過程若有檔案失敗，將生成 `conversion_error_log.txt` 供您檢視。

## 🚀 安裝與使用 (Installation & Usage)

### 1\. 環境需求

  * Windows / macOS / Linux
  * Python 3.6 或以上版本
  * *(Windows 用戶)* 建議直接使用附帶的 `run.bat`

### 2\. 從 Notion 匯出資料

1.  前往 Notion **Settings & Members** \> **Settings** \> **Export all workspace content**。
2.  **Export format**: 選擇 `Markdown & CSV`。
3.  **Include subpages**: 務必勾選。
4.  下載匯出的 ZIP 檔案。

### 3\. 執行轉換

#### Windows 使用者（推薦）

直接雙擊資料夾中的 **`run.bat`** 檔案。

#### Mac / Linux 使用者

開啟終端機 (Terminal)，移動到程式目錄並執行：

```bash
python notion_to_obsidian_bulk.py
```

*(若需修改設定，請先執行 `python config_setup.py`)*

### 4\. 操作流程

1.  **設定視窗**：程式啟動後會跳出設定視窗，勾選您偏好的選項後點擊「儲存並開始轉換」。
2.  **選擇檔案**：在彈出的檔案瀏覽視窗中，選擇您剛下載的 Notion ZIP 檔。
3.  **等待處理**：觀察終端機的進度條，程式將自動執行解壓縮、清洗、轉換與修復。
4.  **完成**：完成後會依設定自動開啟目標資料夾（或生成的 `_Obsidian_Ready.zip`）。

## ⚙️ 進階設定 (Configuration)

除了 GUI 上的選項外，您可以直接編輯生成的 `config.ini` 檔案來控制更多細節功能：

| 設定項目 (config.ini) | 預設值 | 說明 |
| :--- | :--- | :--- |
| `move_assets` | False | 是否移動圖片/附件到特定資料夾 (建議 False 以保持連結穩定) |
| `enable_yaml` | True | 是否開啟 Notion Properties 轉 YAML 功能 |
| `enable_toggles` | True | 是否開啟 Toggle List (`<details>`) 轉換功能 |
| `fix_tables` | True | 是否開啟表格斷行修復功能 |
| `delete_source_csv` | True | 轉換完成後是否刪除原始 CSV 檔 |

## 🛠️ 技術細節

  * **Toggle 邏輯**：程式透過縮排 (Indentation) 計算層級，將連續的縮排內容包覆在 `<details>` 標籤內，並排除程式碼區塊內的內容。
  * **YAML 處理**：讀取檔案前幾行，辨識 `Property: Value` 格式，將其轉換為標準的 YAML 格式並置於檔案最上方。
  * **CSV 處理**：除了轉為 Markdown 連結列表外，新增了比對檔案大小的邏輯，確保不會因為 Notion 匯出分割檔案而遺失資料。

## License

MIT License
