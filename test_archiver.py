"""Tests du module archiver.py pour la partie Neal."""

from __future__ import annotations

import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import archiver


class TestArchiver(unittest.TestCase):
    def setUp(self) -> None:
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
        self.temp_dir.cleanup()

    def test_creer_archive_cree_un_tar_gz_valide(self) -> None:
        archive_path = archiver.creer_archive([self.log1, self.log2], dossier_temp=self.base_path)

        self.assertTrue(archive_path.exists())
        self.assertEqual(archive_path.suffixes, [".tar", ".gz"])

        with tarfile.open(archive_path, "r:gz") as archive:
            noms = sorted(archive.getnames())

        self.assertEqual(noms, ["app1.log", "app2.log"])

    def test_deplacer_archive_place_le_fichier_dans_backups(self) -> None:
        archive_path = archiver.creer_archive([self.log1], dossier_temp=self.base_path)

        archive_finale = archiver.deplacer_archive(archive_path, self.backups_dir)

        self.assertFalse(archive_path.exists())
        self.assertTrue(archive_finale.exists())
        self.assertEqual(archive_finale.parent, self.backups_dir.resolve())

    def test_nettoyer_anciens_rapports_supprime_seulement_les_vieux_json(self) -> None:
        ancien = self.rapports_dir / "ancien.json"
        recent = self.rapports_dir / "recent.json"
        autre = self.rapports_dir / "note.txt"

        ancien.write_text('{"old": true}\n', encoding="utf-8")
        recent.write_text('{"recent": true}\n', encoding="utf-8")
        autre.write_text("ne pas supprimer\n", encoding="utf-8")

        maintenant = time.time()
        vieux_temps = maintenant - (40 * 24 * 60 * 60)
        os_times = (vieux_temps, vieux_temps)
        recent_times = (maintenant, maintenant)

        import os

        os.utime(ancien, os_times)
        os.utime(recent, recent_times)

        supprimes = archiver.nettoyer_anciens_rapports(self.rapports_dir, retention_jours=30)

        self.assertEqual([p.name for p in supprimes], ["ancien.json"])
        self.assertFalse(ancien.exists())
        self.assertTrue(recent.exists())
        self.assertTrue(autre.exists())

    def test_archiver_et_nettoyer_gere_toute_la_sequence(self) -> None:
        vieux_rapport = self.rapports_dir / "rapport_ancien.json"
        vieux_rapport.write_text('{"ancien": true}\n', encoding="utf-8")

        maintenant = time.time()
        vieux_temps = maintenant - (45 * 24 * 60 * 60)

        import os

        os.utime(vieux_rapport, (vieux_temps, vieux_temps))

        with patch("archiver.verifier_espace_disque", return_value=10_000_000):
            resultat = archiver.archiver_et_nettoyer(
                fichiers_logs=[self.log1, self.log2],
                dossier_backups=self.backups_dir,
                dossier_rapports=self.rapports_dir,
                retention_jours=30,
            )

        archive_finale = Path(resultat["archive"])
        self.assertTrue(archive_finale.exists())
        self.assertEqual(archive_finale.parent, self.backups_dir.resolve())
        self.assertEqual(resultat["nombre_rapports_supprimes"], 1)
        self.assertFalse(vieux_rapport.exists())

    def test_erreur_si_aucun_log_fourni(self) -> None:
        with self.assertRaises(ValueError):
            archiver.creer_archive([], dossier_temp=self.base_path)

    def test_erreur_si_espace_disque_insuffisant(self) -> None:
        with patch("archiver.subprocess.run") as run_mock:
            run_mock.return_value.stdout = (
                "Filesystem 1024-blocks Used Available Capacity Mounted on\n"
                "/dev/sda1 100000 99000 1 99% /tmp\n"
            )
            run_mock.return_value.stderr = ""
            run_mock.return_value.returncode = 0

            with self.assertRaises(RuntimeError):
                archiver.verifier_espace_disque(self.backups_dir, espace_min_requis=10_000)


if __name__ == "__main__":
    unittest.main()
