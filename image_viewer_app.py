import os
import random
import time
import tkinter as tk
from PIL import Image, ImageTk, ImageOps
from dotenv import load_dotenv
from tkinter import ttk
from script.logger import log_to_csv
from script.View.settings_menu import *
from script.View.statistics_window import StatisticsButton
# Charger le fichier .env qui est à côté de ce fichier
load_dotenv()


# Accéder aux variables d'environnement
folder_path = os.getenv('folder_path')

class ImageViewerApp:
    def __init__(self, root, folder_path, session_duration, mode="normal", image_time=None, settings_menu=None):
        self.root = root
        self.folder_path = folder_path
        self.session_duration = session_duration
        self.mode = mode
        self.image_time = image_time  # Durée par image pour le mode normal
        self.image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
        
        random.shuffle(self.image_files)
        self.current_index = random.randint(0, len(self.image_files) - 1)
        self.done_images_number = 0
        self.start_time = time.time()
        self.end_time = self.start_time + session_duration
        self.paused = False
        self.paused_time = time.time()
        self.time_spent_on_image = 0
        self.timer_active = True
        self.session_history = []  # Historique de la session
        self.image_start_time = time.time()
        self.mirror_horizontal = False
        self.mirror_vertical = False

        self.start_size = (1000, 800)
        self.settings_menu = settings_menu;
        # Calcul du temps par image en mode "classe" (progressif)
        if mode == "classe":
            self.class_mode_times = self.calculate_class_mode_times(session_duration)
            self.current_image_time = self.class_mode_times[0]
        else:
            self.current_image_time = image_time


        # self.initial_remaining_total_time = session_duration
        # self.initial_remaining_image_time = current_image_time

        # Taille minimale de la fenêtre
        self.root.minsize(1000, 800)

        # Initialiser la fenêtre Tkinter
        self.root.title("Visionneuse d'images")
        self.root.config(bg="black")

        # Barre noire en haut (toujours visible)
        self.top_bar = tk.Frame(self.root, bg="black", height=40)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        self.session_time_label = tk.Label(self.top_bar, text="Temps total écoulé : 00:00", fg="white", bg="black", font=("Arial", 12))
        self.session_time_label.pack(side=tk.LEFT, padx=10)

        self.image_time_label = tk.Label(self.top_bar, text="Temps restant sur l'image : 00:00", fg="white", bg="black", font=("Arial", 12))
        self.image_time_label.pack(side=tk.RIGHT, padx=10)

        # Zone d'affichage de l'image
        self.label = tk.Label(self.root, bg="black")
        self.label.pack(expand=True, fill=tk.BOTH)

        # Barre noire en bas (options - cachable)
        self.bottom_bar = tk.Frame(self.root, bg="black", height=40)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.bottom_bar.place(relx=0.5, rely=1, anchor="s", relwidth=1, height=50)

        self.mirror_h_button = tk.Button(self.bottom_bar, text="Miroir H", command=self.toggle_mirror_horizontal)
        # self.mirror_h_button.pack(side=tk.LEFT, padx=5)
        self.mirror_h_button.place(relx=0.32, rely=.5, anchor="center", height=40)

        self.mirror_v_button = tk.Button(self.bottom_bar, text="Miroir V", command=self.toggle_mirror_vertical)
        # self.mirror_v_button.pack(side=tk.LEFT, padx=5)
        self.mirror_v_button.place(relx=0.4, rely=.5, anchor="center", height=40)

        self.prev_button = tk.Button(self.bottom_bar, text="◄ Précédent", command=self.prev_image)
        # self.prev_button.pack(side=tk.LEFT, padx=5)
        self.prev_button.place(relx=0.5, rely=.5, anchor="center", height=40)

        self.pause_button = tk.Button(self.bottom_bar, text="⏸ Pause", command=self.pause_session)
        # self.pause_button.pack(side=tk.LEFT, padx=5)
        self.pause_button.place(relx=0.58, rely=.5, anchor="center", height=40)

        self.next_button = tk.Button(self.bottom_bar, text="Suivant ►", command=self.next_image)
        # self.next_button.pack(side=tk.LEFT, padx=5)
        self.next_button.place(relx=0.66, rely=.5, anchor="center", height=40)
        
        # Barre du bas cachable avec clic sur l'image
        self.label.bind("<Button-1>", self.toggle_bottom_bar)
        self.root.attributes("-fullscreen", True)
        def toggle_fullscreen(event=None):
            # Alterner le mode plein écran
            self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
        self.root.bind("<Escape>", toggle_fullscreen)

        # Afficher la première image
        self.show_image(self.current_index)

        # Lier les touches clavier et l'événement de redimensionnement
        self.bind_keys()
        # self.root.bind("<Configure>", self.resize_image)  # Écouter les événements de redimensionnement
        self.update_timer()

    def bind_keys(self):
        """Lier les touches du clavier pour naviguer."""
        self.root.bind("<Left>", lambda event: self.prev_image())
        self.root.bind("<Right>", lambda event: self.next_image())
        self.root.bind("<space>", lambda event: self.pause_session())

    def show_image(self, index):
        """Afficher l'image redimensionnée à la taille de la fenêtre."""
        self.image_path = os.path.join(self.folder_path, self.image_files[index])
        self.load_image()

    def format_time(self, seconds):
        """Convertit un temps en secondes en un format HH:MM:SS si supérieur à 1 heure, sinon MM:SS ou SS."""
        if seconds >= 3600:  # Plus de 1 heure
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
       
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes):02}:{int(seconds):02}"
        
    def load_image(self):
        """Charger et redimensionner l'image à la taille de la fenêtre."""
        img = Image.open(self.image_path)
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        img_width, img_height = img.size
        window_ratio = window_width / window_height
        img_ratio = img_width / img_height

        self.start_size = img_width, img_height

        if window_ratio > img_ratio:
            # Ajuster l'image pour que sa hauteur soit égale à la hauteur de la fenêtre
            new_height = window_height
            new_width = int(new_height * img_ratio)
        else:
            # Ajuster l'image pour que sa largeur soit égale à la largeur de la fenêtre
            new_width = window_width
            new_height = int(new_width / img_ratio)

        if new_width == 0 or new_height == 0:
            img = img.resize((img.width, img.height), Image.Resampling.LANCZOS)
            self.img = ImageTk.PhotoImage(img)
            self.label.config(image=self.img)
            return

        # Appliquer les miroirs si activés
        if self.mirror_horizontal:
            img = ImageOps.mirror(img)
        if self.mirror_vertical:
            img = ImageOps.flip(img)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.img = ImageTk.PhotoImage(img)
        self.label.config(image=self.img)

    def resize_image(self, event):
        """Redimensionner l'image lors du redimensionnement de la fenêtre."""
        img = Image.open(self.image_path)
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        if abs(self.start_size[0] - window_width) < 50 and abs(self.start_size[1] - window_height) < 50:
            return
        self.load_image()

    def prev_image(self):
        """Passer à l'image précédente."""
        self.end_time += time.time() - self.image_start_time if self.paused is False else  self.paused_time - self.image_start_time

        self.time_spent_on_image = 0
        
        self.current_index = (self.current_index - 1) % len(self.image_files)
        self.show_image(self.current_index)
        self.image_start_time = time.time()

    def next_image(self, completed = False):
        if not completed: 
            self.end_time += time.time() - self.image_start_time if self.paused is False else  self.paused_time - self.image_start_time
        """Passer à l'image suivante."""
        self.time_spent_on_image = 0
        

        self.current_index = (self.current_index + 1) % len(self.image_files)
        self.show_image(self.current_index)
        self.image_start_time = time.time()

    def pause_session(self):
        """Mettre en pause ou reprendre la session."""
        if self.paused:
            self.pause_button.config(text="⏸ Pause")
            self.end_time += time.time() - self.paused_time
            self.image_start_time += time.time() - self.paused_time
            self.paused = False
        else:
            self.paused = True
            self.pause_button.config(text="▶ Reprendre")
            self.paused_time = time.time()


    def log_time_spent(self):
        """Enregistrer le temps passé sur chaque image et l'ajouter à l'historique."""
        time_spent = time.time() - self.image_start_time

        # Enregistrer dans le fichier CSV
        csv_directory = self.settings_menu.settings["csv_directory"]
        csv_filename = self.settings_menu.settings["csv_filename"]
        csv_path = os.path.join(csv_directory, csv_filename)
        log_to_csv(csv_path, time_spent, self.session_duration, self.mode)

        self.time_spent_on_image = 0

    def toggle_bottom_bar(self, event):
        """Afficher ou cacher la barre du bas."""
        if self.bottom_bar.winfo_ismapped():
            self.bottom_bar.pack_forget()
        else:
            self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def toggle_mirror_horizontal(self):
        """Activer/désactiver le miroir horizontal."""
        self.mirror_horizontal = not self.mirror_horizontal
        self.load_image()

    def toggle_mirror_vertical(self):
        """Activer/désactiver le miroir vertical."""
        self.mirror_vertical = not self.mirror_vertical
        self.load_image()

    def calculate_class_mode_times(self, session_duration):
        """Calculer les temps d'affichage progressifs pour le mode classe."""
        # time_slots = [30, 60, 180, 300, 600, 1200, 1800, 2400, 3000, 3600, 5400, 7200]
        # total_time = 0
        class_mode_times = []
        sessions_times = [30 * 60, 60 * 60, 90 * 60, 120 * 60, 180 * 60, 360 * 60]

        if session_duration >= sessions_times[0]:
            class_mode_times = [ 30, 30, 30, 30, 30, 30, 60, 60, 60, 60, 120,
                                180, 180, 300, 600 ] 
        if session_duration >= sessions_times[1]:
            class_mode_times.extend([600, 1200 ])
        if session_duration >= sessions_times[2]:
            class_mode_times.extend([ 1800 ])
        if session_duration >= sessions_times[3]:
            class_mode_times.extend([ 1800 ])
        if session_duration >= sessions_times[4]:
            class_mode_times.extend([ 3600 ])
        if session_duration >= sessions_times[5]:
            class_mode_times.extend([ 3600, 7200 ])

        print(class_mode_times)
        return class_mode_times

    def update_timer(self):
        """Mettre à jour le minuteur et afficher le temps restant."""
        if not self.paused and self.timer_active:
            time_left = self.end_time - time.time()
            if time_left <= 0 and self.current_image_time - (time.time() - self.image_start_time)  <= 0:
                self.timer_active = False
                self.time_label.config(text="Session terminée.")
                choose_session_duration()
            else:
                # Mettre à jour le temps de session et temps restant par image
                self.session_time_label.config(text=f"Temps total écoulé : {self.format_time(max(0, time_left))} / {self.format_time(self.session_duration)}")

                image_time_left = self.current_image_time - (time.time() - self.image_start_time)
                self.image_time_label.config(text=f"Temps restant sur l'image : {self.format_time(max(0, image_time_left))} / {self.format_time(self.current_image_time)}")

                # Passer à l'image suivante si le temps par image est écoulé
                if image_time_left <= 0:
                    self.log_time_spent()
                    if self.mode == "classe":
                        self.done_images_number = self.done_images_number + 1 
                        # Calculer l'index basé sur le nombre d'images terminées (self.current_index)
                        index = min(self.done_images_number, len(self.class_mode_times) - 1)
                        
                        # Mettre à jour le temps d'affichage pour l'image suivante
                        self.current_image_time = self.class_mode_times[index]
                    
                    self.next_image(completed=True)

                self.root.after(1000, self.update_timer)  # Appel toutes les secondes
        else:
            self.root.after(1000, self.update_timer)  # Vérifier toutes les secondes

    def run(self):
        self.root.mainloop()


def choose_session_duration():
    """Choisir la durée de la session dans une nouvelle fenêtre."""
    durations = {
        "30 minutes": 30 * 60,
        "1 heure": 60 * 60,
        "1h30": 90 * 60,
        "2 heures": 120 * 60,
        "3 heures": 180 * 60,
        "6 heures": 360 * 60
    }

    def start_session(duration, mode, image_time, settings_menu):
        """Lancer la session avec la durée choisie."""
        if settings_menu.settings.get("current_folder") == None:
            tk.messagebox.showerror("Error", f"Select a folder to use first. Up in the parameters. You only have to do it once.")
            return
        duration_seconds = durations[duration]
        session_window.destroy()  # Fermer la fenêtre de sélection
        root = tk.Tk()
        app = ImageViewerApp(root, settings_menu.settings["current_folder"], session_duration=duration_seconds, mode=mode, image_time=image_time, settings_menu=settings_menu)
        app.run()
    
    session_window = tk.Tk()
    session_window.title("Choisir la durée de la session")
    
    top_menu_bar = tk.Frame(session_window, bg="white", height=40)
    top_menu_bar.pack(side=tk.TOP, fill=tk.X)
    
    # Sub window settings
    settings_menu = SettingsMenu(top_menu_bar)
    
    # Sub window statistics
    csv_file = os.path.join(settings_menu.settings.get("csv_directory"), settings_menu.settings.get("csv_filename"))
    
    if not os.path.exists(csv_file):
        csv_file = "session_log.csv"
    
    statistics_button = StatisticsButton(top_menu_bar, csv_file)

    

    tk.Label(session_window, text="Choisissez la durée de la session :").pack(pady=10, padx=10)

    duration_var = tk.StringVar(value="1 heure")
    mode_var = tk.StringVar(value="normal")

    image_time_var = tk.StringVar(value="30")  # Par défaut, 30 sec par image pour le mode normal

    for label in durations.keys():
        tk.Radiobutton(session_window, text=label, variable=duration_var, value=label).pack()

    # Choix entre "mode normal" et "mode classe"
    tk.Label(session_window, text="Mode :").pack(pady=10, padx=10)
    tk.Radiobutton(session_window, text="Mode normal", variable=mode_var, value="normal").pack()
    tk.Radiobutton(session_window, text="Mode classe", variable=mode_var, value="classe").pack()

    # Si mode normal, demander le temps par image
    tk.Label(session_window, text="Durée par image (en secondes) pour le mode normal :").pack(pady=10, padx=10)
    tk.Entry(session_window, textvariable=image_time_var).pack()

    tk.Button(session_window, text="Démarrer", command=lambda: start_session(duration_var.get(), mode_var.get(), int(image_time_var.get()), settings_menu)).pack(pady=10, padx=10)

    session_window.mainloop()
    

if __name__ == "__main__":
    choose_session_duration()