import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from dotenv import load_dotenv

from cy_mistral import analyze_comfyui_log_with_mistral, chat_with_mistral


class ComfyUILogAssistant(tk.Tk):
    """Interface graphique pour analyser les logs ComfyUI avec Mistral."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Assistant ComfyUI - Analyse des logs")
        self.geometry("1200x820")
        self.minsize(960, 680)

        load_dotenv()
        self.log_path = os.getenv("COMFYUI_FILE_LOG", "").strip()
        self.role = "Expert Python, comfyuil et génération d'image via IA"

        self.chat_history: List[Dict[str, str]] = []
        self.errors: List[Dict[str, str]] = []
        self._error_map: Dict[str, Dict[str, str]] = {}

        self._build_ui()
        self._refresh_log_indicator()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 8))

        self.log_label = ttk.Label(header, text="Chemin du log ComfyUI : non défini", foreground="#555")
        self.log_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.analyze_button = ttk.Button(header, text="Analyser le log", command=self._on_analyze_click)
        self.analyze_button.pack(side=tk.RIGHT)

        splitter = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        splitter.pack(fill=tk.BOTH, expand=True)

        top_section = ttk.Frame(splitter)
        splitter.add(top_section, weight=3)

        table_frame = ttk.LabelFrame(top_section, text="Anomalies détectées")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("timestamp", "gravite", "resume", "categorie")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("timestamp", text="Horodatage")
        self.tree.heading("gravite", text="Gravité")
        self.tree.heading("resume", text="Résumé")
        self.tree.heading("categorie", text="Catégorie")

        self.tree.column("timestamp", width=140, anchor=tk.W)
        self.tree.column("gravite", width=100, anchor=tk.CENTER)
        self.tree.column("resume", width=520, anchor=tk.W)
        self.tree.column("categorie", width=200, anchor=tk.W)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        detail_frame = ttk.Frame(splitter)
        splitter.add(detail_frame, weight=2)

        info_frame = ttk.LabelFrame(detail_frame, text="Détail de l'anomalie")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.detail_text = ScrolledText(info_frame, wrap=tk.WORD, height=12)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.configure(state=tk.DISABLED)

        chat_frame = ttk.LabelFrame(detail_frame, text="Chat Mistral")
        chat_frame.pack(fill=tk.BOTH, expand=False)

        self.chat_display = ScrolledText(chat_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        entry_frame = ttk.Frame(chat_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 4))

        self.chat_entry = ttk.Entry(entry_frame)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.chat_entry.bind("<Return>", self._on_chat_send)

        self.send_button = ttk.Button(entry_frame, text="Envoyer", command=self._on_chat_send)
        self.send_button.pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="Prêt.")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W, padding=(12, 4))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _refresh_log_indicator(self) -> None:
        if self.log_path and Path(self.log_path).exists():
            self.log_label.configure(text=f"Log : {self.log_path}", foreground="#1d6f42")
        else:
            self.log_label.configure(text="Chemin du log ComfyUI introuvable", foreground="#c0392b")

    def _set_busy(self, is_busy: bool) -> None:
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.analyze_button.configure(state=state)
        self.send_button.configure(state=state)
        self.chat_entry.configure(state=state)
        if is_busy:
            self.status_var.set("Traitement en cours...")
        else:
            self.status_var.set("Prêt.")

    def _on_analyze_click(self) -> None:
        if not self.log_path:
            messagebox.showerror("Configuration", "La variable COMFYUI_FILE_LOG est absente du fichier .env.")
            return

        log_file = Path(self.log_path)
        if not log_file.exists():
            messagebox.showerror("Fichier introuvable", f"Le fichier de log n'existe pas : {log_file}")
            return

        self._set_busy(True)

        def worker() -> None:
            try:
                log_text = self._read_log_tail(log_file)
                errors = analyze_comfyui_log_with_mistral(log_text)
                self.after(0, lambda: self._update_errors(errors))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Analyse", str(exc)))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def _read_log_tail(self, log_file: Path, max_bytes: int = 180_000) -> str:
        size = log_file.stat().st_size
        start = max(0, size - max_bytes)
        with log_file.open("rb") as fh:
            fh.seek(start)
            data = fh.read()
        text = data.decode("utf-8", errors="ignore")
        if start > 0:
            text = "\n".join(text.splitlines()[1:])
        return text

    def _update_errors(self, errors: Optional[List[Dict[str, str]]]) -> None:
        self.errors = errors or []
        self._error_map = {}
        self.tree.delete(*self.tree.get_children())
        self._set_detail_text("Sélectionnez une anomalie pour afficher le détail.")

        if not self.errors:
            self.status_var.set("Aucune anomalie détectée par Mistral.")
            return

        for idx, err in enumerate(self.errors):
            iid = err.get("id") or f"ERR-{idx:03d}"
            self._error_map[iid] = err
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    err.get("timestamp") or "",
                    err.get("gravite") or "",
                    err.get("resume") or "",
                    err.get("categorie") or ""
                ),
            )
        self.status_var.set(f"{len(self.errors)} anomalie(s) détectée(s).")

    def _on_tree_select(self, event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        error = self._error_map.get(iid)
        if not error:
            return

        detail_lines = []
        if error.get("resume"):
            detail_lines.append(f"Résumé : {error['resume']}")
        if error.get("gravite"):
            detail_lines.append(f"Gravité : {error['gravite']}")
        if error.get("categorie"):
            detail_lines.append(f"Catégorie : {error['categorie']}")
        if error.get("timestamp"):
            detail_lines.append(f"Horodatage : {error['timestamp']}")
        if error.get("details"):
            detail_lines.append("\nDétails :\n" + error["details"])
        if error.get("recommandation"):
            detail_lines.append("\nRecommandation :\n" + error["recommandation"])
        if error.get("extrait"):
            detail_lines.append("\nExtrait du log :\n" + error["extrait"])

        self._set_detail_text("\n\n".join(detail_lines) or "Aucun détail disponible.")

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.configure(state=tk.DISABLED)

    def _append_chat(self, speaker: str, message: str) -> None:
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{speaker}: {message}\n\n")
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _register_assistant_response(self, message: str) -> None:
        """Ajoute la reponse de Mistral a l'historique et a l'affichage."""
        self.chat_history.append({"role": "assistant", "content": message})
        self._append_chat("Mistral", message)

    def _on_chat_send(self, event=None) -> None:
        user_message = self.chat_entry.get().strip()
        if not user_message:
            return

        self.chat_entry.delete(0, tk.END)
        self._append_chat("Vous", user_message)
        self.chat_history.append({"role": "user", "content": user_message})
        self._set_busy(True)

        def worker() -> None:
            try:
                messages = list(self.chat_history)
                selection = self.tree.selection()
                if selection:
                    context = self._error_map.get(selection[0])
                else:
                    context = None

                if context:
                    context_text = (
                        "\n\nContexte actuel :\n"
                        f"Résumé : {context.get('resume', '')}\n"
                        f"Détails : {context.get('details', '')}\n"
                        f"Recommandation : {context.get('recommandation', '')}"
                    ).strip()
                    if context_text:
                        messages.append({"role": "user", "content": context_text})

                response = chat_with_mistral(messages, role=self.role)
                self.after(0, lambda resp=response: self._register_assistant_response(resp))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Chat", str(exc)))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = ComfyUILogAssistant()
    app.mainloop()
