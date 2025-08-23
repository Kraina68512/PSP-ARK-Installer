import requests
import zipfile
import shutil
import os
import customtkinter as ctk
import psutil
from tkinter import messagebox, filedialog
from PIL import Image
import json

# ---------- Setup ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("735x570")
app.title("PSP ARK Installer | v0.5 - Beta")

latest_api_url = "https://api.github.com/repos/PSP-Archive/ARK-4/releases/latest"
latest_url = "https://github.com/PSP-Archive/ARK-4/releases/latest/download/ARK4.zip"
output_file = "temp/ARK4.zip"
output_dir = "temp/ARK4"

# ---------- Header ----------
header_frame = ctk.CTkFrame(app, corner_radius=15)
header_frame.pack(fill="x", pady=10, padx=10)

title_label = ctk.CTkLabel(header_frame, text="⚡ PSP ARK Loader Installer", font=("Arial", 20, "bold"))
title_label.pack(side="left", padx=15, pady=10)

status_label = ctk.CTkLabel(header_frame, text="Ready to install", font=("Arial", 14))
status_label.pack(side="right", padx=15)

# ---------- Progress ----------
progress_frame = ctk.CTkFrame(app, corner_radius=15)
progress_frame.pack(fill="x", pady=10, padx=10)

progress = ctk.CTkProgressBar(progress_frame, width=500)
progress.set(0)
progress.pack(pady=10)

progress_text = ctk.CTkLabel(progress_frame, text="0%", font=("Arial", 12))
progress_text.pack()

# ---------- Drive selection ----------
drive_frame = ctk.CTkFrame(app, corner_radius=15)
drive_frame.pack(pady=10, padx=10, fill="x")

drive_label = ctk.CTkLabel(drive_frame, text="📂 Select PSP drive/folder:", font=("Arial", 14))
drive_label.grid(row=0, column=0, padx=10, pady=10)

drive_var = ctk.StringVar()
drive_combo = ctk.CTkComboBox(drive_frame, variable=drive_var, width=350)
drive_combo.grid(row=0, column=1, padx=10, pady=10)

def detect_drives():
    drives = []
    if os.name == "nt":  # Windows
        for p in psutil.disk_partitions(all=False):
            if "removable" in p.opts.lower():
                drives.append(p.device)
    else:
        media_root = "/media"
        if os.path.exists(media_root):
            for d in os.listdir(media_root):
                drives.append(os.path.join(media_root, d))
    return drives

def refresh_drives():
    drives = detect_drives()
    if drives:
        drive_combo.configure(values=drives)
        drive_var.set(drives[0])
    else:
        drive_combo.configure(values=["<Choose manually>"])
        drive_var.set("<Choose manually>")

refresh_button = ctk.CTkButton(drive_frame, text="🔄 Refresh", command=refresh_drives)
refresh_button.grid(row=0, column=2, padx=10, pady=10)

refresh_drives()

# ---------- Log output ----------
log_frame = ctk.CTkFrame(app, corner_radius=15)
log_frame.pack(fill="both", expand=True, pady=10, padx=10)

log_label = ctk.CTkLabel(log_frame, text="📜 Installation Log", font=("Arial", 14, "bold"))
log_label.pack(anchor="w", padx=10, pady=5)

log_box = ctk.CTkTextbox(log_frame, height=200, state="disabled")
log_box.pack(fill="both", expand=True, padx=10, pady=5)

def log(message: str):
    log_box.configure(state="normal")
    log_box.insert("end", f"{message}\n")
    log_box.see("end")
    log_box.configure(state="disabled")
    app.update()

# ---------- Logic ----------
def is_removable(path: str) -> bool:
    if os.name == "nt":
        for p in psutil.disk_partitions(all=False):
            if path.startswith(p.device):
                return "removable" in p.opts.lower()
        return False
    else:
        return path.startswith("/media/") or path.startswith("/mnt/")

def install():
    dest = drive_var.get()
    if not dest or not os.path.exists(dest):
        messagebox.showerror("Error", "Please select a valid drive or folder!")
        return

    os.makedirs("temp", exist_ok=True)

    # Download
    status_label.configure(text="Searching for version name...")
    log("📡 Searching for version name...")

    response = requests.get(latest_api_url)
    data = response.json()
    latest_tag = data["tag_name"]

    latest_tag_dict = {"version": latest_tag}

    with open(os.path.join(dest, "ARK-4.json"), "w", encoding="utf-8") as file:
        json.dump(latest_tag_dict, file, indent=4)
    log("    - Created ARK-4 version file")


    status_label.configure(text="Downloading...")
    log("📥 Downloading latest ARK release...")
    response = requests.get(latest_url, stream=True)
    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    progress.set(0)

    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    fraction = downloaded / total
                    progress.set(fraction)
                    progress_text.configure(text=f"{int(fraction*100)}%")
                    app.update()

    # Extract
    status_label.configure(text="Extracting...")
    log("📦 Extracting archive...")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    progress.set(0.3)
    progress_text.configure(text="30%")

    # Copy files
    status_label.configure(text="Copying files...")
    log("📂 Copying files to PSP...")

    try:
        iso = os.path.join(dest, "ISO")
        os.makedirs(iso, exist_ok=True)
        progress.set(0.01)
        progress_text.configure(text="1%")

        log(f"    - Successfully created dir \"ISO\"")

        seplugins = os.path.join(dest, "seplugins")
        os.makedirs(seplugins, exist_ok=True)
        progress.set(0.01)
        progress_text.configure(text="1%")

        log(f"    - Successfully created dir \"seplugins\"")

        savedata_dst = os.path.join(dest, "PSP", "SAVEDATA")
        os.makedirs(savedata_dst, exist_ok=True)
        shutil.copytree(os.path.join(output_dir, "ARK_01234"),
                        os.path.join(savedata_dst, "ARK_01234"),
                        dirs_exist_ok=True)
        progress.set(0.5)
        progress_text.configure(text="50%")

        log(f"    - Successfully copyed \"ARK_01234\"")

        game_dst = os.path.join(dest, "PSP", "GAME")
        os.makedirs(game_dst, exist_ok=True)
        shutil.copytree(os.path.join(output_dir, "ARK_Loader"),
                        os.path.join(game_dst, "ARK_Loader"),
                        dirs_exist_ok=True)
        progress.set(0.7)
        progress_text.configure(text="70%")

        log(f"    - Successfully copyed \"ARK_Loader\"")

        game_dst = os.path.join(dest, "PSP", "GAME")
        os.makedirs(game_dst, exist_ok=True)
        shutil.copytree(os.path.join(output_dir, "UPDATE"),
                        os.path.join(game_dst, "UPDATE"),
                        dirs_exist_ok=True)
        progress.set(0.9)
        progress_text.configure(text="90%")

        log(f"    - Successfully copyed \"UPDATE\"")

        game_dst = os.path.join(dest, "PSP")
        os.makedirs(game_dst, exist_ok=True)
        shutil.copytree(os.path.join(output_dir, "themes"),
                        os.path.join(game_dst, "themes"),
                        dirs_exist_ok=True)
        progress.set(0.9)
        progress_text.configure(text="100%")

        log(f"    - Successfully copyed \"themes\"")

        for extra in ["ARK_cIPL"]:
            src = os.path.join(output_dir, "PSP", extra)
            if os.path.exists(src):
                shutil.copytree(src, os.path.join(game_dst, "GAME", extra), dirs_exist_ok=True)
                log(f"    - Successfully copyed \"{extra}\"")

        progress.set(1.0)
        progress_text.configure(text="100%")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy files: {e}")
        log(f"❌ Error: {e}")
        return

    status_label.configure(text="Done!")
    log("✅ Installation completed!")
    messagebox.showinfo("Success", "ARK successfully installed!")

# ---------- Buttons ----------
button_frame = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
button_frame.pack(pady=20)

install_button = ctk.CTkButton(
    button_frame,
    text="🚀 Install",
    font=("Arial", 18, "bold"),
    height=50,
    command=install
)
install_button.pack(side="left", padx=10)

# ---------- Add Plugin ----------
def add_plugin_window():
    dest = drive_var.get()
    if not os.path.exists(os.path.join(dest, "ARK-4.json")):
        messagebox.showerror("Error", "Please select a valid drive or folder! (Install ARK-4!)")
        return

    win = ctk.CTkToplevel(app)
    win.title("Add Plugin")
    win.geometry("400x310")

    ctk.CTkLabel(win, text="Plugin Type:").pack(pady=(10, 5))
    plugin_type = ctk.CTkComboBox(win, values=["File", "Folder"])
    plugin_type.set("File")
    plugin_type.pack(pady=5)

    ctk.CTkLabel(win, text="Plugin Level:").pack(pady=(10, 5))
    plugin_level = ctk.CTkComboBox(win, values=["VSH", "GAME", "POPS"])
    plugin_level.set("GAME")
    plugin_level.pack(pady=5)

    path_var = ctk.StringVar(value="Not Chosen")

    def choose_path():
        if plugin_type.get() == "File":
            chosen = filedialog.askopenfilename(title="Choose the plugin's file",
                                                filetypes=[("ARK-4 Plugin File", "*.prx")])
        else:
            chosen = filedialog.askdirectory(title="Choose the plugin's folder")
        if chosen:
            path_var.set(chosen)

    choose_btn = ctk.CTkButton(win, text="📂 Choose...", command=choose_path)
    choose_btn.pack(pady=10)

    path_label = ctk.CTkLabel(win, textvariable=path_var, wraplength=350)
    path_label.pack(pady=5)

    def save_plugin():
        if path_var.get() == "Not Chosen":
            messagebox.showerror("Error", "Choose the file or folder of plugin!")
            return

        plugin_path = path_var.get()
        plugin_path_basename = os.path.basename(plugin_path)

        seplugins_dir = os.path.join(dest, "seplugins")
        os.makedirs(seplugins_dir, exist_ok=True)

        level = plugin_level.get()
        txt_file = os.path.join(seplugins_dir, "PLUGINS.txt")

        if plugin_type.get() == "Folder":
            target_path = os.path.join(seplugins_dir, plugin_path_basename)
            shutil.copytree(plugin_path, target_path, dirs_exist_ok=True)

            prx_file = None
            for file in os.listdir(target_path):
                if file.endswith(".prx"):
                    prx_file = file
                    break
            if not prx_file:
                messagebox.showerror("Error", "Choose the file or folder of plugin!")
                return

            plugin_ref = f"ms0:/seplugins/{plugin_path_basename}/{prx_file}"
        else:
            target_path = os.path.join(seplugins_dir, plugin_path_basename)
            shutil.copy2(plugin_path, target_path)
            plugin_ref = f"ms0:/seplugins/{plugin_path_basename}"

        plugin_entry = f"{level}, {plugin_ref}, 0\n"
        with open(txt_file, "a", encoding="utf-8") as f:
            f.write(plugin_entry)

        log(f"🔌 Added plugin: {plugin_path_basename} [{level}]")
        win.destroy()

    save_btn = ctk.CTkButton(win, text="✅ Add", command=save_plugin)
    save_btn.pack(pady=15)

add_plugin_button = ctk.CTkButton(
    button_frame,
    text="🔌 Add Plugin",
    font=("Arial", 18, "bold"),
    height=50,
    command=add_plugin_window
)
add_plugin_button.pack(side="left", padx=10)

# ---------- Add Game ----------
def add_game():
    dest = drive_var.get()
    if not dest or not os.path.exists(dest):
        messagebox.showerror("Error", "Please select a valid drive or folder!")
        return
    
    if not os.path.exists(os.path.join(dest, "ARK-4.json")):
        messagebox.showerror("Error", "Please select a valid drive or folder! (Install ARK-4!)")
        return

    game_file = filedialog.askopenfilename(
        title="Select ISO/CSO Game File",
        filetypes=[("PSP Game Files", "*.iso *.cso")]
    )
    if not game_file:
        return

    iso_dir = os.path.join(dest, "ISO")
    os.makedirs(iso_dir, exist_ok=True)

    target_path = os.path.join(iso_dir, os.path.basename(game_file))

    buffer_size = 1024 * 1024 * 8  # 8 MB
    total_size = os.path.getsize(game_file)
    copied_size = 0

    status_label.configure(text="Copying game...")
    log(f"📂 Copying {os.path.basename(game_file)} to ISO folder...")

    with open(game_file, "rb") as src, open(target_path, "wb") as dst:
        while True:
            chunk = src.read(buffer_size)
            if not chunk:
                break
            dst.write(chunk)
            copied_size += len(chunk)

            fraction = copied_size / total_size
            progress.set(fraction)
            progress_text.configure(text=f"{int(fraction * 100)}%")
            app.update()

    progress.set(1.0)
    progress_text.configure(text="100%")
    status_label.configure(text="Done!")

    log(f"🎮 Game added: {os.path.basename(game_file)}")
    messagebox.showinfo("Success", f"Game {os.path.basename(game_file)} added successfully!")

add_game_button = ctk.CTkButton(
    button_frame,
    text="➕ Add Game",
    font=("Arial", 18, "bold"),
    height=50,
    command=add_game
)
add_game_button.pack(side="left", padx=10)

# ---------- Banner ----------
banner = ctk.CTkFrame(app, corner_radius=0, fg_color="#1e1e1e")
banner.place(x=0, y=0, relwidth=1, relheight=1)

banner_label_1 = ctk.CTkLabel(
    banner, 
    text="⚡ PSP ⚡", 
    font=("Arial", 45, "bold")
)
banner_label_1.pack(expand=True)

pil_image = Image.open("res/banner.png")
pil_image = pil_image.resize((400, 100))
banner_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(400, 100))
banner_image_label = ctk.CTkLabel(banner, image=banner_image, text="")
banner_image_label.pack(pady=20)

banner_label_2 = ctk.CTkLabel(
    banner, 
    text="Installer", 
    font=("Arial", 45, "bold")
)
banner_label_2.pack(expand=True)

def slide_banner(step=0):
    if step == 0:
        app.after(1000, lambda: slide_banner(step+1))
        return

    x = (step-1) * 40
    if x < app.winfo_width():
        banner.place(x=x, y=0, relwidth=1, relheight=1)
        app.after(15, lambda: slide_banner(step+1))
    else:
        banner.place_forget()

app.after(100, slide_banner)

app.mainloop()
