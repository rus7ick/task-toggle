import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, date
import pandas as pd
import os
import json
import tkinter.scrolledtext as scrolledtext

class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Toggle")

        self.tasks = []
        self.current_task = None
        self.start_time = None
        self.filename = f"tasks_{date.today().strftime('%Y-%m')}.json"

        self.setup_ui()
        self.load_monthly_tasks()
        self.auto_export_previous_month()
        self.update_timer()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="\u015eu an ne yapıyorsun?", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
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
        tk.Button(btn_frame, text="Program Hakkında", command=self.show_about).grid(row=0, column=4, padx=5)

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
        self.save_monthly_tasks()

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
        self.save_monthly_tasks()

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
            self.save_monthly_tasks()

    def export_to_excel(self):
        month = simpledialog.askstring("Ay Seçimi", "Excel'e aktarılacak ayı girin (YYYY-MM):")
        if not month:
            return
        json_file = f"tasks_{month}.json"
        if not os.path.exists(json_file):
            messagebox.showerror("Hata", f"{json_file} bulunamadı.")
            return

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Dosyası", "*.xlsx")])
        if file_path:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Başarılı", f"Excel dosyası kaydedildi:\n{file_path}")

    def save_monthly_tasks(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def load_monthly_tasks(self):
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

    def auto_export_previous_month(self):
        today = date.today()
        if today.day != 1:
            return

        previous_month = (today.replace(day=1) - pd.Timedelta(days=1)).strftime("%Y-%m")
        json_file = f"tasks_{previous_month}.json"
        excel_file = f"tasks_{previous_month}.xlsx"

        if os.path.exists(json_file) and not os.path.exists(excel_file):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df.to_excel(excel_file, index=False)

    def show_about(self):
        about_text = """
GÖREV TAKİP PROGRAMI ÖZELLİKLERİ

📌 GENEL
- Kullanıcı dostu grafik arayüz (Tkinter)
- Yerel veri kaydı (.json ve .xlsx)
- İnternet bağlantısı gerekmez

📝 GÖREV TAKİBİ
- Görev başlatma ve süre takibi
- Başlangıç, bitiş, toplam süre (dk)
- Canlı süre güncellemesi

🧳 GÖREV YÖNETİMİ
- Silme ve düzenleme
- Aylık listeleme ve tablo görünümü

📁 VERİ SAKLAMA
- Aylık dosyalama: tasks_YYYY-MM.json
- Otomatik veri kaydı

📄 EXCEL AKTARIMI
- Kullanıcıdan ay seçimi (YYYY-MM)
- Excel olarak dışa aktarım

🔄 OTOMATİK EXCEL
- Ayın ilk günü kontrolü
- Önceki aya ait veriler otomatik .xlsx

🌟 KULLANIM ALANLARI
- Freelance iş takibi
- Evden çalışma verimliliği
- Akademik zaman yönetimi
- Günlük üretkenlik analizi

ℹ️ PROGRAM BİLGİSİ
- Sürüm: 1.0.0
- Geliştirici: rus7ick
- Lisans: Açık Kaynak Lisansı
- Son Güncelleme: Mayıs 2025

📬 İLETİŞİM
Herhangi bir geri bildirim, hata bildirimi veya öneri için:
✉️ E-posta: rus7ick@gmail.com

🤝 KATKIDA BULUN
Proje açık kaynaklıdır. Geliştirmelere, önerilere ve katkılara açıktır.
GitHub üzerinden katkıda bulunabilirsiniz:
🔗 https://github.com/rus7ick/task-toggle
        """

        about_window = tk.Toplevel(self.root)
        about_window.title("Hakkında")
        about_window.geometry("540x560")

        text_area = scrolledtext.ScrolledText(about_window, wrap=tk.WORD, font=("Arial", 11))
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, about_text)
        text_area.config(state=tk.DISABLED)

root = tk.Tk()
app = TaskTrackerApp(root)
root.mainloop()
