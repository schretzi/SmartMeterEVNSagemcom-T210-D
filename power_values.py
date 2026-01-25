class PowerValues:
    def __init__(self):
        self.values = {
            '0100010800FF': { "short": 'WirkenergieP', "long": 'Wirkenergie Bezug', "unit": 'kWh', "factor": 0.001, "mqttTopicName": 'WirkenergieBezug', "keySmartmeter": '1.0.1.8.0.255' },
            '0100020800FF': { "short": 'WirkenergieN', "long": 'Wirkenergie Lieferung', "unit": 'kWh', "factor": 0.001, "mqttTopicName": 'WirkenergieLieferung', "keySmartmeter": '1.0.2.8.0.255' },
            '0100010700FF': { "short": 'MomentanleistungP', "long": 'Wirkleistung Bezug', "unit": 'W', "factor": 1, "mqttTopicName": 'WirkleistungBezug', "keySmartmeter": '1.0.1.7.0.255' },
            '0100020700FF': { "short": 'MomentanleistungN', "long": 'Wirkleistung Lieferung', "unit": 'W', "factor": 1, "mqttTopicName": 'WirkleistungLieferung', "keySmartmeter": '1.0.2.7.0.255' },
            '0100200700FF': { "short": 'SpannungL1', "long": 'Spannung L1', "unit": 'V', "factor": 0.1, "mqttTopicName": 'SpannungL1', "keySmartmeter": '1.0.32.7.0.255' },
            '0100340700FF': { "short": 'SpannungL2', "long": 'Spannung L2', "unit": 'V', "factor": 0.1, "mqttTopicName": 'SpannungL2', "keySmartmeter": '1.0.52.7.0.255' },
            '0100480700FF': { "short": 'SpannungL3', "long": 'Spannung L3', "unit": 'V', "factor": 0.1, "mqttTopicName": 'SpannungL3', "keySmartmeter": '1.0.72.7.0.255' },
            '01001F0700FF': { "short": 'StromL1', "long": 'Strom L1', "unit": 'A', "factor": 0.01, "mqttTopicName": 'StromL1', "keySmartmeter": '1.0.31.7.0.255' },
            '0100330700FF': { "short": 'StromL2', "long": 'Strom L2', "unit": 'A', "factor": 0.01, "mqttTopicName": 'StromL2', "keySmartmeter": '1.0.51.7.0.255' },
            '0100470700FF': { "short": 'StromL3', "long": 'Strom L3', "unit": 'A', "factor": 0.01, "mqttTopicName": 'StromL3', "keySmartmeter": '1.0.71.7.0.255' },
            '01000D0700FF': { "short": 'Leistungsfaktor', "long": 'Leistungsfaktor', "unit": '', "factor": 0.001, "mqttTopicName": 'Leistungsfaktor', "keySmartmeter": '-------------' }
        }
        
        self.short_map = {}

        # Initialize values
        for key in self.values:
            self.values[key]['valueSmartmeter'] = 0
            self.values[key]['valueDisplay'] = 0
            self.short_map[self.values[key]['short']] = key

    def __iter__(self):
        return iter(self.values.values())

    def is_valid_obis(self, obis):
        return obis in self.values

    def set_value(self, obis, raw_value):
        if obis in self.values:
            self.values[obis]['valueSmartmeter'] = raw_value
            self.values[obis]['valueDisplay'] = raw_value * self.values[obis]['factor']

    def get_display_value(self, short_name):
        if short_name in self.short_map:
            return self.values[self.short_map[short_name]]['valueDisplay']
        return 0