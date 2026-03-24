# LogAnalyzer Pro

Application CLI Python qui analyse des fichiers `.log`, genere un rapport JSON puis archive les journaux traites. Le projet utilise uniquement la bibliotheque standard et respecte la structure demandee par le TP.

## Prerequis

- Python 3.10 ou plus recent
- Aucun paquet externe a installer

## Structure du projet

```text
manage-backup/
├── analyser.py
├── archiver.py
├── backups/
├── logs_test/
├── main.py
├── rapport.py
├── rapports/
└── README.md
```

## Installation

1. Cloner ou copier le depot.
2. Se placer dans le dossier du projet.
3. Verifier Python:

```bash
python --version
```

## Utilisation

Analyse complete avec tous les niveaux:

```bash
python main.py --source "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test"
```

Analyse filtree sur les erreurs:

```bash
python main.py --source "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test" --niveau ERROR
```

Analyse avec destination d'archive personnalisee et retention adaptee:

```bash
python main.py --source "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test" --niveau ALL --dest "C:\Users\Jean-Claude\Desktop\manage-backup\backups" --retention 15
```

Test du module d'archivage seul:

```bash
python archiver.py "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test\app1.log" "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test\app2.log" --dest "C:\Users\Jean-Claude\Desktop\manage-backup\backups" --rapports "C:\Users\Jean-Claude\Desktop\manage-backup\rapports"
```

## Role de chaque module

- `main.py` orchestre l'analyse, la generation du rapport et l'archivage avec gestion d'erreurs et `sys.exit(1)` en cas d'echec fatal.
- `analyser.py` gere la CLI d'analyse, scanne tous les `.log`, lit ligne par ligne, filtre par niveau et calcule les statistiques demandees.
- `rapport.py` construit la structure JSON attendue et ecrit `rapport_YYYY-MM-DD.json` dans `rapports/` avec des chemins absolus.
- `archiver.py` verifie l'espace disque via `subprocess`, cree `backup_YYYY-MM-DD.tar.gz`, le deplace dans `backups/` et supprime les anciens rapports JSON.

## Format des logs

Chaque ligne doit suivre ce format:

```text
YYYY-MM-DD HH:MM:SS NIVEAU message
```

Niveaux pris en charge:

- `ERROR`
- `WARN`
- `INFO`

## Cron demande

Execution tous les dimanches a 03h00:

```cron
0 3 * * 0 /usr/bin/python3 /chemin/absolu/vers/manage-backup/main.py --source /chemin/absolu/vers/manage-backup/logs_test --dest /chemin/absolu/vers/manage-backup/backups --retention 30
```

## Repartition des taches

- Analyse des besoins et mise en conformite du TP: audit et corrections structurelles.
- Module `analyser.py`: CLI, scan des logs, filtrage par niveau, statistiques, metadonnees systeme.
- Module `rapport.py`: construction du JSON, ecriture du rapport, chemins absolus.
- Module `archiver.py`: verification espace disque, creation de l'archive, nettoyage des rapports.
- Module `main.py` et verification finale: orchestration, messages d'erreur, tests locaux.

## Commandes de verification

```bash
python -m py_compile main.py analyser.py rapport.py archiver.py test_archiver.py
python -m unittest -v test_archiver.py
python main.py --source "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test" --niveau ALL
python main.py --source "C:\Users\Jean-Claude\Desktop\manage-backup\logs_test" --niveau ERROR
```
