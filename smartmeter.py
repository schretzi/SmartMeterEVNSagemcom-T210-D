import json
import sys
import os
from datetime import datetime
import time
import logging
import socket
from power_values import PowerValues
from config_handler import get_configuration
from serial_reader import SerialReader

# Load Configuration
cfg = get_configuration()

class AppMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.serial_restarts = 0
        self.mqtt_last_success = True
        self.mqtt_failures = 0
        self.mqtt_successes = 0
        self.influxdb_last_success = True
        self.influxdb_failures = 0
        self.influxdb_successes = 0

    def get_uptime(self):
        return time.time() - self.start_time

    def inc_serial_restarts(self):
        self.serial_restarts += 1

# Setup Logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.levelno >= logging.ERROR:
            log_record["file"] = record.filename
            log_record["line"] = record.lineno
        return json.dumps(log_record)


class ErrorLocationFormatter(logging.Formatter):
    def format(self, record):
        record.error_location = ""
        if record.levelno >= logging.ERROR:
            record.error_location = f" ({record.filename}:{record.lineno})"
        return super().format(record)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG) # Set root logger to the most permissive level

if cfg.logging.console.enabled:
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = getattr(logging, cfg.logging.console.level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    
    if cfg.logging.console.format == 'json':
        console_handler.setFormatter(JSONFormatter())
    elif cfg.logging.console.format == 'raw':
        console_handler.setFormatter(ErrorLocationFormatter('%(message)s%(error_location)s'))
    else:
        console_handler.setFormatter(
            ErrorLocationFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s%(error_location)s')
        )
    root_logger.addHandler(console_handler)

if cfg.logging.file.enabled and cfg.logging.file.path:
    file_handler = logging.FileHandler(cfg.logging.file.path)
    file_level = getattr(logging, cfg.logging.file.level.upper(), logging.INFO)
    file_handler.setLevel(file_level)

    if cfg.logging.file.format == 'json':
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(
            ErrorLocationFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s%(error_location)s')
        )
    root_logger.addHandler(file_handler)

if hasattr(cfg.logging, 'loki') and cfg.logging.loki.enabled and cfg.logging.loki.url:
    try:
        import logging_loki
        from multiprocessing import Queue
        loki_handler = logging_loki.LokiQueueHandler(
            Queue(-1),
            url=cfg.logging.loki.url,
            tags={"application": "smartmeter", "hostname": socket.gethostname()},
            version="1",
        )
        loki_level = getattr(logging, cfg.logging.loki.level.upper(), logging.INFO)
        loki_handler.setLevel(loki_level)
        root_logger.addHandler(loki_handler)
    except ImportError:
        logging.error("python-logging-loki module not found. Please install it to use Loki logging.")

logger = logging.getLogger("SmartMeter")

#Print used configuration from dict config
logger.info("Verwendete Konfiguration:")
logger.info(cfg)
logger.info("\n")

metrics = AppMetrics()

# Serial Reader Init
reader = SerialReader(cfg.mbus.port, cfg.mbus.baudRate, cfg.key, metrics)

#MQTT Init
mqtt_handler = None
if cfg.mqtt.enabled:
    from mqtt_handler import MQTTHandler
    mqtt_handler = MQTTHandler(cfg.mqtt.brokerIP, cfg.mqtt.brokerPort, cfg.mqtt.authentication.username, cfg.mqtt.authentication.password, cfg.mqtt.mqttApiVersion)

influx_handler = None
if cfg.influxdb.enabled:
    from influx_handler import InfluxHandler
    influx_handler = InfluxHandler(cfg.influxdb.serverIP, cfg.influxdb.serverPort, cfg.influxdb.database, cfg.influxdb.authentication.username, cfg.influxdb.authentication.password, cfg.influxdb.version, cfg.influxdb.organization, cfg.influxdb.database)
    
prometheus_handler = None
if cfg.prometheus.enabled:
    from prometheus_handler import PrometheusHandler
    prometheus_handler = PrometheusHandler(cfg.prometheus.port, metrics)

pv = PowerValues()

def process_data_handlers(pv, metrics, cfg, mqtt_handler, influx_handler, prometheus_handler):
    """
    Handles logging, and sending data to MQTT, InfluxDB, and Prometheus.
    """
    # Console Logging of Power Values
    if cfg.logging.console.enabled:
        now = datetime.now()
        logger.info("\n\t\t*** KUNDENSCHNITTSTELLE ***\n\nOBIS Code\tBezeichnung\t\t\t Wert")
        logger.info(now.strftime("%d.%m.%Y %H:%M:%S"))
        for item in pv:
            val = item['valueDisplay']
            if item['unit'] in ['V', 'A']:
                val = round(val, 2)
            logger.info("{0:<14}\t{1:<30} [{2}]:\t {3}".format(item['keySmartmeter'], item['long'], item['unit'], val))
        
        gesamt = pv.get_display_value('MomentanleistungP') - pv.get_display_value('MomentanleistungN')
        logger.info(f"-------------\tWirkleistunggesamt [W]:\t\t {gesamt}")

    # MQTT Handler
    if cfg.mqtt.enabled and mqtt_handler:
        mqtt_handler.ensure_connection()
        all_published = True
        for item in pv:
            if not mqtt_handler.publish(f"{cfg.mqtt.mqttPrefix}{item['mqttTopicName']}", item['valueDisplay']):
                all_published = False

        gesamt = pv.get_display_value('MomentanleistungP') - pv.get_display_value('MomentanleistungN')
        if not mqtt_handler.publish(f"{cfg.mqtt.mqttPrefix}Wirkleistunggesamt", gesamt):
            all_published = False

        metrics.mqtt_last_success = all_published
        if all_published:
            metrics.mqtt_successes += 1
        else:
            metrics.mqtt_failures += 1

    # InfluxDB Handler
    if cfg.influxdb.enabled and influx_handler:
        if cfg.influxdb.sendValues:
            if influx_handler.write_values(pv):
                metrics.influxdb_successes += 1
                metrics.influxdb_last_success = True
            else:
                metrics.influxdb_failures += 1
                metrics.influxdb_last_success = False

        if cfg.influxdb.sendMetrics:
            influx_handler.write_metrics(metrics)

    # Prometheus Handler
    if cfg.prometheus.enabled and prometheus_handler:
        if cfg.prometheus.exposeValues:
            prometheus_handler.update_values(pv)
        if cfg.prometheus.exposeMetrics:
            prometheus_handler.update_metrics()

while 1:
    reader.read(pv)
    process_data_handlers(pv, metrics, cfg, mqtt_handler, influx_handler, prometheus_handler)
