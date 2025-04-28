*** Settings ***
Documentation     🎶 Test Audio Media Player sur Android Automotive OS (AAOS)
Library            ../keywords/test_audio.py    WITH NAME    AudioTest
Library            OperatingSystem
Library            Process

Suite Setup        Log    🚀 Démarrage de la Suite de Tests Audio Media Player
Suite Teardown     Log    🏁 Fin de la Suite de Tests Audio Media Player

*** Test Cases ***

🔵 Initialiser Appium
    Log    🚗 Initialisation Appium
    AudioTest.setup_driver

🎵 Ouvrir Local Media Player
    Log    🎵 Ouverture du Media Player local
    AudioTest.ouvrir_media_player

🔵 Gérer éventuel bouton "Cancel"
    Log    🔵 Vérification et clic éventuel sur 'Cancel'
    AudioTest.cliquer_si_cancel

🎶 Ouvrir catégorie Ringtones
    Log    🎶 Ouverture catégorie Ringtones
    AudioTest.entrer_dans_ringtones

🎶 Sélectionner et lire 'Andromeda'
    Log    🎶 Sélection de la sonnerie 'Andromeda' et démarrage de la lecture
    AudioTest.selectionner_et_lancer_andromeda

🎧 Enregistrer audio AVANT arrêt
    Log    🎧 Capture audio AVANT STOP
    AudioTest.enregistrer_audio    before_stop.wav

🚨 Envoyer STOP au Media Player
    Log    🚨 Envoi du STOP (Pause Media Player)
    Run Process    adb    -s    emulator-5554    shell    input    keyevent    127    shell=True
    Sleep    1s

🎧 Enregistrer audio APRÈS arrêt
    Log    🎧 Capture audio APRÈS STOP
    AudioTest.enregistrer_audio    after_stop.wav

📊 Analyse Audio AVANT
    Log    📊 Analyse détaillée fichier 'before_stop.wav'
    AudioTest.analyser_audio_precis    before_stop.wav    before_stop.png

📊 Analyse Audio APRÈS
    Log    📊 Analyse détaillée fichier 'after_stop.wav'
    AudioTest.analyser_audio_precis    after_stop.wav    after_stop.png

🔙 Revenir au Launcher
    Log    🔙 Retour à l'écran d'accueil AAOS
    AudioTest.revenir_launcher

🔵 Fermer Appium
    Log    🚪 Fermeture propre de la session Appium
    AudioTest.fermer_driver
