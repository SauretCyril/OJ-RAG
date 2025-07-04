         # Si des filtres par nom sont actifs, vérifier si le fichier correspond à au moins un des motifs
                #if active_name_filters:
                    # Par défaut, on exclut le fichier s'il ne correspond à aucun filtre actif
                # should_display = False
                     # Vérifier s'il y a des filtres par nom actifs
            #active_name_filters = {name: info['pattern'] for name, info in self.NAME_FILTERS.items() 
            #    if self.active_filters.get(name, False)}
            # 
             
                # # Vérifier si le fichier correspond à au moins un des motifs de filtres actifs
                # for filter_name, pattern in active_name_filters.items():
                #     if pattern in item:
                #         should_display = True
                #         break
                    
                #     # Si le fichier ne correspond à aucun filtre actif, passer au suivant
                # if not should_display:
                #     continue
                      # CORRECTION : Vérifier si on est en mode explorateur spécialisé
                if self.explorer_type != "standard":
                 # En mode spécialisé, on n'affiche que les fichiers du groupe correspondant
                 # Le groupe actif a déjà été défini dans customize_by_type()
                #  group_for_type = None
                #  for group_name, group_info in self.FILE_GROUPS.items():
                #      if file_type in group_info['types']:
                #          group_for_type = group_name
                #          break
            #     print (f"<FILE> fichier {item}: => {group_for_type}")
            #     # Afficher uniquement si le fichier appartient au groupe associé au type d'explorateur
            #     if group_for_type == self.explorer_type or (
            #         self.explorer_type == "document" and group_for_type == "Documents") or (
            #         self.explorer_type == "config" and group_for_type == "Configuration") or (
            #         self.explorer_type == "data" and group_for_type == "Données") or (
            #         self.explorer_type == "IA" and group_for_type == "IA"):
            #         self.tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], 
            #                         tags=(f"color_{color.replace('#', '')}",))
            # else:
                # En mode standard, on utilise les filtres actifs normalement
                # is_in_active_group = False
                # for group_name, group_info in self.FILE_GROUPS.items():
                #     if file_type in group_info['types'] and self.active_filters.get(group_name, False):
                #         is_in_active_group = True
                #         break
                
                # if is_in_active_group: