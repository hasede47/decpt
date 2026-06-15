# Architectures DECEPTR v1 MVP

Ce dossier contient les trois vues d'architecture du projet final.

| Document | Description |
|---|---|
| `architecture-fonctionnelle.md` | Couches fonctionnelles, pipeline de traitement, flux de donnees et acteurs |
| `architecture-reseau.md` | Zones reseau, ports, flux autorises et correspondance Docker |
| `architecture-technique.md` | Services Docker, images, ports, stockage, fichiers et commandes |

Versions PDF:

| PDF | Description |
|---|---|
| `architecture-fonctionnelle.pdf` | Architecture fonctionnelle |
| `architecture-reseau.pdf` | Architecture reseau |
| `architecture-technique.pdf` | Architecture technique |
| `architectures-deceptr.pdf` | Document combine avec les trois architectures |
| `DECEPTR_Guide_Complet_Installation_Configuration.pdf` | Guide complet type dossier projet: build de zero, architecture, installation manuelle, configuration manuelle, tests, exploitation et checklist |

Ces documents correspondent au dossier final:

```text
D:\assir\Ismagi\PFA\DECEPTR-FINAL
```

Regenerer les PDF:

```powershell
cd D:\assir\Ismagi\PFA\DECEPTR-FINAL\docs
node .\build-pdfs.js
python .\build-deceptr-complete-guide.py
python .\docx-guide-to-reportlab-pdf.py
```
