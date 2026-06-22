import servo_controller as servo_module
import time

s = servo_module.ServoController()
s.set_angle(1, 90)
time.sleep(1)
print("Demandé: 90")
input("Vérifie visuellement la position, puis Entrée...")

s.set_angle(1, 54)
time.sleep(1)
print("Demandé: 54")
input("Vérifie visuellement, puis Entrée...")

s.set_angle(1, 18)
time.sleep(1)
print("Demandé: 18")
input("Vérifie visuellement — est-ce que ça force/bute ?")