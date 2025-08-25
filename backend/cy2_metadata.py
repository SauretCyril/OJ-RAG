from PIL import Image
import json

def extract_comfyui_metadata(image_path):
    """Extraire les métadonnées spécifiques à ComfyUI"""
    try:
        prompts_data = {}

        with Image.open(image_path) as img: 
            # ComfyUI stocke ses données dans les métadonnées PNG
            if hasattr(img, 'text') and img.text:
                # Chercher les clés spécifiques à ComfyUI
                if 'workflow' in img.text:
                    try:
                        workflow_data = json.loads(img.text['workflow'])
                        prompts_data['workflow'] = workflow_data
                    except json.JSONDecodeError:
                        pass

                if 'prompt' in img.text:
                    try:
                        prompt_data = json.loads(img.text['prompt'])
                        prompts_data['prompt'] = prompt_data
                    except json.JSONDecodeError:
                        pass

                # Extraire les prompts des nœuds
                positive_prompt, negative_prompt = parse_comfyui_prompts(prompts_data)
                model_info = extract_model_info(prompts_data)

                if positive_prompt or negative_prompt:
                    return {
                        'positive_prompt': positive_prompt,
                        'negative_prompt': negative_prompt,
                        'workflow_data': json.dumps(prompts_data) if prompts_data else None,
                        'model_info': model_info
                    }
        return None

    except Exception as e:
        print(f"[ERROR-1254] Error extracting ComfyUI metadata for {image_path}: {e}")
        return None

def parse_comfyui_prompts(comfyui_data):
    """Parser les prompts positifs et négatifs depuis les données ComfyUI"""
    try:
        positive_prompt = ""
        negative_prompt = ""

        for data_key, data_value in comfyui_data.items():
            if isinstance(data_value, dict):
                for node_id, node_data in data_value.items():
                    if isinstance(node_data, dict) and 'inputs' in node_data:
                        inputs = node_data['inputs']
                        class_type = node_data.get('class_type', '').lower()

                        # Champs explicites
                        if not positive_prompt and 'positive' in inputs:
                            positive_prompt = inputs['positive']
                        if not negative_prompt and 'negative' in inputs:
                            negative_prompt = inputs['negative']
                        # Champs text selon le type
                        if 'text' in inputs:
                            text_content = inputs['text']
                            if not positive_prompt and (
                                'positive' in class_type or 
                                ('clip' in class_type and 'negative' not in class_type)
                            ):
                                positive_prompt = text_content
                            elif not negative_prompt and 'negative' in class_type:
                                negative_prompt = text_content
                            elif not positive_prompt:
                                positive_prompt = text_content

        return positive_prompt, negative_prompt

    except Exception as e:
        print(f"[ERROR] Error parsing ComfyUI prompts: {e}")
        return "", ""

def extract_model_info(comfyui_data):
    """Extraire les informations du modèle utilisé"""
    try:
        model_info = {}

        for data_key, data_value in comfyui_data.items():
            if isinstance(data_value, dict):
                for node_id, node_data in data_value.items():
                    if isinstance(node_data, dict):
                        class_type = node_data.get('class_type', '').lower()
                        inputs = node_data.get('inputs', {})

                        # Modèles
                        if any(keyword in class_type for keyword in ['checkpoint', 'model', 'flux']):
                            if 'ckpt_name' in inputs:
                                model_info['checkpoint'] = inputs['ckpt_name']
                            if 'model_name' in inputs:
                                model_info['model'] = inputs['model_name']
                            if 'vae_name' in inputs:
                                model_info['vae'] = inputs['vae_name']

                        # Paramètres de génération
                        if any(keyword in class_type for keyword in ['sampler', 'scheduler']):
                            model_info.update({
                                'steps': inputs.get('steps'),
                                'cfg': inputs.get('cfg'),
                                'sampler_name': inputs.get('sampler_name'),
                                'scheduler': inputs.get('scheduler'),
                                'seed': inputs.get('seed')
                            })

        return model_info

    except Exception as e:
        print(f"[ERROR] Error extracting model info: {e}")
        return {}

def remove_image_metadata(self, image_path):
    """Supprimer les métadonnées d'une image de la base de données"""
    try:
        image_path = os.path.normpath(image_path)
        conn, cursor = self.get_db_connection()
            
        # Supprimer les métadonnées
        cursor.execute(
            "DELETE FROM image_metadata WHERE function_name = ? AND image_path = ?",
            (self.title, image_path)
        )
            
        # Supprimer l'entrée "viewed" aussi
        cursor.execute(
            "DELETE FROM viewed_images WHERE function_name = ? AND image_path = ?",
            (self.title, image_path)
        )
            
        conn.commit()
        conn.close()
           
        print(f"[INFO] Metadata removed for: {os.path.basename(image_path)}")
            
    except Exception as e:
        print(f"[ERROR] Error removing metadata: {e}")

def Extract_all_metadata(self):
    """Charger les métadonnées pour tous les fichiers présents dans la table viewed_images avec une barre de progression"""
    try:
        conn, cursor = self.get_db_connection()
        cursor.execute(
            "SELECT image_path FROM viewed_images WHERE function_name = ?",
            (self.title,)
        )
        image_paths = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Vérifier quelles images n'ont pas encore de métadonnées
        images_needing_metadata = []
        for image_path in image_paths:
            existing_metadata = self.get_image_metadata(image_path)
            if not existing_metadata:
                images_needing_metadata.append(image_path)

        total = len(images_needing_metadata)
        if total == 0:
            messagebox.showinfo("Info", "Toutes les images ont déjà des métadonnées.")
            return

        # Créer une fenêtre de progression
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Extraction des métadonnées")
        progress_win.geometry("400x120")
        progress_win.resizable(False, False)
        progress_label = ttk.Label(progress_win, text="Extraction des métadonnées...")
        progress_label.pack(pady=(20, 10))
        progress_bar = ttk.Progressbar(progress_win, length=350, mode="determinate", maximum=total)
        progress_bar.pack(pady=(0, 10))
        percent_label = ttk.Label(progress_win, text="0%")
        percent_label.pack()

        self.root.update_idletasks()

        for idx, image_path in enumerate(images_needing_metadata, 1):
            metadata = self.extract_image_metadata(image_path)
            if metadata:
                nsfw_score = get_nsfw_score(image_path)
                metadata['nsfw_score'] = nsfw_score
                self.store_image_metadata(image_path, metadata)
            progress_bar["value"] = idx
            percent_label.config(text=f"{int(idx/total*100)}%")
            progress_win.update_idletasks()

        progress_win.destroy()
        messagebox.showinfo("Terminé", f"Métadonnées extraites pour {total} images.")

    except Exception as e:
        print(f"[ERROR] Erreur lors du chargement des métadonnées : {e}")
        messagebox.showerror("Erreur", f"Erreur lors du chargement des métadonnées : {e}")


def store_image_metadata( image_path, metadata):
    """Stocker les métadonnées d'une image en base"""
    try:
        if not metadata:
            return False

        image_path = os.path.normpath(image_path)
        conn, cursor = self.get_db_connection()

        model_info = metadata.get('model_info', {})

        # Convertir les valeurs pour éviter les erreurs de type
        positive_prompt = str(metadata.get('positive_prompt', '')) if metadata.get('positive_prompt') else ''
        negative_prompt = str(metadata.get('negative_prompt', '')) if metadata.get('negative_prompt') else ''
        workflow_data = str(metadata.get('workflow_data', '')) if metadata.get('workflow_data') else ''

        cursor.execute('''
            INSERT OR REPLACE INTO image_metadata 
            (function_name, image_path, file_size, width, height, format, mode, 
             file_hash, creation_date, modified_date, exif_data,
             positive_prompt, negative_prompt, workflow_data,
             model_checkpoint, model_vae, generation_steps, cfg_scale,
             sampler_name, scheduler, seed, nsfw_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.title, 
            image_path, 
            metadata['file_size'], 
            metadata['width'], 
            metadata['height'], 
            metadata['format'], 
            metadata['mode'], 
            metadata['file_hash'],
            metadata['creation_date'], 
            metadata['modified_date'], 
            metadata['exif_data'],
            positive_prompt,
            negative_prompt,
            workflow_data,
            str(model_info.get('checkpoint', '')) if model_info.get('checkpoint') else '',
            str(model_info.get('vae', '')) if model_info.get('vae') else '',
            model_info.get('steps') if model_info.get('steps') is not None else None,
            model_info.get('cfg') if model_info.get('cfg') is not None else None,
            str(model_info.get('sampler_name', '')) if model_info.get('sampler_name') else '',
            str(model_info.get('scheduler', '')) if model_info.get('scheduler') else '',
            model_info.get('seed') if model_info.get('seed') is not None else None,
            metadata.get('nsfw_score', 0.0)  # <-- Ajout ici
        ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Error storing metadata: {e}")
        return

def get_image_metadata(self, image_path):
    """Récupérer les métadonnées d'une image depuis la base"""
    try:
        image_path = os.path.normpath(image_path)
        conn, cursor = self.get_db_connection()
        cursor.execute('''
            SELECT file_size, width, height, format, mode, file_hash, 
                   creation_date, modified_date, exif_data, extracted_date,
                   positive_prompt, negative_prompt, workflow_data,
                   model_checkpoint, model_vae, generation_steps, cfg_scale,
                   sampler_name, scheduler, seed, nsfw_score
            FROM image_metadata 
            WHERE function_name = ? AND image_path = ?
        ''', (self.title, image_path))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'file_size': result[0],
                'width': result[1],
                'height': result[2],
                'format': result[3],
                'mode': result[4],
                'file_hash': result[5],
                'creation_date': result[6],
                'modified_date': result[7],
                'exif_data': json.loads(result[8]) if result[8] else None,
                'extracted_date': result[9],
                'positive_prompt': result[10] or '',
                'negative_prompt': result[11] or '',
                'workflow_data': result[12] or '',
                'model_checkpoint': result[13] or '',
                'model_vae': result[14] or '',
                'generation_steps': result[15],
                'cfg_scale': result[16],
                'sampler_name': result[17] or '',
                'scheduler': result[18] or '',
                'seed': result[19],
                'nsfw_score': result[20]  # <-- AJOUT ICI
            }
        return None
        
    except Exception as e:
        print(f"[ERROR] Error getting metadata: {e}")
        return None
