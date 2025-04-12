import os
import tkinter as tk
from tkinter import filedialog
import json
import os

class SettingsMenu:
    def __init__(self, root, settings_file="settings.json"):
        self.root = root
        self.settings_file = settings_file
        self.settings = self.load_settings()
        
        # Créer le bouton roue crantée pour accéder aux paramètres
        self.settings_button = tk.Button(self.root, text="⚙️ Paramètres", bg="gray", fg="white", command=self.open_settings_window)
        self.settings_button.pack(side=tk.RIGHT, pady=10, padx=10)
        # self.settings_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def load_settings(self):
        """Charger les paramètres à partir du fichier JSON."""
        default_settings = {
            "folders": [],
            "csv_directory": "",
            "csv_filename": "session_log.csv",
            "recursive_read": False
        }
        
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                # S'assurer que tous les paramètres par défaut sont présents
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        return default_settings

    def save_settings(self):
        """Enregistrer les paramètres dans le fichier JSON."""
        with open(self.settings_file, 'w') as file:
            json.dump(self.settings, file)

    def open_settings_window(self):
        """Ouvrir la fenêtre de paramètres."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Paramètres")

        # Sélectionner le dossier cible pour les images
        tk.Label(settings_window, text="Dossier cible des images :").pack(pady=5, padx=10)
        if self.settings.get("current_folder") != None:
            select_folder_button = tk.Button(settings_window, text=self.settings.get("current_folder"), command=self.select_folder)
        else:   
            select_folder_button = tk.Button(settings_window, text="Sélectionner un dossier", command=self.select_folder)
        select_folder_button.pack(pady=5, padx=10)

        # Option pour lire récursivement les fichiers
        recursive_var = tk.BooleanVar(value=self.settings.get("recursive_read", False))
        recursive_check = tk.Checkbutton(settings_window, text="Lire tous les fichiers récursivement", variable=recursive_var)
        recursive_check.pack(pady=5, padx=10)

        # Afficher l'historique des dossiers
        if self.settings["folders"]:
            tk.Label(settings_window, text="Dossiers récents :").pack(pady=5, padx=10)
            for folder in self.settings["folders"]:
                folder_button = tk.Button(settings_window, text=folder, command=lambda f=folder: self.use_folder(f))
                folder_button.pack()

        # Effacer l'historique des dossiers
        clear_history_button = tk.Button(settings_window, text="Effacer l'historique des dossiers", command=self.clear_history)
        clear_history_button.pack(pady=10)

        # Choisir le dossier d'enregistrement du CSV
        tk.Label(settings_window, text="Dossier de sauvegarde du CSV :").pack(pady=5, padx=10)
        if self.settings.get("csv_directory") != None:
            select_csv_folder_button = tk.Button(settings_window, text=self.settings.get("csv_directory"), command=self.select_csv_folder)  
        else: 
            select_csv_folder_button = tk.Button(settings_window, text="Choisir le dossier CSV", command=self.select_csv_folder)  
        
        select_csv_folder_button.pack(pady=5, padx=10)

        # Nom du fichier CSV
        tk.Label(settings_window, text="Nom du fichier CSV :").pack(pady=5, padx=10)
        csv_name_entry = tk.Entry(settings_window)
        csv_name_entry.insert(0, self.settings["csv_filename"])
        csv_name_entry.pack(pady=5, padx=10)

        # Enregistrer les modifications
        save_button = tk.Button(settings_window, text="Enregistrer", command=lambda: self.save_csv_settings(csv_name_entry.get(), recursive_var.get()))
        save_button.pack(pady=10)

    def select_folder(self):
        """Ouvrir un dialogue pour choisir un dossier et l'ajouter à l'historique."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.settings["folders"].append(folder_selected)
            self.save_settings()
            self.use_folder(folder_selected)
            # tk.messagebox.showinfo("Succès", f"Dossier {folder_selected} sélectionné.")

    def use_folder(self, folder):
        """Utiliser un ancien dossier sélectionné."""
        if folder:
            self.settings["current_folder"] = folder
            # tk.messagebox.showinfo("Succès", f"Dossier {folder} utilisé.")
            self.save_settings()
            self.root.update()

    def clear_history(self):
        """Effacer l'historique des dossiers sélectionnés."""
        self.settings["folders"] = []
        self.save_settings()
        self.root.update()
        # tk.messagebox.showinfo("Succès", "Historique des dossiers effacé.")

    def select_csv_folder(self):
        """Choisir le dossier où enregistrer le fichier CSV."""
        csv_folder = filedialog.askdirectory()
        if csv_folder:
            self.settings["csv_directory"] = csv_folder
            self.save_settings()
            self.root.update()

            # tk.messagebox.showinfo("Succès", f"Dossier CSV {csv_folder} sélectionné.")

    def save_csv_settings(self, csv_filename, recursive_read):
        """Enregistrer le nom du fichier CSV et son dossier."""
        self.settings["csv_filename"] = csv_filename
        self.settings["recursive_read"] = recursive_read
        self.save_settings()
        tk.messagebox.showinfo("Succès", "Paramètres sauvegardés.")