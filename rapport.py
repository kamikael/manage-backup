#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generation du rapport JSON pour LogAnalyzer Pro."""

import json
import os
from datetime import datetime


def obtenir_dossier_rapports() -> str:
    """Retourne le chemin absolu du dossier rapports base sur __file__."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")


def construire_nom_rapport() -> str:
    """Construit le nom de fichier du rapport du jour."""
    return f"rapport_{datetime.now().strftime('%Y-%m-%d')}.json"


def construire_structure_json(analyse: dict[str, object]) -> dict[str, object]:
    """Construit la structure JSON attendue par le TP."""
    metadata = analyse.get("metadata", {})
    statistiques = analyse.get("statistiques", {})
    fichiers_traites = analyse.get("fichiers_traites", [])

    return {
        "metadata": {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "utilisateur": metadata.get("utilisateur", "inconnu"),
            "os": metadata.get("os", "inconnu"),
            "source": os.path.abspath(str(metadata.get("source", ""))),
        },
        "statistiques": {
            "total_lignes": int(statistiques.get("total_lignes", 0)),
            "par_niveau": {
                "ERROR": int(statistiques.get("par_niveau", {}).get("ERROR", 0)),
                "WARN": int(statistiques.get("par_niveau", {}).get("WARN", 0)),
                "INFO": int(statistiques.get("par_niveau", {}).get("INFO", 0)),
            },
            "top5_erreurs": list(statistiques.get("top5_erreurs", [])),
        },
        "fichiers_traites": [os.path.abspath(str(fichier)) for fichier in fichiers_traites],
    }


def generer_rapport(analyse: dict[str, object]) -> str:
    """Genere le rapport JSON et retourne son chemin absolu."""
    if not isinstance(analyse, dict):
        raise TypeError("Les donnees d'analyse doivent etre fournies dans un dictionnaire.")

    dossier_rapports = obtenir_dossier_rapports()
    os.makedirs(dossier_rapports, exist_ok=True)
    chemin_rapport = os.path.abspath(os.path.join(dossier_rapports, construire_nom_rapport()))

    structure = construire_structure_json(analyse)

    # Le rapport est ecrit en UTF-8 avec une structure stable pour le TP.
    with open(chemin_rapport, "w", encoding="utf-8") as flux:
        json.dump(structure, flux, indent=4, ensure_ascii=False)

    return chemin_rapport
