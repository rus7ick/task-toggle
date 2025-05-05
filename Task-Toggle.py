import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Toplevel
from tkcalendar import DateEntry
from datetime import datetime, date
import pandas as pd
import os
import json

class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Toggle")

        self.tasks = []
        self.current_task = None
        self.start_time = None
        self.filename = f"tasks_{date.today()}.json"

        self.setup_ui()
        self.load_daily_tasks()
        self.update_timer()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="Şu an ne yapıyorsun?", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(frame, font=("Arial", 14), width=40)
        self.entry.pack(side=tk.LEFT)
        self.entry.bind("<Return>", self.start_new_task)

        self.current_label = tk.Label(self.root, text="", font=("Arial", 12), fg="green")
        self.current_label.pack(pady=5)

        columns = ("Görev", "Başlangıç", "Bitiş", "Süre (dk)")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
        self.tree.pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Süreyi Durdur", command=self.stop_task, bg="red", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Excel'e Aktar", command=self.export_to_excel).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Sil", command=self.delete_task).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Düzenle", command=self.edit_task).grid(row=0, column=3, padx=5)

        # Hakkında butonu sağ alt köşe
        about_frame = tk.Frame(self.root)
        about_frame.pack(anchor='se', padx=10, pady=10, side=tk.RIGHT)
        tk.Button(about_frame, text="Hakkında", command=self.show_about).pack()

    def update_timer(self):
        if self.current_task and self.start_time:
            duration = round((datetime.now() - self.start_time).total_seconds() / 60, 2)
            self.current_label.config(text=f"Aktif Görev: {self.current_task} ({duration} dk)")
        else:
            self.current_label.config(text="")
        self.root.after(1000, self.update_timer)

    def start_new_task(self, event):
        task_name = self.entry.get().strip()
        if not task_name:
            messagebox.showwarning("Uyarı", "Lütfen bir görev adı girin.")
            return

        if self.current_task:
            self.stop_task()

        self.current_task = task_name
        self.start_time = datetime.now()
        self.entry.delete(0, tk.END)

    def stop_task(self):
        if not self.current_task or not self.start_time:
            messagebox.showinfo("Bilgi", "Aktif bir görev yok.")
            return

        end_time = datetime.now()
        duration = round((end_time - self.start_time).total_seconds() / 60, 2)

        task = {
            "Görev": self.current_task,
            "Başlangıç": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Bitiş": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Süre (dk)": duration
        }

        self.tasks.append(task)
        self.save_daily_tasks()

        self.tree.insert("", "end", values=(task["Görev"], self.start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"), duration))

        self.current_task = None
        self.start_time = None

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Bilgi", "Lütfen silinecek bir görev seçin.")
            return

        index = self.tree.index(selected[0])
        self.tree.delete(selected[0])
        del self.tasks[index]
        self.save_daily_tasks()

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Bilgi", "Lütfen düzenlenecek bir görev seçin.")
            return

        index = self.tree.index(selected[0])
        current_name = self.tasks[index]["Görev"]
        new_name = simpledialog.askstring("Görev Düzenle", "Yeni görev adını girin:", initialvalue=current_name)
        if new_name:
            self.tasks[index]["Görev"] = new_name
            self.tree.item(selected[0], values=(new_name, self.tasks[index]["Başlangıç"][11:], self.tasks[index]["Bitiş"][11:], self.tasks[index]["Süre (dk)"]))
            self.save_daily_tasks()

    def export_to_excel(self):
        top = Toplevel(self.root)
        top.title("Tarih Seçimi")

        tk.Label(top, text="Başlangıç Tarihi:").grid(row=0, column=0, padx=10, pady=5)
        start_date = DateEntry(top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        start_date.grid(row=0, column=1, padx=10)

        tk.Label(top, text="Bitiş Tarihi:").grid(row=1, column=0, padx=10, pady=5)
        end_date = DateEntry(top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        end_date.grid(row=1, column=1, padx=10)

        def export():
            start = datetime.strptime(start_date.get(), "%Y-%m-%d")
            end = datetime.strptime(end_date.get(), "%Y-%m-%d")

            filtered_tasks = [task for task in self.tasks if start <= datetime.strptime(task["Başlangıç"], "%Y-%m-%d %H:%M:%S") <= end]

            if not filtered_tasks:
                messagebox.showinfo("Bilgi", "Seçilen tarih aralığında görev bulunamadı.")
                return

            df = pd.DataFrame(filtered_tasks)
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Dosyası", "*.xlsx")])
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Başarılı", f"Excel dosyası kaydedildi:\n{file_path}")
            top.destroy()

        tk.Button(top, text="Aktar", command=export).grid(row=2, column=0, columnspan=2, pady=10)

    def save_daily_tasks(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def load_daily_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
            for task in self.tasks:
                self.tree.insert("", "end", values=(
                    task["Görev"],
                    task["Başlangıç"][11:],
                    task["Bitiş"][11:],
                    task["Süre (dk)"]
                ))

    def show_about(self):
        about_text = (
            "Görev Takip Uygulaması Özellikleri:\n\n"
            "- Yeni görev başlatıp süre takibi yapabilirsiniz.\n"
            "- Aktif görevleri durdurduğunuzda kayıt altına alınır.\n"
            "- Kayıtlı görevleri liste halinde görebilir, silebilir veya düzenleyebilirsiniz.\n"
            "- Görevleri seçilen tarih aralığına göre Excel dosyasına aktarabilirsiniz.\n"
            "- Günlük olarak veriler JSON dosyasına kaydedilir.\n\n"
            "Kullanım:\n"
            "- Görev ismini yazın ve Enter tuşuna basın.\n"
            "- 'Süreyi Durdur' butonuyla görevi bitirin.\n"
            "- Kayıtlı görevler üzerinde değişiklik yapabilir ya da silebilirsiniz.\n"
            "- Excel'e aktarmak için tarih seçimi yaparak dışa aktarabilirsiniz.\n\n"
            "Geliştirici: rus7ick \n"
            "GitHub: https://github.com/rus7ick/task-toggle \n"
            "Sürüm: 1.0.0"
        )
        messagebox.showinfo("Hakkında", about_text)

root = tk.Tk()
app = TaskTrackerApp(root)
root.mainloop()
