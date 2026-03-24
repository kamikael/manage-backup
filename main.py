#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Point d'entree principal de LogAnalyzer Pro."""

import argparse
import os
import sys

from analyser import NIVEAUX_VALIDES, analyser
from archiver import archiver_et_nettoyer
from rapport import generer_rapport, obtenir_dossier_rapports


def construire_parser() -> argparse.ArgumentParser:
    """Construit le parseur CLI principal."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="LogAnalyzer Pro - analyse, rapport et archivage.")
    parser.add_argument(
        "--source",
        required=True,
        help="Dossier contenant les fichiers .log a analyser.",
    )
    parser.add_argument(
        "--niveau",
        choices=NIVEAUX_VALIDES,
        default="ALL",
        help="Filtre de niveau a appliquer pendant l'analyse.",
    )
    parser.add_argument(
        "--dest",
        default=os.path.join(base_dir, "backups"),
        help="Dossier de destination des archives (par defaut: backups/).",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=30,
        help="Retention des rapports JSON en jours (30 par defaut).",
    )
    return parser


def main() -> int:
    """Orchestre les modules avec gestion d'erreurs explicite."""
    args = construire_parser().parse_args()

    try:
        # L'analyse est isolee pour remonter un message clair en cas d'echec.
        resultat_analyse = analyser(source=args.source, niveau=args.niveau)
    except Exception as exc:
        print(f"Erreur fatale pendant l'analyse des logs: {exc}")
        sys.exit(1)

    try:
        # Le rapport est genere avant archivage pour conserver une trace exploitable.
        chemin_rapport = generer_rapport(resultat_analyse)
    except Exception as exc:
        print(f"Erreur fatale pendant la generation du rapport JSON: {exc}")
        sys.exit(1)

    try:
        # L'archivage et le nettoyage restent separes pour mieux cibler les erreurs.
        resultat_archivage = archiver_et_nettoyer(
            fichiers_logs=resultat_analyse["fichiers_traites"],
            dossier_backups=os.path.abspath(args.dest),
            dossier_rapports=obtenir_dossier_rapports(),
            retention_jours=args.retention,
        )
    except Exception as exc:
        print(f"Erreur fatale pendant l'archivage et le nettoyage: {exc}")
        sys.exit(1)

    print("Analyse terminee avec succes.")
    print(f"Rapport JSON: {chemin_rapport}")
    print(f"Archive: {resultat_archivage['archive']}")
    print(f"Rapports supprimes: {resultat_archivage['nombre_rapports_supprimes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
