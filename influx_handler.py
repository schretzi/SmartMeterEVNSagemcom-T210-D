import sys
import os
import time
import logging

logger = logging.getLogger(__name__)

class InfluxHandler:
    def __init__(self, host, port, database, user, password, version, organisation, dbname):
        self.host = host
        self.port = port
        self.database = database
        self.client = None
        self.user = user
        self.password = password
        self.version = int(version)
        self.dbname = dbname
        self.organisation = organisation

        self.url = f"http://{self.host}:{self.port}"

        if self.version == 1:
            try:
                from influxdb import InfluxDBClient
                self.client = InfluxDBClient(host=self.host, port=self.port, username=self.user, password=self.password, database=self.database)
            except Exception as err:
                logger.error(f"Kann nicht mit InfluxDB v1 verbinden! Fehler: {err}")

        elif self.version == 2 or self.version == 3:
            try:
                from influxdb_client import InfluxDBClient
                from influxdb_client.client.write_api import SYNCHRONOUS
                
                self.client = InfluxDBClient(url=self.url, token=self.password, org=self.organisation)
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

            except Exception as err:
                logger.error(f"Kann nicht mit InfluxDB v{self.version} verbinden! Fehler: {err}")

    def write_values(self, pv):
        if self.version == 1:
            if not self.client:
                logger.error("InfluxDB Client not initialized")
                return False

            try:
                mytime = int(time.time()*1000000000)
                json_body = [
                {
                    "measurement": "Wirkenergie",
                    "fields": {
                        "Bezug": pv.get_display_value('WirkenergieP'),
                        "Lieferung": pv.get_display_value('WirkenergieN')
                    },
                    "time": mytime
                },
                {
                    "measurement": "Momentanleistung",
                    "fields": {
                        "Bezug": pv.get_display_value('MomentanleistungP'),
                        "Lieferung": pv.get_display_value('MomentanleistungN'),
                        "Gesamt": pv.get_display_value('MomentanleistungP') - pv.get_display_value('MomentanleistungN')
                    },
                    "time": mytime
                },
                {
                    "measurement": "Spannung",
                    "fields": {
                        "L1": pv.get_display_value('SpannungL1'),
                        "L2": pv.get_display_value('SpannungL2'),
                        "L3": pv.get_display_value('SpannungL3'),
                    },
                    "time": mytime
                },
                {
                    "measurement": "Strom",
                    "fields": {
                        "L1": pv.get_display_value('StromL1'),
                        "L2": pv.get_display_value('StromL2'),
                        "L3": pv.get_display_value('StromL3'),
                    },
                    "time": mytime
                },
                {
                    "measurement": "Leistungsfaktor",
                    "fields": {
                        "value": pv.get_display_value('Leistungsfaktor')
                    },
                    "time": mytime
                }
                ]
                self.client.write_points(json_body, database=self.database)
                return True
            except BaseException as err:
                logger.error(f"Es ist ein Fehler aufgetreten. Fehler: {err}")
                return False
        elif self.version == 2 or self.version == 3:
            if not hasattr(self, 'write_api') or not self.write_api:
                logger.error("InfluxDB Write API not initialized")
                return False
            try:
                from influxdb_client import Point
                mytime = int(time.time()*1000000000)
                
                points = []
                
                point1 = Point("Wirkenergie").field("Bezug", pv.get_display_value('WirkenergieP')).field("Lieferung", pv.get_display_value('WirkenergieN')).time(mytime)
                points.append(point1)
                
                point2 = Point("Momentanleistung").field("Bezug", pv.get_display_value('MomentanleistungP')).field("Lieferung", pv.get_display_value('MomentanleistungN')).field("Gesamt", pv.get_display_value('MomentanleistungP') - pv.get_display_value('MomentanleistungN')).time(mytime)
                points.append(point2)
                
                point3 = Point("Spannung").field("L1", pv.get_display_value('SpannungL1')).field("L2", pv.get_display_value('SpannungL2')).field("L3", pv.get_display_value('SpannungL3')).time(mytime)
                points.append(point3)
                
                point4 = Point("Strom").field("L1", pv.get_display_value('StromL1')).field("L2", pv.get_display_value('StromL2')).field("L3", pv.get_display_value('StromL3')).time(mytime)
                points.append(point4)
                
                point5 = Point("Leistungsfaktor").field("value", pv.get_display_value('Leistungsfaktor')).time(mytime)
                points.append(point5)
                
                self.write_api.write(bucket=self.database, record=points)
                return True
            except BaseException as err:
                logger.error(f"Es ist ein Fehler aufgetreten. Fehler: {err}")
                return False

        else:
            logger.error("Ungültige InfluxDB Version angegeben!")
            return False

    def write_metrics(self, metrics):
        if not self.client:
            logger.error("InfluxDB Client not initialized")
            return False
        
        try:
            mytime = int(time.time()*1000000000)
            
            fields = {
                "uptime_seconds": metrics.get_uptime(),
                "serial_restarts": metrics.serial_restarts,
                "mqtt_last_success": 1 if metrics.mqtt_last_success else 0,
                "mqtt_failures": metrics.mqtt_failures,
                "mqtt_successes": metrics.mqtt_successes,
                "influxdb_last_success": 1 if metrics.influxdb_last_success else 0,
                "influxdb_failures": metrics.influxdb_failures,
                "influxdb_successes": metrics.influxdb_successes
            }

            if self.version == 1:
                json_body = [{"measurement": "app_metrics", "fields": fields, "time": mytime}]
                self.client.write_points(json_body, database=self.database)

            elif self.version == 2 or self.version == 3:
                if not hasattr(self, 'write_api') or not self.write_api:
                    logger.error("InfluxDB Write API not initialized")
                    return False
                
                from influxdb_client import Point
                point = Point("app_metrics").time(mytime)
                for key, value in fields.items():
                    point.field(key, value)
                self.write_api.write(bucket=self.database, record=point)
            
            return True
        except BaseException as err:
            logger.error(f"Fehler beim Schreiben der App-Metriken: {err}")
            return False
