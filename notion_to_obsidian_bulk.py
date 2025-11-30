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
import sys
import configparser
import filecmp

# ================= 全域設定 (將由 Config 控制) =================
CONFIG_FILE = 'config.ini'
SETTINGS = {
    'move_assets': False,
    'enable_yaml': True,
    'fix_tables': True,
    'delete_source_csv': True,
    'auto_zip': True,
    'open_folder': True
}

def load_settings():
    global SETTINGS
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding='utf-8')
            if 'General' in config:
                for key in SETTINGS:
                    if key in config['General']:
                        SETTINGS[key] = config['General'].getboolean(key)
        except Exception as e:
            print(f"設定檔讀取錯誤: {e}")

# ================= 核心功能 =================

def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', printEnd="\r"):
    if total == 0: return
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total: sys.stdout.write('\n')

def get_clean_name(name):
    # 移除 Notion ID
    pattern = r" [0-9a-f]{32}"
    new_name = re.sub(pattern, "", name)
    return new_name

def process_tags(text):
    def tag_replacer(match):
        tags_content = match.group(1)
        tags = [t.strip() for t in tags_content.split(',')]
        hashtag_list = [f"#{t}" for t in tags if t]
        return "Tags: " + " ".join(hashtag_list)
    return re.sub(r"^Tags:\s(.+)", tag_replacer, text, flags=re.MULTILINE)

def process_properties_to_yaml(text):
    if not SETTINGS['enable_yaml']: return text
    lines = text.split('\n')
    new_lines = []
    yaml_props = {}
    state = 0
    prop_pattern = re.compile(r'^([^:\n]+):\s*(.*)$')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if state == 0:
            new_lines.append(line)
            if stripped.startswith('# '): state = 1
            continue
        if state == 1:
            if not stripped: continue
            match = prop_pattern.match(stripped)
            if match and not stripped.startswith(('http:', 'https:', 'ftp:', 'mailto:', '>')):
                key = match.group(1).strip()
                val = match.group(2).strip()
                if len(key) < 50: 
                    yaml_props[key] = val
                    continue
            state = 2
            new_lines.append(line)
            continue
        if state == 2: new_lines.append(line)
    if yaml_props:
        yaml_block = ["---"]
        for k, v in yaml_props.items():
            if ':' in v or '#' in v: v = f'"{v}"'
            yaml_block.append(f"{k}: {v}")
        yaml_block.append("---\n")
        return '\n'.join(yaml_block) + '\n'.join(new_lines)
    return text

def fix_table_formatting(text):
    if not SETTINGS['fix_tables']: return text
    lines = text.split('\n')
    new_lines = []
    buffer = ""
    in_code_block = False
    in_math_block = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            if buffer: new_lines.append(buffer); buffer = ""
            new_lines.append(line); continue
        if line.strip() == '$$':
            in_math_block = not in_math_block
            if buffer: new_lines.append(buffer); buffer = ""
            new_lines.append(line); continue
        if in_code_block or in_math_block: new_lines.append(line); continue
        stripped = line.strip()
        if buffer:
            buffer += "<br>" + stripped
            if stripped.endswith('|'): new_lines.append(buffer); buffer = ""
            continue
        if stripped.startswith('|'):
            if stripped.endswith('|'): new_lines.append(line)
            else: buffer = line
        else: new_lines.append(line)
    if buffer: new_lines.append(buffer)
    return '\n'.join(new_lines)

def clean_content(text):
    # 原本的 convert_toggles 已移除
    text = fix_table_formatting(text)
    def link_replacer(match):
        label = match.group(1)
        url = match.group(2)
        if url.startswith("about:blank"): return f"[[{label}]]"
        decoded_url = urllib.parse.unquote(url)
        if decoded_url.startswith(('http://', 'https://', 'ftp://', 'mailto:')): return match.group(0)
        parts = decoded_url.split('/')
        clean_parts = [get_clean_name(p) for p in parts]
        clean_url = '/'.join(clean_parts)
        if clean_url.lower().endswith('_all.csv'):
            clean_url = clean_url.replace('_all.csv', '.csv')
        if clean_url.lower().endswith('.csv'): 
            clean_url = clean_url[:-4] + '.md'
        encoded_clean_url = clean_url.replace(" ", "%20")
        return f"[{label}]({encoded_clean_url})"
    text = re.sub(r"\[(.*?)\]\((.*?)\)", link_replacer, text)
    text = process_tags(text)
    text = process_properties_to_yaml(text)
    callout_map = {'💡': 'TIP', '⚠️': 'WARNING', '🚫': 'FAILURE', '✅': 'SUCCESS', 'ℹ️': 'INFO', '🔥': 'DANGER'}
    for emoji, kind in callout_map.items():
        text = text.replace(f"> {emoji}", f"> [!{kind}]")
        text = text.replace(f"> **{emoji}**", f"> [!{kind}]")
    return text

def handle_smart_merge_csv(target_dir):
    print("正在執行 CSV 智慧合併與清理...")
    csv_files = []
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            if f.endswith('.csv'):
                csv_files.append(os.path.join(root, f))
    all_variants = [f for f in csv_files if f.lower().endswith('_all.csv')]
    for all_file in all_variants:
        original_file = all_file[:-8] + ".csv"
        if os.path.exists(original_file):
            size_all = os.path.getsize(all_file)
            size_orig = os.path.getsize(original_file)
            if size_all > size_orig:
                try: shutil.move(all_file, original_file)
                except Exception as e: print(f"  [錯誤] 合併失敗: {e}")
            else:
                try: os.remove(all_file)
                except: pass
        else:
            try: os.rename(all_file, original_file)
            except: pass

def convert_csv_to_md(file_path, error_list):
    try:
        dirname = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(filename)[0]
        md_filename = name_no_ext + ".md"
        md_path = os.path.join(dirname, md_filename)

        if os.path.exists(md_path):
            mode = 'a' 
            header_text = "\n\n## Database Items\n"
        else:
            mode = 'w'
            header_text = f"# {name_no_ext}\n\n"

        links = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.reader(csvfile)
            try: headers = next(reader) 
            except StopIteration: return 
            for row in reader:
                if row:
                    item_name = row[0]
                    clean_item_name = get_clean_name(item_name)
                    if clean_item_name: links.append(f"- [[{clean_item_name}]]")
        if links:
            with open(md_path, mode, encoding='utf-8') as md_file:
                md_file.write(header_text)
                md_file.write("\n".join(links))
                md_file.write("\n")
            if SETTINGS['delete_source_csv']:
                try: os.remove(file_path)
                except: pass
    except Exception as e: error_list.append(f"[CSV 失敗] {os.path.basename(file_path)}: {e}")

def select_and_extract_zip():
    root = tk.Tk()
    root.withdraw()
    print(">>> 請在彈出的視窗中選擇 Notion 匯出的 ZIP 檔...")
    zip_path = filedialog.askopenfilename(title="請選擇 Notion 匯出的 ZIP 檔", filetypes=[("Zip files", "*.zip"), ("All files", "*.*")])
    if not zip_path: return None
    base_dir = os.path.dirname(zip_path)
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_path = os.path.join(base_dir, f"{zip_name}_Obsidian_Ready")
    if not os.path.exists(extract_path): os.makedirs(extract_path)
    print(f"正在解壓縮至: {extract_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(extract_path)
        inner_items = os.listdir(extract_path)
        inner_zips = [f for f in inner_items if f.lower().endswith('.zip')]
        if inner_zips:
            print(f"偵測到 {len(inner_zips)} 個內部壓縮檔，正在展開並清理...")
            for zf in inner_zips:
                zf_full_path = os.path.join(extract_path, zf)
                try:
                    with zipfile.ZipFile(zf_full_path, 'r') as inner_zip_ref:
                        inner_zip_ref.extractall(extract_path)
                    os.remove(zf_full_path) 
                except zipfile.BadZipFile: print(f"  - 警告: 無法解壓 {zf}")
        has_content = False
        for root, dirs, files in os.walk(extract_path):
            if any(f.lower().endswith(('.md', '.csv')) for f in files): has_content = True; break
        if not has_content:
            if not messagebox.askyesno("警告", "目標資料夾沒有 .md 筆記，是否繼續？"): return None
        return extract_path
    except zipfile.BadZipFile: messagebox.showerror("錯誤", "無效的 ZIP 檔案。"); return None

def process_renaming(target_dir):
    print("步驟 1/4: 清洗檔案與資料夾名稱...")
    all_files = []
    all_dirs = []
    for dirpath, dirnames, filenames in os.walk(target_dir, topdown=False):
        for name in filenames:
            if name.endswith(('.md', '.csv', '.png', '.jpg', '.jpeg', '.pdf', '.html')):
                all_files.append((dirpath, name))
        for name in dirnames: all_dirs.append((dirpath, name))
    total_ops = len(all_files) + len(all_dirs)
    current_op = 0
    print_progress(0, total_ops, prefix='進度:', suffix='完成', length=40)
    for dirpath, name in all_files:
        new_name = get_clean_name(name)
        if new_name != name:
            old_path = os.path.join(dirpath, name)
            new_path = os.path.join(dirpath, new_name)
            if not os.path.exists(new_path): os.rename(old_path, new_path)
        current_op += 1
        print_progress(current_op, total_ops, prefix='進度:', suffix='完成', length=40)
    for dirpath, name in all_dirs:
        new_name = get_clean_name(name)
        if new_name != name:
            old_path = os.path.join(dirpath, name)
            new_path = os.path.join(dirpath, new_name)
            if not os.path.exists(new_path): os.rename(old_path, new_path)
        current_op += 1
        print_progress(current_op, total_ops, prefix='進度:', suffix='完成', length=40)

def compress_folder_to_zip(folder_path):
    base_name = folder_path
    zip_filename = base_name + ".zip"
    total_files = 0
    for root, dirs, files in os.walk(folder_path): total_files += len(files)
    print_progress(0, total_files, prefix='壓縮:', suffix='完成', length=40)
    current_count = 0
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
                current_count += 1
                print_progress(current_count, total_files, prefix='壓縮:', suffix='完成', length=40)
    return zip_filename

def open_file_explorer(path):
    if platform.system() == "Windows": os.startfile(path)
    elif platform.system() == "Darwin": subprocess.Popen(["open", path])
    else: subprocess.Popen(["xdg-open", path])

def main():
    load_settings()
    target_dir = select_and_extract_zip()
    if not target_dir: return
    error_log = []

    # 1. 重命名 (去除 ID)
    process_renaming(target_dir)

    # 2. 智慧合併 CSV
    handle_smart_merge_csv(target_dir)

    # 3. 轉換 CSV 為 MD
    print("步驟 2/4: 轉換 Database 表格...")
    csv_files = []
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for name in filenames:
            if name.endswith('.csv'): csv_files.append(os.path.join(dirpath, name))
    
    total_csv = len(csv_files)
    print_progress(0, total_csv, prefix='進度:', suffix='完成', length=40)
    for i, csv_path in enumerate(csv_files):
        convert_csv_to_md(csv_path, error_log)
        print_progress(i + 1, total_csv, prefix='進度:', suffix='完成', length=40)

    # 4. 修復內容
    print("步驟 3/4: 修復表格、連結、Tags、Properties 與格式...")
    md_files = []
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for name in filenames:
            if name.endswith('.md'): md_files.append(os.path.join(dirpath, name))
                
    total_md = len(md_files)
    processed_count = 0
    print_progress(0, total_md, prefix='進度:', suffix='完成', length=40)
    
    for i, file_path in enumerate(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
            new_content = clean_content(content)
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
                processed_count += 1
        except Exception as e: error_log.append(f"[筆記失敗] {os.path.basename(file_path)}: {e}")
        print_progress(i + 1, total_md, prefix='進度:', suffix='完成', length=40)

    print("-" * 40)
    print(f"✅ 轉換成功！共修改了 {processed_count} 篇筆記。")

    if error_log:
        print("\n" + "="*20 + " ⚠️ 轉換異常報告 " + "="*20)
        for err in error_log: print(err)
        print("="*56 + "\n")
        if messagebox.askyesno("轉換報告", f"共有 {len(error_log)} 個錯誤。是否儲存日誌 (conversion_error_log.txt)？"):
            parent_dir = os.path.dirname(target_dir)
            log_path = os.path.join(parent_dir, "conversion_error_log.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("=== Notion to Obsidian Conversion Error Log ===\n")
                f.write("\n".join(error_log))
            print(f"已儲存錯誤日誌至: {log_path}")

    # 5. 根據新設定執行後續動作
    zip_generated_path = None
    if SETTINGS['auto_zip']:
        print("\n步驟 4/4: 重新打包為 ZIP...")
        zip_generated_path = compress_folder_to_zip(target_dir)
        print(f"已建立壓縮檔: {zip_generated_path}")
    else:
        print("\n步驟 4/4: 跳過壓縮步驟。")

    if SETTINGS['open_folder']:
        parent_dir = os.path.dirname(target_dir)
        open_file_explorer(parent_dir)
    
    # 建立完成訊息
    msg = "轉換完成！"
    if zip_generated_path:
        msg += f"\n\nZIP 檔已儲存於：\n{zip_generated_path}"
    if SETTINGS['open_folder']:
        msg += "\n\n已為您開啟檔案位置。"
        
    messagebox.showinfo("完成", msg)

if __name__ == "__main__":
    main()