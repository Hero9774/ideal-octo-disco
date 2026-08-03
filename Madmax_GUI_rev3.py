import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import shutil
import os
import re
import xml.etree.ElementTree as ET

# Definiert die ungefähre Größe eines k32 Plots in Bytes (ca. 101.4 GiB)
K32_SIZE_BYTES = 108886656000

IS_WINDOWS = os.name == 'nt'

# Ungefaehre Plotgroessen in Bytes je K-Groesse (mit etwas Puffer)
PLOT_SIZES = {
    "25": 1_800_000_000,
    "26": 3_600_000_000,
    "27": 7_300_000_000,
    "28": 14_800_000_000,
    "29": 30_000_000_000,
    "30": 61_000_000_000,
    "31": 125_000_000_000,
    "32": 108_886_656_000,
}


def _startup_info():
    """Blendet unter Windows das Konsolenfenster aus.

    Unter Linux/macOS existiert subprocess.STARTUPINFO nicht - dort wird
    None zurueckgegeben, was von Popen korrekt ignoriert wird.
    """
    if not IS_WINDOWS:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si


class MadMaxPlotterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mad Max Plotter GUI")
        self.root.geometry("900x1000")
        
        # Dark Mode Theme (Chia-inspiriert)
        self.setup_dark_theme()

        # Prozess-Steuerung
        self.plot_process = None
        self.stop_plotting_flag = threading.Event()

        # GUI-Variablen
        self.madmax_path_var = tk.StringVar()
        self.chia_path_var = tk.StringVar()
        
        # OS-Erkennung
        self.detect_binaries_on_startup()
        
        # Standardwerte Keys (leer)
        self.farmer_key_var = tk.StringVar(value="")
        self.pool_contract_var = tk.StringVar(value="")
        self.pool_public_key_var = tk.StringVar(value="")
        
        # Plot Einstellungen
        self.plot_type_var = tk.StringVar(value="pool")
        self.plot_count_var = tk.StringVar(value="1")
        self.k_size_var = tk.StringVar(value="32")
        
        # Pfade
        self.temp1_path_var = tk.StringVar()
        self.temp2_path_var = tk.StringVar()
        self.final_path_var = tk.StringVar()
        self.stage_path_var = tk.StringVar()
        
        # Parameter Variablen
        self.threads_var = tk.StringVar(value="4")
        self.buckets_var = tk.StringVar(value="256")
        self.buckets3_var = tk.StringVar(value="256")
        self.rmulti2_var = tk.StringVar(value="1")
        
        # Boolean Flags
        self.wait_for_copy_var = tk.BooleanVar(value=False)
        self.direct_out_var = tk.BooleanVar(value=False)
        self.unique_var = tk.BooleanVar(value=False)
        self.tmptoggle_var = tk.BooleanVar(value=False)
        self.auto_check_var = tk.BooleanVar(value=False)
        
        # Status-Anzeigen
        self.max_plots_var = tk.StringVar(value="Mögliche Plots: 0")
        self.remaining_plots_var = tk.StringVar(value="Verbleibend: 0")

        # Liste aller Variablen zum Speichern
        self.config_vars = {
            'madmax_path': self.madmax_path_var,
            'chia_path': self.chia_path_var,
            'farmer_key': self.farmer_key_var,
            'pool_contract_key': self.pool_contract_var,
            'pool_public_key': self.pool_public_key_var,
            'plot_type': self.plot_type_var,
            'k_size': self.k_size_var,
            'temp1_path': self.temp1_path_var,
            'temp2_path': self.temp2_path_var,
            'final_path': self.final_path_var,
            'stage_path': self.stage_path_var,
            'plot_count': self.plot_count_var,
            'threads': self.threads_var,
            'buckets': self.buckets_var,
            'buckets3': self.buckets3_var,
            'rmulti2': self.rmulti2_var,
            'wait_for_copy': self.wait_for_copy_var,
            'direct_out': self.direct_out_var,
            'unique': self.unique_var,
            'tmptoggle': self.tmptoggle_var,
            'auto_check': self.auto_check_var,
        }

        self.setup_gui()
        self.initialize_combobox_defaults()
        self.toggle_plot_type()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def detect_binaries_on_startup(self):
        madmax_bin = "chia_plot.exe" if os.name == 'nt' else "chia_plot"
        found_madmax = shutil.which(madmax_bin)
        if found_madmax:
            self.madmax_path_var.set(found_madmax)

        chia_bin = "chia.exe" if os.name == 'nt' else "chia"
        found_chia = shutil.which(chia_bin)
        if found_chia:
            self.chia_path_var.set(found_chia)
        elif IS_WINDOWS:
            # Windows: Standard-Installationspfad der Chia-GUI probieren
            appdata_chia = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Chia\resources\app\daemon\chia.exe")
            if os.path.exists(appdata_chia):
                self.chia_path_var.set(appdata_chia)
        else:
            # Linux/macOS: uebliche Installationsorte probieren
            for candidate in (
                os.path.expanduser("~/.local/bin/chia"),
                "/usr/local/bin/chia",
                "/usr/bin/chia",
                os.path.expanduser("~/chia-blockchain/venv/bin/chia"),
            ):
                if os.path.exists(candidate):
                    self.chia_path_var.set(candidate)
                    break

    def initialize_combobox_defaults(self):
        """Setzt die Standardwerte für Comboboxen nach GUI-Initialisierung"""
        self.k_size_combo.current(6)  # Index 6 = "32"
        self.buckets_combo.current(2)  # Index 2 = "256"

    def setup_dark_theme(self):
        """Konfiguriert Dark Mode Theme wie Chia GUI"""
        style = ttk.Style()
        
        # Chia Dark Mode Farben
        bg_dark = "#1a1a1a"      # Dunkelgrau - Hintergrund
        bg_lighter = "#2d2d2d"   # Helleres Grau - Frames
        fg_light = "#e0e0e0"     # Helles Grau - Text
        accent_green = "#86EF28"  # Grün - Akzente (Chia Farbe)
        accent_hover = "#63a514"  # Dunkleres Grün
        
        # Root Hintergrund
        self.root.configure(bg=bg_dark)
        
        # ttk Theme konfigurieren
        style.theme_use('clam')
        
        # TFrame
        style.configure('TFrame', background=bg_dark)
        style.configure('TLabelframe', background=bg_dark, foreground=fg_light, font=('Arial', 11, 'bold'))
        style.configure('TLabelframe.Label', background=bg_dark, foreground=accent_green, font=('Arial', 11, 'bold'))
        
        # TLabel
        style.configure('TLabel', background=bg_dark, foreground=fg_light, font=('Arial', 11))
        
        # TEntry
        style.configure('TEntry', 
                       fieldbackground=bg_lighter, 
                       foreground=fg_light,
                       borderwidth=1,
                       font=('Arial', 11))
        style.map('TEntry', 
                 fieldbackground=[('focus', bg_lighter)])
        
        # TButton
        style.configure('TButton',
                       background=bg_lighter,
                       foreground=accent_green,
                       borderwidth=1,
                       focuscolor='none',
                       padding=7,
                       font=('Arial', 11))
        style.map('TButton',
                 background=[('active', accent_hover)],
                 foreground=[('active', '#ffffff')])
        
        # Start Button (grün)
        style.configure('Start.TButton',
                       background=accent_green,
                       foreground='#000000',
                       font=('Arial', 12, 'bold'),
                       padding=10)
        style.map('Start.TButton',
                 background=[('active', accent_hover)])
        
        # TCheckbutton
        style.configure('TCheckbutton', background=bg_dark, foreground=fg_light, font=('Arial', 11))
        style.map('TCheckbutton',
                 background=[('active', bg_dark)])
        
        # TRadiobutton
        style.configure('TRadiobutton', background=bg_dark, foreground=fg_light, font=('Arial', 11))
        style.map('TRadiobutton',
                 background=[('active', bg_dark)])
        
        # TCombobox
        style.configure('TCombobox',
                       fieldbackground=bg_dark,
                       foreground=fg_light,
                       borderwidth=1,
                       font=('Arial', 11))
        style.map('TCombobox',
                 fieldbackground=[('readonly', bg_dark)],
                 foreground=[('readonly', fg_light)])
        
        # Notebook und Tabs
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=bg_lighter, foreground=fg_light, 
                       padding=[25, 15], font=('Arial', 12, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', bg_lighter)],
                 foreground=[('selected', accent_green)],
                 padding=[('selected', [25, 15])])
        
        # Progressbar
        style.configure('TProgressbar', background=accent_green, troughcolor=bg_lighter, borderwidth=0)

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(pady=5, padx=5, fill="x")

        tab_plots_keys = ttk.Frame(self.notebook, padding="10")
        tab_params = ttk.Frame(self.notebook, padding="10")
        tab_paths_check = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(tab_plots_keys, text="🔑 Plots & Keys")
        self.notebook.add(tab_params, text="⚙️ Parameter")
        self.notebook.add(tab_paths_check, text="📁 Pfade & Tools")

        # --- Tab 1: Plots & Keys ---
        config_frame = ttk.LabelFrame(tab_plots_keys, text="Plot-Einstellungen", padding="10")
        config_frame.pack(fill="x", pady=5)
        config_frame.grid_columnconfigure(1, weight=1)

        # MadMax Pfad
        ttk.Label(config_frame, text="MadMax Pfad:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.madmax_path_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(config_frame, text="Durchsuchen", command=self.select_madmax_exe).grid(row=0, column=2, padx=5, pady=5)

        # K-Größe
        ttk.Label(config_frame, text="K-Größe (-k):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.k_size_combo = ttk.Combobox(config_frame, textvariable=self.k_size_var, values=["25", "26", "27", "28", "29", "30", "31", "32"], state="readonly", width=10)
        self.k_size_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Plot Typ (Pool/Solo)
        ttk.Label(config_frame, text="Plot Typ:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        plot_type_frame = ttk.Frame(config_frame)
        plot_type_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(plot_type_frame, text="Pool Plots (NFT)", variable=self.plot_type_var, value="pool", command=self.toggle_plot_type).pack(side="left", padx=5)
        ttk.Radiobutton(plot_type_frame, text="Solo Plots (OG)", variable=self.plot_type_var, value="solo", command=self.toggle_plot_type).pack(side="left", padx=5)

        # Keys
        ttk.Label(config_frame, text="Farmer Key (-f):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.farmer_key_var).grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(config_frame, text="Pool Contract (-c):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.pool_contract_entry = ttk.Entry(config_frame, textvariable=self.pool_contract_var)
        self.pool_contract_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Label(config_frame, text="Pool Public Key (-p):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.pool_public_key_entry = ttk.Entry(config_frame, textvariable=self.pool_public_key_var)
        self.pool_public_key_entry.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Auto-Key Detection Button
        auto_key_button = ttk.Button(config_frame, text="🔑 Keys automatisch erkennen", command=self.auto_detect_keys)
        auto_key_button.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        
        # Anzahl
        count_frame = ttk.Frame(tab_plots_keys, padding="5")
        count_frame.pack(fill="x", pady=5)
        count_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(count_frame, text="Anzahl Plots:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(count_frame, textvariable=self.plot_count_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(count_frame, textvariable=self.max_plots_var).grid(row=0, column=2, sticky="w", padx=20, pady=5)
        ttk.Label(count_frame, textvariable=self.remaining_plots_var).grid(row=0, column=3, sticky="w", padx=20, pady=5)

        # --- Tab 2: Parameter ---
        params_frame = ttk.LabelFrame(tab_params, text="Performance-Parameter", padding="10")
        params_frame.pack(fill="x", pady=5)
        params_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(params_frame, text="Threads (-r):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.threads_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(params_frame, text="Buckets (-u):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.buckets_combo = ttk.Combobox(params_frame, textvariable=self.buckets_var, values=["64", "128", "256", "512", "1024"], state="readonly", width=10)
        self.buckets_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(params_frame, text="Buckets Phase 3+4 (-v):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.buckets3_var, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(params_frame, text="P2 Thread Multiplier (-K):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.rmulti2_var, width=10).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Flags
        flags_frame = ttk.LabelFrame(tab_params, text="Optionen", padding="10")
        flags_frame.pack(fill="x", pady=5)
        ttk.Checkbutton(flags_frame, text="Wait for Copy (-w)", variable=self.wait_for_copy_var).pack(anchor="w", padx=5, pady=5)
        ttk.Checkbutton(flags_frame, text="Direct Output (-D)", variable=self.direct_out_var).pack(anchor="w", padx=5, pady=5)
        ttk.Checkbutton(flags_frame, text="Unique Plot (-Z)", variable=self.unique_var).pack(anchor="w", padx=5, pady=5)
        ttk.Checkbutton(flags_frame, text="Tmp Toggle (-G)", variable=self.tmptoggle_var).pack(anchor="w", padx=5, pady=5)

        # --- Tab 3: Pfade & Tools ---
        paths_frame = ttk.LabelFrame(tab_paths_check, text="Pfade", padding="10")
        paths_frame.pack(fill="x", pady=5)
        paths_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(paths_frame, text="Temp 1 (-t):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(paths_frame, textvariable=self.temp1_path_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(paths_frame, text="Durchsuchen", command=lambda: self.select_folder(self.temp1_path_var)).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(paths_frame, text="Temp 2 (-2):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(paths_frame, textvariable=self.temp2_path_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(paths_frame, text="Durchsuchen", command=lambda: self.select_folder(self.temp2_path_var)).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(paths_frame, text="Final Dir (-d):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(paths_frame, textvariable=self.final_path_var).grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(paths_frame, text="Durchsuchen", command=lambda: self.select_folder(self.final_path_var, update_max_plots=True)).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(paths_frame, text="Stage Dir (-s):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(paths_frame, textvariable=self.stage_path_var).grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(paths_frame, text="Durchsuchen", command=lambda: self.select_folder(self.stage_path_var)).grid(row=3, column=2, padx=5, pady=5)
        
        check_frame = ttk.LabelFrame(tab_paths_check, text="Tools (Plot-Check & Config)", padding="10")
        check_frame.pack(fill="x", pady=5)
        check_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(check_frame, text="Chia Pfad:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(check_frame, textvariable=self.chia_path_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(check_frame, text="Durchsuchen", command=self.select_chia_exe).grid(row=0, column=2, padx=5, pady=5)

        ttk.Checkbutton(check_frame, text="✅ Erstellte Plots automatisch prüfen", variable=self.auto_check_var).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        self.check_file_button = ttk.Button(check_frame, text="Einzelne Plot-Datei prüfen...", command=self.check_single_plot)
        self.check_file_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.check_dir_button = ttk.Button(check_frame, text="Plot-Verzeichnis prüfen...", command=self.check_plot_directory)
        self.check_dir_button.grid(row=2, column=2, sticky="ew", padx=5, pady=5)
        
        xml_frame = ttk.Frame(check_frame, padding="5")
        xml_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
        xml_frame.grid_columnconfigure(0, weight=1)
        xml_frame.grid_columnconfigure(1, weight=1)
        ttk.Button(xml_frame, text="📂 Config Laden", command=self.select_and_load).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(xml_frame, text="💾 Config Speichern", command=self.select_and_save).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # --- Controls & Output ---
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.pack(fill="x", pady=5)
        self.start_button = ttk.Button(control_frame, text="▶️ Plotten Starten", command=self.start_plotting, style='Start.TButton')
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stopp", command=self.stop_plotting, style='Start.TButton', state="disabled")
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)

        progress_frame = ttk.Frame(main_frame, padding="5")
        progress_frame.pack(fill="x", pady=5)
        ttk.Label(progress_frame, text="Gesamtfortschritt:").pack(side="left", padx=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", expand=True, padx=5)

        output_frame = ttk.LabelFrame(main_frame, text="MadMax-Ausgabe", padding="10")
        output_frame.pack(fill="both", expand=True, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=12, state="disabled")
        self.output_text.pack(fill="both", expand=True)

    # --- Funktionen ---

    def select_and_save(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xml", initialfile="madmax_config.xml", filetypes=[("XML", "*.xml")])
        if filename: self.save_settings_to_xml(filename)

    def save_settings_to_xml(self, filename):
        root = ET.Element("MadMaxConfig")
        for name, var in self.config_vars.items():
            setting = ET.SubElement(root, "Setting", name=name)
            setting.text = str(var.get())
        try:
            ET.indent(ET.ElementTree(root), space="  ")
            ET.ElementTree(root).write(filename, encoding='utf-8', xml_declaration=True)
            self.log_message(f"✅ Gespeichert: {filename}")
        except Exception as e: messagebox.showerror("Fehler", str(e))

    def select_and_load(self):
        filename = filedialog.askopenfilename(defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if filename: self.load_settings_from_xml(filename)

    def load_settings_from_xml(self, filename):
        try:
            tree = ET.parse(filename)
            for setting in tree.getroot().findall('Setting'):
                name = setting.get('name')
                if name and name in self.config_vars:
                    self.config_vars[name].set(setting.text if setting.text is not None else "")
            self.toggle_plot_type()
            self.update_max_plots_display(self.final_path_var.get())
            self.log_message(f"📥 Geladen: {filename}")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def toggle_plot_type(self):
        if self.plot_type_var.get() == "pool":
            self.pool_contract_entry.config(state="normal")
            self.pool_public_key_entry.config(state="disabled")
        else: 
            self.pool_contract_entry.config(state="disabled")
            self.pool_public_key_entry.config(state="normal")

    def select_madmax_exe(self):
        ft = [("Exe", "*.exe"), ("All", "*.*")] if os.name == 'nt' else [("Bin", "*"), ("All", "*.*")]
        p = filedialog.askopenfilename(title="MadMax auswählen", filetypes=ft)
        if p: self.madmax_path_var.set(p)

    def select_chia_exe(self):
        ft = [("Exe", "*.exe"), ("All", "*.*")] if os.name == 'nt' else [("Bin", "*"), ("All", "*.*")]
        default_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Chia") if IS_WINDOWS else os.path.expanduser("~")
        p = filedialog.askopenfilename(title="Chia auswählen", filetypes=ft, initialdir=default_dir if os.path.exists(default_dir) else "")
        if p: self.chia_path_var.set(p)

    def auto_detect_keys(self):
        """Versucht, Keys automatisch von Chia zu erkennen"""
        chia_path = self.chia_path_var.get().strip()
        if not chia_path:
            messagebox.showerror("Fehler", "Chia-Pfad nicht gesetzt. Bitte zuerst den Chia-Pfad angeben.")
            return
        
        if not os.path.exists(chia_path):
            messagebox.showerror("Fehler", "Chia-Pfad existiert nicht.")
            return
        
        threading.Thread(target=self._run_key_detection, args=(chia_path,), daemon=True).start()

    def _run_key_detection(self, chia_path):
        """Führt Chia Key Show aus und extrahiert die Keys"""
        try:
            self.log_message("🔍 Erkenne Chia Keys...")
            si = _startup_info()
            
            # Führe "chia keys show" aus
            p = subprocess.Popen([chia_path, "keys", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, encoding='utf-8', errors='replace', startupinfo=si)
            stdout, stderr = p.communicate()
            
            if p.returncode != 0:
                self.log_message(f"❌ Fehler beim Key-Abrufen: {stderr}")
                return
            
            # Parse Ausgabe
            farmer_key = None
            pool_public_key = None
            
            for line in stdout.split('\n'):
                line = line.strip()
                if 'Farmer public key' in line:
                    farmer_key = line.split(':')[1].strip() if ':' in line else None
                elif 'Pool public key' in line:
                    pool_public_key = line.split(':')[1].strip() if ':' in line else None
            
            # Update GUI mit erkannten Keys aus "keys show"
            if farmer_key:
                self.farmer_key_var.set(farmer_key)
                self.log_message(f"✅ Farmer Key erkannt: {farmer_key[:16]}...")
            if pool_public_key:
                self.pool_public_key_var.set(pool_public_key)
                self.log_message(f"✅ Pool Public Key erkannt: {pool_public_key[:16]}...")
            
            # Jetzt versuche Pool Contract Address mit "chia plotnft show" zu ermitteln
            self.log_message("🔍 Erkenne Pool Contract Address...")
            p2 = subprocess.Popen([chia_path, "plotnft", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                text=True, encoding='utf-8', errors='replace', startupinfo=si)
            stdout2, stderr2 = p2.communicate()
            
            if p2.returncode == 0:
                pool_contract = None
                for line in stdout2.split('\n'):
                    line = line.strip()
                    if 'Pool contract address' in line:
                        pool_contract = line.split(':')[1].strip() if ':' in line else None
                        break
                
                if pool_contract:
                    self.pool_contract_var.set(pool_contract)
                    self.log_message(f"✅ Pool Contract Address erkannt: {pool_contract[:20]}...")
                else:
                    self.log_message("⚠️ Keine Pool Contract Address gefunden (möglicherweise OG-Plot).")
            else:
                self.log_message("⚠️ Pool Contract Address konnte nicht ermittelt werden.")
            
            if not (farmer_key or pool_public_key):
                self.log_message("⚠️ Keine Keys gefunden. Chia möglicherweise nicht initialisiert.")
        except Exception as e:
            self.log_message(f"❌ Exception bei Key-Erkennung: {e}")

    def select_folder(self, entry_var, update_max_plots=False):
        p = filedialog.askdirectory(title="Ordner auswählen")
        if p:
            entry_var.set(p)
            if update_max_plots: self.update_max_plots_display(p)

    def update_max_plots_display(self, path):
        if not path: return
        try:
            usage = shutil.disk_usage(path)
            size = PLOT_SIZES.get(self.k_size_var.get(), K32_SIZE_BYTES)
            k = self.k_size_var.get()
            self.max_plots_var.set(f"Mögliche Plots (k{k}): {usage.free // size}")
        except Exception:
            pass

    def on_closing(self):
        if self.plot_process and self.plot_process.poll() is None:
            if not messagebox.askyesno("Warnung", "Plotten läuft. Beenden?"): return
            self.stop_plotting()
        self.root.destroy()
    
    def log_message(self, message):
        self.root.after(0, self._update_log_gui, message)

    def _update_log_gui(self, message):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

    def update_progress(self, c, t): self.root.after(0, lambda: self.progress_bar.configure(value=(c/t)*100 if t>0 else 0))
    def update_remaining(self, r): self.root.after(0, lambda: self.remaining_plots_var.set(f"Verbleibend: {r}"))
    
    def set_controls_state(self, running=True):
        self.root.after(0, lambda: self.start_button.config(state="disabled" if running else "normal"))
        self.root.after(0, lambda: self.stop_button.config(state="normal" if running else "disabled"))

    # --- Plot Start Logik ---
    def start_plotting(self):
        madmax_exe = self.madmax_path_var.get().strip()
        if not madmax_exe: 
            messagebox.showerror("Fehler", "MadMax Pfad fehlt.")
            return
            
        # Keys bereinigen
        farmer_key = self.farmer_key_var.get().strip()
        farmer_key = farmer_key.replace(" ", "").replace('"', "").replace("'", "")
        
        # Validierung: Farmer Key sollte 96 Hex-Zeichen sein
        if not re.fullmatch(r'[0-9a-fA-F]{96}', farmer_key):
            messagebox.showerror("Fehler", f"Farmer Key ungültig (erwartet 96 Hex-Zeichen, erhalten {len(farmer_key)})")
            return
        
        self.log_message(f"✅ Farmer Key validiert: {farmer_key[:16]}...{farmer_key[-16:]}")
        
        temp1 = self.temp1_path_var.get().strip()
        temp2 = self.temp2_path_var.get().strip()
        final_dir = self.final_path_var.get().strip()
        stage_dir = self.stage_path_var.get().strip()
        
        # Validierung: Mindestens temp1 und final_dir müssen gesetzt sein
        if not temp1:
            messagebox.showerror("Fehler", "Temp 1 Pfad fehlt - erforderlich!")
            return
        if not final_dir:
            messagebox.showerror("Fehler", "Final Dir Pfad fehlt.")
            return
        
        plot_count = 1
        try: plot_count = int(self.plot_count_var.get())
        except: pass

        k_size = self.k_size_var.get()
        plot_type = self.plot_type_var.get()
        pool_key = ""
        key_flag = ""
        
        if plot_type == "pool":
            pool_key = self.pool_contract_var.get().strip()
            key_flag = "-c"
            if len(pool_key) < 60:
                messagebox.showerror("Fehler", "Pool Contract Address scheint zu kurz.")
                return
        else:
            pool_key = self.pool_public_key_var.get().strip()
            key_flag = "-p"
            if len(pool_key) != 96:
                messagebox.showerror("Fehler", "Pool Public Key Länge falsch.")
                return
        
        self.set_controls_state(True)
        self.stop_plotting_flag.clear()
        self.update_remaining(plot_count)
        self.update_progress(0, plot_count)

        threading.Thread(target=self.plotting_thread_worker, args=(
            madmax_exe, farmer_key, key_flag, pool_key, temp1, temp2, final_dir, stage_dir, 
            plot_count, k_size, self.threads_var.get().strip(), self.buckets_var.get().strip(),
            self.buckets3_var.get().strip(), self.rmulti2_var.get().strip(),
            self.wait_for_copy_var.get(), self.direct_out_var.get(), self.unique_var.get(),
            self.tmptoggle_var.get(), self.auto_check_var.get(), self.chia_path_var.get().strip()
        ), daemon=True).start()

    def stop_plotting(self):
        """Signalisiert dem Plot-Thread, dass er stoppen soll"""
        self.log_message("🛑 Stoppsignal empfangen...")
        self.stop_plotting_flag.set()
        
        if self.plot_process and self.plot_process.poll() is None:
            try:
                self.plot_process.terminate()
                self.log_message("Unterprozess beendet.")
            except Exception as e:
                self.log_message(f"Fehler beim Beenden des Prozesses: {e}")
                
        if self.plot_process is None or self.plot_process.poll() is not None:
             self.set_controls_state(False)

    def plotting_thread_worker(self, exe, f_key, key_flag, p_key, t1, t2, final, stage, total, k_size, 
                               threads, buckets, buckets3, rmulti2, wait_copy, direct_out, unique, 
                               tmptoggle, auto_check, chia):
        self.log_message(f"DEBUG: MadMax exe={exe}, f_key={repr(f_key[:16])}..., key_flag={key_flag}")
        self.log_message(f"DEBUG paths: t1={repr(t1)}, t2={repr(t2)}, final={repr(final)}, stage={repr(stage)}")
        
        # Hilfsfunktion zum Normalisieren von Pfaden mit abschließendem Separator
        def normalize_path(path):
            """Normalisiert Pfade und haengt den Trenner des jeweiligen
            Systems an - MadMax erwartet einen abschliessenden Separator."""
            if path:
                path = os.path.normpath(path.strip())
                if not path.endswith(os.sep):
                    path += os.sep
            return path
        
        # Normalisiere alle Pfade
        t1 = normalize_path(t1)
        t2 = normalize_path(t2)
        final = normalize_path(final)
        stage = normalize_path(stage)
        
        plots_done = 0
        try:
            for i in range(total):
                if self.stop_plotting_flag.is_set(): break
                self.log_message(f"--- Start Plot {i+1}/{total} [MadMax] ---")
                self.update_remaining(total - i)

                # MadMax Befehl zusammenstellen
                cmd = [exe]
                
                # Obligatorische Parameter
                cmd.extend(["-k", k_size])
                cmd.extend(["-n", "1"])  # Immer 1 Plot pro Aufruf
                cmd.extend(["-f", f_key])
                cmd.extend([key_flag, p_key])
                cmd.extend(["-t", t1])
                cmd.extend(["-d", final])
                
                # Optionale Temp 2
                if t2:
                    cmd.extend(["-2", t2])
                
                # Optionales Stage Dir
                if stage:
                    cmd.extend(["-s", stage])
                
                # Performance-Parameter
                if threads and threads.isdigit() and int(threads) > 0:
                    cmd.extend(["-r", threads])
                
                if buckets and buckets.isdigit() and int(buckets) > 0:
                    cmd.extend(["-u", buckets])
                
                if buckets3 and buckets3.isdigit() and int(buckets3) > 0:
                    cmd.extend(["-v", buckets3])
                
                if rmulti2 and rmulti2.isdigit() and int(rmulti2) > 0:
                    cmd.extend(["-K", rmulti2])
                
                # Boolean Flags
                if wait_copy:
                    cmd.append("-w")
                if direct_out:
                    cmd.append("-D")
                if unique:
                    cmd.append("-Z")
                if tmptoggle:
                    cmd.append("-G")
                
                # DEBUG AUSGABE
                self.log_message(f"DEBUG CMD: {cmd}")

                created_file = None
                si = _startup_info()
                
                try:
                    self.plot_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=si)
                    
                    # Prozess-Ausgabe lesen
                    for line in iter(self.plot_process.stdout.readline, ''):
                        if not line: break
                        
                        if self.stop_plotting_flag.is_set(): 
                            self.plot_process.terminate()
                            break

                        l = line.strip()
                        self.log_message(l)
                        
                        # Versuch, den Namen der Plot-Datei zu erfassen
                        if ".plot" in l:
                            m = re.search(r'([a-zA-Z]:[\\/][^"\n\r]+\.plot|/[^"\n\r]+\.plot)', l)
                            if m: created_file = m.group(1)
                    
                    # Warten auf den Prozess
                    rc = self.plot_process.wait()
                    self.plot_process = None
                    
                    if rc == 0:
                        plots_done += 1
                        self.update_progress(plots_done, total)
                        self.log_message("--- Plot fertig ---")
                        if auto_check and chia and created_file and os.path.exists(created_file):
                            self.run_check(chia, created_file)
                    elif self.stop_plotting_flag.is_set():
                         self.log_message("--- Plot abgebrochen (manuell gestoppt) ---")
                    else:
                        self.log_message(f"!!! FEHLER Code {rc} !!!")
                        break
                except Exception as e:
                    self.log_message(f"Exception beim Plotten: {e}")
                    break
        except Exception as e: self.log_message(f"Globaler Fehler im Plot-Worker: {e}")
        
        self.set_controls_state(False)
        self.log_message("--- Plot-Worker beendet ---")

    def run_check(self, chia, f):
        self.log_message(f"Prüfe: {f}")
        si = _startup_info()
        try:
            p = subprocess.Popen([chia, "plots", "check", "-n", "30", "-f", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=si)
            for l in iter(p.stdout.readline, ''): 
                if l: self.log_message("[CHK] " + l.strip())
            p.wait()
        except: pass

    def check_single_plot(self):
        f = filedialog.askopenfilename(filetypes=[("Plot", "*.plot")])
        if f and self.chia_path_var.get(): threading.Thread(target=self.run_check, args=(self.chia_path_var.get(), f), daemon=True).start()

    def check_plot_directory(self):
        d = filedialog.askdirectory()
        if d and self.chia_path_var.get():
             threading.Thread(target=lambda: self.run_check_dir(self.chia_path_var.get(), d), daemon=True).start()

    def run_check_dir(self, chia, d):
        si = _startup_info()
        p = subprocess.Popen([chia, "plots", "check", "-d", d], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=si)
        for l in iter(p.stdout.readline, ''): self.log_message("[CHK] " + l.strip())

if __name__ == "__main__":
    root = tk.Tk()
    app = MadMaxPlotterApp(root)
    root.mainloop()
