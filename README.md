# Notion to Obsidian Converter

一個簡單、強大且自動化的 Python 腳本，專為將 Notion 匯出的筆記遷移至 Obsidian 而設計。

這不僅僅是移除檔名亂碼，還特別針對 **中文內容**、**表格斷行問題** 以及 **Database CSV** 進行了深度優化，確保您的知識庫能無縫轉移。

## ✨ 主要功能 (Features)

- **🛡️ 完整保留中文檔名**：不同於其他只保留英數字的腳本，此工具完美支援中文、日文等非英文檔名，僅移除 Notion 產生的 32 碼 ID。
- **📂 自動解壓縮與巢狀處理**：自動偵測並解壓 Notion 匯出的 ZIP 檔，包含處理內層的巢狀壓縮檔 (Nested ZIPs)。
- **📊 智慧修復表格 (Table Fix)**：Notion 表格匯出時常因換行導致 Markdown 語法破碎，本腳本會自動偵測並合併斷行，使用 `<br>` 還原表格結構。
- **🗃️ Database CSV 轉 Markdown**：自動將 Notion Database 匯出的 `.csv` 檔案轉換為 Markdown 索引頁 (Index Note)，保留頁面連結，不再讓資料庫變孤兒。
- **🔗 連結完美修復**：
    - 自動修正內部連結路徑 (Internal Links)。
    - 修復 `about:blank` 類型的無效連結。
    - 轉換 Notion Callout 為 Obsidian Callout 語法。
- **🏷️ 標籤轉換**：將 Notion 的 `Tags: A, B` 格式自動轉換為 Obsidian 可識別的 `#A #B`。
- **📦 自動打包**：處理完成後，自動將結果壓縮為 `_Obsidian_Ready.zip` 並開啟資料夾，方便直接匯入。

## 🚀 使用方法 (Usage)

### 1. 準備工作

確保您的電腦已安裝 [Python 3](https://www.python.org/downloads/)。

### 2. 下載腳本

將本專案的 `notion_to_obsidian.py` (或您命名的檔案) 下載到您的電腦。

### 3. 從 Notion 匯出

1. 在 Notion 中前往 **Settings & Members** > **Settings** > **Export all workspace content**。
2. Export format 選擇 **Markdown & CSV**。
3. **Include subpages** 務必勾選。
4. 下載匯出的 ZIP 檔案。

### 4. 執行轉換

1. 雙擊執行腳本 (或是透過終端機 `python notion_to_obsidian.py`)。
2. 程式會跳出檔案選擇視窗，請選擇您剛下載的 Notion ZIP 檔。
3. 等待程式執行（視檔案大小而定）。
4. 完成後，程式會自動開啟資料夾，您會看到一個檔名結尾為 `_Obsidian_Ready.zip` 的檔案。

### 5. 匯入 Obsidian

1. 將 `_Obsidian_Ready.zip` 解壓縮。
2. 開啟 Obsidian，選擇 **"Open folder as vault"**。
3. 選擇解壓縮後的資料夾即可開始使用！

## 🛠️ 技術細節 (Technical Details)

- **表格修復邏輯**：腳本會逐行掃描 Markdown，偵測以 `|` 開頭但未閉合的斷行，將其暫存並與下一行合併，直到表格列完整閉合。同時會避開 Code Block (`````) 與 Math Block (`$$`) 以免誤判。
- **CSV 處理**：讀取 CSV 的第一欄（通常是 Title），將其轉換為 `[[WikiLink]]` 列表，並存為同名的 `.md` 檔案。

## ⚠️ 注意事項

- **備份**：此腳本不會修改您的原始 ZIP 檔，但建議在操作前保留原始匯出檔的備份。
- **圖片路徑**：腳本預設不移動圖片位置 (`MOVE_ASSETS = False`)，以保持與 Notion 匯出結構一致，這通常對 Obsidian 相容性最好。

## License

MIT License
