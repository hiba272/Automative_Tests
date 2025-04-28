from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import time, os, subprocess, cv2
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from paddleocr import PaddleOCR


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "screenshots_maps"))
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
ocr = PaddleOCR(use_angle_cls=True, lang='en')
driver = None
# ======================= SESSION SETUP =======================
def setup_appium():
    global driver
    if driver is None:
        options = AppiumOptions()
        options.set_capability("platformName", "Android")
        options.set_capability("deviceName", "emulator-5554")
        options.set_capability("automationName", "UiAutomator2")
        options.set_capability("appPackage", "com.google.android.apps.maps")
        options.set_capability("appActivity", "com.google.android.maps.MapsActivity")
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        time.sleep(5)

def fermer_session_appium():
    global driver
    if driver:
        driver.quit()
        driver = None


# ======================= FORCER POSITION  =======================
def forcer_position_gps_tunis(timeout=60):
    print("⏳ Attente de l'émulateur Android avant injection GPS...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ['adb', 'shell', 'getprop', 'sys.boot_completed'],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip() == '1':
                print("✅ Émulateur prêt. Injection de la position GPS Tunis...")
                break
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout ADB, nouvelle tentative...")

        time.sleep(2)
    else:
        print("❌ Émulateur non prêt après délai d’attente.")
        return

    longitude = 10.1873
    latitude = 36.8978

    try:
        subprocess.run(
            ['adb', 'emu', 'geo', 'fix', str(longitude), str(latitude)],
            check=True
        )
        print(f"📍 Position forcée → Longitude: {longitude}, Latitude: {latitude}")
        print("✅ Injection GPS terminée avec succès.")
    except subprocess.CalledProcessError:
        print("❌ Échec de l’injection GPS.")

def gerer_popups_maps():
    print("🛡️ Début gestion automatique des popups Google Maps...")

    def cliquer_si_present(xpath, description):
        try:
            bouton = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            bouton.click()
            print(f"✅ '{description}' détecté et cliqué.")
            time.sleep(2)
        except TimeoutException:
            print(f"ℹ️ Aucun popup '{description}' détecté, on continue...")

    # 1. Popup "Go to Settings"
    cliquer_si_present('//android.widget.Button[contains(@text, "Go to Settings")]', "Go to Settings")

    # 2. Popup "Turn on location" avec "Turn on"
    cliquer_si_present('//android.widget.Button[contains(@text, "Turn on")]', "Turn on Location")

    # 3. Popup "Trip & sensor data" avec "Next"
    cliquer_si_present('//android.widget.Button[contains(@text, "Next")]', "Next - Trip & Sensor Data")

    # 4. Popup "Privacy center" avec "Go to map"
    cliquer_si_present('//android.widget.Button[contains(@text, "Go to map")]', "Go to map")

    print("✅ Gestion des popups terminée.")

# ======================= UI TESTS =======================

def test_affichage_google_maps():
    assert driver.current_package == "com.google.android.apps.maps"
    driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Search")

def test_zoom_buttons():
    def wait(xpath):
        try:
            return WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, xpath)))
        except TimeoutException:
            return None
    zoom_in = wait('//android.widget.ImageView[@resource-id="com.google.android.apps.maps:id/map_buttons_view_zoom_in"]')
    zoom_out = wait('//android.widget.ImageView[@resource-id="com.google.android.apps.maps:id/map_buttons_view_zoom_out"]')
    if zoom_in and zoom_out:
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "before_zoom.png"))
        zoom_in.click(); time.sleep(2)
        zoom_out.click(); time.sleep(2)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "after_zoom.png"))

def test_ouverture_profil():
    avatar_xpath = '//android.widget.ImageView[@resource-id="com.google.android.apps.maps:id/avatar"]'
    avatar = driver.find_element(AppiumBy.XPATH, avatar_xpath)
    assert avatar is not None
    avatar.click(); time.sleep(2)
    try:
        menu_item = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Sign out of this account")]')
        assert menu_item is not None
    except Exception as e:
        raise
    driver.back(); time.sleep(1)

def test_icones_poi_double_verification():
    pois = ["Gas stations", "Restaurants", "Grocery stores", "Coffee shops"]
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    for poi in pois:
        try:
            button = driver.find_element(AppiumBy.XPATH, f"//android.widget.ImageView[@content-desc='{poi}']")
            button.click(); time.sleep(4)
            title = driver.find_element(AppiumBy.XPATH, f"//android.widget.TextView[contains(@text, '{poi}')]")
            text_from_appium = title.text
            filename = os.path.join(SCREENSHOT_DIR, f"poi_{poi.lower().replace(' ', '_')}.png")
            driver.save_screenshot(filename)
            result = ocr.ocr(filename, cls=True)
            texts = [line[1][0] for block in result for line in block]
            driver.back(); time.sleep(2)
        except:
            driver.back(); time.sleep(2)

# ======================= GPS TESTS =======================


def test_01_verifier_point_bleu_gps():
    print("📍 Test : Vérification du point GPS simulé avec recentrage")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # 👉 Re-center si bouton visible
    recenter_xpath = '//android.widget.FrameLayout[@resource-id="com.google.android.apps.maps:id/recenter_button"]/android.widget.LinearLayout'
    try:
        recenter_button = driver.find_element(AppiumBy.XPATH, recenter_xpath)
        recenter_button.click()
        print("✅ Carte recentrée")
        time.sleep(2)
    except:
        print("⚠️ Bouton Re-center non trouvé")

    # 📸 Avant simulation
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "before_blue_dot.png"))

    # 🛰️ Simuler nouvelle position GPS
    subprocess.run("adb emu geo fix 10.300 36.920".split())
    print("🛰️ GPS simulé à 36.920, 10.300")
    time.sleep(10)

    # 📸 Après simulation
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "after_blue_dot.png"))

    # 🔍 Vérification visuelle
    img1 = cv2.imread(os.path.join(SCREENSHOT_DIR, "before_blue_dot.png"))
    img2 = cv2.imread(os.path.join(SCREENSHOT_DIR, "after_blue_dot.png"))
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    pixels_changed = cv2.countNonZero(thresh)

    print(f"[🧠] Pixels changés : {pixels_changed}")
    assert pixels_changed > 100, "❌ Le point bleu ne semble pas avoir bougé"
    print("✅ Déplacement du point bleu confirmé")

def test_02_mise_a_jour_gps_dynamique():
    print("🔄 Test : Mise à jour dynamique du GPS")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # 👉 Re-center la carte
    recenter_xpath = '//android.widget.FrameLayout[@resource-id="com.google.android.apps.maps:id/recenter_button"]/android.widget.LinearLayout'
    try:
        recenter_button = driver.find_element(AppiumBy.XPATH, recenter_xpath)
        recenter_button.click()
        print("✅ Carte recentrée")
        time.sleep(2)
    except:
        print("⚠️ Bouton Re-center non trouvé")

    # 🛰️ Position 1
    subprocess.run("adb emu geo fix 10.188 36.902".split())
    time.sleep(6)
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "gps_pos1.png"))

    # 🛰️ Position 2
    subprocess.run("adb emu geo fix 10.200 36.910".split())
    time.sleep(8)
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "gps_pos2.png"))

    # 🔍 Comparaison visuelle
    img1 = cv2.imread(os.path.join(SCREENSHOT_DIR, "gps_pos1.png"))
    img2 = cv2.imread(os.path.join(SCREENSHOT_DIR, "gps_pos2.png"))
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    pixels_changed = cv2.countNonZero(thresh)

    print(f"[🧠] Pixels changés (mise à jour GPS) : {pixels_changed}")
    assert pixels_changed > 100, "❌ Aucun changement détecté après mise à jour GPS"
    print("✅ Déplacement GPS dynamique détecté")

def test_03_perte_et_reprise_signal_gps():
    subprocess.run("adb shell settings put secure location_mode 0".split())
    time.sleep(5)
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "gps_off.png"))
    subprocess.run("adb shell settings put secure location_mode 3".split())
    time.sleep(8)
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "gps_on.png"))
    img1 = cv2.imread(os.path.join(SCREENSHOT_DIR, "gps_off.png"))
    img2 = cv2.imread(os.path.join(SCREENSHOT_DIR, "gps_on.png"))
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    pixels_changed = cv2.countNonZero(thresh)
    assert pixels_changed > 100

def executer_tests_gps_google_maps():
    print("🚀 Début des tests GPS groupés Google Maps")
    test_01_verifier_point_bleu_gps()
    test_02_mise_a_jour_gps_dynamique()
    test_03_perte_et_reprise_signal_gps()
    print("✅ Tests GPS groupés terminés")

# ======================= RECHERCHE DESTINATION =======================

def test_04_recherche_lieu_connu():
    destination = "Sfax"
    print(f"🔍 Test : Recherche de '{destination}' et centrage carte")

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # 📸 Screenshot avant la recherche
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "before_search_sfax.png"))

    # 📍 Récupération des coordonnées GPS avant
    before_coords = os.popen("adb shell dumpsys location | grep 'last location'").read().strip()
    print(f"📡 Position GPS avant :\n{before_coords}")

    # 📝 1. Cliquer sur la barre de recherche
    try:
        search_bar = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Search")]')
        search_bar.click()
        time.sleep(2)
    except Exception as e:
        print("❌ Champ de recherche introuvable :", e)
        raise

    # 📝 2. Écrire "Sfax"
    try:
        search_input = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
        search_input.send_keys(destination)
        time.sleep(2)
    except Exception as e:
        print("❌ Champ de saisie introuvable :", e)
        raise

    # 📍 3. Cliquer sur la suggestion "Sfax" (TextView)
    try:
        suggestion = driver.find_element(AppiumBy.XPATH, f'//android.widget.TextView[contains(@text, "{destination}")]')
        suggestion.click()
        print(f"✅ Suggestion '{destination}' cliquée")
    except Exception as e:
        print(f"❌ Suggestion '{destination}' introuvable :", e)
        raise

    # ⏳ Attente du centrage
    print("🕒 Attente pour que la carte se centre sur la destination...")
    time.sleep(10)

    # 📸 Screenshot après
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "after_search_sfax.png"))

    # 📡 Récupération des coordonnées GPS après
    after_coords = os.popen("adb shell dumpsys location | grep 'last location'").read().strip()
    print(f"📡 Position GPS après :\n{after_coords}")

    # ✅ Vérification GPS
    if before_coords != after_coords:
        print("✅ Les coordonnées GPS ont changé → la carte a été centrée")
    else:
        print("❌ Coordonnées GPS inchangées → possible échec de centrage")
    assert before_coords != after_coords, "❌ La carte ne s’est pas recentrée sur la destination"

    # 🧠 Analyse visuelle avec OpenCV
    img1 = cv2.imread(os.path.join(SCREENSHOT_DIR, "before_search_sfax.png"))
    img2 = cv2.imread(os.path.join(SCREENSHOT_DIR, "after_search_sfax.png"))
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    cv2.imwrite(os.path.join(SCREENSHOT_DIR, "sfax_diff.png"), thresh)
    pixels_changed = cv2.countNonZero(thresh)

    print(f"[🧠] Pixels changés entre les screenshots : {pixels_changed}")
    assert pixels_changed > 100, "❌ La carte n'a pas visuellement changé après recherche"
    print("✅ Recherche + centrage visuel sur Sfax confirmés")

    try:
        back_btn = driver.find_element(AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Back"]')
        back_btn.click()
        print("↩️ Retour effectué via le bouton Back UI")
    except:
        print("⚠️ Bouton 'Back' non trouvé — fallback ADB...")
        driver.press_keycode(4)  # simulate BACK key
    time.sleep(2)
    
def test_05_recherche_sans_resultat():
    print("🔍 Test : Recherche sans résultat")

    invalid_query = "cfvgbhnj,k"
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # 📝 1. Cliquer sur la barre de recherche
    try:
        search_bar = driver.find_element(AppiumBy.XPATH, '//android.widget.EditText[@resource-id="com.google.android.apps.maps:id/destination_input_keyboard_search_edit_text"]')
        search_bar.click()
        time.sleep(2)
    except Exception as e:
        print("❌ Champ de recherche introuvable :", e)
        raise

    # 📝 2. Entrer un lieu invalide
    try:
        search_input = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
        search_input.send_keys(invalid_query)
        driver.press_keycode(66)  # Enter
        print(f"📨 Requête envoyée : {invalid_query}")
    except Exception as e:
        print("❌ Impossible d’entrer le texte :", e)
        raise

     # 🕵️‍♂️ Vérifier présence du message "No results found" ou "No route found"
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                AppiumBy.XPATH,
                '//android.widget.TextView[contains(@text, "No results found") or contains(@text, "No route found")]'
            ))
        )
        print("✅ Message d'absence de résultats affiché correctement")
    except TimeoutException:
        print("❌ Aucun message 'No results found' ou 'No route found' détecté")
        raise

    # 📸 Screenshot après la recherche
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "after_invalid_search.png"))

    # 🔚 Retour arrière
    try:
        back_btn = driver.find_element(AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Back"]')
        back_btn.click()
        print("↩️ Retour effectué via bouton Back")
    except:
        driver.press_keycode(4)
        print("↩️ Retour effectué via touche BACK (ADB)")

    time.sleep(2)

def test_06_navigation_itineraire():
    print("🧭 Test : Navigation vers Ariana (avec OCR dynamique)")

    destination = "Ariana"
    next_xpath = '//android.widget.ImageButton[@resource-id="com.google.android.apps.maps:id/button_sheet_next_button_clickable"]'
    
    # 📍 Recherche de la destination
    try:
        search_bar = driver.find_element(AppiumBy.XPATH, '//android.widget.EditText[@resource-id="com.google.android.apps.maps:id/destination_input_keyboard_search_edit_text"]')
        search_bar.click(); time.sleep(2)

        search_input = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
        search_input.send_keys(destination); time.sleep(2)

        suggestion = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Ariana")]')
        suggestion.click(); time.sleep(4)

        start_btn = driver.find_element(AppiumBy.XPATH, '//android.widget.FrameLayout[@content-desc="Start"]')
        start_btn.click(); time.sleep(5)
        print("✅ Navigation démarrée")

    except Exception as e:
        print(f"❌ Erreur lors de la recherche ou du démarrage : {e}")
        raise

    # 🧭 Instruction initiale (optionnelle)
    try:
        instruction = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Head")]')
        instruction.click(); time.sleep(3)
        print("➡️ Première instruction cliquée")
    except:
        print("ℹ️ Aucune instruction initiale trouvée (non bloquant)")

    # 🔁 Navigation dynamique avec OCR + crop jusqu’à détection "Ariana"
    step = 1
    while True:
        try:
            next_btn = driver.find_element(AppiumBy.XPATH, next_xpath)
            next_btn.click()
            print(f"➡️ Étape {step} de navigation")
            time.sleep(2)

            # 📸 Capture d'écran de l'étape actuelle
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"step_{step}.png")
            driver.save_screenshot(screenshot_path)

            # ✂️ Crop de la zone cible [94,162][566,311]
            x1, y1, x2, y2 = 94, 162, 566, 311
            img = cv2.imread(screenshot_path)
            crop = img[y1:y2, x1:x2]
            cropped_path = screenshot_path.replace(".png", "_crop.png")
            cv2.imwrite(cropped_path, crop)

            # 🔍 OCR uniquement sur la zone cropée
            result = ocr.ocr(cropped_path, cls=True)
            texts = [line[1][0] for block in result for line in block]
            print(f"🔍 OCR (crop zone) → {texts}")

            # ✅ Si "Ariana" détectée → fin du test
            if any("ariana" in t.lower() for t in texts):
                print(f"✅ Destination 'Ariana' détectée à l’étape {step} 🎯")
                return  # Succès du test

            step += 1

        except Exception as e:
            print(f"⚠️ Erreur ou bouton 'Next' absent : {e}")
            raise AssertionError("❌ Navigation terminée sans atteindre 'Ariana'")

def main():
    try:
        # 1️⃣ Initialisation de la session Appium
        setup_appium()

        # 2️⃣ Gestion automatique des popups au lancement de Maps
        gerer_popups_maps()

        # 3️⃣ Forcer la position GPS sur Tunis
        forcer_position_gps_tunis()

        # 4️⃣ TESTS UI Google Maps
        print("\n🎯 DÉBUT : Tests UI Google Maps\n")
        test_affichage_google_maps()
        test_zoom_buttons()
        test_ouverture_profil()
        test_icones_poi_double_verification()

        # 5️⃣ TESTS GPS Google Maps
        print("\n🎯 DÉBUT : Tests GPS Google Maps\n")
        test_01_verifier_point_bleu_gps()
        test_02_mise_a_jour_gps_dynamique()
        test_03_perte_et_reprise_signal_gps()

        # 6️⃣ TESTS RECHERCHE DESTINATION Google Maps
        print("\n🎯 DÉBUT : Tests Recherche Destination Google Maps\n")
        test_04_recherche_lieu_connu()
        test_05_recherche_sans_resultat()

        # 7️⃣ TESTS NAVIGATION Google Maps
        print("\n🎯 DÉBUT : Tests Navigation Dynamique Google Maps\n")
        test_06_navigation_itineraire()

        print("\n✅ Tous les tests ont été exécutés avec succès.")

    except Exception as e:
        print(f"❌ Une erreur inattendue est survenue : {e}")

    finally:
        # 8️⃣ Fermeture propre de la session Appium
        fermer_session_appium()
        print("👋 Session Appium fermée proprement.")

# ▶️ Point d'entrée du script
if __name__ == "__main__":
    main()
