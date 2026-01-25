import sys
import logging
from prometheus_client import start_http_server, Gauge

logger = logging.getLogger(__name__)

class PrometheusHandler:
    def __init__(self, port, metrics):
        self.port = int(port)
        self.metrics = metrics
        self.gauges = {}
        self.app_metrics = {
            'uptime_seconds': Gauge('smartmeter_app_uptime_seconds', 'Application uptime in seconds.'),
            'serial_restarts_total': Gauge('smartmeter_app_serial_restarts_total', 'Total number of serial connection restarts.'),
            'mqtt_write_success': Gauge('smartmeter_app_mqtt_write_success', 'Status of the last MQTT write cycle (1 for success, 0 for failure).'),
            'mqtt_write_failures_total': Gauge('smartmeter_app_mqtt_write_failures_total', 'Total number of failed MQTT write cycles.'),
            'mqtt_write_successes_total': Gauge('smartmeter_app_mqtt_write_successes_total', 'Total number of successful MQTT write cycles.'),
            'influxdb_write_success': Gauge('smartmeter_app_influxdb_write_success', 'Status of the last InfluxDB write (1 for success, 0 for failure).'),
            'influxdb_write_failures_total': Gauge('smartmeter_app_influxdb_write_failures_total', 'Total number of failed InfluxDB writes.'),
            'influxdb_write_successes_total': Gauge('smartmeter_app_influxdb_write_successes_total', 'Total number of successful InfluxDB writes.')
        }

        try:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            sys.exit(1)

    def update_values(self, pv):
        # Update gauges for each value in PowerValues
        for item in pv:
            key = item['short']
            if key not in self.gauges:
                self.gauges[key] = Gauge(key, item['long'])
            
            self.gauges[key].set(item['valueDisplay'])
            
        # Calculate and update total power
        gesamt = pv.get_display_value('MomentanleistungP') - pv.get_display_value('MomentanleistungN')
        key_gesamt = 'Wirkleistunggesamt'
        if key_gesamt not in self.gauges:
             self.gauges[key_gesamt] = Gauge(key_gesamt, 'Wirkleistung Gesamt')
        self.gauges[key_gesamt].set(gesamt)

    def update_metrics(self):
        self.app_metrics['uptime_seconds'].set(self.metrics.get_uptime())
        self.app_metrics['serial_restarts_total'].set(self.metrics.serial_restarts)
        self.app_metrics['mqtt_write_success'].set(1 if self.metrics.mqtt_last_success else 0)
        self.app_metrics['mqtt_write_failures_total'].set(self.metrics.mqtt_failures)
        self.app_metrics['mqtt_write_successes_total'].set(self.metrics.mqtt_successes)
        self.app_metrics['influxdb_write_success'].set(1 if self.metrics.influxdb_last_success else 0)
        self.app_metrics['influxdb_write_failures_total'].set(self.metrics.influxdb_failures)
        self.app_metrics['influxdb_write_successes_total'].set(self.metrics.influxdb_successes)
