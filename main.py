import os
import sys
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
from colormath.color_objects import SpectralColor, LabColor, sRGBColor
from colormath.color_conversions import convert_color

APP_TITLE = "CXF → CIE Lab"
DEVELOPER_INFO = "developed by Ivan leonov | ialeonov@gmail.com | © 2025"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def parse_cxf(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    ns = '{http://colorexchangeformat.com/CxF3-core}'
    objects = root.findall(f".//{ns}ObjectCollection")
    color_data = {}
    lab_data = {}
    spec_mode = None

    for oc in objects:
        for color in oc:
            name = color.attrib.get('Name')

            for spec in color.findall(f".//{ns}ReflectanceSpectrum"):
                spec_code = spec.get('ColorSpecification')
                if spec_code in ['CSM0D502', 'CS000']:
                    spec_mode = '1'
                    color_data[name] = spec.text
                elif 'M0D50' in spec_code or spec_code == 'CSeXact_Advanced009489M0-NPD50-2':
                    spec_mode = '2'
                    color_data[name] = spec.text

            for lab in color.findall(f".//{ns}ColorCIELab"):
                if lab.attrib.get("ColorSpecification") in ['CSM0D502', 'CS000']:
                    try:
                        L = float(lab.find(f"{ns}L").text)
                        A = float(lab.find(f"{ns}A").text)
                        B = float(lab.find(f"{ns}B").text)
                        lab_data[name] = (L, A, B)
                    except:
                        continue

    return color_data, lab_data, spec_mode

def pad_spectral_data(values, mode):
    if mode == '1':
        values = ['0.0'] * 6 + values + ['0.0'] * 13
    elif mode == '2':
        values = ['0.0'] * 4 + values + ['0.0'] * 10
    return [float(v) for v in values]

def convert_to_lab(data_dict, lab_dict, mode):
    results = []
    all_keys = sorted(set(data_dict.keys()) | set(lab_dict.keys()))

    for name in all_keys:
        if name in lab_dict:
            lab = lab_dict[name]
        elif name in data_dict:
            values = pad_spectral_data(data_dict[name].strip().split(), mode)
            spectral = SpectralColor(*values)
            lab = convert_color(spectral, LabColor).get_value_tuple()
        else:
            continue

        lab_obj = LabColor(*lab)
        rgb_obj = convert_color(lab_obj, sRGBColor)
        rgb = (
            max(0, min(255, int(rgb_obj.clamped_rgb_r * 255))),
            max(0, min(255, int(rgb_obj.clamped_rgb_g * 255))),
            max(0, min(255, int(rgb_obj.clamped_rgb_b * 255))),
        )
        results.append((name, lab, rgb))

    return results

def process_file(filepath):
    try:
        data_dict, lab_dict, mode = parse_cxf(filepath)
        result_data = convert_to_lab(data_dict, lab_dict, mode)
        display_results(result_data)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обработать файл:\n{str(e)}")

def browse_and_process():
    filepath = filedialog.askopenfilename(filetypes=[("CXF files", "*.cxf")])
    if not filepath:
        return
    process_file(filepath)

def on_drop(event):
    filepath = event.data.strip().strip('{}')
    if not filepath.lower().endswith('.cxf'):
        messagebox.showerror("Ошибка", "Файл должен быть в формате .cxf")
        return
    process_file(filepath)

def display_results(result_data):
    for widget in output_frame.winfo_children():
        widget.destroy()

    # Прокручиваемая область
    canvas = tk.Canvas(output_frame, bg="#f9f9f9", highlightthickness=0)
    scrollbar = tk.Scrollbar(output_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f9f9f9")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Заголовки в строку 0
    tk.Label(scrollable_frame, text="Цвет", font=("Segoe UI", 10, "bold"), bg="#f9f9f9").grid(row=0, column=0, padx=10, pady=(5, 2))
    tk.Label(scrollable_frame, text="Название", font=("Segoe UI", 10, "bold"), bg="#f9f9f9").grid(row=0, column=1, padx=10, pady=(5, 2), sticky="w")
    tk.Label(scrollable_frame, text="L", font=("Segoe UI", 10, "bold"), bg="#f9f9f9").grid(row=0, column=2, padx=10, pady=(5, 2))
    tk.Label(scrollable_frame, text="a", font=("Segoe UI", 10, "bold"), bg="#f9f9f9").grid(row=0, column=3, padx=10, pady=(5, 2))
    tk.Label(scrollable_frame, text="b", font=("Segoe UI", 10, "bold"), bg="#f9f9f9").grid(row=0, column=4, padx=10, pady=(5, 2))

    # Строки с цветами, начиная с row=1
    for idx, (name, lab, rgb) in enumerate(result_data, start=1):
        # Квадратик цвета
        canvas_preview = tk.Canvas(scrollable_frame, width=90, height=70, highlightthickness=1, highlightbackground="#ccc", bg="#f9f9f9")
        canvas_preview.create_rectangle(0, 0, 90, 70, fill="#%02x%02x%02x" % rgb, outline="")
        canvas_preview.grid(row=idx, column=0, padx=10, pady=5)

        # Название цвета
        tk.Label(scrollable_frame, text=name, font=("Segoe UI", 10), bg="#f9f9f9", anchor="w").grid(row=idx, column=1, sticky="w")

        # LAB
        tk.Label(scrollable_frame, text=f"{lab[0]:.2f}", font=("Consolas", 10), bg="#f9f9f9", anchor="e").grid(row=idx, column=2, padx=10)
        tk.Label(scrollable_frame, text=f"{lab[1]:.2f}", font=("Consolas", 10), bg="#f9f9f9", anchor="e").grid(row=idx, column=3, padx=10)
        tk.Label(scrollable_frame, text=f"{lab[2]:.2f}", font=("Consolas", 10), bg="#f9f9f9", anchor="e").grid(row=idx, column=4, padx=10)


def save_to_file():
    from tkinter import scrolledtext
    filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
    if filepath:
        content_lines = []
        for child in output_frame.winfo_children():
            if isinstance(child, tk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Label):
                        content_lines.append(sub.cget("text"))
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(content_lines))
            messagebox.showinfo("Готово", f"Сохранено:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c:\n{str(e)}")

# --- GUI ---
root = TkinterDnD.Tk()
root.title(APP_TITLE)
root.geometry("700x550")
root.configure(bg="#f9f9f9")

header_frame = tk.Frame(root, bg="#f9f9f9")
header_frame.pack(pady=(10, 5))

try:
    logo_img = Image.open(resource_path("logo.png"))
    logo_img = logo_img.resize((150, 50))
    logo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(header_frame, image=logo, bg="#f9f9f9")
    logo_label.pack(side=tk.LEFT, padx=(0, 10))
except Exception as e:
    print(f"[Ошибка логотипа]: {e}")

title_label = tk.Label(
    header_frame,
    text=APP_TITLE,
    font=("Segoe UI", 18, "bold"),
    bg="#f9f9f9",
    fg="#333"
)
title_label.pack(side=tk.LEFT, anchor="center")

btn_frame = tk.Frame(root, bg="#f9f9f9")
btn_frame.pack(pady=5)

btn_load = ttk.Button(btn_frame, text="Загрузить CXF", command=browse_and_process)
btn_load.grid(row=0, column=0, padx=10)

btn_save = ttk.Button(btn_frame, text="Сохранить результат", command=save_to_file)
btn_save.grid(row=0, column=1, padx=10)

or_label = tk.Label(root, text="или", font=("Segoe UI", 11, "italic"), bg="#f9f9f9", fg="#666666")
or_label.pack(pady=(5, 5))

drop_label = tk.Label(root, text="Перетащи CXF-файл сюда", font=("Segoe UI", 11), bg="#eeeeee", fg="#666666",
                      relief=tk.RIDGE, bd=2, padx=10, pady=10)
drop_label.pack(padx=20, pady=(5, 5), fill=tk.X)

drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind('<<Drop>>', on_drop)

output_frame = tk.Frame(root, bg="#f9f9f9", height=300)
output_frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
output_frame.pack_propagate(False)

footer = tk.Label(root, text=DEVELOPER_INFO, font=("Segoe UI", 9), bg="#f9f9f9", fg="#888")
footer.pack(pady=(0, 10))

root.mainloop()