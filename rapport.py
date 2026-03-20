"""
Module rapport.py

Gère la génération et la sauvegarde de rapports d'analyse au format JSON.
Conçu pour être utilisé de pair avec des modules d'analyse (ex: analyser.py)
en respectant un contrat de données strict défini via TypedDict.
"""

import json
import logging
import os
import platform
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


# ============================================================================
# CONTRATS DE DONNÉES (INTERFACES)
# ============================================================================

class StatistiquesNiveaux(TypedDict):
    """Représente les statistiques par niveau de gravité de log."""
    ERROR: int
    WARN: int
    INFO: int


class DonneesAnalyse(TypedDict, total=False):
    """
    Structure stricte attendue pour les données d'analyse brutes.
    Ce contrat garantit la consistance des données entre l'analyseur
    et le générateur de rapport.
    """
    total_lignes: int
    par_niveau: StatistiquesNiveaux
    top5_erreurs: List[str]
    fichiers: List[str]


# ============================================================================
# FONCTIONS UTILITAIRES PRIVÉES
# ============================================================================

def _obtenir_metadonnees_systeme(source: str) -> Dict[str, str]:
    """
    Récupère les métadonnées de l'environnement d'exécution de manière sécurisée.

    Args:
        source (str): Le chemin ou nom de la source analysée (fichiers logs).

    Returns:
        Dict[str, str]: Un dictionnaire structuré des métadonnées système.
    """
    date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Récupération résiliente de l'utilisateur actif (Windows et Linux/Mac)
    utilisateur = os.environ.get("USERNAME") or os.environ.get("USER") or "inconnu"
    systeme_os = platform.system() or "inconnu"
    
    return {
        "date": date_actuelle,
        "utilisateur": utilisateur,
        "os": systeme_os,
        "source": source
    }


def _construire_structure_json(data: DonneesAnalyse, source: str) -> Dict[str, Any]:
    """
    Construit la structure arborescente finale du dictionnaire pour l'export.

    Args:
        data (DonneesAnalyse): Les données brutes respectant le contrat.
        source (str): L'origine des données pour historisation.

    Returns:
        Dict[str, Any]: Le dictionnaire formaté et prêt à être sérialisé en JSON.
    """
    return {
        "metadata": _obtenir_metadonnees_systeme(source),
        "statistiques": {
            "total_lignes": data.get("total_lignes", 0),
            "par_niveau": data.get("par_niveau", {
                "ERROR": 0,
                "WARN": 0,
                "INFO": 0
            }),
            "top5_erreurs": data.get("top5_erreurs", [])
        },
        "fichiers_traites": data.get("fichiers", [])
    }


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

def generer_rapport(data: DonneesAnalyse, source: str) -> Optional[bool]:
    """
    Génère et sauvegarde un fichier JSON structuré, encapsulant l'analyse des logs.
    
    Le fichier est stocké de manière absolue et automagique dans un 
    sous-dossier '/rapports/', qui sera créé si inexistant. Le fichier
    sera encodé en UTF-8 pour garantir l'intégrité des données textuelles.

    Args:
        data (DonneesAnalyse): Le dictionnaire brut extrait par l'analyseur.
        source (str): L'identifiant (chemin) des logs qui ont été traités.

    Returns:
        Optional[bool]: True si le fichier a été généré avec succès.
                        None en cas d'erreur de permission, E/S ou de format.
    """
    # 1. Validation de l'intégrité des entrées
    if not isinstance(data, dict):
        logging.error("Échec de la génération : L'argument 'data' doit être un dictionnaire.")
        return None
        
    if not source:
        logging.error("Échec de la génération : L'argument 'source' est vide.")
        return None

    # 2. Formatage des données
    donnees_finales = _construire_structure_json(data, source)

    # 3. Résolution des chemins de destination absolus
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    dossier_rapports = os.path.join(dossier_script, "rapports")
    
    date_jour = datetime.now().strftime("%Y-%m-%d")
    nom_fichier = f"rapport_{date_jour}.json"
    chemin_sortie = os.path.join(dossier_rapports, nom_fichier)

    # 4. Pré-requis matériels (Création ou vérification d'existence du dossier)
    try:
        if not os.path.exists(dossier_rapports):
            os.makedirs(dossier_rapports)
    except PermissionError as e:
        logging.error(f"Échec : Permission refusée pour créer le dossier '{dossier_rapports}'. {e}")
        return None

    # 5. Sérialisation et écriture physique
    try:
        with open(chemin_sortie, 'w', encoding='utf-8') as f:
            json.dump(donnees_finales, f, indent=4, ensure_ascii=False)
            
        logging.info(f"Rapport généré avec succès : {os.path.abspath(chemin_sortie)}")
        return True
        
    except PermissionError as e:
        logging.error(f"Échec de la sauvegarde JSON : Droit d'écriture manquant. {e}")
        return None
    except IOError as e:
        logging.error(f"Échec de la sauvegarde JSON : Erreur disque/réseau. {e}")
        return None
    except TypeError as e:
        logging.error(f"Échec de la sauvegarde JSON : Données fournies non compatibles JSON. {e}")
        return None
    except Exception as e:
        logging.error(f"Échec de la sauvegarde JSON : Erreur inattendue. {e}")
        return None


# ============================================================================
# POINT D'ENTRÉE LOCAL (TESTING INTENSIF)
# ============================================================================

if __name__ == "__main__":
    import time
    
    # On force un affichage clair dans la console pour le test
    logging.basicConfig(level=logging.INFO, format="> %(message)s")
    
    print("\n" + "="*60)
    print("🚀 DÉMARRAGE DU TEST DU MODULE RAPPORT.PY 🚀")
    print("="*60 + "\n")
    
    print("[1/3] Construction des données fictives (simulation d'analyser.py)...")
    # Simulation des données respectant strictement le contrat DonneesAnalyse
    data_test: DonneesAnalyse = {
        "total_lignes": 1542,
        "par_niveau": {"ERROR": 12, "WARN": 45, "INFO": 1485},
        "top5_erreurs": ["Connection Refused", "Timeout API", "Disk Full"],
        "fichiers": ["app1.log", "app2.log", "auth.log"]
    }
    time.sleep(0.5)
    print("      ✓ Données générées avec succès.")
    
    # Le chemin vers le dossier logs demandé
    dossier_logs = "log/fichiers_serveur/"
    print(f"\n[2/3] Configuration du dossier source : '{dossier_logs}'")
    time.sleep(0.5)
    print("      ✓ Source configurée.")
    
    print("\n[3/3] Lancement de la génération du rapport via generer_rapport()...")
    time.sleep(1)
    
    # Appel de la fonction
    resultat = generer_rapport(data_test, dossier_logs)
    
    print("\n" + "="*60)
    if resultat is True:
        print("✅ SUCCÈS TOTAL : Le fichier JSON a bien été créé !")
        print("📁 Allez vérifier le contenu du dossier 'rapports' juste à côté.")
    else:
        print("❌ ÉCHEC : Une erreur s'est produite lors de la création du fichier.")
    print("="*60 + "\n")
