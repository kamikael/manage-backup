#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Analyse des fichiers de logs pour LogAnalyzer Pro."""

import argparse
import glob
import os
import platform
from collections import Counter


NIVEAUX_VALIDES = ("ERROR", "WARN", "INFO", "ALL")


def construire_parser() -> argparse.ArgumentParser:
    """Construit le parseur CLI du module d'analyse."""
    parser = argparse.ArgumentParser(description="Analyse des fichiers logs.")
    parser.add_argument(
        "--source",
        required=True,
        help="Chemin absolu ou relatif du dossier contenant les fichiers .log.",
    )
    parser.add_argument(
        "--niveau",
        choices=NIVEAUX_VALIDES,
        default="ALL",
        help="Niveau de filtrage a appliquer (ALL par defaut).",
    )
    return parser


def parse_arguments() -> argparse.Namespace:
    """Lit les arguments de ligne de commande du module."""
    return construire_parser().parse_args()


def trouver_fichiers_logs(dossier: str) -> list[str]:
    """Retourne la liste absolue des fichiers .log presents dans un dossier."""
    dossier_absolu = os.path.abspath(dossier)
    motif = os.path.join(dossier_absolu, "*.log")
    return sorted(os.path.abspath(chemin) for chemin in glob.glob(motif))


def extraire_niveau_et_message(ligne: str) -> tuple[str | None, str]:
    """Extrait le niveau et le message d'une ligne de log au format attendu."""
    morceaux = ligne.strip().split(maxsplit=3)
    if len(morceaux) < 4:
        return None, ""
    return morceaux[2], morceaux[3]


def ligne_correspond_au_filtre(niveau: str | None, niveau_filtre: str) -> bool:
    """Indique si une ligne doit etre prise en compte selon le filtre demande."""
    if niveau is None:
        return False
    return niveau_filtre == "ALL" or niveau == niveau_filtre


def analyser_logs(fichiers: list[str], niveau_filtre: str) -> dict[str, object]:
    """Analyse les logs ligne par ligne et calcule les statistiques attendues."""
    total_lignes = 0
    compteur_niveaux = {"ERROR": 0, "WARN": 0, "INFO": 0}
    erreurs_messages: Counter[str] = Counter()

    for fichier in fichiers:
        with open(fichier, "r", encoding="utf-8") as flux:
            for ligne in flux:
                niveau, message = extraire_niveau_et_message(ligne)
                if not ligne_correspond_au_filtre(niveau, niveau_filtre):
                    continue

                total_lignes += 1
                if niveau in compteur_niveaux:
                    compteur_niveaux[niveau] += 1

                if niveau == "ERROR":
                    erreurs_messages[message] += 1

    return {
        "total_lignes": total_lignes,
        "par_niveau": compteur_niveaux,
        "top5_erreurs": [message for message, _ in erreurs_messages.most_common(5)],
    }


def recuperer_metadata(source: str) -> dict[str, str]:
    """Recupere les metadonnees systeme demandees par le TP."""
    utilisateur = os.environ.get("USERNAME") or os.environ.get("USER") or "inconnu"
    os_systeme = platform.system() or "inconnu"
    return {
        "utilisateur": utilisateur,
        "os": os_systeme,
        "source": os.path.abspath(source),
    }


def analyser(source: str | None = None, niveau: str = "ALL") -> dict[str, object]:
    """Execute l'analyse complete et retourne une structure exploitable par rapport.py."""
    if source is None:
        args = parse_arguments()
        source = args.source
        niveau = args.niveau

    source_absolue = os.path.abspath(source)
    if not os.path.isdir(source_absolue):
        raise FileNotFoundError(f"Dossier source introuvable: {source_absolue}")

    fichiers = trouver_fichiers_logs(source_absolue)
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier .log trouve dans: {source_absolue}")

    statistiques = analyser_logs(fichiers, niveau)
    metadata = recuperer_metadata(source_absolue)

    # La structure retournee est volontairement alignee sur le JSON attendu.
    return {
        "metadata": metadata,
        "statistiques": statistiques,
        "fichiers_traites": fichiers,
    }


if __name__ == "__main__":
    print(analyser())
