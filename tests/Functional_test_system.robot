*** Settings ***
Library           ../keywords/Functional_test_system.py
Library           OperatingSystem
Library           Process

Suite Setup       Setup Suite
Suite Teardown    Teardown Suite
Test Setup        Open AAOS Settings
Test Teardown     Close AAOS Settings

*** Variables ***
${AAOS_DRIVER}          None
${PHONE_DRIVER}         None

${PHONE_UDID}           emulator-5556
${AAOS_UDID}            emulator-5554

*** Test Cases ***

🔵 Tester Bluetooth AAOS
    [Documentation]    Teste activation/désactivation du Bluetooth sur l'émulateur AAOS.
    full_bluetooth_test    ${AAOS_DRIVER}    ${AAOS_UDID}    aaos

🔗 Tester Bluetooth Pairing
    [Documentation]    Teste l'appairage Bluetooth entre le téléphone et AAOS.
    test_bluetooth_pairing

📶 Tester Wi-Fi
    [Documentation]    Teste l'activation/désactivation du Wi-Fi avec OCR AndroidWifi.
    test_wifi_connection    ${AAOS_DRIVER}

☀️ Tester Brightness Slider
    [Documentation]    Teste le curseur de luminosité.
    test_brightness_slider_functionality    ${AAOS_DRIVER}

🌗 Tester Adaptive Brightness
    [Documentation]    Teste la luminosité adaptative.
    test_adaptive_brightness_functionality    ${AAOS_DRIVER}

📅 Tester Changement de Date
    [Documentation]    Teste le changement manuel de la date.
    test_date_change    ${AAOS_DRIVER}

⏰ Tester Changement d'Heure
    [Documentation]    Teste le changement manuel de l'heure.
    test_time_change    ${AAOS_DRIVER}

🌍 Tester Changement de Langue
    [Documentation]    Teste le changement de langue FR ➔ EN ➔ FR.
    change_language_cycle    ${AAOS_DRIVER}

*** Keywords ***

Setup Suite
    Log    🚀 Initialisation Appium Driver pour AAOS
    ${AAOS_DRIVER}=    init_driver    ${AAOS_UDID}    emulator-5554
    Set Suite Variable    ${AAOS_DRIVER}
    Sleep    3s

Teardown Suite
    Log    🚪 Fermeture Appium Driver AAOS
    Run Keyword If    '${AAOS_DRIVER}' != 'None'    ${AAOS_DRIVER}.quit()
    Sleep    2s

Open AAOS Settings
    Log    🚀 Ouverture de Settings AAOS via adb
    Run Process    adb    -s    ${AAOS_UDID}    shell    am start -n com.android.car.settings/com.android.car.settings.Settings_Launcher_Homepage
    Sleep    2s

Close AAOS Settings
    Log    🚪 Fermeture de Settings AAOS via adb
    Run Process    adb    -s    ${AAOS_UDID}    shell    am force-stop com.android.car.settings
    Sleep    2s
