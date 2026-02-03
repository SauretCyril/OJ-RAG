#!/usr/bin/env python3
"""
Test de connexion ComfyUI pour vérifier que l'exécution de workflow fonctionne
"""

import os
import sys
import json
from cy6_wkf001_Basic import comfyui_basic_task
from cy6_websocket_api_client import server_address
import urllib.request

def test_comfyui_connection():
    """Teste la connexion à ComfyUI"""
    print("🔍 Test de connexion ComfyUI...")
    
    try:
        # Test de base - est-ce que ComfyUI répond ?
        response = urllib.request.urlopen(f'http://{server_address}/system_stats', timeout=10)
        stats = response.read().decode()
        print(f"✅ ComfyUI est accessible sur {server_address}")
        
        # Parser les stats pour afficher des infos utiles
        stats_data = json.loads(stats)
        print(f"   Version ComfyUI: {stats_data.get('system', {}).get('comfyui_version', 'Unknown')}")
        print(f"   Python: {stats_data.get('system', {}).get('python_version', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ComfyUI n'est pas accessible: {e}")
        print(f"   Assurez-vous que ComfyUI fonctionne sur {server_address}")
        return False

def test_workflow_execution():
    """Teste l'exécution d'un workflow basique"""
    print("\n🔍 Test d'exécution de workflow...")
    
    # Workflow basique pour test
    basic_workflow = {
        "3": {"inputs": {"seed": 156680208700286, "steps": 20, "cfg": 8.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler", "_meta": {"title": "KSampler"}},
        "4": {"inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"}, "class_type": "CheckpointLoaderSimple", "_meta": {"title": "Load Checkpoint"}},
        "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage", "_meta": {"title": "Empty Latent Image"}},
        "6": {"inputs": {"text": "beautiful landscape", "clip": ["4", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "CLIP Text Encode (Prompt)"}},
        "7": {"inputs": {"text": "bad quality", "clip": ["4", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "CLIP Text Encode (Prompt)"}},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode", "_meta": {"title": "VAE Decode"}},
        "9": {"inputs": {"filename_prefix": "ComfyUI_test", "images": ["8", 0]}, "class_type": "SaveImage", "_meta": {"title": "Save Image"}}
    }
    
    basic_values = {
        "1": {"id": "6", "type": "prompt", "value": "beautiful landscape, nature, test image"},
        "2": {"id": "7", "type": "prompt", "value": "bad quality, blurry"},
        "3": {"id": "3", "type": "seed", "value": "156680208700286"}
    }
    
    try:
        # Créer les fichiers temporaires
        os.makedirs("data/Workflows", exist_ok=True)
        
        workflow_path = "data/Workflows/test_workflow.json" 
        values_path = "data/Workflows/test_values.json"
        
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(basic_workflow, f, ensure_ascii=False, indent=2)
            
        with open(values_path, "w", encoding="utf-8") as f:
            json.dump(basic_values, f, ensure_ascii=False, indent=2)
        
        print("✅ Fichiers de test créés")
        
        # Tester l'exécution
        print("🚀 Lancement du workflow de test sur ComfyUI...")
        task = comfyui_basic_task()
        prompt_id = task.addToQueue(workflow_path, values_path)
        
        print(f"✅ Workflow ajouté à la queue ComfyUI avec l'ID: {prompt_id}")
        
        # Essayer de récupérer les images (peut prendre du temps)
        print("⏳ Attente de la génération des images...")
        images = task.GetImages(prompt_id)
        
        if images:
            print(f"✅ Images générées avec succès! Nombre d'images: {len(images)}")
        else:
            print("⚠️  Aucune image récupérée (mais pas forcément un problème)")
            
        # Nettoyer
        if os.path.exists(workflow_path):
            os.remove(workflow_path)
        if os.path.exists(values_path):
            os.remove(values_path)
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du workflow: {e}")
        return False

def main():
    print("🧪 Test de la connexion ComfyUI pour cy8_prompts_manager")
    print("=" * 60)
    
    # Test 1: Connexion de base
    if not test_comfyui_connection():
        print("\n💡 Conseils de dépannage:")
        print("   - Vérifiez que ComfyUI est lancé")
        print("   - Vérifiez que ComfyUI écoute sur 127.0.0.1:8188")
        print("   - Vérifiez qu'aucun firewall ne bloque la connexion")
        return
    
    # Test 2: Exécution de workflow
    print("\n" + "=" * 60)
    if test_workflow_execution():
        print(f"\n🎉 Tous les tests passent ! ComfyUI est prêt pour cy8_prompts_manager")
    else:
        print(f"\n⚠️  Problème avec l'exécution de workflow")

if __name__ == "__main__":
    main()