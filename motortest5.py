##############################################################################
# Trikolka Mk.2 by Chlupovka Dynamics #          work in progress            #
##############################################################################

##############################################################################
# inspirovano skripty:                                                       #
# https://github.com/recantha/EduKit3-RC-Keyboard/blob/master/rc_keyboard.py #
# https://www.jonwitts.co.uk/archives/896                                    #
# https://forums.raspberrypi.com/viewtopic.php?t=298877                      #
##############################################################################
# aby vse fungovalo, je na modrem gamepadu potreba stisknout tlacitko Analog #
##############################################################################
# diagnostika gamepadu a znaceni tlacitek:                                   #
# příkaz na terminálu "approxeng_input_show_controls"                        #
##############################################################################
# dokumentace Approximate Engineering - Input:                               #
# https://approxeng.github.io/approxeng.input/index.html                     #
##############################################################################

import sys, termios, tty, os, time # hlavni systemove knihovny, asi nejsou vsechny potreba, ale pro jistotu :)
import RPi.GPIO as GPIO # GPIO knihovna, funguje s nasim h-mustkem lepe, nez gpiozero
from approxeng.input.selectbinder import ControllerResource # knihovna approximate engineering pro gamepad

# nastaveni GPIO propojeni s H-mustkem (nazvy promennych odpovidaji znaceni kontaktu na mustku):
in1 = 24
in2 = 23
ena = 25
in3 = 17
in4 = 27
enb = 4

# uvodni nastaveni GPIO:
GPIO.setmode(GPIO.BCM) # metoda cislovani GPIO pinu
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(ena,GPIO.OUT)
GPIO.setup(in3,GPIO.OUT)
GPIO.setup(in4,GPIO.OUT)
GPIO.setup(enb,GPIO.OUT)

# oba motory pro jistotu vypneme
GPIO.output(in1,GPIO.LOW)
GPIO.output(in2,GPIO.LOW)
GPIO.output(in3,GPIO.LOW)
GPIO.output(in4,GPIO.LOW)

# nastaveni pinu pro PWM rizeni otacek obou motoru:
p1 = GPIO.PWM(ena,1000)
p2 = GPIO.PWM(enb,1000)

# promenna s hodnotou nastavene rychlosti (na startu 0%):
dc = 0

# nastavime startovni vykon obou motoru:
p1.start(dc)
p2.start(dc)

# nastaveni serva
control = 19 # ridici pin
GPIO.setup(control, GPIO.OUT)
servo = GPIO.PWM(control, 50) # na servo posilame signal s nizsi frekvenci (50 Hz), nez na motory
servo.start(0) # spustime servo

##### hlavni cast #####
while True:
    with ControllerResource() as joystick: # je-li pripojen gamepad, vytvori se jeho instance s nazvem "joystick"
        print("Gamepad pripojen")
        ##### obecna nastaveni #####
        while joystick.connected:  # cyklus bezi, jen kdyz je pripojen gamepad
            y = joystick['ly'] # ulozeni hodnot osy y leveho kniplu do promenne
            x = joystick['rx'] # ulozeni hodnot osy x praveho kniplu do promenne 
            held = joystick.check_presses() # ulozeni stisknutych tlacitek do promenne 
            x = x * 100. # vynasobeni hodnot osy x, aby se dal jemneji rozlisit pohyb kniplu
            y = y * 100. # vynasobeni hodnot osy y, aby se daly primo prevest na hodnotu PWM pro motory
            print("X:", x, "| Y:", y) # tapetuje konzoli hodnotami os x a y
            servo.ChangeDutyCycle(0) # melo by pomoci aspon trochu snizit "cukani" serva (servo jitter)
            time.sleep(0.05) # mala pauza, ktera zlepsuje citelnost konzole, ale zhorsuje reakcni dobu - v pripade potreby lze zmenit nebo odkomentovat
        ##### rizeni motoru #####    
            if (y > 0): # je-li levy knipl stlaceny nahoru
                p1.ChangeDutyCycle(y) # PWM obou motoru je nastaveno primo na vynasobenou hodnotu osy y 
                p2.ChangeDutyCycle(y)
                GPIO.output(in1,GPIO.HIGH) # motor 1 jede dopredu
                GPIO.output(in2,GPIO.LOW) # motor 1 jede dopredu
                GPIO.output(in3,GPIO.HIGH) # motor 2 jede dopredu
                GPIO.output(in4,GPIO.LOW) # motor 2 jede dopredu
            if (y < 0): # je-li levy knipl stlaceny dolu
                p1.ChangeDutyCycle(abs(y)) # osa y se musi pro oba motory prevest na absolutni hodnotu (odstrani se minus), jinak by skript nahlasil chybu, ze PWM nemuze byt zaporne
                p2.ChangeDutyCycle(abs(y))
                GPIO.output(in1,GPIO.LOW) # motor 1 jede dozadu
                GPIO.output(in2,GPIO.HIGH) # motor 1 jede dozadu
                GPIO.output(in3,GPIO.LOW) # motor 2 jede dozadu
                GPIO.output(in4,GPIO.HIGH) # motor 2 jede dozadu
        ##### rizeni serva #####
            if x > 10:  # je-li joystick stlaceny doprava (hodnota 10 dovoli mit kolem nuly "mrtvou" zonu, na kterou servo nereaguje)
                servo.ChangeDutyCycle(7) # hodnota 7 otoci servo 
                time.sleep(0.1)
                servo.ChangeDutyCycle(0)
            if x < -10: # je-li joystick stlaceny doleva (hodnota -10 dovoli mit kolem nuly "mrtvou" zonu, na kterou servo nereaguje)
                servo.ChangeDutyCycle(12) # hodnota 12 otoci servo
                time.sleep(0.1)
                servo.ChangeDutyCycle(0)
            if x > -10 and x < 10: # "mrtva" zona kolem stredu osy x, servo nereaguje
                servo.ChangeDutyCycle(9) # hodnota 9 servo vycentruje
                time.sleep(0.1)
                servo.ChangeDutyCycle(0) 
        ##### stisky tlacitek #####
            if held['r1']: # je-li stisknuto pravy spodni trigger
                p1.ChangeDutyCycle(0) # vypne oba motory - pro pripad, ze kvuli sleepu nastavenemu vyse nezaznamena skript spravne rychle vynulovani kniplu
                p2.ChangeDutyCycle(0)
                GPIO.output(in1,GPIO.LOW) # pro jistotu vypneme oba motory i takto :)
                GPIO.output(in2,GPIO.LOW)
                GPIO.output(in3,GPIO.LOW)
                GPIO.output(in4,GPIO.LOW)
            if held['r2']: # je-li stisknuto tlacitko "Start"
                print("KONEC!")
                GPIO.cleanup() # uvolnime GPIO
                exit(0) # vypneme skript