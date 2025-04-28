*** Settings ***
Documentation     🎙️ Test Google Assistant pour ouverture du Play Store sur AAOS
Library            ../keywords/Test_micro_Input.py  WITH NAME    AssistantTest
Library            OperatingSystem
Library            Process

Suite Setup        Log    🚀 Démarrage de la suite Assistant Play Store
Suite Teardown     Log    🏁 Fin de la suite Assistant Play Store

*** Test Cases ***

🔵 Initialiser Appium
    Log    🚗 Initialisation Appium
    AssistantTest.setup_appium

🎙️ Ouvrir Google Assistant
    Log    🚀 Ouverture de Google Assistant via ADB
    AssistantTest.ouvrir_google_assistant

🎵 Envoyer Audio "Open Play Store"
    Log    🎙️ Lecture audio pour commande vocale
    AssistantTest.envoyer_audio_open_play_store
    Sleep    7s    # Temps pour laisser l'assistant répondre

🔎 Vérifier ouverture du Play Store
    Log    🔎 Vérification si Play Store est ouvert
    ${playstore_ouvert}=    AssistantTest.verifier_play_store
    Run Keyword If    '${playstore_ouvert}' == 'True'    Log    ✅ Play Store ouvert avec succès
    ...    ELSE    Log    ❌ Play Store non détecté

🔵 Fermer Appium
    Log    🚪 Fermeture propre d'Appium
    AssistantTest.close_appium
