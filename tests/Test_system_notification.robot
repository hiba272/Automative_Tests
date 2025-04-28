*** Settings ***
Library           ../keywords/Test_system_notification.py
Library           OperatingSystem
Library           Process

Suite Setup       Setup Appium Session
Suite Teardown    Close Appium Session
Test Setup        Open Notifications Panel
Test Teardown     Close Notifications Panel

*** Variables ***
${SCREENSHOT_NAME}      notification_test_final.png

*** Test Cases ***

🔔 Vérifier Notifications par ADB
    [Documentation]    Vérifie si une notification est détectée via ADB.
    ${result}=    check_notification_with_adb
    Run Keyword If    not ${result}    Fail    ❌ Aucune notification détectée via ADB !

🔔 Vérifier Notifications par OCR
    [Documentation]    Vérifie si une notification est détectée via PaddleOCR.
    ${result}=    check_notification_with_ocr
    Run Keyword If    not ${result}    Fail    ❌ Aucune notification détectée via OCR !

📸 Capturer Capture d'Écran
    [Documentation]    Capture une capture d'écran pour analyse manuelle.
    capture_screenshot    ${SCREENSHOT_NAME}

*** Keywords ***

Setup Appium Session
    Log    🚀 Démarrage session Appium
    setup_appium

Close Appium Session
    Log    🚪 Fermeture session Appium
    close_app

Open Notifications Panel
    Log    📩 Ouverture du panneau Notifications
    open_notifications

Close Notifications Panel
    Log    🚪 Fermeture du panneau Notifications
    close_notifications
