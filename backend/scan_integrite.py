import os
import re
import json
import glob
from pathlib import Path

def scan_workspace(root_dir="g:/G_WCS/OJ-RAG"):
    """Analyse le workspace pour détecter des données sensibles"""
    
    # Motifs à rechercher
    patterns = {
        "api_key": r"(api[_-]?key|apikey|api[_-]?token|access[_-]?token|secret[_-]?key)[\"']?\s*[:=]\s*[\"']([a-zA-Z0-9_\-\.]{20,})[\"']",
        "password": r"(password|passwd|pwd|secret)[\"']?\s*[:=]\s*[\"']([^\"']{3,})[\"']",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "connection_string": r"(mongodb|mysql|postgresql|redis|jdbc|odbc)://[^\s<>\"']+",
        "private_key": r"-----BEGIN.*PRIVATE KEY-----",
        "sensitive_paths": r"(/etc/shadow|/home/|C:\\Users\\|/var/www|/var/log)",
    }
    
    # Extensions à analyser
    extensions = ['.py', '.json', '.txt', '.ini', '.cfg', '.env', '.xml', '.yaml', '.yml', '.md', '.js']
    
    # Exclusions (répertoires ou fichiers à ignorer)
    exclusions = ['.git', '.venv', '__pycache__', 'node_modules', 'venv']
    
    findings = []
    
    for ext in extensions:
        files = glob.glob(f"{root_dir}/**/*{ext}", recursive=True)
        for file_path in files:
            # Vérifier les exclusions
            if any(excl in file_path for excl in exclusions):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern_name, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        findings.append({
                            "file": file_path,
                            "type": pattern_name,
                            "line": content.count('\n', 0, match.start()) + 1,
                            "matched_text": match.group(0)[:50] + ('...' if len(match.group(0)) > 50 else '')
                        })
            except Exception as e:
                print(f"Erreur lors de l'analyse de {file_path}: {e}")
    
    return findings

if __name__ == "__main__":
    results = scan_workspace()
    
    if not results:
        print("Aucune information sensible détectée.")
    else:
        print(f"⚠️ {len(results)} potentielles informations sensibles détectées:")
        for item in results:
            print(f"\n{item['type']} trouvé dans {item['file']} à la ligne {item['line']}:")
            print(f"  {item['matched_text']}")
        
        # Sauvegarder les résultats
        with open("security_scan_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\nRésultats sauvegardés dans security_scan_results.json")