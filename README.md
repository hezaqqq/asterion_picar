# Robot autonome d'inspection souterraine — Adeept PiCar-B

Robot mobile autonome conçu pour la surveillance et l'inspection d'infrastructures souterraines techniques (tunnels, galeries, réseaux d'assainissement). Il embarque des capteurs infrarouges, un capteur ultrasonique et une caméra pour naviguer, détecter les obstacles et analyser son environnement en temps réel.

---

## Contexte du projet

Les infrastructures souterraines nécessitent des inspections régulières, mais ces environnements sont contraignants : espaces confinés, faible visibilité, risques pour les opérateurs. Ce projet développe une solution robotisée légère et autonome capable de se substituer aux interventions humaines dans ces zones.

## Fonctionnalités

- **Suivi de ligne** — navigation balisée via capteurs infrarouges (IR)
- **Évitement d'obstacles** — détection ultrasonique, arrêt automatique sous 4 cm
- **Vision par ordinateur** — détection de couleur, suivi de ligne par caméra, lecture de panneaux et flèches directionnelles
- **Navigation labyrinthique** — exploration autonome d'un tunnel simulant un réseau souterrain
- **Feux de détresse** — LEDs WS2812 et GPIO clignotantes en cas de blocage

## Architecture du code

| Fichier | Rôle |
|---|---|
| `led_controller.py` | LEDs GPIO (`RobotLEDController`) |
| `WS2812_led_controller.py` | Ruban WS2812 via SPI (`LEDController`) |
| `servo_controller.py` | Servomoteurs PCA9685 (`ServoController`) |
| `motor_controller.py` | Moteurs DC + servo de direction (`MotorController`) |
| `ultrasonic_sensor.py` | Capteur ultrasonique HC-SR04 (`UltrasonicSensor`) |
| `line_reading.py` | Capteurs IR de suivi de ligne (`LineReading`) |
| `robot_controller.py` | Contrôleur principal + arrêt sur obstacle (`RobotController`) |
| `backward.py` | Marche arrière et correction de trajectoire par gyroscope (`GyroSteeringController`) |
| `line_following.py` | Suivi de ligne autonome complet (`LineFollowingController`) |

## Ressources matérielles

| Composant | Détail |
|---|---|
| Plateforme | Adeept PiCar-B (réf. ADR012) |
| Contrôleur | Raspberry Pi |
| Capteur de distance | HC-SR04 (ultrason, GPIO 23/24) |
| Capteurs de ligne | 3× IR (GPIO 17, 27, 22) |
| Servomoteurs | PCA9685 I2C (0x5f, 50 Hz) |
| Moteurs DC | 4× via PCA9685 (1 kHz) |
| LEDs adressables | Ruban WS2812 × 14 (SPI) |
| LEDs GPIO | 9× (GPIO 1–25) |
| ADC gyroscope | ADS7830 I2C (0x48) |

## Prérequis logiciels

```bash
# Dépendances Python
pip install gpiozero spidev numpy smbus adafruit-circuitpython-motor adafruit-circuitpython-pca9685 --break-system-packages

# Vision par ordinateur
pip install opencv-python --break-system-packages
```

Langages utilisés : Python 3, OpenCV.

## Liens

- [Site Adeept](https://www.adeept.com/)
- [Raspberry Pi](https://www.raspberrypi.org/downloads/)
- [Code source Web UI Adeept](https://github.com/adeept/Adeept_Bot_Controller_WebUI.git)


*Adeept — fondée en 2015, spécialisée dans le matériel open source et l'éducation STEM.*
*Marque et logo Adeept © Shenzhen Adeept Technology Co., Ltd.*