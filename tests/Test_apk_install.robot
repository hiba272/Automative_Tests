*** Settings ***
Documentation    📦 Test Installation, Vérification, Lancement et Désinstallation APK sur Android Automotive OS
Library          ../keywords/Test_apk_install.py    WITH NAME    APKTest
Library          OperatingSystem
Library          Process

Suite Setup      Log    🚀 Démarrage de la Suite de Tests Installation APK
Suite Teardown   Log    🏁 Fin de la Suite de Tests Installation APK

*** Test Cases ***

🔵 Installer l'application APK
    Log    📦 Installation APK
    APKTest.installer_application    C:/Users/hibac/Desktop/simple_file_manager.apk

🔎 Vérification installation via pm list
    Log    🔎 Vérification via 'pm list packages'
    APKTest.verifier_installation_pm    com.simplemobiletools.filemanager

🔎 Vérification installation via dumpsys package
    Log    🔎 Vérification via 'dumpsys package'
    APKTest.verifier_installation_dumpsys    com.simplemobiletools.filemanager

🔎 Vérification de l'Activity principale
    Log    🔎 Vérification de l'Activity principale
    APKTest.verifier_activity    com.simplemobiletools.filemanager    com.simplemobiletools.filemanager.activities.MainActivity

🚀 Lancer l'application
    Log    🚀 Lancement de l'application APK
    APKTest.lancer_application    com.simplemobiletools.filemanager    com.simplemobiletools.filemanager.activities.MainActivity

🛢️ Désinstaller l'application
    Log    🛢️ Désinstallation de l'application
    APKTest.desinstaller_application    com.simplemobiletools.filemanager
