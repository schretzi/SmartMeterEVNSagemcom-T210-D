import sys
import os
import time
import paho.mqtt.client as mqtt
import logging

logger = logging.getLogger(__name__)

class MQTTHandler:
    def __init__(self, broker_ip, port, user, password, mqtt_version=1):
        self.connected = False
        
        # Handle paho-mqtt v2 migration
        client_args = {"client_id": "SmartMeter"}
        if hasattr(mqtt, "CallbackAPIVersion"):
            if mqtt_version == 2:
                client_args["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION2
            else:
                client_args["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION1
        
        self.client = mqtt.Client(**client_args)
        
        if user and password:
            self.client.username_pw_set(user, password)
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
                   
        try:
            self.client.connect(broker_ip, int(port), 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Fehler beim Verbinden zum MQTT Broker! {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to MQTT Broker")
            self.connected = True

        elif rc == 5:
            logger.error("MQTT Connection refused: Not authorized")
            self.connected = False

        elif rc == 4:
            logger.error("MQTT Connection refused: Bad username or password")
            self.connected = False

        elif rc == 3:
            logger.error("MQTT Connection refused: Identifier rejected")
            self.connected = False

        elif rc == 2:
            logger.error("MQTT Connection refused: Server unavailable")
            self.connected = False

        elif rc == 1:
            logger.error("MQTT Connection refused: Unacceptable protocol version")
            self.connected = False
            
        else:
            logger.error(f"Failed to connect, return code {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc, properties=None):
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT Broker (RC: {rc})")
        else:
            logger.info("Disconnected from MQTT Broker")
        self.connected = False

    def ensure_connection(self):
        # Connection is handled automatically by loop_start()
        pass

    def publish(self, topic, payload):
        try:
            info = self.client.publish(topic, payload, qos=1)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to queue publish to {topic}, return code {info.rc}")
                return False
            
            info.wait_for_publish(timeout=2)
            if not info.is_published():
                logger.error(f"Failed to publish to {topic} (Timeout or Broker rejected)")
                return False
            return True
        except Exception as e:
            logger.error(f"Exception during publish: {e}")
            return False