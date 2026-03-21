# LogAnalyzer Pro

Projet centre ici sur la partie Neal : `archiver.py`.

## Structure

```text
loganalyzer/
├── archivage/
│   ├── app1.log
│   ├── app2.log
│   └── app3.log
├── main.py
├── rapport.py
├── archiver.py
├── backups/
├── rapports/
└── test_archiver.py
```

## Role de Neal

Le module `archiver.py` intervient apres l'analyse des logs et apres la generation du rapport JSON.

Il doit :

- archiver les fichiers `.log` traites dans un fichier `.tar.gz`
- deplacer cette archive dans `backups/`
- supprimer les anciens rapports `.json` dans `rapports/`
- verifier l'espace disque avant l'archivage

## Fonction principale

```python
archiver_et_nettoyer(fichiers_logs, dossier_backups, dossier_rapports, retention_jours=30)
```

Attendus :

- `fichiers_logs` : liste de chemins absolus vers les fichiers `.log`
- `dossier_backups` : chemin absolu vers `backups/`
- `dossier_rapports` : chemin absolu vers `rapports/`
- `retention_jours` : duree de retention, `30` par defaut

Le module leve des exceptions et laisse `main.py` gerer les erreurs fatales.

## Verification

```bash
python3 -m py_compile archiver.py test_archiver.py
python3 -m unittest -v test_archiver.py
```
