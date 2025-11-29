import os
import re
import urllib.parse
import shutil
import zipfile
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
import subprocess

# =================配置區=================
# 為了保持檔案結構穩定，建議不移動圖片，讓 Obsidian 自動管理相對路徑
# 若設為 True，需確保沒有同名圖檔衝突
MOVE_ASSETS = False 
# =======================================

def get_clean_name(name):
    """
    清洗函數：移除 Notion 32 碼 ID
    保留中文、空格與常見符號 (如 - _ )
    """
    # 邏輯：尋找 " 空格 + 32個十六進位字元"，且位於副檔名前或字串結尾
    pattern = r" [0-9a-f]{32}(?=(\.[^.]+$|$))"
    new_name = re.sub(pattern, "", name)
    return new_name

def process_tags(text):
    """
    將 Notion 的 Tags: A, B 轉換為 Obsidian 的 #A #B
    """
    def tag_replacer(match):
        tags_content = match.group(1)
        # 依逗號分割
        tags = [t.strip() for t in tags_content.split(',')]
        # 加上 # 前綴
        hashtag_list = [f"#{t}" for t in tags if t]
        return "Tags: " + " ".join(hashtag_list)

    return re.sub(r"^Tags:\s(.+)", tag_replacer, text, flags=re.MULTILINE)

def fix_table_formatting(text):
    """
    修復 Notion 匯出時表格斷行的問題。
    Notion 的表格若有換行，匯出時會變成多行文字，導致 Markdown 表格語法失效。
    此函數會將斷開的表格列合併，並用 <br> 取代換行。
    同時會避開 Code Block (```) 與 Math Block ($$)，以免破壞程式碼或公式。
    """
    lines = text.split('\n')
    new_lines = []
    buffer = ""
    in_code_block = False
    in_math_block = False
    
    for line in lines:
        # 偵測程式碼區塊 ```
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            if buffer: # 如果進入 code block 前有未完成的表格列，先強制寫入 (防呆)
                new_lines.append(buffer)
                buffer = ""
            new_lines.append(line)
            continue

        # 偵測數學公式區塊 $$ (Notion 常用格式)
        if line.strip() == '$$':
            in_math_block = not in_math_block
            if buffer:
                new_lines.append(buffer)
                buffer = ""
            new_lines.append(line)
            continue

        # 若在特殊區塊內，直接保留原樣
        if in_code_block or in_math_block:
            new_lines.append(line)
            continue

        stripped = line.strip()
        
        # --- 表格修復邏輯 ---
        if buffer:
            # 如果 buffer 有內容，表示上一行是「以 | 開頭但沒結尾」的斷行表格
            # 我們將這一行合併進去，並用 <br> 取代換行
            buffer += "<br>" + stripped
            
            # 檢查這行是否補上了結尾的 |
            if stripped.endswith('|'):
                new_lines.append(buffer)
                buffer = ""
            continue
            
        # 檢查是否為表格的開始 (以 | 開頭)
        if stripped.startswith('|'):
            # 檢查是否完整 (以 | 結尾)
            if stripped.endswith('|'):
                # 完整的表格列，直接加入
                new_lines.append(line)
            else:
                # 不完整 (斷行了)，放入 buffer 等待下一行拼接
                # 注意：buffer 存入原始 line (保留縮排)，但後續拼接用 stripped
                buffer = line
        else:
            # 普通文字行
            new_lines.append(line)
            
    # 如果檔案結束還有 buffer，把它倒出來
    if buffer:
        new_lines.append(buffer)
        
    return '\n'.join(new_lines)

def clean_content(text):
    """
    清洗 Markdown 內容主邏輯
    """
    # 0. 優先修復表格格式 (避免斷行影響後續 Regex)
    text = fix_table_formatting(text)

    # 1. 修復連結 [Label](Path/To/Folder ID/File ID.md)
    def link_replacer(match):
        label = match.group(1)
        url = match.group(2)
        
        # 處理 about:blank
        if url.startswith("about:blank"):
            # 嘗試修復為 Wiki Link
            return f"[[{label}]]"

        decoded_url = urllib.parse.unquote(url)
        
        if decoded_url.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            return match.group(0)
            
        parts = decoded_url.split('/')
        clean_parts = [get_clean_name(p) for p in parts]
        clean_url = '/'.join(clean_parts)
        
        encoded_clean_url = urllib.parse.quote(clean_url)
        return f"[{label}]({encoded_clean_url})"

    text = re.sub(r"\[(.*?)\]\((.*?)\)", link_replacer, text)
    
    # 2. 處理 Tags
    text = process_tags(text)
    
    # 3. 轉換 Callout
    callout_map = {
        '💡': 'TIP', '⚠️': 'WARNING', '🚫': 'FAILURE', 
        '✅': 'SUCCESS', 'ℹ️': 'INFO', '🔥': 'DANGER'
    }
    
    for emoji, kind in callout_map.items():
        text = text.replace(f"> {emoji}", f"> [!{kind}]")
        text = text.replace(f"> **{emoji}**", f"> [!{kind}]")

    return text

def convert_csv_to_md(file_path):
    """
    將 CSV 資料庫轉換為 Markdown 索引頁
    """
    try:
        dirname = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(filename)[0]
        md_filename = name_no_ext + ".md"
        md_path = os.path.join(dirname, md_filename)

        if os.path.exists(md_path):
            mode = 'a' 
            header_text = "\n\n## Database Items (Converted from CSV)\n"
        else:
            mode = 'w'
            header_text = f"# {name_no_ext}\n\n"

        links = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.reader(csvfile)
            try:
                headers = next(reader) 
            except StopIteration:
                return 

            for row in reader:
                if row:
                    item_name = row[0] # 第一欄通常是 Title
                    clean_item_name = get_clean_name(item_name)
                    if clean_item_name:
                        links.append(f"- [[{clean_item_name}]]")

        if links:
            with open(md_path, mode, encoding='utf-8') as md_file:
                md_file.write(header_text)
                md_file.write("\n".join(links))
                md_file.write("\n")
            
    except Exception as e:
        print(f"  [略過] CSV 轉換異常 {file_path}: {e}")

def select_and_extract_zip():
    root = tk.Tk()
    root.withdraw()
    
    print(">>> 請在彈出的視窗中選擇 Notion 匯出的 ZIP 檔...")
    zip_path = filedialog.askopenfilename(
        title="請選擇 Notion 匯出的 ZIP 檔",
        filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
    )
    
    if not zip_path:
        return None
        
    base_dir = os.path.dirname(zip_path)
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    
    # [修改] 使用 _Obsidian_Ready 作為後綴
    extract_path = os.path.join(base_dir, f"{zip_name}_Obsidian_Ready")
    
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
        
    print(f"正在解壓縮至: {extract_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # --- 處理巢狀 ZIP (Notion 雙層壓縮) ---
        inner_items = os.listdir(extract_path)
        inner_zips = [f for f in inner_items if f.lower().endswith('.zip')]
        
        if inner_zips:
            print(f"偵測到 {len(inner_zips)} 個內部壓縮檔，正在展開並清理...")
            for zf in inner_zips:
                zf_full_path = os.path.join(extract_path, zf)
                try:
                    with zipfile.ZipFile(zf_full_path, 'r') as inner_zip_ref:
                        inner_zip_ref.extractall(extract_path)
                    
                    # 關鍵：解壓後刪除 ZIP，保持乾淨
                    os.remove(zf_full_path) 
                except zipfile.BadZipFile:
                    print(f"  - 警告: 無法解壓 {zf}")

        # --- 驗證 ---
        has_content = False
        for root, dirs, files in os.walk(extract_path):
            if any(f.lower().endswith(('.md', '.csv')) for f in files):
                has_content = True
                break
        
        if not has_content:
            proceed = messagebox.askyesno("警告", "目標資料夾沒有 .md 筆記，是否繼續？")
            if not proceed: return None
                
        return extract_path
        
    except zipfile.BadZipFile:
        messagebox.showerror("錯誤", "無效的 ZIP 檔案。")
        return None

def process_renaming(target_dir):
    """
    執行檔名清洗：先檔案，後資料夾 (Bottom-up)
    """
    print("步驟 1/3: 清洗檔案與資料夾名稱...")
    
    # 1. 檔案
    for dirpath, dirnames, filenames in os.walk(target_dir, topdown=False):
        for name in filenames:
            if name.endswith(('.md', '.csv', '.png', '.jpg', '.jpeg', '.pdf', '.html')):
                new_name = get_clean_name(name)
                if new_name != name:
                    old_path = os.path.join(dirpath, name)
                    new_path = os.path.join(dirpath, new_name)
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)

    # 2. 資料夾
    for dirpath, dirnames, filenames in os.walk(target_dir, topdown=False):
        for name in dirnames:
            new_name = get_clean_name(name)
            if new_name != name:
                old_path = os.path.join(dirpath, name)
                new_path = os.path.join(dirpath, new_name)
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)

def compress_folder_to_zip(folder_path):
    """
    將指定資料夾壓縮為 ZIP 檔案
    回傳 ZIP 檔案的完整路徑
    """
    base_name = folder_path
    shutil.make_archive(base_name, 'zip', folder_path)
    return base_name + ".zip"

def open_file_explorer(path):
    """
    跨平台開啟檔案總管
    """
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def main():
    target_dir = select_and_extract_zip()
    if not target_dir: return

    # 1. 重命名
    process_renaming(target_dir)

    # 2. CSV 轉 MD
    print("步驟 2/3: 轉換 Database 表格...")
    csv_files = []
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for name in filenames:
            if name.endswith('.csv'):
                csv_files.append(os.path.join(dirpath, name))
    
    for csv_path in csv_files:
        convert_csv_to_md(csv_path)

    # 3. 內容修復
    print("步驟 3/3: 修復表格、連結、Tags 與格式...")
    processed_count = 0
    
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for name in filenames:
            if name.endswith('.md'):
                file_path = os.path.join(dirpath, name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = clean_content(content)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        processed_count += 1
                except Exception as e:
                    print(f"  [錯誤] {name}: {e}")

    print("-" * 40)
    print(f"✅ 轉換成功！共處理了 {processed_count} 篇筆記。")
    
    # 4. 壓縮與清理
    print("步驟 4/4: 重新打包為 ZIP...")
    zip_path = compress_folder_to_zip(target_dir)
    print(f"已建立壓縮檔: {zip_path}")
    
    # 開啟 ZIP 所在的資料夾 (父目錄)
    parent_dir = os.path.dirname(target_dir)
    print(f"正在開啟檔案位置: {parent_dir}")
    open_file_explorer(parent_dir)

    messagebox.showinfo("完成", f"轉換並打包完成！\n\nZIP 檔已儲存於：\n{zip_path}\n\n已為您開啟檔案位置。")

if __name__ == "__main__":
    main()