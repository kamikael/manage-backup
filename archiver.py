#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archivage et nettoyage pour LogAnalyzer Pro."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from datetime import date
from pathlib import Path


DEFAULT_RETENTION_DAYS = 30
SPACE_BUFFER_BYTES = 1024 * 1024


def verifier_espace_disque(destination: str | os.PathLike[str], espace_min_requis: int) -> int:
    """Verifie l'espace disque disponible via subprocess avant archivage."""
    destination_path = Path(destination).expanduser().resolve()
    destination_path.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        commande = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-PSDrive -Name '{destination_path.drive[:1]}').Free",
        ]
    else:
        commande = ["df", "-Pk", str(destination_path)]

    try:
        resultat = subprocess.run(
            commande,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Impossible de verifier l'espace disque: commande systeme introuvable.") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout).strip()
        raise RuntimeError(f"Impossible de verifier l'espace disque: {message}") from exc

    if os.name == "nt":
        sortie = resultat.stdout.strip().splitlines()
        if not sortie:
            raise RuntimeError("Sortie invalide lors de la verification de l'espace disque.")
        espace_libre_octets = int(sortie[-1].strip())
    else:
        lignes = [ligne for ligne in resultat.stdout.splitlines() if ligne.strip()]
        if len(lignes) < 2:
            raise RuntimeError("Sortie invalide lors de la verification de l'espace disque.")
        colonnes = lignes[-1].split()
        if len(colonnes) < 4:
            raise RuntimeError("Format inattendu pour la sortie de verification de disque.")
        espace_libre_octets = int(colonnes[3]) * 1024

    if espace_libre_octets < espace_min_requis:
        raise RuntimeError(
            "Espace disque insuffisant pour creer l'archive: "
            f"{espace_libre_octets} octets disponibles, {espace_min_requis} requis."
        )

    return espace_libre_octets


def creer_archive(
    fichiers_logs: list[str | os.PathLike[str]],
    dossier_temp: str | os.PathLike[str] | None = None,
) -> Path:
    """Cree une archive .tar.gz contenant les fichiers de logs traites."""
    if not fichiers_logs:
        raise ValueError("Aucun fichier .log fourni pour l'archivage.")

    fichiers_valides: list[Path] = []
    for fichier in fichiers_logs:
        chemin = Path(fichier).expanduser().resolve()
        if chemin.suffix.lower() != ".log":
            raise ValueError(f"Fichier invalide pour l'archivage: {chemin}")
        if not chemin.is_file():
            raise FileNotFoundError(f"Fichier log introuvable: {chemin}")
        fichiers_valides.append(chemin)

    temp_dir = Path(dossier_temp).expanduser().resolve() if dossier_temp else Path(tempfile.gettempdir()).resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = temp_dir / f"backup_{date.today().isoformat()}.tar.gz"

    # Les fichiers sont ajoutes par nom simple pour obtenir une archive propre.
    with tarfile.open(archive_path, "w:gz") as archive:
        for fichier in fichiers_valides:
            archive.add(fichier, arcname=fichier.name)

    return archive_path.resolve()


def deplacer_archive(archive_path: str | os.PathLike[str], destination: str | os.PathLike[str]) -> Path:
    """Deplace l'archive vers le dossier backups demande."""
    archive = Path(archive_path).expanduser().resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"Archive introuvable: {archive}")

    destination_path = Path(destination).expanduser().resolve()
    destination_path.mkdir(parents=True, exist_ok=True)
    archive_finale = destination_path / archive.name
    shutil.move(str(archive), str(archive_finale))
    return archive_finale.resolve()


def nettoyer_anciens_rapports(
    dossier_rapports: str | os.PathLike[str],
    retention_jours: int = DEFAULT_RETENTION_DAYS,
) -> list[Path]:
    """Supprime les rapports JSON plus vieux que la retention configuree."""
    if retention_jours < 0:
        raise ValueError("La retention ne peut pas etre negative.")

    rapports_path = Path(dossier_rapports).expanduser().resolve()
    rapports_path.mkdir(parents=True, exist_ok=True)

    seuil_secondes = retention_jours * 24 * 60 * 60
    maintenant = time.time()
    supprimes: list[Path] = []

    for rapport in rapports_path.glob("*.json"):
        age_secondes = maintenant - os.path.getmtime(rapport)
        if age_secondes > seuil_secondes:
            rapport.unlink()
            supprimes.append(rapport.resolve())

    return supprimes


def estimer_espace_requis(fichiers_logs: list[str | os.PathLike[str]]) -> int:
    """Estime l'espace minimum requis avant creation de l'archive."""
    total_taille = 0
    for fichier in fichiers_logs:
        chemin = Path(fichier).expanduser().resolve()
        if not chemin.is_file():
            raise FileNotFoundError(f"Fichier log introuvable: {chemin}")
        total_taille += chemin.stat().st_size
    return total_taille + max(SPACE_BUFFER_BYTES, total_taille // 10)


def archiver_et_nettoyer(
    fichiers_logs: list[str | os.PathLike[str]],
    dossier_backups: str | os.PathLike[str],
    dossier_rapports: str | os.PathLike[str],
    retention_jours: int = DEFAULT_RETENTION_DAYS,
) -> dict[str, object]:
    """Orchestre la verification disque, l'archivage et le nettoyage des rapports."""
    logs_absolus = [str(Path(fichier).expanduser().resolve()) for fichier in fichiers_logs]
    backups_path = Path(dossier_backups).expanduser().resolve()
    rapports_path = Path(dossier_rapports).expanduser().resolve()

    espace_min_requis = estimer_espace_requis(logs_absolus)
    espace_libre = verifier_espace_disque(backups_path, espace_min_requis)
    archive_temp = creer_archive(logs_absolus)
    archive_finale = deplacer_archive(archive_temp, backups_path)
    rapports_supprimes = nettoyer_anciens_rapports(rapports_path, retention_jours)

    return {
        "archive": str(archive_finale),
        "espace_libre_octets": espace_libre,
        "rapports_supprimes": [str(rapport) for rapport in rapports_supprimes],
        "nombre_rapports_supprimes": len(rapports_supprimes),
    }


def construire_parser() -> argparse.ArgumentParser:
    """Construit le parseur CLI du module d'archivage."""
    parser = argparse.ArgumentParser(description="Archive les logs et nettoie les rapports JSON.")
    parser.add_argument("fichiers_logs", nargs="+", help="Chemins absolus des fichiers .log a archiver.")
    parser.add_argument("--dest", required=True, help="Dossier absolu de destination des archives.")
    parser.add_argument("--rapports", required=True, help="Dossier absolu contenant les rapports JSON.")
    parser.add_argument(
        "--retention",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Duree de retention des rapports JSON en jours (defaut: {DEFAULT_RETENTION_DAYS}).",
    )
    return parser


def main() -> int:
    """Point d'entree CLI autonome du module d'archivage."""
    args = construire_parser().parse_args()
    try:
        resultat = archiver_et_nettoyer(
            fichiers_logs=args.fichiers_logs,
            dossier_backups=args.dest,
            dossier_rapports=args.rapports,
            retention_jours=args.retention,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erreur d'archivage: {exc}")
        return 1

    print(f"Archive creee: {resultat['archive']}")
    print(f"Rapports supprimes: {resultat['nombre_rapports_supprimes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
