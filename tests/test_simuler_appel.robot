*** Settings ***
Library           ../keywords/test_simuler_appel.py
Library           OperatingSystem
Library           Process

Suite Setup       Setup Appium Session
Suite Teardown    Close Appium Session
Test Setup        No Operation
Test Teardown     No Operation

*** Variables ***
${NUMERO_SIMULE}      123456

*** Test Cases ***

📞 Tester Simulation Appel et Détection OCR
    [Documentation]    Simule un appel GSM entrant et détecte via OCR si l'appel est affiché à l'écran.
    test_simuler_et_verifier_appel    ${NUMERO_SIMULE}

*** Keywords ***

Setup Appium Session
    Log    🚀 Démarrage session Appium
    setup_appium

Close Appium Session
    Log    🚪 Fermeture session Appium
    fermer_appium
