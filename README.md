# MadMax Plotter GUI

Eine grafische Oberfläche für den
[MadMax Chia Plotter](https://github.com/madMAx43v3r/chia-plotter) — geschrieben
in Python mit Tkinter, ohne externe Abhängigkeiten. Läuft unter **Windows und
Linux**.

Der MadMax-Plotter ist ein Kommandozeilenwerkzeug mit rund zwei Dutzend
Parametern. Diese GUI nimmt einem das Merken der Flags ab, validiert die
Eingaben vor dem Start, zeigt den Fortschritt an und speichert Konfigurationen
als XML.

## Funktionen

**Plot-Erstellung**
- Pool-Plots (NFT, `-c`) und Solo-Plots (OG, `-p`) per Umschalter
- K-Größen 25 bis 32
- Stapelverarbeitung: mehrere Plots nacheinander, jeweils als eigener Prozess
- Abbruch jederzeit möglich, ohne die GUI zu blockieren

**Automatische Erkennung**
- Findet die Binaries `chia_plot` und `chia` selbstständig über `PATH`
- Kennt zusätzlich die üblichen Installationsorte beider Systeme
- Liest Farmer Key und Pool Public Key aus `chia keys show`
- Ermittelt die Pool Contract Address aus `chia plotnft show`

**Validierung vor dem Start**
- Farmer Key wird gegen 96 Hex-Zeichen geprüft
- Pool Contract Address und Pool Public Key auf plausible Länge
- Pflichtpfade (Temp 1, Final Dir) müssen gesetzt sein

Das erspart Fehlversuche, die sonst erst nach Minuten Laufzeit auffallen.

**Plot-Prüfung**
- Optionale automatische Prüfung nach jedem erstellten Plot
  (`chia plots check -n 30`)
- Manuelle Prüfung einzelner Dateien oder ganzer Verzeichnisse

**Konfiguration**
- Alle Einstellungen als XML speichern und laden
- Berechnet aus dem freien Speicher im Zielverzeichnis, wie viele Plots der
  gewählten K-Größe noch hineinpassen

**Oberfläche**
- Drei Reiter: Plots & Keys, Parameter, Pfade & Tools
- Dark Theme in Anlehnung an die Chia-GUI
- Live-Ausgabe des Plotters im Fenster, Fortschrittsbalken über alle Plots

## Unterstützte Parameter

| Flag | Bedeutung | Standard |
| --- | --- | --- |
| `-k` | K-Größe | 32 |
| `-n` | Anzahl Plots | 1 (pro Prozessaufruf) |
| `-f` | Farmer Public Key | — |
| `-c` | Pool Contract Address (NFT) | — |
| `-p` | Pool Public Key (OG) | — |
| `-t` | Temp-Verzeichnis 1 | — |
| `-2` | Temp-Verzeichnis 2 | optional |
| `-d` | Zielverzeichnis | — |
| `-s` | Stage-Verzeichnis | optional |
| `-r` | Threads | 4 |
| `-u` | Buckets Phase 1+2 | 256 |
| `-v` | Buckets Phase 3+4 | 256 |
| `-K` | Thread-Multiplikator Phase 2 | 1 |
| `-w` | Auf Kopiervorgang warten | aus |
| `-D` | Direktausgabe | aus |
| `-Z` | Unique Plot | aus |
| `-G` | Temp-Verzeichnisse abwechseln | aus |

## Voraussetzungen

- Python 3.9 oder neuer — `ET.indent()` wird für die XML-Ausgabe verwendet
- Tkinter
  - Windows: in den offiziellen Python-Installern enthalten
  - Debian/Ubuntu: `sudo apt install python3-tk`
  - Fedora: `sudo dnf install python3-tkinter`
- Der [MadMax-Plotter](https://github.com/madMAx43v3r/chia-plotter)
  (`chia_plot` bzw. `chia_plot.exe`)
- Optional: Chia-Installation für Key-Erkennung und Plot-Prüfung

Externe Python-Pakete werden nicht benötigt.

## Start

**Linux**

```bash
python3 Madmax_GUI_rev3.py
```

Oder direkt, da die Datei einen Shebang enthält:

```bash
chmod +x Madmax_GUI_rev3.py
./Madmax_GUI_rev3.py
```

**Windows**

```
python Madmax_GUI_rev3.py
```

Ein Doppelklick funktioniert ebenfalls, wenn `.py` mit Python verknüpft ist.

> Wichtig: Die Datei ist ein Python-Programm, kein Shell-Skript. Ein Aufruf mit
> `sh datei.py` oder `bash datei.py` scheitert mit Meldungen wie
> `import: not found`.

## Verwendung

Typischer Ablauf beim ersten Start:

1. Reiter **Pfade & Tools**: Chia-Pfad prüfen, meist bereits erkannt
2. Reiter **Plots & Keys**: „Keys automatisch erkennen" anklicken
3. Plot-Typ wählen — Pool (NFT) oder Solo (OG)
4. Reiter **Pfade & Tools**: Temp 1 auf eine schnelle SSD, Final Dir auf die
   Zielplatte
5. Reiter **Parameter**: Threads an die CPU anpassen
6. Anzahl Plots eintragen, „Plotten Starten"
7. Über „Config Speichern" die Einstellungen sichern

### Hinweise zu den Parametern

**Temp 1** trägt die Hauptlast und sollte auf einer NVMe oder SSD liegen. Ein
k32-Plot erzeugt dort etwa 220 GB Schreibvolumen pro Durchgang. **Temp 2** kann
auf einem anderen Laufwerk liegen, um die Last zu verteilen.

**Threads** entspricht sinnvollerweise der Anzahl physischer Kerne. Mehr als das
bringt bei MadMax meist nichts, weil der Plotter im I/O-Limit landet.

**Buckets**: 256 ist ein guter Ausgangswert. Höhere Werte senken den
Speicherbedarf, erhöhen aber die Anzahl der Dateizugriffe.

Die GUI ruft MadMax bewusst mit `-n 1` auf und startet für jeden Plot einen
eigenen Prozess. Das kostet minimal Zeit, ermöglicht aber sauberen Abbruch
zwischen den Plots und eine Prüfung nach jedem einzelnen Plot.

### Plattformunterschiede

Pfade werden über `os.path.normpath` und `os.sep` normalisiert — Eingaben
funktionieren also mit den Trennern des jeweiligen Systems. Das Ausblenden des
Konsolenfensters greift nur unter Windows; unter Linux erzeugt der Plotter
ohnehin kein eigenes Fenster.

Die Chia-Erkennung sucht unter Windows im Standard-Installationspfad der
Chia-GUI, unter Linux in `~/.local/bin`, `/usr/local/bin`, `/usr/bin` sowie im
venv einer Quellinstallation.

## Bekannte Einschränkungen

- Der Fortschrittsbalken zählt fertige Plots, nicht den Fortschritt innerhalb
  eines Plots
- Beim Stoppen wird `terminate()` verwendet; temporäre Dateien im
  Temp-Verzeichnis bleiben unter Umständen liegen und sollten manuell entfernt
  werden
- Die Plotgrößen für die Anzeige „Mögliche Plots" sind Näherungswerte

## Sicherheitshinweis

Gespeicherte XML-Konfigurationen enthalten Farmer Key, Pool Public Key und Pool
Contract Address im Klartext. Diese Werte sind öffentliche Schlüssel und geben
keinen Zugriff auf Guthaben — Vorsicht ist trotzdem angebracht, wenn du
Konfigurationsdateien weitergibst oder in ein öffentliches Repository legst.

Der Mnemonic beziehungsweise private Schlüssel wird vom Programm zu keinem
Zeitpunkt gelesen oder gespeichert.

## Lizenz

MIT — siehe [LICENSE](LICENSE).

MadMax Plotter und Chia sind eigenständige Projekte mit eigenen Lizenzen. Dieses
Programm ruft sie lediglich auf und ist mit ihnen nicht offiziell verbunden.

## Links

- [MadMax Chia Plotter](https://github.com/madMAx43v3r/chia-plotter)
- [Chia Network](https://www.chia.net/)
- [Chia Dokumentation zu Plots](https://docs.chia.net/plotting-basics)
