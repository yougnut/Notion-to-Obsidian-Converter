@echo off
title Notion to Obsidian 轉換工具
chcp 65001 >nul

echo ========================================================
echo       Notion to Obsidian 批量轉換工具
echo ========================================================
echo.
echo [1/2] 正在啟動設定視窗...
python config_setup.py
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ 設定程序未正常結束，將嘗試使用預設設定繼續...
)

echo.
echo [2/2] 正在啟動轉換程式...
echo.
python notion_to_obsidian_bulk.py

if %errorlevel% neq 0 (
    echo.
    echo --------------------------------------------------------
    echo [錯誤] 程式執行失敗。
    echo 請確認已安裝 Python，且所有 .py 檔案都在同一資料夾中。
    echo --------------------------------------------------------
    pause
    exit /b
)

echo.
echo ========================================================
echo 執行結束。請按任意鍵關閉視窗...
pause >nul