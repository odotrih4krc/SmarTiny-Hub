import machine
import network
import socket
import time
import dht
import sdcard
import os

led = machine.Pin(15, machine.Pin.OUT)
dht_sensor = dht.DHT11(machine.Pin(14))

def load_config():
    with open('config.txt', 'r') as f:
        config = {}
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    return config

config = load_config()
SSID = config['SSID']
PASSWORD = config['PASSWORD']

spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(13), mosi=machine.Pin(15), miso=machine.Pin(14))
sd = sdcard.SDCard(spi, machine.Pin(12))
os.mount(sd, "/sd")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

print("Connected to Wi-Fi:", wlan.ifconfig())

html = """
<!DOCTYPE html>
<html>
<head>
    <title>SmarTiny Home</title>
</head>
<body>
    <h1>SmarTiny Lights</h1>
    <h2>LED Control</h2>
    <form>
        <input type="button" value="Turn ON" onclick="fetch('/led/on')">
        <input type="button" value="Turn OFF" onclick="fetch('/led/off')">
    </form>
    <h2>Temperature and Humidity</h2>
    <p id="sensor"></p>
    <script>
        setInterval(() => {
            fetch('/sensor').then(response => response.text()).then(data => {
                document.getElementById('sensor').innerHTML = data;
            });
        }, 2000);
    </script>
</body>
</html>
"""

addr = socket.getaddrinfo('0.0.0.0', 80)[0]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("Listening on", addr)

def save_data(temperature, humidity):
    with open("/sd/data.csv", "a") as f:
        f.write("{},{}\n".format(temperature, humidity))

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = cl.recv(1024)
    request = str(request)
    print("Request:", request)
    
    if '/led/on' in request:
        led.on()
    if '/led/off' in request:
        led.off()
    if '/sensor' in request:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        response = "Temperature: {}°C, Humidity: {}%".format(temperature, humidity)
        cl.send(response.encode())
        save_data(temperature, humidity)
    else:
        cl.send(html.encode())

    cl.close()
    
    time.sleep(3600)