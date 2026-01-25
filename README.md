# SmartMeterEVN (Fork)

Dieses Projekt basiert auf der Arbeit von Michael Reitbauer.
Alle Infos zum ursprünglichen Projekt befinden sich auf seinem Blog: https://www.michaelreitbauer.at/smart-meter-monitoring/

## Über diesen Fork
Das ursprüngliche Projekt wurde seit einiger Zeit nicht mehr aktualisiert und unterstützt die neuesten Versionen der Abhängigkeiten nicht mehr. Daher habe ich das Projekt geforkt und notwendige Updates vorgenommen, um die Kompatibilität mit den neuesten Versionen von Bibliotheken und Frameworks sicherzustellen.

Mein Verteilerkasten befindet sich bei mir einer Ecke im Haus die leider nur über schlechten WLAN Empfang verfügt, dadurch schaffe ich innerhalb des Verteilerkastens überhaupt keine WLAN Verbindung und damit fallen die kommerziellen Produkte leider aus. Mithilfe des Raspberry Pi, einem WLAN-USB-Stick und einer externen Antenne konnte ich das Auslesen der Kundenschnittstelle und die Übertragung zu meinen Servern ermöglichen. Wenn ihr also ähnliche Probleme habt oder die Anbindung einfach so gerne selber bauen wollt, könnt ihr gerne mein Skript verwenden.

## Projektbeschreibung
Dieses Projekt ermöglicht es, den Smartmeter der EVN (Netz Niederösterreich) über die Kundenschnittstelle auszulesen, die Daten zu entschlüsseln und an verschiedene Dienste weiterzuleiten.

Unterstützte Ausgabemöglichkeiten:
*   Konsole (Raw, Logfmt, JSON)
*   MQTT (z.B. für Home Assistant)
*   InfluxDB (v1 und v2/v3)
*   Prometheus (Metrics Exporter)
*   Loki (Logging)
*   Logfile (JSON)

## Aktueller Status

Das Projekt ist neu und läuft erst seit kurzem produktiv. Ich verwende bei mir InfluxDB 2.8 - v3 läuft auf meiner Synology aufgrund der älteren CPU nicht, Mosquitto MQTT Server 2.0, Prometheus 3.9, Loki 3.6 und Grafana 12.3.

Ist Influxdb und Prometheus nicht redundant? Ja durchaus. Influxdb verwende ich bereits um historische Daten und Auswertungen in Homeassistant zu machen, damit passen die Werte des Stromverbrauchs dort auch gut dazu. Prometheus verwende ich mit dem node-exporter um das Systemmonitoring zu machen. Es reicht aber vollauf nur eine der beiden Technologien zu verwenden.

Wie Michael in seinem Blog schon geschrieben hatte läuft das ganze Skript (noch nicht) komplett fehlerfrei, ich bin bei den ersten Tests aber noch nicht auf das Problem der zwischenzeitlichen Abstürze gekommen. Momentan liegt meine Hoffnung in Restarts über das systemd service und besseren Monitoring um den Fehler hoffentlich bald zu finden und zu beheben.

## Voraussetzungen

### Hardware
*   Raspberry Pi mit aktuellem Raspberry Pi OS
*   M-Bus zu USB Konverter (angeschlossen an der Kundenschnittstelle des Zählers)
*   Sagemcom Drehstromzähler T210-D

### Zugangsdaten
*   **Kundenschlüssel (Key):** Dieser muss bei der Netz NÖ angefordert werden.
    *   E-Mail an: smartmeter@netz-noe.at
    *   Benötigte Daten: Kundennummer oder Vertragskontonummer, Zählernummer, Handynummer.

## Installation

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/schretzi/SmartMeterEGVNSagemcom-T210-D.git
    cd SmartMeterEVNSagemcom-T210-D
    ```

2.  **Installationsskript ausführen:**
    Das `install.sh` Skript übernimmt die Installation aller Abhängigkeiten und optionaler Server-Dienste.
    ```bash
    sudo ./install.sh
    ```
    
    Während der Installation werden Sie gefragt:
    *   **Python Umgebung:** Wählen Sie zwischen System-Python oder einem Virtual Environment (venv). **Empfehlung: venv**.
    *   **Server Installation:** Sie können optional InfluxDB, Grafana, Loki, Prometheus und Mosquitto (MQTT Broker) direkt mitinstallieren.

## Konfiguration

Führen Sie das Einrichtungsskript aus, um die Konfigurationsdatei `config.json` zu erstellen:

```bash
./einrichtung.sh
```

Das Skript führt Sie interaktiv durch die Konfiguration:
*   Serieller Port (z.B. `/dev/ttyUSB0`) und Baudrate (Standard: 2400).
*   Eingabe des Kundenschlüssels (Key).
*   Aktivierung und Konfiguration der gewünschten Ausgabekanäle (MQTT, InfluxDB, Prometheus, Loki).

## Verwendung

### Manueller Start
Zum Testen kann das Skript manuell gestartet werden.

Wenn ein **Virtual Environment (venv)** verwendet wurde:
```bash
sudo ./.venv/bin/python3 smartmeter.py
```

Wenn **System-Python** verwendet wurde:
```bash
sudo python3 smartmeter.py
```

### Als Service einrichten (Autostart)
Um das Auslesen automatisch im Hintergrund laufen zu lassen, nutzen Sie das `service.sh` Skript.

**Hinweis:** Wenn Sie ein Virtual Environment nutzen, müssen Sie ggf. den Pfad zum Python-Interpreter im `service.sh` oder in der erstellten Service-Datei anpassen (`/etc/systemd/system/smartmeter.service`).

```bash
sudo ./service.sh
```

## Unterstützung
Spendenlink des Original-Autors: https://www.paypal.me/greenMikeEU

## License

This project is licensed under the GNU General Public License v3.0 License - see the LICENSE.md file for details