def json_to_pdf(json_file_path, pdf_output=None, title="Conversion JSON"):
    """
    Fonction générique pour convertir n'importe quel fichier JSON en PDF bien formaté.
    Gère automatiquement les hiérarchies, listes et types de données variés.
    
    Args:
        json_file_path (str): Chemin vers le fichier JSON
        pdf_output (str): Chemin pour le fichier PDF de sortie (optionnel)
        title (str): Titre du document PDF
    """
    import os
    import json
    import logging
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    try:
        # Déterminer le nom du fichier PDF de sortie
        if pdf_output is None:
            pdf_output = os.path.splitext(json_file_path)[0] + ".pdf"
        
        # Lire le fichier JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            pdf_output,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()

        # Ajouter des styles personnalisés uniquement s'ils n'existent pas déjà
        if 'Title' not in styles:
            styles.add(ParagraphStyle(
                name='Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.darkblue
            ))
        else:
            # Modifier le style existant
            styles['Title'].fontSize = 18
            styles['Title'].spaceAfter = 12
            styles['Title'].textColor = colors.darkblue

        if 'Heading2Custom' not in styles:
            styles.add(ParagraphStyle(
                name='Heading2Custom',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.darkblue
            ))

        if 'NormalCustom' not in styles:
            styles.add(ParagraphStyle(
                name='NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ))

        if 'List' not in styles:
            styles.add(ParagraphStyle(
                name='List',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=20,
                spaceAfter=3
            ))
        
        # Contenu du PDF
        story = []
        
        # Titre
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 0.5*cm))
        
        # Fonction récursive pour traiter n'importe quelle structure JSON
        def process_json_object(obj, level=0, key=None):
            elements = []
            
            # Pour un titre de section éventuel
            if key and level <= 2:  # Limiter à 3 niveaux de titres
                style_name = 'Title' if level == 0 else 'Heading2Custom'
                elements.append(Paragraph(str(key), styles[style_name]))
                elements.append(Spacer(1, 0.3*cm))
            elif key:
                elements.append(Paragraph(f"<b>{str(key)}:</b>", styles['NormalCustom']))
            
            # Traitement selon le type de l'objet
            if isinstance(obj, dict):
                # C'est un dictionnaire
                for k, v in obj.items():
                    # Appel récursif pour chaque valeur
                    child_elements = process_json_object(v, level + 1, k)
                    elements.extend(child_elements)
                    elements.append(Spacer(1, 0.2*cm))
                    
            elif isinstance(obj, list):
                # C'est une liste - convertir en liste à puces
                list_items = []
                
                for item in obj:
                    if isinstance(item, (dict, list)):
                        # Pour les objets complexes dans la liste
                        sub_elements = process_json_object(item, level + 1)
                        # Créer un contenu composite pour l'élément de liste
                        if sub_elements:
                            # Prendre seulement le premier élément comme texte de la puce
                            if isinstance(sub_elements[0], Paragraph):
                                list_items.append(ListItem(sub_elements[0]))
                            else:
                                list_items.append(ListItem(Paragraph(str(item), styles['List'])))
                            # Ajouter les autres éléments après la liste à puces
                            elements.extend(sub_elements[1:])
                    else:
                        # Pour les éléments simples
                        list_items.append(ListItem(Paragraph(str(item), styles['List'])))
                
                if list_items:
                    elements.append(ListFlowable(list_items, bulletType='bullet', start=None))
                    
            else:
                # C'est une valeur simple
                if key is None:  # C'est un élément de liste déjà formaté
                    elements.append(Paragraph(str(obj), styles['NormalCustom']))
            
            return elements
        
        # Traiter l'ensemble des données JSON
        story.extend(process_json_object(data))
        
        # Générer le PDF
        doc.build(story)
        
        logging.info(f"PDF généré avec succès: {pdf_output}")
        return pdf_output
        
    except Exception as e:
        logging.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return None