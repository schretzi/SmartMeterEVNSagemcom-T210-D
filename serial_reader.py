import serial
import sys
import time
import logging
import xml.etree.ElementTree as ET
from binascii import unhexlify
from Cryptodome.Cipher import AES
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator

logger = logging.getLogger(__name__)

class SerialReader:
    def __init__(self, port, baudrate, key, metrics):
        self.port = port
        self.baudrate = baudrate
        self.key = key
        self.ser = None
        self.translator = GXDLMSTranslator()
        self.metrics = metrics
        self.retry_count = 0
        self._connect()

    def _connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.retry_count = 0
        except Exception as e:
            self.retry_count += 1
            logger.error(f"Failed to open serial port {self.port}: {e} (Attempt {self.retry_count}/5)")
            if self.retry_count >= 5:
                logger.critical("Failed to open serial port 5 times in a row. Exiting.")
                sys.exit(1)

    def _reconnect(self):
        self.metrics.inc_serial_restarts()
        logger.warning("wrong M-Bus Start, restarting")
        time.sleep(2.5)
        try:
            if self.ser:
                self.ser.flushOutput()
                self.ser.close()
                self.ser.open()
            else:
                self._connect()
        except Exception as e:
            logger.error(f"Failed to reconnect serial port: {e}")

    def _decrypt(self, frame, system_title, frame_counter):
        try:
            frame_bytes = unhexlify(frame)
            encryption_key = unhexlify(self.key)
            init_vector = unhexlify(system_title + frame_counter)
            cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
            return cipher.decrypt(frame_bytes).hex()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def _parse_xml(self, xml_data, power_values):
        try:
            root = ET.fromstring(xml_data)
            items = list(root.iter())
            for i, child in enumerate(items):
                if child.tag == 'OctetString' and 'Value' in child.attrib:
                    value = child.attrib['Value']
                    if power_values.is_valid_obis(value):
                        if i + 1 < len(items) and 'Value' in items[i+1].attrib:
                            raw_val = int(items[i+1].attrib['Value'], 16)
                            power_values.set_value(value, raw_val)
        except Exception as e:
            logger.error(f"XML Parsing failed: {e}")

    def read(self, power_values):
        """
        Reads from serial, decrypts, parses XML and updates power_values.
        Blocking call until one full valid frame is processed.
        """
        raw_serial_data = None
        decrypted_apdu = None
        while True:
            try:
                if not self.ser or not self.ser.is_open:
                    self._connect()
                    if not self.ser or not self.ser.is_open:
                        time.sleep(5)
                        continue

                data = self.ser.read(size=282).hex()
                raw_serial_data = data
                decrypted_apdu = None
                
                if not data:
                    continue

                mbus_start = data[0:8]
                
                if not (mbus_start[0:2] == "68" and mbus_start[2:4] == mbus_start[4:6] and mbus_start[6:8] == "68"):
                    self._reconnect()
                    continue
                
                logger.info("Daten ok")

                frame_len = int("0x" + mbus_start[2:4], 16)
                system_title = data[22:38]
                frame_counter = data[44:52]
                frame = data[52:12+frame_len*2]

                apdu = self._decrypt(frame, system_title, frame_counter)
                decrypted_apdu = apdu
                
                if not apdu or apdu[0:4] != "0f80":
                    continue

                xml = self.translator.pduToXml(apdu)
                self._parse_xml(xml, power_values)
                return

            except Exception as e:
                logger.error(f"Error in serial read loop: {e}")
                logger.error(f"Original serial data: {raw_serial_data}")
                if decrypted_apdu:
                    logger.error(f"Decrypted APDU: {decrypted_apdu}")
                else:
                    logger.error("Decrypted APDU: not available")
                self._reconnect()
                time.sleep(1)