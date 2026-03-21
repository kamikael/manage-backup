#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module analyser.py
"""

import argparse
import glob
import os
import platform
from collections import Counter



def parse_arguments():
    """
    Lit les arguments passés en ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Analyse des fichiers logs")

    parser.add_argument(
        "--source",
        required=True,
        help="Chemin du dossier contenant les fichiers logs"
    )

    parser.add_argument(
        "--niveau",
        choices=["ERROR", "WARN", "INFO", "ALL"],
        default="ALL",
        help="Niveau de filtrage des logs"
    )

    return parser.parse_args()


def trouver_fichiers_logs(dossier):
    """
    Retourne la liste des fichiers .log dans un dossier.
    """
    chemin = os.path.join(dossier, "*.log")
    return glob.glob(chemin)


def analyser_logs(fichiers, niveau_filtre):
    """
    Analyse les fichiers logs et calcule les statistiques.
    """

    total_lignes = 0

    compteur_niveaux = {
        "ERROR": 0,
        "WARN": 0,
        "INFO": 0
    }

    erreurs_messages = []

    for fichier in fichiers:

        with open(fichier, "r", encoding="utf-8") as f:

            for ligne in f:

                total_lignes += 1

                try:
                    parties = ligne.strip().split(" ")

                    niveau = parties[2]
                    message = " ".join(parties[3:])

                except IndexError:
                    continue

                if niveau in compteur_niveaux:
                    compteur_niveaux[niveau] += 1

                if niveau == "ERROR":
                    erreurs_messages.append(message)

    # top 5 erreurs
    top5 = Counter(erreurs_messages).most_common(5)

    top5_erreurs = [erreur for erreur, count in top5]

    return {
        "total_lignes": total_lignes,
        "par_niveau": compteur_niveaux,
        "top5_erreurs": top5_erreurs
    }


def recuperer_metadata(source):
    """
    Récupère les métadonnées système.
    """

    utilisateur = os.environ.get("USER") or os.environ.get("USERNAME")

    os_systeme = platform.system()

    return {
        "utilisateur": utilisateur,
        "os": os_systeme,
        "source": source
    }


def analyser():
    """
    Fonction principale du module.
    """

    args = parse_arguments()

    source = os.path.abspath(args.source)

    fichiers = trouver_fichiers_logs(source)

    stats = analyser_logs(fichiers, args.niveau)

    metadata = recuperer_metadata(source)

    resultat = {
        "metadata": metadata,
        "statistiques": stats,
        "fichiers_traites": fichiers
    }

    return resultat
if __name__ == "__main__":
    resultats = analyser()
    print(resultats)