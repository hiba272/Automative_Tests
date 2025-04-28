*** Settings ***
Documentation     ❄️ Tests Fonctionnels HVAC (Climatisation) via Appium, OCR, et YOLO
Library            ../keywords/functional_hvac.py    WITH NAME    HVAC
Library            OperatingSystem
Library            Process

Suite Setup        Log    🚀 Démarrage des tests HVAC
Suite Teardown     Log    🏁 Fin des tests HVAC

*** Test Cases ***

🔵 Setup Appium
    Log    🚗 Initialisation Appium
    HVAC.setup_appium

🔵 Ouvrir la barre de climatisation
    Log    📌 Ouverture de la barre climatisation
    HVAC.ouvrir_barre_climatisation

🧪 Tester température gauche (OCR + Crop)
    Log    🧪 Test Température Gauche (OCR)
    HVAC.executer_test_temperature_gauche

🧪 Tester température droite (Lecture directe Appium)
    Log    🧪 Test Température Droite (Appium)
    HVAC.executer_test_temperature_droite

🧪 Tester bouton AUTO avec YOLO
    Log    🧪 Test bouton AUTO (détection visuelle YOLO)
    HVAC.test_bouton_auto_verifie_yolo

🧪 Activer/Désactiver Climatisation AC
    Log    🧪 Activer / Désactiver AC
    HVAC.activer_desactiver_climatisation

🔵 Fermer la barre de climatisation
    Log    📌 Fermeture de la barre climatisation
    HVAC.fermer_barre_climatisation

🔵 Fermer Appium
    Log    📴 Fermeture session Appium
    HVAC.fermer_appium
