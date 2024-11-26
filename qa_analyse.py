from transformers import LongformerTokenizer, LongformerModel
import torch
import numpy as np
from PyPDF2 import PdfReader
import re
from qa_gpt import extract_text_from_pdf,get_answer
from functools import lru_cache
import concurrent.futures
from typing import Dict, List, Tuple
import torch.multiprocessing as mp

# Initialiser le cache global pour les embeddings
EMBEDDING_CACHE = {}

@lru_cache(maxsize=128)
def cached_extract_features(text: str) -> np.ndarray:
    """Version mise en cache de extract_features"""
    if text in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[text]
    
    features = extract_features(text)
    EMBEDDING_CACHE[text] = features
    return features

""" def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text """


def preprocess_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les caractères spéciaux et la ponctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Charger le modèle et le tokenizer
tokenizer = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
model = LongformerModel.from_pretrained("allenai/longformer-base-4096")

# Fonction corrigée pour calculer la similarité cosinus
def cosine_similarity(vec1, vec2):
    # Les vecteurs sont déjà normalisés dans extract_features
    return np.dot(vec1.flatten(), vec2.flatten())

# Fonction pour extraire les caractéristiques
def extract_features(text):
    # Tokenize et encode le texte
    inputs = tokenizer(text, return_tensors="pt", max_length=4096, truncation=True, padding="max_length")
    
    # Obtenir les embeddings
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Obtenir les embeddings de la dernière couche
    token_embeddings = outputs.last_hidden_state
    
    # Créer un masque d'attention étendu
    attention_mask = inputs['attention_mask']
    mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    
    # Appliquer le masque et calculer la moyenne
    sum_embeddings = torch.sum(token_embeddings * mask_expanded, dim=1)
    sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    mean_embeddings = sum_embeddings / sum_mask
    
    # Normaliser le vecteur final
    features = mean_embeddings.squeeze(0).numpy()
    features = features / np.linalg.norm(features)
    
    return features

def calculate_similarity_score(features1, features2):
    # Convertir en arrays numpy si ce ne sont pas déjà des arrays
    if torch.is_tensor(features1):
        features1 = features1.numpy()
    if torch.is_tensor(features2):
        features2 = features2.numpy()
    
    # Calculer la similarité cosinus
    similarity = np.dot(features1, features2)
    
    return float(similarity)

# Fonction de débogage pour afficher les informations sur les tenseurs
def debug_tensor(tensor, name):
    print(f"\nDébug {name}:")
    print(f"Type: {type(tensor)}")
    print(f"Shape: {tensor.shape if hasattr(tensor, 'shape') else 'no shape'}")
    if torch.is_tensor(tensor):
        print(f"Device: {tensor.device}")

def display_features_info(features, source_name):
    print(f"\n{source_name} Features Information:")
    print(f"Shape: {features.shape}")
    print(f"Sample of first 5 features: {features.flatten()[:5]}")
    print(f"Min value: {features.min():.4f}")
    print(f"Max value: {features.max():.4f}")
    print(f"Mean value: {features.mean():.4f}")

def get_job_sections(text):
    """Identifie les différentes sections du texte de l'offre d'emploi"""
    section_markers = {
        'requirements': [
            "profil recherché", "profil souhaité", "compétences requises", "votre profil",
            "nous recherchons", "vous possédez", "vous maîtrisez", "vous devez",
            "compétences techniques", "prérequis", "requirements", "compétences",
            "expérience", "qualifications", "diplôme", "formation", "niveau"
        ],
        'duties': [
            "responsabilités", "missions", "tâches", "duties", "responsibilities", "fonctions",
            "description du poste", "objectifs", "activités", "role", "rôle"
        ],
        'skills': [
            "compétences", "skills", "qualifications", "aptitudes", "savoir-faire",
            "connaissances", "maîtrise", "expertise", "technologies", "outils",
            "environnement technique", "stack", "langages", "frameworks"
        ]
    }
    
    sections = {
        'requirements': [],
        'duties': [],
        'skills': []
    }
    
    # Découper le texte en paragraphes
    paragraphs = re.split(r'\n\s*\n', text.lower())
    
    # Debug
    print("\nDébug - Nombre de paragraphes trouvés:", len(paragraphs))
    
    for para in paragraphs:
        para = para.strip()
        if not para:  # Ignorer les paragraphes vides
            continue
            
        # Vérifier si le paragraphe correspond à une section
        for section_type, markers in section_markers.items():
            # Vérifier si le paragraphe contient un marqueur au début ou dans son contenu
            if any(marker in para.lower() for marker in markers):
                sections[section_type].append(para)
                break
    
    # Debug
    print("\nDébug - Sections trouvées:")
    for section, content in sections.items():
        print(f"\n{section}: {len(content)} paragraphes")
        if content:
            print("Premier paragraphe:", content[0][:100], "...")
    
    return sections

def extract_requirements(text):
    """Extrait les exigences/compétences obligatoires du texte de l'offre d'emploi"""
    # Prétraiter le texte
    text = text.lower().strip()
    
    # Séparer les sections
    sections = get_job_sections(text)
    
    # Debug
    print("\nDébug - Texte d'entrée:", text[:200], "...")
    
    # Marqueurs d'obligation plus étendus et organisés par catégorie
    markers = {
        'mandatory': [
            "obligatoire", "impératif", "requis", "required", "must", "indispensable",
            "nécessaire", "exigé", "maitrise", "maîtrise", "expertise", "avoir",
            "disposer de", "justifier de", "minimum"
        ],
        'preferred': [
            "souhaité", "apprécié", "serait un plus", "idéalement", "préférable",
            "optionnel", "optional", "nice to have", "bonus"
        ],
        'skills': [
            "compétence", "connaissance", "savoir", "capacité", "aptitude",
            "expérience", "skill", "ability", "proficiency"
        ]
    }
    
    # Structure pour stocker les requirements
    requirements = {
        'mandatory_tech': [],
        'optional_tech': [],
        'soft_skills': []
    }
    
    # Traiter chaque section pertinente
    relevant_sections = []
    for section_type in ['requirements', 'skills']:
        relevant_sections.extend(sections[section_type])
    
    # Si aucune section n'est trouvée, analyser tout le texte
    if not relevant_sections:
        relevant_sections = [text]
    
    # Debug
    print(f"\nDébug - Nombre de sections à analyser: {len(relevant_sections)}")
    
    # Traiter chaque section
    for section in relevant_sections:
        # Découper en phrases
        sentences = re.split(r'[.!?]+', section)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Vérifier les technologies
            tech_keywords = get_it_keywords()
            for category in ['languages', 'frameworks_libraries', 'dev_tools']:
                if isinstance(tech_keywords[category], list):
                    techs = tech_keywords[category]
                else:
                    techs = [item for sublist in tech_keywords[category].values() for item in sublist]
                
                for tech in techs:
                    if tech.lower() in sentence:
                        # Déterminer si c'est obligatoire
                        is_mandatory = any(marker in sentence for marker in markers['mandatory'])
                        is_preferred = any(marker in sentence for marker in markers['preferred'])
                        
                        if is_mandatory:
                            requirements['mandatory_tech'].append((tech, sentence))
                        elif not is_mandatory or is_preferred:
                            requirements['optional_tech'].append((tech, sentence))
            
            # Vérifier les soft skills
            for skill in [
                "autonome", "rigoureux", "organisé", "problem solving",
                "analytical", "team player", "agile", "scrum",
                "communication", "apprentissage", "veille technologique",
                "collaborer", "constructif", "améliorer", "esprit d'équipe", "motivé",
                "adaptabilité", "flexibilité", "initiative", "leadership"
            ]:
                if skill in sentence.lower():
                    requirements['soft_skills'].append((skill, sentence))
    
    # Debug final
    print("\nDébug - Requirements trouvés:")
    print(f"Mandatory tech: {len(requirements['mandatory_tech'])}")
    print(f"Optional tech: {len(requirements['optional_tech'])}")
    print(f"Soft skills: {len(requirements['soft_skills'])}")
    
    return requirements

def check_requirements_in_cv(cv_text, requirements):
    """Vérifie si les exigences sont présentes dans le CV avec une analyse plus précise"""
    cv_text = cv_text.lower()
    results = {
        'mandatory_matches': [],
        'mandatory_missing': [],
        'optional_matches': [],
        'optional_missing': [],
        'soft_skills_matches': []
    }
    
    def check_requirement(req, context):
        # Recherche plus flexible avec des variations possibles
        req_pattern = r'\b' + re.escape(req.lower()) + r'[es]?\b'
        found = bool(re.search(req_pattern, cv_text))
        
        # Vérifier aussi les synonymes courants pour certains termes
        synonyms = {
            'git': ['github', 'gitlab'],
            'javascript': ['js', 'ecmascript'],
            'python': ['py', 'python3'],
            # Ajouter d'autres synonymes selon besoin
        }
        
        if not found and req.lower() in synonyms:
            for syn in synonyms[req.lower()]:
                if syn in cv_text:
                    found = True
                    break
        
        if found:
            similarity = calculate_similarity_score(
                extract_features(req),
                extract_features(cv_text)
            )
        else:
            similarity = 0.0
        
        return found, similarity
    
    # Vérifier les compétences techniques obligatoires
    for tech, context in requirements['mandatory_tech']:
        found, similarity = check_requirement(tech, context)
        if found and similarity > 0.6:
            results['mandatory_matches'].append((tech, similarity, context))
        else:
            results['mandatory_missing'].append((tech, 0.0, context))
    
    # Vérifier les compétences techniques optionnelles
    for tech, context in requirements['optional_tech']:
        found, similarity = check_requirement(tech, context)
        if found and similarity > 0.6:
            results['optional_matches'].append((tech, similarity, context))
        else:
            results['optional_missing'].append((tech, 0.0, context))
    
    # Vérifier les soft skills
    for skill, context in requirements['soft_skills']:
        found, similarity = check_requirement(skill, context)
        if found and similarity > 0.5:  # Seuil plus bas pour les soft skills
            results['soft_skills_matches'].append((skill, similarity, context))
    
    return results

# ...existing code...

def get_it_keywords():
    """Retourne un dictionnaire enrichi des mots-clés IT par catégorie"""
    return {
        'languages': [
            # Langages généraux
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby',
            'golang', 'rust', 'kotlin', 'swift', 'scala', 'perl', 'matlab',
            # Langages web
            'html', 'html5', 'css', 'css3', 'sass', 'less',
            # SQL et requêtage
            'sql', 'plsql', 'tsql', 'nosql',
            # Langages Data Science - inclure R mais nécessite validation contextuelle
            #'r',
            # Scripting
            'bash', 'shell', 'powershell', 'vba', 'lua'
        ],
        'frameworks_libraries': {
            'frontend': [
                'react', 'angular', 'vue.js', 'svelte', 'jquery', 'bootstrap',
                'material-ui', 'tailwind', 'webpack', 'vite', 'next.js', 'nuxt'
            ],
            'backend': [
                'django', 'flask', 'fastapi', 'spring', 'spring boot', 'node.js',
                'express.js', 'laravel', 'symfony', '.net core', 'rails'
            ],
            'mobile': [
                'react native', 'flutter', 'ionic', 'xamarin', 'android sdk',
                'ios sdk', 'swift ui', 'jetpack compose'
            ],
            'testing': [
                'junit', 'pytest', 'jest', 'selenium', 'cypress', 'phpunit',
                'mocha', 'chai', 'karma'
            ]
        },
        'dev_tools': {
            'version_control': [
                'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial',
                'github actions', 'git flow', 'github desktop'
            ],
            'ide_editors': [
                'visual studio code', 'vscode', 'intellij', 'pycharm', 'eclipse',
                'android studio', 'xcode', 'sublime text', 'atom', 'vim', 'emacs'
            ],
            'project_tools': [
                'jira', 'confluence', 'trello', 'asana', 'notion',
                'azure devops', 'youtrack', 'linear'
            ],
            'ci_cd': [
                'jenkins', 'travis ci', 'circle ci', 'gitlab ci',
                'azure pipelines', 'teamcity', 'bamboo'
            ]
        }
    }

def is_valid_language_context(sentence):
    """Vérifie si le contexte indique qu'on parle de langages de programmation"""
    language_contexts = [
        "langage", "language", "programmation", "développement", "development",
        "code", "coding", "programming", "tech stack", "stack technique",
        "compétences techniques", "technical skills"
    ]
    return any(context in sentence.lower() for context in language_contexts)

def check_valid_tech_name(tech, sentence):
    """Vérifie si le nom de la technologie est valide en tenant compte du contexte"""
    # Cas spéciaux pour les technologies d'une seule lettre
    if len(tech) <= 1:
        # Pour 'R', vérifier si on parle de langages de programmation
        if tech.lower() == 'r' and is_valid_language_context(sentence):
            return True
        return False
    
    # Cas spéciaux pour C++ et C#
    if tech.lower() in ['c++', 'c#',"c"]:
        return True
        
    # Pour les autres technologies
    return len(tech) >= 2 and not tech.isdigit()

# ...existing code...

def analyze_tech_stack(text, cv_text):
    """Analyse détaillée de la stack technique"""
    text = text.lower()
    cv_text = cv_text.lower()
    tech_keywords = get_it_keywords()
    analysis = {
        'languages': [],
        'frameworks': {'frontend': [], 'backend': [], 'mobile': [], 'testing': []},
        'tools': {'version_control': [], 'ide_editors': [], 'project_tools': [], 'ci_cd': []}
    }
    
    def check_technology_presence(tech, text):
        """Vérifie plus précisément la présence d'une technologie"""
        # Éviter les faux positifs avec des mots partiels
        tech_pattern = r'\b' + re.escape(tech) + r'\b'
        exact_match = bool(re.search(tech_pattern, text))
        
        if exact_match:
            # Rechercher des indicateurs de niveau ou d'expérience
            context_pattern = r'(?:\w+\s+){0,3}' + re.escape(tech) + r'(?:\s+\w+){0,3}'
            context_matches = re.finditer(context_pattern, text)
            
            for match in context_matches:
                context = match.group(0).lower()
                # Détecter les négations ou limitations
                if any(neg in context for neg in ['pas', 'non', 'débutant', 'basic']):
                    return False, 0.3
                # Détecter les affirmations positives
                if any(pos in context for pos in ['expert', 'maîtrise', 'confirmé', 'avancé']):
                    return True, 0.9
            
            return True, 0.7
        return False, 0.0

    # Analyse des langages avec vérification précise
    for lang in tech_keywords['languages']:
        if lang in text.lower():
            found, base_similarity = check_technology_presence(lang, cv_text.lower())
            if found:
                similarity = calculate_similarity_score(
                    extract_features(lang),
                    extract_features(cv_text)
                )
                # Moyenne pondérée entre la similarité contextuelle et sémantique
                final_similarity = (base_similarity * 0.7 + similarity * 0.3)
            else:
                final_similarity = 0.0
                
            analysis['languages'].append({
                'name': lang,
                'required': True,
                'found_in_cv': found,
                'similarity': final_similarity
            })
    
    # Analyse des frameworks par catégorie
    for category, frameworks in tech_keywords['frameworks_libraries'].items():
        for framework in frameworks:
            if framework in text:
                in_cv = framework in cv_text
                similarity = calculate_similarity_score(
                    extract_features(framework),
                    extract_features(cv_text)
                ) if in_cv else 0
                analysis['frameworks'][category].append({
                    'name': framework,
                    'required': True,
                    'found_in_cv': in_cv,
                    'similarity': similarity
                })
    
    # Analyse des outils par catégorie
    for category, tools in tech_keywords['dev_tools'].items():
        for tool in tools:
            if tool in text:
                in_cv = tool in cv_text
                similarity = calculate_similarity_score(
                    extract_features(tool),
                    extract_features(cv_text)
                ) if in_cv else 0
                analysis['tools'][category].append({
                    'name': tool,
                    'required': True,
                    'found_in_cv': in_cv,
                    'similarity': similarity
                })
    
    return analysis

def display_tech_analysis(analysis):
    """Affiche l'analyse technique de manière formatée"""
    print("\n=== Analyse détaillée de la Stack Technique ===")
    
    def display_category(items, category_name):
        if items:
            total_score = sum(item['similarity'] for item in items)
            avg_score = total_score / len(items)
            print(f"\n{category_name} (Score moyen: {avg_score:.2f}):")
            for item in items:
                confidence = "Haute" if item['similarity'] > 0.8 else "Moyenne" if item['similarity'] > 0.5 else "Faible"
                status = "✓" if item['found_in_cv'] else "✗"
                print(f"{status} {item['name']} (match: {item['similarity']:.2f}, confiance: {confidence})")
    
    display_category(analysis['languages'], "🔤 Langages de programmation")
    for category, frameworks in analysis['frameworks'].items():
        if frameworks:
            print(f"\n  {category.title()}:")
            for fw in frameworks:
                status = "✓" if fw['found_in_cv'] else "✗"
                print(f"  {status} {fw['name']} (match: {fw['similarity']:.2f})")
    
    print("\n🛠️ Outils de développement:")
    for category, tools in analysis['tools'].items():
        if tools:
            print(f"\n  {category.replace('_', ' ').title()}:")
            for tool in tools:
                status = "✓" if tool['found_in_cv'] else "✗"
                print(f"  {status} {tool['name']} (match: {tool['similarity']:.2f})")

def calculate_global_score(tech_analysis, raw_similarity, requirements_matches, requirements_missing):
    """Calcule un score global basé sur tous les critères analysés avec pondération ajustée"""
    scores = {
        'general_match': raw_similarity,
        'tech_skills': 0.0,
        'requirements_match': 0.0
    }
    
    # Score des compétences techniques avec importance relative
    tech_scores = {
        'languages': [],
        'frameworks': [],
        'tools': []
    }
    
    # Pondération par catégorie
    category_weights = {
        'languages': 0.4,        # 40% pour les langages
        'frameworks': 0.35,      # 35% pour les frameworks
        'tools': 0.25           # 25% pour les outils
    }
    
    # Calcul des scores par catégorie
    for lang in tech_analysis['languages']:
        tech_scores['languages'].append(lang['similarity'] if lang['found_in_cv'] else 0)
    
    for category in tech_analysis['frameworks'].values():
        for fw in category:
            tech_scores['frameworks'].append(fw['similarity'] if fw['found_in_cv'] else 0)
    
    for category in tech_analysis['tools'].values():
        for tool in category:
            tech_scores['tools'].append(tool['similarity'] if tool['found_in_cv'] else 0)
    
    # Calcul du score technique pondéré
    for category, scores_list in tech_scores.items():
        if scores_list:
            scores['tech_skills'] += (sum(scores_list) / len(scores_list)) * category_weights[category]
    
    # Score des exigences générales
    total_reqs = len(requirements_matches) + len(requirements_missing)
    if total_reqs > 0:
        match_scores = [score for _, score in requirements_matches]
        missing_scores = [score for _, score in requirements_missing]
        all_scores = match_scores + missing_scores
        scores['requirements_match'] = sum(all_scores) / total_reqs
    
    # Calcul du score global pondéré
    weights = {
        'general_match': 0.2,      # 20% pour la similarité générale
        'tech_skills': 0.5,        # 50% pour les compétences techniques
        'requirements_match': 0.3   # 30% pour les autres exigences
    }
    
    global_score = sum(score * weights[key] for key, score in scores.items())
    
    return global_score, scores

def display_final_score(global_score, detailed_scores):
    """Affiche le score final et les détails"""
    print("\n📊 === Résumé des Scores ===")
    print(f"\nScore Global: {global_score:.2%}")
    print("\nDétail des scores:")
    print(f"- Similarité générale: {detailed_scores['general_match']:.2%}")
    print(f"- Compétences techniques: {detailed_scores['tech_skills']:.2%}")
    print(f"- Correspondance aux exigences: {detailed_scores['requirements_match']:.2%}")
    
    # Interprétation du score
    if global_score >= 0.8:
        print("\n✨ Excellent match! Profil très adapté au poste.")
    elif global_score >= 0.6:
        print("\n👍 Bon match! Profil intéressant pour le poste.")
    elif global_score >= 0.4:
        print("\n💡 Match moyen. Certaines compétences à développer.")
    else:
        print("\n⚠️ Match faible. Profil peu adapté au poste.")

def analyze_it_requirements(text):
    """Analyse les exigences IT spécifiques dans le texte"""
    text = text.lower()
    tech_keywords = get_it_keywords()
    requirements = {
        'languages': [],
        'frameworks': [],
        'tools': []
    }
    
    # Vérifier les langages
    for lang in tech_keywords['languages']:
        if lang in text:
            requirements['languages'].append(lang)
    
    # Vérifier les frameworks de toutes les catégories
    for category, frameworks in tech_keywords['frameworks_libraries'].items():
        for framework in frameworks:
            if framework in text:
                requirements['frameworks'].append(framework)
    
    # Vérifier les outils de toutes les catégories
    for category, tools in tech_keywords['dev_tools'].items():
        for tool in tools:
            if tool in text:
                requirements['tools'].append(tool)
    
    return requirements

def analyze_missing_skills(job_text, cv_text, tech_analysis, req_results):
    """Analyse et liste tous les éléments demandés dans l'offre mais absents du CV"""
    missing_elements = {
        'mandatory': [],    # Compétences obligatoires manquantes
        'optional': [],     # Compétences optionnelles manquantes
        'technologies': {   # Technologies manquantes par catégorie
            'languages': [],
            'frameworks': [],
            'tools': []
        }
    }
    
    # Ajouter les compétences obligatoires manquantes
    for tech, _, context in req_results['mandatory_missing']:
        missing_elements['mandatory'].append({
            'skill': tech,
            'context': context.strip()
        })
    
    # Ajouter les compétences optionnelles manquantes
    for tech, _, context in req_results['optional_missing']:
        missing_elements['optional'].append({
            'skill': tech,
            'context': context.strip()
        })
    
    # Ajouter les technologies manquantes
    for lang in tech_analysis['languages']:
        if not lang['found_in_cv'] and lang['required']:
            missing_elements['technologies']['languages'].append(lang['name'])
    
    for category in tech_analysis['frameworks'].values():
        for fw in category:
            if not fw['found_in_cv'] and fw['required']:
                missing_elements['technologies']['frameworks'].append(fw['name'])
    
    for category in tech_analysis['tools'].values():
        for tool in category:
            if not tool['found_in_cv'] and tool['required']:
                missing_elements['technologies']['tools'].append(tool['name'])
    
    return missing_elements

def display_missing_skills(missing_elements):
    """Affiche les éléments manquants de manière structurée"""
    print("\n🔍 === Éléments manquants dans le CV ===")
    
    if missing_elements['mandatory']:
        print("\n❗ Compétences obligatoires manquantes:")
        for item in missing_elements['mandatory']:
            print(f"  • {item['skill']}")
            print(f"    Contexte: \"{item['context']}\"")
    
    if missing_elements['optional']:
        print("\n⚠️ Compétences optionnelles manquantes:")
        for item in missing_elements['optional']:
            print(f"  • {item['skill']}")
    
    print("\n🔧 Technologies manquantes:")
    tech_categories = missing_elements['technologies']
    
    if tech_categories['languages']:
        print("\n  Langages:")
        for lang in tech_categories['languages']:
            print(f"  • {lang}")
    
    if tech_categories['frameworks']:
        print("\n  Frameworks:")
        for fw in tech_categories['frameworks']:
            print(f"  • {fw}")
    
    if tech_categories['tools']:
        print("\n  Outils:")
        for tool in tech_categories['tools']:
            print(f"  • {tool}")

def get_cv_metadata():
    """Retourne les informations supplémentaires sur le CV"""
    return {
        'age': 56,  # Exemple d'âge en dur
        # Ajouter d'autres informations si nécessaire
    }

def analyze_age_compatibility(cv_metadata, job_text):
    """Analyse la compatibilité de l'âge avec les exigences du poste"""
    age = cv_metadata.get('age', None)
    if age is None:
        return "Age information not provided."
    
    # Exemple de critères d'âge dans l'offre d'emploi
    age_criteria = re.findall(r'\b(\d{2})\s*ans\b', job_text.lower())
    if not age_criteria:
        return "No specific age criteria found in the job description."
    
    age_criteria = [int(age) for age in age_criteria]
    min_age = min(age_criteria)
    max_age = max(age_criteria)
    
    if min_age <= age <= max_age:
        return f"Age {age} is within the acceptable range ({min_age}-{max_age})."
    else:
        return f"Age {age} is outside the acceptable range ({min_age}-{max_age})."

def list_missing_requirements(req_results):
    """Liste les exigences manquantes dans le CV"""
    missing_requirements = {
        'mandatory': [],
        'optional': []
    }
    
    for tech, _, context in req_results['mandatory_missing']:
        missing_requirements['mandatory'].append({
            'skill': tech,
            'context': context.strip()
        })
    
    for tech, _, context in req_results['optional_missing']:
        missing_requirements['optional'].append({
            'skill': tech,
            'context': context.strip()
        })
    
    return missing_requirements

def display_missing_requirements(missing_requirements):
    """Affiche les exigences techniques sous forme de tableau avec leur contexte"""
    print("\n🔍 === Analyse des Exigences Techniques ===")
    
    def print_requirements_table(requirements, title):
        if not requirements:
            return
            
        max_skill_length = max(len(item['skill']) for item in requirements)
        max_skill_length = max(max_skill_length, 15)  # Minimum 15 caractères
        
        # Calculer la largeur totale du tableau
        total_width = max_skill_length + 50  # 50 caractères pour le contexte
        
        # En-tête du tableau
        print(f"\n{title}")
        print("┌" + "─" * (max_skill_length + 2) + "┬" + "─" * 52 + "┐")
        print(f"│ {'Compétence'.ljust(max_skill_length)} │ {'Contexte'.ljust(50)} │")
        print("├" + "─" * (max_skill_length + 2) + "┼" + "─" * 52 + "┤")
        
        # Contenu du tableau
        for item in sorted(requirements, key=lambda x: x['skill']):
            skill = item['skill'].ljust(max_skill_length)
            # Tronquer le contexte si nécessaire et ajouter ...
            context = item['context'][:47] + "..." if len(item['context']) > 47 else item['context'].ljust(50)
            print(f"│ {skill} │ {context} │")
        
        # Pied du tableau
        print("└" + "─" * (max_skill_length + 2) + "┴" + "─" * 52 + "┘")
    
    print_requirements_table(missing_requirements['mandatory'], "❗ Compétences Obligatoires Manquantes")
    print_requirements_table(missing_requirements['optional'], "⚠️ Compétences Optionnelles Manquantes")

def list_missing_soft_skills(req_results):
    """Liste les soft skills manquants dans le CV"""
    missing_soft_skills = []
    
    # On ajoute tous les soft skills qui ne sont PAS dans soft_skills_matches
    all_soft_skills = [
        "autonome", "rigoureux", "organisé", "problem solving",
        "analytical", "team player", "agile", "scrum",
        "communication", "apprentissage", "veille technologique",
        "collaborer", "constructif", "améliorer", "esprit d'équipe", "motivé",
        "adaptabilité", "flexibilité", "initiative", "leadership"
    ]
    
    # Obtenir les soft skills trouvés
    found_skills = [skill for skill, _, _ in req_results['soft_skills_matches']]
    
    # Identifier les soft skills manquants
    for skill in all_soft_skills:
        if skill not in found_skills:
            missing_soft_skills.append({
                'skill': skill,
                'context': "Soft skill requis non trouvé dans le CV"
            })
    
    return missing_soft_skills

def display_missing_soft_skills(missing_soft_skills):
    """Affiche les soft skills sous forme de tableau avec statut trouvé/non trouvé"""
    print("\n🔍 === Analyse des Soft Skills ===")
    print("\n┌─────────────────────────┬──────────┐")
    print("│ Soft Skill              │ Statut   │")
    print("├─────────────────────────┼──────────┤")
    
    # Liste complète des soft skills
    all_soft_skills = [
        "autonome", "rigoureux", "organisé", "problem solving",
        "analytical", "team player", "agile", "scrum",
        "communication", "apprentissage", "veille technologique",
        "collaborer", "constructif", "améliorer", "esprit d'équipe", "motivé",
        "adaptabilité", "flexibilité", "initiative", "leadership"
    ]
    
    # Créer un ensemble des soft skills manquants pour une recherche plus rapide
    missing_skills_set = {item['skill'] for item in missing_soft_skills}
    
    # Afficher chaque soft skill avec son statut
    for skill in sorted(all_soft_skills):
        # Padding du nom de la compétence pour l'alignement
        skill_padded = skill.ljust(21)
        # Symbole ✓ si trouvé, ✗ si manquant
        status = "✗ Absent" if skill in missing_skills_set else "✓ Présent"
        status_padded = status.ljust(8)
        print(f"│ {skill_padded} │ {status_padded} │")
    
    print("└─────────────────────────┴──────────┘")

def display_analysis_results(cv_text, job_text, raw_similarity, adjusted_similarity, 
                           requirements, req_results, tech_analysis, global_score, 
                           detailed_scores, missing_elements, cv_metadata):
    """Affiche les résultats d'analyse de manière structurée et hiérarchisée"""
    
    print("\n====================================================")
    print("📊 ANALYSE DE COMPATIBILITÉ CV-OFFRE D'EMPLOI")
    print("====================================================")
    
    # 1. Score global et résumé
    print("\n1️⃣ RÉSUMÉ GÉNÉRAL")
    print("------------------")
    
    print(f"Similarité brute: {raw_similarity:.2%}")
    print(f"Similarité ajustée: {adjusted_similarity:.2%}")
    print(f"Score global: {global_score:.2%}")
    
    # 2. Compétences techniques
    print("\n2️⃣ COMPÉTENCES TECHNIQUES")
    print("-------------------------")
    print("Obligatoires:")
    print(f"✓ Trouvées: {len(req_results['mandatory_matches'])}")
    print(f"✗ Manquantes: {len(req_results['mandatory_missing'])}")
    
    if requirements['mandatory_tech']:
        print("\nDétail des technologies obligatoires:")
        for tech, context in requirements['mandatory_tech']:
            match_status = "✓" if any(t[0] == tech for t in req_results['mandatory_matches']) else "✗"
            print(f"{match_status} {tech}")
    
    # 3. Stack technique
    print("\n3️⃣ STACK TECHNIQUE")
    print("------------------")
    
    # Langages
    found_langs = [lang for lang in tech_analysis['languages'] if lang['found_in_cv']]
    missing_langs = [lang for lang in tech_analysis['languages'] if not lang['found_in_cv']]
    
    print(f"\nLangages: {len(found_langs)}/{len(tech_analysis['languages'])}")
    if found_langs:
        print("Trouvés:")
        for lang in found_langs:
            print(f"✓ {lang['name']} ({lang['similarity']:.2%})")
    if missing_langs:  # Ajout de l'affichage des langages manquants
        print("\nManquants:")
        for lang in missing_langs:
            print(f"✗ {lang['name']}")

    # 4. Compétences comportementales
    print("\n4️⃣ SOFT SKILLS")
    print("-------------")
    print(f"Trouvés: {len(req_results['soft_skills_matches'])}")
    for skill, score, _ in req_results['soft_skills_matches']:
        print(f"• {skill} ({score:.2%})")
    
    # 5. Points d'amélioration
    print("\n5️⃣ POINTS D'AMÉLIORATION")
    print("----------------------")
    if missing_elements['mandatory']:
        print("\nPrioritaires:")
        for item in missing_elements['mandatory']:
            print(f"! {item['skill']}")
    
    # 6. Recommandation finale
    print("\n6️⃣ RECOMMANDATION")
    print("----------------")
    if global_score >= 0.8:
        print("✨ Excellent match! Profil très adapté au poste.")
    elif global_score >= 0.6:
        print("👍 Bon match! Profil intéressant pour le poste.")
    elif global_score >= 0.4:
        print("💡 Match moyen. Certaines compétences à développer.")
    else:
        print("⚠️ Match faible. Profil peu adapté au poste.")

# Ajouter après la définition de EMBEDDING_CACHE et cached_extract_features

def process_tech_batch(batch_data):
    """Traite un lot de technologies en parallèle"""
    tech, cv_text, text = batch_data
    tech_pattern = r'\b' + re.escape(tech.lower()) + r'\b'
    found = bool(re.search(tech_pattern, cv_text.lower()))
    
    if found:
        similarity = calculate_similarity_score(
            cached_extract_features(tech),
            cached_extract_features(cv_text)
        )
        return {
            'name': tech,
            'required': True,
            'found_in_cv': True,
            'similarity': similarity
        }
    return {
        'name': tech,
        'required': True,
        'found_in_cv': False,
        'similarity': 0.0
    }

def optimize_analyze_tech_stack(text: str, cv_text: str) -> Dict:
    """Version optimisée de analyze_tech_stack utilisant le traitement parallèle"""
    text = text.lower()
    cv_text = cv_text.lower()
    tech_keywords = get_it_keywords()
    
    def process_category(items):
        batch_data = [(item, cv_text, text) for item in items if item.lower() in text.lower()]
        if not batch_data:
            return []
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_tech_batch, batch_data))
        return [r for r in results if r is not None]
    
    # Traitement des différentes catégories en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Lancer l'analyse des langages
        languages_future = executor.submit(process_category, tech_keywords['languages'])
        
        # Lancer l'analyse des frameworks
        frameworks_futures = {
            category: executor.submit(process_category, frameworks)
            for category, frameworks in tech_keywords['frameworks_libraries'].items()
        }
        
        # Lancer l'analyse des outils
        tools_futures = {
            category: executor.submit(process_category, tools)
            for category, tools in tech_keywords['dev_tools'].items()
        }
        
        # Récupérer les résultats
        analysis = {
            'languages': languages_future.result(),
            'frameworks': {
                category: future.result()
                for category, future in frameworks_futures.items()
            },
            'tools': {
                category: future.result()
                for category, future in tools_futures.items()
            }
        }
    
    return analysis

def optimize_check_requirements_in_cv(cv_text: str, requirements: Dict) -> Dict:
    """Version optimisée de check_requirements_in_cv utilisant le traitement parallèle"""
    cv_text = cv_text.lower()
    results = {
        'mandatory_matches': [],
        'mandatory_missing': [],
        'optional_matches': [],
        'optional_missing': [],
        'soft_skills_matches': []
    }
    
    def check_batch(items, is_mandatory=True, is_soft_skill=False):
        threshold = 0.5 if is_soft_skill else 0.6
        matches = []
        missing = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for tech, context in items:
                futures.append(
                    executor.submit(check_single_requirement, tech, context, cv_text, threshold)
                )
            
            for future, (tech, context) in zip(futures, items):
                found, similarity = future.result()
                if found:
                    matches.append((tech, similarity, context))
                else:
                    missing.append((tech, 0.0, context))
        
        return matches, missing
    
    def check_single_requirement(tech, context, cv_text, threshold):
        req_pattern = r'\b' + re.escape(tech.lower()) + r'[es]?\b'
        found = bool(re.search(req_pattern, cv_text))
        
        # Vérifier les synonymes
        synonyms = {
            'git': ['github', 'gitlab'],
            'javascript': ['js', 'ecmascript'],
            'python': ['py', 'python3'],
        }
        
        if not found and tech.lower() in synonyms:
            found = any(syn in cv_text for syn in synonyms[tech.lower()])
        
        if found:
            similarity = calculate_similarity_score(
                cached_extract_features(tech),
                cached_extract_features(cv_text)
            )
            return found, similarity if similarity > threshold else 0.0
        return False, 0.0
    
    # Traitement parallèle des différentes catégories
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Lancer les analyses en parallèle
        mandatory_future = executor.submit(check_batch, requirements['mandatory_tech'])
        optional_future = executor.submit(check_batch, requirements['optional_tech'], False)
        soft_skills_future = executor.submit(
            check_batch, requirements['soft_skills'], False, True
        )
        
        # Récupérer les résultats
        results['mandatory_matches'], results['mandatory_missing'] = mandatory_future.result()
        results['optional_matches'], results['optional_missing'] = optional_future.result()
        matches, _ = soft_skills_future.result()
        results['soft_skills_matches'] = matches
    
    return results

# Modifier le main pour utiliser cette nouvelle fonction
if __name__ == "__main__":
    
    try:
        # Test paths
        cv_path = "G:/OneDrive/Entreprendre/CV/persona/IngeEtudeDev/CV_Cyril_SAURET_Ingé-Etudes-Dev_ind1.pdf"
        job_path = "G:/OneDrive/Entreprendre/Actions-4/M433/M433_annonce_.pdf"
        
        print("1. Extracting text from PDFs...")
        cv_text1 = extract_text_from_pdf(cv_path)
        job_text1 = extract_text_from_pdf(job_path)
        #print(job_text1)
        
        q1_cv="peux tu me faire un plan détaillé du cv avec les rubriques : "
        q1_cv+="-Titre CV,"
        q1_cv+= "-Expériences professionnelles avec [qu'elle entreprise, les dates de début et fin (calcule la durée), les taches décrites]," 
        q1_cv+="- Formations,"
        q1_cv+="- les outils [style github,Visualcode..],"
        q1_cv+="- Langages informatique,"
        q1_cv+="- savoir-être," 
        q1_cv+="- méthodologie,"
        q1_cv+="- base de données,"
        cv_text = get_answer(q1_cv,cv_text1)
        print (cv_text)
        q2_job="peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :"
        q2_job+="- Titre poste proposé "
        q2_job+="- Description du poste décomposée en tache ou responsabilité "
        q2_job+="- requirements (expérience attendues, ),"
        q2_job+="- skills (languages, outils obligatoires),"
        q2_job+="- duties  (fonctions ou taches que le salarier devra savoir faire),"
        q2_job+="- Savoir-être (soft skill),"
        q2_job+="- autres (toutes informations autre utile à connaitre)"
        job_text = get_answer(q2_job,job_text1)
        print (job_text)
        if not cv_text or not job_text:
            raise ValueError("Could not extract text from one or both PDFs")
            
        print("\n2. Extracting features...")
        cv_features = extract_features(cv_text)
        job_features = extract_features(job_text)
        
        # Afficher les informations sur les features
        #display_features_info(cv_features, "CV")
        #display_features_info(job_features, "Job Description")
        
        print("\n3. Computing similarity...")
        raw_similarity = cosine_similarity(cv_features, job_features)
        adjusted_similarity = calculate_similarity_score(cv_features, job_features)
        
        print(f"\nResults:")
        print(f"Raw similarity score: {raw_similarity:.4f}")
        print(f"Adjusted similarity score: {adjusted_similarity:.4f}")
        
        # Optional: Print first few characters of extracted text
        #print("\nExtracted text samples:")
        #print(f"CV (first 100 chars): {cv_text[:100]}...")
        #print(f"Job (first 100 chars): {job_text[:100]}...")
        
        print("\n4. Analyzing specific requirements...")
        requirements = extract_requirements(job_text)
        req_results = optimize_check_requirements_in_cv(cv_text, requirements)
        # Display requirements analysis
        print("\nRequirements Analysis:")
        print(f"Mandatory Matches: {len(req_results['mandatory_matches'])}")
        print(f"Mandatory Missing: {len(req_results['mandatory_missing'])}")
        print(f"Optional Matches: {len(req_results['optional_matches'])}")
        print(f"Optional Missing: {len(req_results['optional_missing'])}")
        print(f"Soft Skills Matches: {len(req_results['soft_skills_matches'])}")
        print("\nDétail des requirements trouvés:")
        for tech, context in requirements['mandatory_tech']:
            print(f"\nTechnologie obligatoire: {tech}")
            print(f"Contexte: {context}")

        for tech, context in requirements['optional_tech']:
            print(f"\nTechnologie optionnelle: {tech}")
            print(f"Contexte: {context}")
        
        print("\n5. Analyzing age compatibility...")
        cv_metadata = get_cv_metadata()
        age_compatibility = analyze_age_compatibility(cv_metadata, job_text)
        print("\nAge Analysis:")
        print(age_compatibility)
        
        print("\n6. Analyzing IT-specific requirements...")
        it_requirements = analyze_it_requirements(job_text)
        
        print("\nIT Skills Requirements Analysis:")
        for category, skills in it_requirements.items():
            if skills:
                print(f"\n{category.title()}:")
                for skill in skills:
                    skill_features = extract_features(skill)
                    cv_features = extract_features(cv_text)
                    similarity = calculate_similarity_score(skill_features, cv_features)
                    
                    status = "✓" if similarity > 0.6 else "✗"
                    print(f"{status} {skill} (match: {similarity:.2f})")
        
        print("\n7. Analyzing detailed tech stack...")
        tech_analysis = optimize_analyze_tech_stack(job_text, cv_text)
        display_tech_analysis(tech_analysis)
        
        print("\n8. Calculating global score...")
        global_score, detailed_scores = calculate_global_score(
            tech_analysis, 
            raw_similarity,
            [(req, score) for req, score, _ in req_results['mandatory_matches']],
            [(req, 0.0) for req, _, _ in req_results['mandatory_missing']]
        )
        display_final_score(global_score, detailed_scores)
        
        print("\n9. Analyzing missing skills...")
        missing_elements = analyze_missing_skills(job_text, cv_text, tech_analysis, req_results)
        display_missing_skills(missing_elements)
        
        # Include CV metadata in the analysis
        print("\n10. CV Metadata Analysis:")
        print(f"Age: {cv_metadata['age']}")
        
        print("\n11. Listing missing requirements...")
        missing_requirements = list_missing_requirements(req_results)
        display_missing_requirements(missing_requirements)
        
        print("\n12. Listing missing soft skills...")
        missing_soft_skills = list_missing_soft_skills(req_results)
        display_missing_soft_skills(missing_soft_skills)

        # Affichage des résultats
        display_analysis_results(
            cv_text, job_text, raw_similarity, adjusted_similarity,
            requirements, req_results, tech_analysis, global_score,
            detailed_scores, missing_elements, cv_metadata
        )

    except Exception as e:
        print(f"Error during execution: {str(e)}")
