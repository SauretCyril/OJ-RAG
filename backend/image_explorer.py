import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
import sqlite3
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading


class DirectoryWatcher(FileSystemEventHandler):
    def __init__(self, image_explorer):
        self.image_explorer = image_explorer

    def on_created(self, event):
        """Appelé lorsqu'un fichier est créé dans le répertoire surveillé"""
        if not event.is_directory:
            # Vérifier si le fichier est une image
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            if event.src_path.lower().endswith(image_extensions):
                print(f"[INFO] New image detected: {event.src_path}")
                self.image_explorer.add_new_image(event.src_path)

class DirectoryWatcherThread:
    def __init__(self, image_explorer):
        self.image_explorer = image_explorer
        self.observer = Observer()

    def start(self):
        event_handler = DirectoryWatcher(self.image_explorer)
        self.observer.schedule(event_handler, self.image_explorer.current_directory, recursive=False)
        self.observer.start()
        print(f"[INFO] Started watching directory: {self.image_explorer.current_directory}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

class ImageExplorer:
    def __init__(self, root, db_path, default_directory, cible_directory):
        self.root = root
        self.root.title("Image Explorer")
        self.root.geometry("1200x800")
        
        # Répertoire par défaut (passé via le constructeur)
        self.current_directory = os.path.normpath(default_directory)
        self.cible_directory = os.path.normpath(cible_directory)
        self.image_files = []
        self.image_widgets = []
        self.pending_changes = []  # Liste des changements en attente
        self.view_mode = "new"  # "new" ou "viewed"
        self.zoomed_images = {}  # Dictionnaire pour suivre les images zoomées
        
        # Initialiser la base de données avec le chemin fourni
        self.db_path = os.path.normpath(db_path)
        self.init_database()
        
        self.setup_ui()
        # Charger automatiquement les images du répertoire par défaut
        if os.path.exists(self.current_directory):
            self.dir_label.config(text=f"Directory: {self.current_directory}")
            self.load_images()
        else:
            self.dir_label.config(text="No directory selected")
            messagebox.showwarning(
                "Invalid Directory",
                f"The default directory does not exist:\n{self.current_directory}\n\nPlease select a valid directory."
            )
            self.select_directory()
        
        # Démarrer le watcher pour surveiller les nouvelles images
        self.watcher_thread = DirectoryWatcherThread(self)
        self.watcher_thread.start()

    def __del__(self):
        """Fermer la connexion à la base de données et arrêter le watcher"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'watcher_thread'):
            self.watcher_thread.stop()
    
    def init_database(self):
        """Initialise la base de données SQLite pour stocker les images vues"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Créer la table si elle n'existe pas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS viewed_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE,
                viewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def is_image_viewed(self, image_path):
        """Vérifier si une image a été vue"""
        image_path = os.path.normpath(image_path)
        self.cursor.execute(
            "SELECT COUNT(*) FROM viewed_images WHERE image_path = ?",
            (image_path,)
        )
        return self.cursor.fetchone()[0] > 0
    
    def mark_image_as_viewed(self, image_path):
        """Marquer une image comme vue (en attente de sauvegarde)"""
        if image_path not in [change[1] for change in self.pending_changes if change[0] == 'viewed']:
            self.pending_changes.append(('viewed', image_path))
            # Masquer visuellement l'image immédiatement
            self.hide_image_widget(image_path)
            # Activer le bouton de sauvegarde
            self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
    def delete_image_pending(self, image_path):
        """Marquer une image pour suppression (en attente de sauvegarde)"""
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Mark for deletion:\n{os.path.basename(image_path)}?\n\nClick 'Save Changes' to apply."
        )
        
        if result:
            if image_path not in [change[1] for change in self.pending_changes]:
                self.pending_changes.append(('delete', image_path))
                # Masquer visuellement l'image immédiatement
                self.hide_image_widget(image_path)
                # Activer le bouton de sauvegarde
                self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
    def hide_image_widget(self, image_path):
        """Masquer visuellement une image sans la supprimer de l'interface"""
        for widget in self.image_widgets:
            if hasattr(widget, 'image_path') and widget.image_path == image_path:
                widget.grid_remove()  # Masquer mais ne pas détruire
    
    def save_changes(self):
        """Sauvegarder tous les changements en attente"""
        if not self.pending_changes:
            return
            
        errors = []
        success_count = 0
        
        for action, image_path in self.pending_changes:
            try:
                print(f"[INFO] Processing {action} for {os.path.basename(image_path)}")
                if action == 'viewed':
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO viewed_images (image_path) VALUES (?)",
                        (image_path,)
                    )
                    success_count += 1
                    
                elif action == 'delete':
                    # Déplacer le fichier vers le répertoire de suppression (trash)
                    if not os.path.exists(self.cible_directory):
                        os.makedirs(self.cible_directory)
                    dest_path = os.path.join(self.cible_directory, os.path.basename(image_path))
                    shutil.move(image_path, dest_path)
                    success_count += 1
                    
            except Exception as e:
                errors.append(f"{os.path.basename(image_path)}: {str(e)}")
        
        # Sauvegarder dans la base de données
        self.conn.commit()
        
        # Vider la liste des changements
        self.pending_changes.clear()
        
        # Recharger l'affichage
        self.load_images()
        
        # Désactiver le bouton de sauvegarde
        self.save_btn.config(state="disabled", text="Save Changes")
        
        # Afficher le résultat
        if errors:
            messagebox.showwarning(
                "Partial Success", 
                f"Processed {success_count} items successfully.\n\nErrors:\n" + "\n".join(errors)
            )
        else:
            messagebox.showinfo("Success", f"Successfully processed {success_count} items!")

    

    def unmark_image_as_viewed(self, image_path):
        """Retirer une image de la liste des images vues"""
        result = messagebox.askyesno(
            "Confirm Unmark", 
            f"Remove from viewed list:\n{os.path.basename(image_path)}?"
        )
        
        if result:
            try:
                self.cursor.execute(
                    "DELETE FROM viewed_images WHERE image_path = ?",
                    (image_path,)
                )
                self.conn.commit()
                self.load_images()
                messagebox.showinfo("Success", "Image removed from viewed list!")
            except Exception as e:
                messagebox.showerror("Error", f"Error removing image from viewed list: {str(e)}")

    def setup_ui(self):
        # Top frame for directory selection
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(top_frame, text="Select Directory", command=self.select_directory).pack(side="left")
        self.dir_label = ttk.Label(top_frame, text=f"Directory: {self.current_directory}")
        self.dir_label.pack(side="left", padx=(10, 0))
        
        # Mode frame
        mode_frame = ttk.Frame(top_frame)
        mode_frame.pack(side="left", padx=(20, 0))
        
        self.mode_label = ttk.Label(mode_frame, text="Mode: New Images", font=("Arial", 9, "bold"))
        self.mode_label.pack()
        
        # self.view_mode_btn = tk.Button(
        #     mode_frame,
        #     text="Show Viewed Images",
        #     command=self.toggle_view_mode,
        #     bg="green",
        #     fg="white",
        #     font=("Arial", 9, "bold")
        # )
        # self.view_mode_btn.pack()
        
        # Bouton pour sauvegarder les changements
        self.save_btn = tk.Button(
            top_frame, 
            text="Save Changes", 
            command=self.save_changes,
            bg="orange",
            fg="white",
            font=("Arial", 10, "bold"),
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=(5, 0))
        
        # Bouton pour réinitialiser les images vues
        #ttk.Button(top_frame, text="Reset Viewed", command=self.reset_viewed_images).pack(side="right")
        
        # Scrollable frame for images
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas (amélioration du scroll)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # Bind focus to canvas for mousewheel to work
        self.canvas.focus_set()
        
    def _on_mousewheel(self, event):
        # Amélioration du scroll avec la molette
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.current_directory = directory
            self.dir_label.config(text=f"Directory: {directory}")
            self.load_images()
     

    def load_images(self):
        # Clear existing widgets
        for widget in self.image_widgets:
            widget.destroy()
        self.image_widgets.clear()
        
        # Get image files based on mode
        self.image_files = []
        
        if self.view_mode == "new":
            # Mode nouvelles images (comportement existant)
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            
            try:
                for filename in os.listdir(self.current_directory):
                    if filename.lower().endswith(image_extensions):
                        image_path = os.path.normpath(os.path.join(self.current_directory, filename))
                        # N'ajouter que les images non vues
                        if not self.is_image_viewed(image_path):
                            self.image_files.append(image_path)
            except Exception as e:
                messagebox.showerror("Error", f"Error reading directory: {str(e)}")
                return
        
       
            
        # Display images
        self.display_images()

    def toggle_image_zoom(self, image_label, image_path):
        """Basculer entre la taille normale et la taille agrandie d'une image"""
        try:
            if image_path in self.zoomed_images:
                # Image est zoomée, revenir à la taille normale
                with Image.open(image_path) as img:
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                
                image_label.config(image=photo)
                image_label.image = photo
                del self.zoomed_images[image_path]
                
            else:
                # Image est en taille normale, zoomer
                with Image.open(image_path) as img:
                    # Calculer la nouvelle taille (max 800x800 pour éviter que ce soit trop grand)
                    original_size = img.size
                    max_size = 800
                    
                    if original_size[0] > max_size or original_size[1] > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                
                image_label.config(image=photo)
                image_label.image = photo
                self.zoomed_images[image_path] = True
            
            # Mettre à jour la région de scroll après le changement de taille
            self.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            
        except Exception as e:
            print(f"Error zooming image {image_path}: {str(e)}")

    def display_images(self):
        row = 0
        col = 0
        max_cols = 3
        
        # Réinitialiser le dictionnaire des images zoomées
        self.zoomed_images.clear()
        
        if not self.image_files:
            # Afficher un message selon le mode
            if self.view_mode == "new":
                message = "No new images to display. All images have been viewed."
            else:
                message = "No viewed images found in database."
                
            no_images_label = ttk.Label(
                self.scrollable_frame, 
                text=message,
                font=("Arial", 14)
            )
            no_images_label.grid(row=0, column=0, columnspan=3, pady=50)
            self.image_widgets.append(no_images_label)
            return
        
        for image_path in self.image_files:
            try:
                # Vérifier si le fichier existe toujours
                if not os.path.exists(image_path):
                    continue
                    
                # Create frame for each image
                image_frame = ttk.Frame(self.scrollable_frame)
                image_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                image_frame.image_path = image_path  # Référence pour masquage
                
                # Load and resize image
                with Image.open(image_path) as img:
                    # Resize image to fit display (max 300x300)
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                
                # Create label for image
                image_label = ttk.Label(image_frame, image=photo)
                image_label.image = photo  # Keep a reference
                image_label.pack()
                
                # Bind double-click to zoom function
                image_label.bind(
                    "<Double-Button-1>", 
                    lambda event, label=image_label, path=image_path: self.toggle_image_zoom(label, path)
                )
                
                # Changer le curseur pour indiquer que l'image est cliquable
                image_label.config(cursor="hand2")
                
                # Frame for buttons
                button_frame = ttk.Frame(image_frame)
                button_frame.pack(pady=5)
                
                if self.view_mode == "new":
                    # Boutons pour les nouvelles images
                    # Create OK button (viewed)
                    ok_btn = tk.Button(
                        button_frame, 
                        text="✓ OK", 
                        bg="green", 
                        fg="white", 
                        font=("Arial", 10, "bold"),
                        width=6,
                        height=1,
                        command=lambda path=image_path: self.mark_image_as_viewed(path)
                    )
                    ok_btn.pack(side="left", padx=2)
                    
                    # Create delete button (X)
                    delete_btn = tk.Button(
                        button_frame, 
                        text="✕ Delete", 
                        bg="red", 
                        fg="white", 
                        font=("Arial", 10, "bold"),
                        width=8,
                        height=1,
                        command=lambda path=image_path: self.delete_image_pending(path)
                    )
                    delete_btn.pack(side="left", padx=2)
                    
                    self.image_widgets.extend([ok_btn, delete_btn])
                
                else:  # view_mode == "viewed"
                    # Boutons pour les images vues
                    # Bouton pour retirer de la liste des vues
                    unmark_btn = tk.Button(
                        button_frame, 
                        text="↺ Unmark", 
                        bg="orange", 
                        fg="white", 
                        font=("Arial", 10, "bold"),
                        width=8,
                        height=1,
                        command=lambda path=image_path: self.unmark_image_as_viewed(path)
                    )
                    unmark_btn.pack(side="left", padx=2)
                    
                    # Bouton pour supprimer le fichier
                    delete_btn = tk.Button(
                        button_frame, 
                        text="✕ Delete", 
                        bg="red", 
                        fg="white", 
                        font=("Arial", 10, "bold"),
                        width=8,
                        height=1,
                        command=lambda path=image_path: self.move_image_to(path)
                    )
                    delete_btn.pack(side="left", padx=2)
                    
                    self.image_widgets.extend([unmark_btn, delete_btn])
                
                # Add filename label
                filename = os.path.basename(image_path)
                filename_label = ttk.Label(image_frame, text=filename, wraplength=280)
                filename_label.pack()
                
                # Add zoom instruction label
                zoom_instruction = ttk.Label(
                    image_frame, 
                    text="Double-click to zoom", 
                    font=("Arial", 8), 
                    foreground="gray"
                )
                zoom_instruction.pack()
                
                # Bind mousewheel to image widgets also
                for widget in [image_frame, image_label, button_frame]:
                    widget.bind("<MouseWheel>", self._on_mousewheel)
                
                self.image_widgets.extend([image_frame, image_label, button_frame, filename_label, zoom_instruction])
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
            except Exception as e:
                print(f"Error loading image {image_path}: {str(e)}")
                
        # Update scroll region
        self.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def move_image_to(self, image_path):
        """Supprimer une image vue (suppression directe, pas de pending)"""
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete:\n{os.path.basename(image_path)}?\n\nThis will permanently delete the file."
        )
        
        if result:
            try:
                # Supprimer le fichier
                if os.name == 'nt':  # Windows
                    try:
                        import send2trash
                        send2trash.send2trash(image_path)
                    except ImportError:
                        os.remove(image_path)
                else:
                    os.remove(image_path)
                
                # Retirer de la base de données
                self.cursor.execute(
                    "DELETE FROM viewed_images WHERE image_path = ?",
                    (image_path,)
                )
                self.conn.commit()
                
                # Recharger l'affichage
                self.load_images()
                messagebox.showinfo("Success", "Image deleted successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting image: {str(e)}")

    def __del__(self):
        """Fermer la connexion à la base de données et arrêter le watcher"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'watcher_thread'):
            self.watcher_thread.stop()

    def add_new_image(self, image_path):
        """Ajouter une nouvelle image à l'interface"""
        try:
            image_path = os.path.normpath(image_path)
            if image_path not in self.image_files:
                self.image_files.append(image_path)
                print(f"[INFO] Adding new image to display: {image_path}")
                self.display_images()
        except Exception as e:
            print(f"[ERROR] Error adding new image: {str(e)}")

def normalize_path(path):
    return os.path.normpath(path)

def main():
    root = tk.Tk()
    db_path_dir = os.path.normpath(r"H:/Entreprendre/Actions-15-Images/I003/")
    db_path_full = os.path.normpath(os.path.join(db_path_dir, "I003_images_.db"))
    default_directory = os.path.normpath(r"E:/Comfyui_G11/ComfyUI/output")
    cible_directory = os.path.normpath(r"E:/Comfyui_G11/ComfyUI/trash")  # <-- Ajoutez le chemin du répertoire de suppression ici
    app = ImageExplorer(root, db_path_full, default_directory, cible_directory)
    root.mainloop()

if __name__ == "__main__":
    main()