import tkinter as tk
import configparser
import os
import sys

CONFIG_FILE = 'config.ini'

# 預設設定值
# 注意：隱藏的選項在此設定預設值 (True/False)，主程式會讀取這些值
DEFAULT_SETTINGS = {
    # --- 隱藏的選項 ---
    'move_assets': 'False',       # 移動圖片 (預設不移動)
    'enable_yaml': 'True',        # YAML 轉換 (預設開啟)
    'fix_tables': 'True',         # 表格修復 (預設開啟)
    'delete_source_csv': 'True',  # 刪除 CSV (預設開啟)
    
    # --- 顯示在介面上的選項 ---
    'auto_zip': 'True',           # [新增] 自動壓縮
    'open_folder': 'True',        # [新增] 開啟資料夾
    'always_show_config': 'True'  # 總是顯示設定視窗
}

def load_config():
    """讀取現有設定，若無則回傳預設值字典"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding='utf-8')
            if 'General' in config:
                return config['General']
        except:
            pass
    return DEFAULT_SETTINGS

def save_config(settings_dict):
    """儲存設定到 ini 檔"""
    config = configparser.ConfigParser()
    config['General'] = settings_dict
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        config.write(f)

def get_bool(settings, key):
    """安全獲取布林值的輔助函式"""
    if hasattr(settings, 'getboolean'):
        return settings.getboolean(key, fallback=(DEFAULT_SETTINGS[key] == 'True'))
    
    val = settings.get(key, DEFAULT_SETTINGS[key])
    if isinstance(val, bool):
        return val
    return str(val).lower() == 'true'

def main():
    current_settings = load_config()
    
    # 判斷是否需要顯示視窗
    always_show = get_bool(current_settings, 'always_show_config')
    should_show = not os.path.exists(CONFIG_FILE) or always_show
    
    if not should_show:
        return

    # --- 建立 GUI ---
    root = tk.Tk()
    root.title("Notion to Obsidian 轉換設定")
    
    # 視窗置中
    window_width = 450
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_c = int((screen_width/2) - (window_width/2))
    y_c = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_c}+{y_c}")

    # 標題
    tk.Label(root, text="轉換偏好設定", font=("Microsoft JhengHei", 14, "bold")).pack(pady=15)
    tk.Label(root, text="請勾選您想要啟用的功能：", font=("Microsoft JhengHei", 10)).pack(pady=5)
    
    frame = tk.Frame(root)
    frame.pack(pady=10, padx=30, anchor="w")

    # 選項定義 (只保留需要顯示的)
    labels = {
        'auto_zip': "轉換完成後重新壓縮為 ZIP 檔",
        'open_folder': "轉換完成後開啟目標資料夾",
        'always_show_config': "下次啟動時再次顯示此設定視窗"
    }
    
    # 選項顯示順序
    visible_order = ['auto_zip', 'open_folder', 'always_show_config']
    
    vars_dict = {}

    for key in visible_order:
        val = get_bool(current_settings, key)
        vars_dict[key] = tk.BooleanVar(value=val)
        
        cb = tk.Checkbutton(
            frame, 
            text=labels[key], 
            variable=vars_dict[key], 
            font=("Microsoft JhengHei", 10),
            justify="left"
        )
        cb.pack(anchor="w", pady=5)

    def on_confirm():
        # 收集設定並儲存
        final_settings = {}
        
        # 1. 先載入所有預設值
        for k, v in DEFAULT_SETTINGS.items():
            final_settings[k] = v
            
        # 2. 如果之前有讀取到設定，保留舊的隱藏設定值
        if hasattr(current_settings, 'keys'): # ConfigParser
            for k in current_settings:
                if k not in visible_order:
                     final_settings[k] = current_settings[k]
        elif isinstance(current_settings, dict):
             for k, v in current_settings.items():
                if k not in visible_order:
                    final_settings[k] = str(v)

        # 3. 覆蓋 GUI 上有顯示的選項
        for k, v in vars_dict.items():
            final_settings[k] = str(v.get())
        
        save_config(final_settings)
        print("設定已儲存。")
        root.destroy()

    # 確認按鈕
    btn = tk.Button(
        root, 
        text="儲存並開始轉換", 
        command=on_confirm, 
        bg="#4CAF50", 
        fg="white", 
        font=("Microsoft JhengHei", 12, "bold"), 
        height=2, 
        width=20
    )
    btn.pack(pady=20)
    
    root.attributes('-topmost', True)
    root.mainloop()

if __name__ == "__main__":
    main()