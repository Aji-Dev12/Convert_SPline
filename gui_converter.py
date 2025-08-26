import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import ezdxf
import os
import threading

class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("DXF Curve Convert by AJI-SWG_Dev v4.0")
        self.geometry("650x550")
        self.minsize(600, 450)

        self.input_path = tk.StringVar()
        self.output_folder = tk.StringVar()

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(main_frame, text="1. Pilih File Input", padding="10")
        input_frame.pack(fill=tk.X, expand=True)
        input_frame.drop_target_register(DND_FILES)
        input_frame.dnd_bind('<<Drop>>', self.on_drop)

        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_path, state="readonly")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.browse_input_btn = ttk.Button(input_frame, text="Pilih File...", command=self.browse_input_file)
        self.browse_input_btn.pack(side=tk.LEFT)

        # --- Output Frame ---
        output_frame = ttk.LabelFrame(main_frame, text="2. Pilih Folder Output", padding="10")
        output_frame.pack(fill=tk.X, expand=True, pady=10)

        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_folder, state="readonly")
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.browse_output_btn = ttk.Button(output_frame, text="Pilih Folder...", command=self.browse_output_folder)
        self.browse_output_btn.pack(side=tk.LEFT)

        # --- Tolerance Frame ---
        tolerance_frame = ttk.LabelFrame(main_frame, text="3. Atur Toleransi Spline", padding="10")
        tolerance_frame.pack(fill=tk.X, expand=True)
        self.tolerance_var = tk.StringVar(value="0.01")
        self.tolerance_entry = ttk.Entry(tolerance_frame, textvariable=self.tolerance_var, width=10)
        self.tolerance_entry.pack(side=tk.LEFT)

        # --- Action Frame ---
        action_frame = ttk.Frame(main_frame, padding="10 0")
        action_frame.pack(fill=tk.X, expand=True)
        self.convert_btn = ttk.Button(action_frame, text="Mulai Konversi", command=self.start_conversion_thread)
        self.convert_btn.pack(pady=10, fill=tk.X, expand=True)

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(main_frame, text="Log Proses", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text['yscrollcommand'] = log_scrollbar.set

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.update_idletasks()

    def on_drop(self, event):
        # event.data is a string of one or more file paths, often wrapped in braces
        path = event.data.strip('{}')
        if path.lower().endswith('.dxf'):
            self.input_path.set(path)
            self.log(f"File dipilih via Drag & Drop: {os.path.basename(path)}")
        else:
            self.log("Error: File yang di-drop harus berekstensi .dxf")

    def browse_input_file(self):
        path = filedialog.askopenfilename(filetypes=[("DXF Files", "*.dxf"), ("All files", "*.*")] )
        if path:
            self.input_path.set(path)
            self.log(f"File input dipilih: {os.path.basename(path)}")

    def browse_output_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder.set(path)
            self.log(f"Folder output dipilih: {path}")

    def start_conversion_thread(self):
        input_dxf = self.input_path.get()
        output_dir = self.output_folder.get()
        try:
            tolerance = float(self.tolerance_var.get())
            if tolerance <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error Input", "Nilai toleransi tidak valid. Harap masukkan angka positif.")
            return

        if not input_dxf or not output_dir:
            messagebox.showerror("Error Input", "Harap pilih file input dan folder output terlebih dahulu.")
            return

        self.convert_btn.config(state="disabled", text="Sedang Memproses...")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        thread = threading.Thread(target=self.run_conversion, args=(input_dxf, output_dir, tolerance))
        thread.start()

    def conversion_finished(self, success, message):
        self.log(message)
        if success:
            messagebox.showinfo("Selesai", "Konversi berhasil diselesaikan!")
        else:
            messagebox.showerror("Error", f"Terjadi error saat konversi.\nLihat log untuk detail.")
        self.convert_btn.config(state="normal", text="Mulai Konversi")

    def run_conversion(self, filename, output_dir, tolerance):
        try:
            self.log(f"Membaca file: {os.path.basename(filename)}...")
            doc = ezdxf.readfile(filename)
            msp = doc.modelspace()
        except Exception as e:
            self.conversion_finished(False, f"Error fatal saat membaca file: {e}")
            return

        entities_to_convert = msp.query("SPLINE POLYLINE LWPOLYLINE")
        self.log(f"Ditemukan {len(entities_to_convert)} entitas yang akan diproses.")
        if not entities_to_convert:
            self.conversion_finished(True, "Tidak ada entitas yang perlu diubah.")
            return

        entities_processed_count = 0
        for entity in list(entities_to_convert):
            if not entity.is_alive:
                continue
            try:
                if entity.dxftype() == 'SPLINE':
                    points = list(entity.flattening(distance=tolerance))
                    if len(points) > 1:
                        self.log(f"  - Mengubah SPLINE (handle: {entity.dxf.handle}) menjadi {len(points) - 1} segmen LINE.")
                        safe_attribs = {
                            'layer': entity.dxf.get('layer', '0'),
                            'color': entity.dxf.get('color', 256),
                            'linetype': entity.dxf.get('linetype', 'BYLAYER'),
                            'lineweight': entity.dxf.get('lineweight', -1),
                        }
                        for i in range(len(points) - 1):
                            msp.add_line(start=points[i], end=points[i+1], dxfattribs=safe_attribs)
                        msp.delete_entity(entity)
                        entities_processed_count += 1
                elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                    self.log(f"  - Meledakkan (Exploding) {entity.dxftype()} (handle: {entity.dxf.handle}).")
                    entity.explode()
                    entities_processed_count += 1
            except Exception as e:
                self.log(f"  - GAGAL memproses entitas {entity.dxftype()} (handle: {entity.dxf.handle}). Error: {e}")

        if entities_processed_count > 0:
            base, ext = os.path.splitext(os.path.basename(filename))
            output_filename = os.path.join(output_dir, f"{base}_convert_byAji_SWG-Dev.dxf")
            self.log(f"\nTotal {entities_processed_count} entitas asli telah diproses.")
            self.log(f"Menyimpan hasil ke file baru: {output_filename}")
            try:
                doc.saveas(output_filename)
                self.conversion_finished(True, "\nSELESAI! File baru berhasil dibuat.")
            except Exception as e:
                self.conversion_finished(False, f"Gagal menyimpan file. Error: {e}")
        else:
            self.conversion_finished(True, "\nTidak ada entitas yang berhasil diubah.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
