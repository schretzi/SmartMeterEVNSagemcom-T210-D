#!/bin/bash
echo "Einrichtung des Smart Meter bitte den Anweißungen folgen"
read -p "Bitte den Seriellen Port angeben (default:/dev/ttyUSB0): " port
port=${port:-/dev/ttyUSB0}
read -p "Bitte die Baudrate eingeben (default:2400): " baudrate
baudrate=${baudrate:-2400}
read -p "Bitte geben Sie den Entschlüsselungs Code vom Netzbetreiber ein: " key
read -p "Sollen die Daten auf der Konsole ausgegeben werden ? (y/n): " userinput
printValue=false
if [[ $userinput =~ ^[yYnN][eE][sS]|[yYjJ]$ ]]; then
	printValue=true
	echo Daten werden auf der Konsole ausgegeben.
fi

read -p "Sollen die Logs an Loki gesendet werden? (y/n): " userinput
useLoki=false
lokiUrl=""
if [[ $userinput =~ ^[yYnN][eE][sS]|[yYjJ]$ ]]; then
    useLoki=true
    read -p "Bitte die URL der Loki Instanz eingeben (z.B. http://localhost:3100/loki/api/v1/push): " lokiUrl
fi
read -p "Sollen die Daten über MQTT ausgegeben werden? (y/n): " userinput
useMQTT=false
mqttbrokerip=""
mqttbrokerport=1883
mqttbrokeruser=""
mqttbrokerpasswort=""
mqttIsAuthenticated=false
if [[ $userinput =~ ^[yYnN][eE][sS]|[yYjJ]$ ]]; then
	useMQTT=true
	read -p "Bitte IP-Adresse des Brokers eingeben: " mqttbrokerip
	read -p "Bitte den Port eingebn. (defaukt:1883): " mqttbrokerport
    mqttbrokerport=${mqttbrokerport:-1883}
	read -p "Bitte den MQTT User eingeben. (Wenn keiner verwendet wird einfach leer lassen und mit Enter bestetigen): " mqttbrokeruser
	read -p "Bitte MQTT User Passwort eingeben. (Wenn kein Passwort verwendet wird einfach leer lassen und mit Enter bestetigen): " mqttbrokerpasswort
    if [ ! -z "$mqttbrokeruser" ]; then mqttIsAuthenticated=true; fi
fi

read -p "Sollen die Daten in InfluxDB gespeichert werden (y/n): " userinput
useInfluxdb=false
influxdbip=""
influxdbport=8086
if [[ $userinput =~ ^[yYnN][eE][sS]|[yYjJ]$ ]]; then
	useInfluxdb=true
	read -p "Bitte IP-Adresse der Influxdb eingeben: " influxdbip
	read -p "Bitte den Port eingebn. (default:8086): " influxdbport
    influxdbport=${influxdbport:-8086}
fi

read -p "Sollen die Daten für Prometheus bereitgestellt werden (y/n): " userinput
usePrometheus=false
prometheusport=8000
if [[ $userinput =~ ^[yYnN][eE][sS]|[yYjJ]$ ]]; then
	usePrometheus=true
	read -p "Bitte den Port für Prometheus eingeben (default:8000): " prometheusport
    prometheusport=${prometheusport:-8000}
fi


rm config.json
cat <<EOF > config.json
{
    "mbus": {
        "port": "$port",
        "baudRate": $baudrate
    },
    "key": "$key",
    "logging": {
        "console": {
            "enabled": $printValue,
            "format": "logfmt",
            "level": "INFO"
        },
        "file": {
            "enabled": false,
            "format": "json",
            "path": "",
            "level": "INFO"
        },
        "loki": {
            "enabled": $useLoki,
            "url": "$lokiUrl",
            "level": "INFO"
        }
    },
    "mqtt": {
        "enabled": $useMQTT,
        "brokerIP": "$mqttbrokerip",
        "brokerPort": $mqttbrokerport,
        "authentication": {
            "isAuthenticated": $mqttIsAuthenticated,
            "username": "$mqttbrokeruser",
            "password": "$mqttbrokerpasswort"
        },
        "mqttApiVersion": 1,
        "mqttPrefix": "smartmeter"
    },
    "influxdb": {
        "enabled": $useInfluxdb,
        "serverIP": "$influxdbip",
        "serverPort": $influxdbport,
        "authentication": {
            "isAuthenticated": false,
            "username": "",
            "password": ""
        },
        "database": "smartmeter",
        "organization": "smartmeter",
        "version": 2,
        "sendMetrics": false,
        "sendValues": true
    },
    "prometheus": {
        "enabled": $usePrometheus,
        "port": $prometheusport,
        "exposeMetrics": true,
        "exposeValues": false
    }
}
EOF