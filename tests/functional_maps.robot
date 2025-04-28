*** Settings ***
Documentation     🗺️ Suite de Tests Automatisés Google Maps sur AAOS
Library            ../keywords/functional_maps.py    WITH NAME    Maps
Library            OperatingSystem
Library            Process

Suite Setup        Log    🚀 Démarrage de la Suite de Tests Maps
Suite Teardown     Log    🏁 Fin de la Suite de Tests Maps

*** Test Cases ***

🔵 Initialisation Appium et Préparation
    Log    🚗 Initialisation Appium
    Maps.setup_appium
    Log    🛡️ Gestion des popups Google Maps
    Maps.gerer_popups_maps
    Log    📍 Forcer la position GPS (Tunis)
    Maps.forcer_position_gps_tunis

🎯 Tests UI Google Maps
    Log    🎯 Test Interface UI Google Maps
    Maps.test_affichage_google_maps
    Maps.test_zoom_buttons
    Maps.test_ouverture_profil
    Maps.test_icones_poi_double_verification

🎯 Tests GPS Google Maps
    Log    🛰️ Exécution des tests GPS Google Maps groupés
    Maps.executer_tests_gps_google_maps

🎯 Tests Recherche Destination
    Log    🔍 Test Recherche Destination Connue
    Maps.test_04_recherche_lieu_connu
    Log    ❌ Test Recherche Sans Résultat
    Maps.test_05_recherche_sans_resultat

🎯 Tests Navigation Dynamique
    Log    🧭 Test Navigation Dynamique jusqu'à Ariana
    Maps.test_06_navigation_itineraire

🔵 Fermeture Session Appium
    Log    📴 Fermeture propre de la session Appium
    Maps.fermer_session_appium
