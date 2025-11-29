@echo off
title Notion to Obsidian 轉換工具
:: 設定編碼為 UTF-8 以正確顯示中文 (若有問題可註解此行)
chcp 65001 >nul

echo ========================================================
echo       Notion to Obsidian 批量轉換工具
echo ========================================================
echo.

:: 嘗試用 'python' 執行
python N2O.py
if %errorlevel% equ 0 goto :END_EXECUTION

echo --------------------------------------------------------
echo [警告] 嘗試使用 'python' 失敗，錯誤代碼: %errorlevel%
echo --------------------------------------------------------
echo 正在嘗試使用 'py' (Python Launcher)...

:: 嘗試用 'py' 執行 (通常在 Windows 安裝 Python 時會附帶)
py notion_to_obsidian_bulk.py
if %errorlevel% equ 0 goto :END_EXECUTION

echo --------------------------------------------------------
echo [嚴重錯誤] 無法啟動 N2O.py！
echo 請檢查以下項目：
echo 1. 'run.bat' 與 'N2O.py' 是否在同一個資料夾。
echo 2. Python 是否已安裝並正確加入到系統 PATH 環境變數中。
echo --------------------------------------------------------
goto :END_PAUSE

:END_EXECUTION
echo.
echo ✅ notion_to_obsidian_bulk.py 程式已執行完畢。
echo.

:END_PAUSE
echo.
echo ========================================================
echo 執行結束。請按任意鍵關閉視窗...
pause >nul
exit /b