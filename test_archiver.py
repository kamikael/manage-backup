#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests unitaires du module archiver.py."""

from __future__ import annotations

import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import archiver


class TestArchiver(unittest.TestCase):
    """Valide les fonctions principales du module d'archivage."""

    def setUp(self) -> None:
        """Prepare un environnement temporaire de test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.logs_dir = self.base_path / "logs"
        self.backups_dir = self.base_path / "backups"
        self.rapports_dir = self.base_path / "rapports"

        self.logs_dir.mkdir()
        self.backups_dir.mkdir()
        self.rapports_dir.mkdir()

        self.log1 = self.logs_dir / "app1.log"
        self.log2 = self.logs_dir / "app2.log"
        self.log1.write_text("2024-04-01 08:22:30 ERROR Echec connexion serveur\n", encoding="utf-8")
        self.log2.write_text("2024-04-01 08:30:00 INFO Tache demarree\n", encoding="utf-8")

    def tearDown(self) -> None:
        """Libere l'environnement temporaire."""
        self.temp_dir.cleanup()

    def test_creer_archive_cree_un_tar_gz_valide(self) -> None:
        """Verifie la creation d'une archive tar.gz exploitable."""
        archive_path = archiver.creer_archive([self.log1, self.log2], dossier_temp=self.base_path)

        self.assertTrue(archive_path.exists())
        self.assertEqual(archive_path.suffixes, [".tar", ".gz"])

        with tarfile.open(archive_path, "r:gz") as archive:
            noms = sorted(archive.getnames())

        self.assertEqual(noms, ["app1.log", "app2.log"])

    def test_deplacer_archive_place_le_fichier_dans_backups(self) -> None:
        """Verifie le deplacement final de l'archive."""
        archive_path = archiver.creer_archive([self.log1], dossier_temp=self.base_path)
        archive_finale = archiver.deplacer_archive(archive_path, self.backups_dir)

        self.assertFalse(archive_path.exists())
        self.assertTrue(archive_finale.exists())
        self.assertEqual(archive_finale.parent, self.backups_dir.resolve())

    def test_nettoyer_anciens_rapports_supprime_seulement_les_vieux_json(self) -> None:
        """Verifie la suppression selective des vieux rapports JSON."""
        ancien = self.rapports_dir / "rapport_ancien.json"
        recent = self.rapports_dir / "rapport_recent.json"
        autre = self.rapports_dir / "note.txt"

        ancien.write_text('{"old": true}\n', encoding="utf-8")
        recent.write_text('{"recent": true}\n', encoding="utf-8")
        autre.write_text("note\n", encoding="utf-8")

        vieux_timestamp = time.time() - (31 * 24 * 60 * 60)
        os_utime = (vieux_timestamp, vieux_timestamp)
        import os
        os.utime(ancien, os_utime)

        supprimes = archiver.nettoyer_anciens_rapports(self.rapports_dir, retention_jours=30)

        self.assertEqual([p.name for p in supprimes], ["rapport_ancien.json"])
        self.assertFalse(ancien.exists())
        self.assertTrue(recent.exists())
        self.assertTrue(autre.exists())

    @patch("archiver.verifier_espace_disque", return_value=10_000_000)
    def test_archiver_et_nettoyer_orchestre_les_etapes(self, _mock_espace: object) -> None:
        """Verifie l'orchestration complete du module."""
        vieux_rapport = self.rapports_dir / "rapport_ancien.json"
        vieux_rapport.write_text('{"ok": true}\n', encoding="utf-8")

        vieux_timestamp = time.time() - (40 * 24 * 60 * 60)
        import os
        os.utime(vieux_rapport, (vieux_timestamp, vieux_timestamp))

        resultat = archiver.archiver_et_nettoyer(
            fichiers_logs=[self.log1, self.log2],
            dossier_backups=self.backups_dir,
            dossier_rapports=self.rapports_dir,
            retention_jours=30,
        )

        self.assertTrue(Path(resultat["archive"]).exists())
        self.assertEqual(resultat["nombre_rapports_supprimes"], 1)
        self.assertFalse(vieux_rapport.exists())


if __name__ == "__main__":
    unittest.main()
