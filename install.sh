#!/bin/bash

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Determine the actual user (if run via sudo)
REAL_USER=${SUDO_USER:-$USER}

echo "Starting installation for user: $REAL_USER"

# Update package lists
apt-get update

# --- Python Environment Setup ---
echo "------------------------------------------------"
echo "Python Environment Setup"
echo "1) Use System Python (installs packages globally)"
echo "2) Use Virtual Environment (venv) - Recommended"
read -p "Select an option (1 or 2): " py_option

if [ "$py_option" == "2" ]; then
    echo "Installing python3-venv..."
    apt-get install -y python3-venv python3-pip

    VENV_DIR="$(pwd)/.venv"
    echo "Creating virtual environment in $VENV_DIR..."
    
    # Create venv as the real user to avoid permission issues later
    sudo -u "$REAL_USER" python3 -m venv "$VENV_DIR"
    
    echo "Installing requirements into venv..."
    if [ -f "requirements.txt" ]; then
        sudo -u "$REAL_USER" "$VENV_DIR/bin/pip" install -r requirements.txt
    else
        echo "Warning: requirements.txt not found in current directory."
    fi
    
    echo "Virtual environment setup complete."
    echo "To run the application, use: $VENV_DIR/bin/python3 smartmeter.py"

else
    echo "Installing python3-pip..."
    apt-get install -y python3-pip
    
    echo "Installing requirements globally..."
    if [ -f "requirements.txt" ]; then
        # Using --break-system-packages for newer Debian/Raspbian versions
        pip3 install -r requirements.txt --break-system-packages
    else
        echo "Warning: requirements.txt not found in current directory."
    fi
fi

# --- Server Installations ---
echo "------------------------------------------------"
echo "Server Installations"

# InfluxDB
read -p "Install InfluxDB? (y/n): " install_influx
if [[ $install_influx =~ ^[Yy]$ ]]; then
    echo "Installing InfluxDB..."
    apt-get install -y influxdb influxdb-client
    systemctl unmask influxdb
    systemctl enable influxdb
    systemctl start influxdb
    echo "InfluxDB installed and started."
fi

# Grafana
read -p "Install Grafana? (y/n): " install_grafana
if [[ $install_grafana =~ ^[Yy]$ ]]; then
    echo "Installing Grafana..."
    # Add Grafana repo
    apt-get install -y apt-transport-https software-properties-common wget
    mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list
    apt-get update
    apt-get install -y grafana
    systemctl enable grafana-server
    systemctl start grafana-server
    echo "Grafana installed and started."
fi

# Loki (via Grafana repo)
read -p "Install Loki? (y/n): " install_loki
if [[ $install_loki =~ ^[Yy]$ ]]; then
    echo "Installing Loki..."
    # Add Grafana repo if not present
    apt-get install -y apt-transport-https software-properties-common wget
    mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list
    apt-get update
    apt-get install -y loki
    systemctl enable loki
    systemctl start loki
    echo "Loki installed and started."
fi

# Prometheus
read -p "Install Prometheus? (y/n): " install_prom
if [[ $install_prom =~ ^[Yy]$ ]]; then
    echo "Installing Prometheus..."
    apt-get install -y prometheus
    systemctl enable prometheus
    systemctl start prometheus
    echo "Prometheus installed and started."
fi

# Mosquitto
read -p "Install Mosquitto (MQTT Broker)? (y/n): " install_mqtt
if [[ $install_mqtt =~ ^[Yy]$ ]]; then
    echo "Installing Mosquitto..."
    apt-get install -y mosquitto mosquitto-clients
    systemctl enable mosquitto
    systemctl start mosquitto
    echo "Mosquitto installed and started."
fi

# --- Log Directory Setup ---
echo "------------------------------------------------"
echo "Setting up log directory..."
LOG_DIR="/var/log/smartmeter"

if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "Created $LOG_DIR"
fi

# Set permissions
chown -R "$REAL_USER":"$REAL_USER" "$LOG_DIR"
chmod -R 755 "$LOG_DIR"
echo "Permissions set for user $REAL_USER on $LOG_DIR"

echo "------------------------------------------------"
echo "Installation finished."