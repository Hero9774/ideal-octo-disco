# MadMax Plotter GUI

Eine grafische Oberfläche für den
[MadMax Chia Plotter](https://github.com/madMAx43v3r/chia-plotter) — geschrieben
in Python mit Tkinter, ohne externe Abhängigkeiten.

Der MadMax-Plotter ist ein Kommandozeilenwerkzeug mit rund zwei Dutzend
Parametern. Diese GUI nimmt einem das Merken der Flags ab, validiert die
Eingaben vor dem Start, zeigt den Fortschritt an und speichert
Konfigurationen als XML.

## Funktionen

**Plot-Erstellung**
- Pool-Plots (NFT, `-c`) und Solo-Plots (OG, `-p`) per Umschalter
- K-Größen 25 bis 32
- Stapelverarbeitung: mehrere Plots nacheinander, jeweils als eigener Prozess
- Abbruch jederzeit möglich, ohne die GUI zu blockieren

**Automatische Erkennung**
- Findet die Binaries `chia_plot` und `chia` selbstständig über `PATH`
- Liest Farmer Key und Pool Public Key aus `chia keys show`
- Ermittelt die Pool Contract Address aus `chia plotnft show`

**Validierung vor dem Start**
- Farmer Key wird gegen 96 Hex-Zeichen geprüft
- Pool Contract Address und Pool Public Key auf plausible Länge
- Pflichtpfade (Temp 1, Final Dir) müssen gesetzt sein

Das erspart Fehlversuche, die sonst erst nach Minuten Laufzeit auffallen.

**Plot-Prüfung**
- Optionale automatische Prüfung nach jedem erstellten Plot (`chia plots check -n 30`)
- Manuelle Prüfung einzelner Dateien oder ganzer Verzeichnisse

**Konfiguration**
- Alle Einstellungen als XML speichern und laden
- Berechnet aus dem freien Speicher im Zielverzeichnis, wie viele k32-Plots
  noch hineinpassen

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

- **Windows** (siehe Einschränkungen)
- Python 3.9 oder neuer — `ET.indent()` wird für die XML-Ausgabe verwendet
- Tkinter (bei den offiziellen Windows-Installern enthalten)
- Der [MadMax-Plotter](https://github.com/madMAx43v3r/chia-plotter) als
  `chia_plot.exe`
- Optional: Chia-Installation für Key-Erkennung und Plot-Prüfung

Externe Python-Pakete werden nicht benötigt.

## Verwendung

```
python Madmax_GUI_rev2.py
```

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
k32-Plot benötigt dort etwa 220 GB Schreibvolumen pro Durchgang. **Temp 2** kann
auf einem anderen Laufwerk liegen, um die Last zu verteilen.

**Threads** entspricht sinnvollerweise der Anzahl physischer Kerne. Mehr als das
bringt bei MadMax meist nichts, weil der Plotter im I/O-Limit landet.

**Buckets**: 256 ist ein guter Ausgangswert. Höhere Werte senken den
Speicherbedarf, erhöhen aber die Anzahl der Dateizugriffe.

Die GUI ruft MadMax bewusst mit `-n 1` auf und startet für jeden Plot einen
eigenen Prozess. Das kostet minimal Zeit, ermöglicht aber sauberen Abbruch
zwischen den Plots und eine Prüfung nach jedem einzelnen Plot.

## Einschränkungen

**Derzeit nur unter Windows lauffähig.** Das Programm erkennt zwar die
Binärnamen betriebssystemabhängig, verwendet aber an drei Stellen
`subprocess.STARTUPINFO()` zum Ausblenden von Konsolenfenstern. Diese Klasse
existiert unter Linux und macOS nicht und führt dort zu einem `AttributeError`.
Zusätzlich wandelt `normalize_path()` alle Pfadtrenner in Backslashes um.

Für Linux-Unterstützung wären beide Stellen anzupassen — die Struktur des
Programms gibt das ohne größere Umbauten her.

**Weitere Punkte**
- Die Berechnung „Mögliche Plots" geht fest von k32 aus und stimmt bei
  anderen K-Größen nicht
- Der Fortschrittsbalken zählt fertige Plots, nicht den Fortschritt innerhalb
  eines Plots
- Beim Stoppen wird `terminate()` verwendet; temporäre Dateien im Temp-Verzeichnis
  bleiben unter Umständen liegen und sollten manuell entfernt werden

## Sicherheitshinweis

Gespeicherte XML-Konfigurationen enthalten Farmer Key, Pool Public Key und
Pool Contract Address im Klartext. Diese Werte sind öffentliche Schlüssel und
kein Zugriff auf Guthaben — Vorsicht ist trotzdem angebracht, wenn du
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
