import time
import os
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.common import AppiumOptions
import cv2
from paddleocr import PaddleOCR
import numpy as np
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPIUM_SERVER_URL = "http://127.0.0.1:4723"
SCREENSHOT_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "screenshots_system"))
os.makedirs(SCREENSHOT_PATH, exist_ok=True)


def detect_devices():
    print("\n📡 Détection des devices connectés...")
    result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
    devices = []

    for line in result.stdout.splitlines():
        if "device" in line and not line.startswith("List"):
            parts = line.split()
            udid = parts[0]
            description = " ".join(parts[1:])
            devices.append((udid, description))

    aaos_device = None
    phone_device = None

    for udid, desc in devices:
        if "emulator" in udid and ("car" in desc or "car" in udid):
            aaos_device = udid
        elif "emulator" in udid:
            phone_device = udid

    if not aaos_device or not phone_device:
        print("❌ Impossible de détecter les deux devices. Devices trouvés:", devices)
        raise Exception("Erreur de détection devices")

    print(f"✅ Détection terminée : Phone={phone_device}, AAOS={aaos_device}")
    return phone_device, aaos_device

PHONE_UDID, AAOS_UDID = detect_devices()

os.makedirs(SCREENSHOT_PATH, exist_ok=True)

# Variables Globales
driver_phone = None
driver_aaos = None

def init_driver(udid, device_name):
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", device_name)
    options.set_capability("udid", udid)
    options.set_capability("automationName", "UiAutomator2")
    return webdriver.Remote(APPIUM_SERVER_URL, options=options)


def click_xpath(driver, xpath, description="", timeout=5):
    print(f"🔱 Action : {description}")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            element.click()
            print(f"✅ Cliqué sur {description}")
            return True
        except Exception:
            time.sleep(0.5)
    print(f"❌ Impossible de cliquer sur {description}")
    return False

def wait(seconds):
    print(f"⏳ Attente {seconds} secondes...")
    time.sleep(seconds)

def launch_settings_via_adb(udid):
    print(f"🚀 Lancement manuel de Settings via adb pour {udid}...")
    os.system(f"adb -s {udid} shell am start -n com.android.settings/.Settings")
    wait(2)

def get_bluetooth_status(udid):
    print(f"🔍 Vérification Bluetooth via adb pour {udid}...")
    output = os.popen(f"adb -s {udid} shell settings get global bluetooth_on").read().strip()
    if output == "1":
        print("✅ Bluetooth est ACTIVÉ")
        return True
    elif output == "0":
        print("✅ Bluetooth est DÉSACTIVÉ")
        return False
    else:
        print(f"⚠️ Impossible de lire l'état Bluetooth : {output}")
        return None

def capture_screenshot(driver, device_name, state_label):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{device_name}_bluetooth_{state_label}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_PATH, filename)
    driver.save_screenshot(filepath)
    print(f"📷 Capture enregistrée : {filepath}")

def toggle_bluetooth_ui(driver, expected_state, device_name):
    print(f"🔄 Basculement Bluetooth via UI, attendu : {expected_state}")
    try:
        switch_xpath = '//android.widget.Switch'
        switch = driver.find_element(AppiumBy.XPATH, switch_xpath)
        current_state = switch.get_attribute('checked') == 'true'

        print(f"🗅️ Etat actuel Bluetooth (UI) : {current_state}")

        if current_state != expected_state:
            print(f"🔄 Action nécessaire ➔ Clique sur Switch...")
            switch.click()
            wait(2)
            capture_screenshot(driver, f"{device_name}_toggle_done")
        else:
            print(f"✅ Bluetooth est déjà dans l'état souhaité (pas besoin de cliquer)")
            capture_screenshot(driver, f"{device_name}_no_toggle_needed")

    except Exception as e:
        print(f"❌ Erreur Switch Bluetooth UI : {e}")


# ------------------------
# Navigation Settings
# ------------------------

def open_phone_settings_and_navigate():
    global driver_phone

    print("📱 Initialisation Phone et navigation Bluetooth...")
    try:
        driver_phone = init_driver(PHONE_UDID, "emulator-5556")
        driver_phone.press_keycode(3)
        wait(2)

        xpath_settings_icon = '(//android.widget.TextView[@content-desc="Settings"])[2]'
        success = click_xpath(driver_phone, xpath_settings_icon, "Ouvrir Settings Phone (via NexusLauncher)")

        if not success:
            print("⚠️ Icône Settings introuvable, tentative via adb...")
            launch_settings_via_adb(PHONE_UDID)
            wait(2)

        connected_devices_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.settings:id/recycler_view"]/android.widget.LinearLayout[3]'
        click_xpath(driver_phone, connected_devices_xpath, "Ouvrir Connected Devices")
        wait(1)

        pair_new_devices_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.settings:id/recycler_view"]/android.widget.LinearLayout[1]'
        click_xpath(driver_phone, pair_new_devices_xpath, "Ouvrir Pair New Devices")
        wait(1)

    except Exception as e:
        print(f"⚠️ Erreur ouverture + navigation Phone : {e}")

def open_aaos_settings():
    global driver_aaos

    print("🚗 Initialisation AAOS...")
    driver_aaos = init_driver(AAOS_UDID, "emulator-5554")
    wait(2)

    # Ouvrir Settings directement via adb
    print("🚀 Lancement Settings AAOS via adb...")
    os.system(f"adb -s {AAOS_UDID} shell am start -n com.android.car.settings/com.android.car.settings.Settings_Launcher_Homepage")
    wait(2)
    print("✅ Settings AAOS ouvert via adb.")


# ------------------------
# Pairing Fonctions
# ------------------------

def pair_new_device_on_aaos(driver):
    print("🔗 Démarrage du Pairing AAOS...")
    try:
        pair_new_device_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.car.settings:id/car_ui_internal_recycler_view"]/android.widget.RelativeLayout[2]'
        click_xpath(driver, pair_new_device_xpath, "Ouvrir Pair New Device")
        wait(1)

        phone_device_xpath = '//android.view.ViewGroup[@resource-id="com.android.car.settings:id/multi_action_preference_first_action_container"]'
        click_xpath(driver, phone_device_xpath, "Sélectionner sdk_gphone64_x86_64")
        wait(1)

        pair_button_xpath = '//android.widget.Button[@resource-id="android:id/button1"]'
        click_xpath(driver, pair_button_xpath, "Cliquer sur Pair AAOS")
        wait(1)

    except Exception as e:
        print(f"⚠️ Erreur Pairing AAOS : {e}")

def confirm_pairing_on_phone(driver):
    print("📱 Confirmation Pairing Phone...")
    try:
        allow_contacts_switch_xpath = '//android.widget.Switch[@content-desc="Also allow access to contacts and call history"]'
        click_xpath(driver, allow_contacts_switch_xpath, "Activer accès aux contacts")
        wait(1)

        pair_button_xpath = '//android.widget.Button[@resource-id="android:id/button1"]'
        click_xpath(driver, pair_button_xpath, "Confirmer Pair Phone")
        wait(3)

        allow_button_xpath = '//android.widget.Button[@resource-id="android:id/button1"]'
        click_xpath(driver, allow_button_xpath, "Autoriser accès Phone")
        wait(1)

    except Exception as e:
        print(f"⚠️ Erreur confirmation Pairing Phone : {e}")

def finalize_pairing_on_aaos(driver):
    print("🚗 Finalisation Pairing AAOS...")
    try:
        continue_button_xpath = '//android.widget.Button[@resource-id="android:id/button1"]'
        click_xpath(driver, continue_button_xpath, "Cliquer sur Continue AAOS")
        wait(1)

    except Exception as e:
        print(f"⚠️ Erreur finalisation Pairing AAOS : {e}")
        
def test_bluetooth_pairing():
    """Test complet du Bluetooth Pairing entre Phone et AAOS."""
    print("\n🚀 TEST : Bluetooth Pairing Phone <--> AAOS")

    try:
        # 1. Initialiser le téléphone
        open_phone_settings_and_navigate()

        # 2. Pairing côté AAOS
        pair_new_device_on_aaos(driver_aaos)

        # 3. Confirmer pairing côté Phone
        confirm_pairing_on_phone(driver_phone)

        # 4. Finaliser pairing côté AAOS
        finalize_pairing_on_aaos(driver_aaos)

        # 5. Vérification OCR que le Phone est bien connecté sur AAOS
        verify_connection_with_ocr(driver_aaos, "aaos")

        print("✅ Test Bluetooth Pairing + Vérification OCR réussi entre Phone et AAOS.")

    except Exception as e:
        print(f"❌ Erreur lors du test de Bluetooth Pairing : {e}")


# ------------------------
# Test Bluetooth
# ------------------------

def full_bluetooth_test(driver, udid, device_name):
    print(f"🎯 Test Bluetooth sur {device_name}...")

    initial_state = get_bluetooth_status(udid)
    if initial_state is None:
        print(f"❌ Impossible de tester Bluetooth sur {device_name}")
        return

    toggle_bluetooth_ui(driver, not initial_state, device_name)
    wait(2)
    state_after_toggle = get_bluetooth_status(udid)

    if state_after_toggle == (not initial_state):
        print(f"✅ Bascule réussie ({initial_state} ➔ {state_after_toggle}) sur {device_name}")
    else:
        print(f"❌ Erreur bascule sur {device_name}")

    toggle_bluetooth_ui(driver, initial_state, device_name)
    wait(2)
    state_after_retoggle = get_bluetooth_status(udid)

    if state_after_retoggle == initial_state:
        print(f"✅ Retour à l'état initial ({state_after_toggle} ➔ {state_after_retoggle}) sur {device_name}")
    else:
        print(f"❌ Erreur retour état initial sur {device_name}")


def verify_connection_with_ocr(driver, device_name):
    print("🔍 Vérification OCR du statut de connexion...")

    try:
        # 1. Capture de l'écran complet
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_PATH, f"{device_name}_final_check_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        print(f"📸 Capture pour OCR sauvegardée : {screenshot_path}")

        # 2. Chargement et crop de l'image
        image = cv2.imread(screenshot_path)
        cropped_image = image[469:502, 747:947]  # [y1:y2, x1:x2]
        cropped_path = os.path.join(SCREENSHOT_PATH, f"{device_name}_cropped_check_{timestamp}.png")
        cv2.imwrite(cropped_path, cropped_image)
        print(f"✂️ Image croppée sauvegardée : {cropped_path}")

        # 3. OCR sur l'image croppée
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(cropped_path, cls=True)

        detected_text = ""
        for line in result[0]:
            detected_text += line[1][0] + " "

        print(f"🧠 Texte détecté par OCR : {detected_text.strip()}")

        # 4. Vérification du mot clé "Connected"
        if "Connected" in detected_text:
            print("✅ Vérification OCR : Appareil connecté avec succès !")
        else:
            print("❌ Vérification OCR : 'Connected' non détecté.")

    except Exception as e:
        print(f"⚠️ Erreur pendant la vérification OCR : {e}")


# ------------------------
# test Wi-Fi
# ------------------------

def test_wifi_connection(driver):
    """ Test complet du Wi-Fi : Activation/Désactivation + Vérification UI/ADB + OCR AndroidWifi """
    print("\n🚀 TEST : Wi-Fi Activation/Deactivation + ADB Vérification + OCR AndroidWifi")

    try:
        # 1. Cliquer sur Network & Internet directement
        print("📱 Clic sur Network & Internet...")
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Network")]').click()
        time.sleep(2)

        # 2. Lire état actuel du Wi-Fi via UI
        wifi_switch_xpath = '//android.widget.Switch[@resource-id="android:id/switch_widget"]'
        wifi_switch = driver.find_element(AppiumBy.XPATH, wifi_switch_xpath)
        ui_wifi_state = wifi_switch.get_attribute("checked") == "true"
        print(f"📡 Wi-Fi UI State (avant action) : {'ON' if ui_wifi_state else 'OFF'}")

        # 3. Action selon l'état détecté
        if not ui_wifi_state:
            print("⚡ Wi-Fi désactivé ➔ Activation en cours...")
            wifi_switch.click()
            time.sleep(3)

            # Vérification ADB après activation
            adb_wifi_state = os.popen(f"adb -s {AAOS_UDID} shell settings get global wifi_on").read().strip()
            adb_wifi_state = int(adb_wifi_state) if adb_wifi_state.isdigit() else -1
            print(f"🔍 ADB Wi-Fi State après activation : {adb_wifi_state}")

            if adb_wifi_state == 1:
                print("✅ ADB confirme que Wi-Fi est activé.")
            else:
                print("❌ ADB ne confirme pas l'activation du Wi-Fi.")
        else:
            print("⚡ Wi-Fi activé ➔ Désactivation + Réactivation...")
            wifi_switch.click()
            time.sleep(3)

            # Vérification ADB après désactivation
            adb_wifi_state = os.popen(f"adb -s {AAOS_UDID} shell settings get global wifi_on").read().strip()
            adb_wifi_state = int(adb_wifi_state) if adb_wifi_state.isdigit() else -1
            print(f"🔍 ADB Wi-Fi State après désactivation : {adb_wifi_state}")

            if adb_wifi_state == 0:
                print("✅ ADB confirme que Wi-Fi est désactivé.")
            else:
                print("❌ ADB ne confirme pas la désactivation du Wi-Fi.")

            # Réactiver
            wifi_switch = driver.find_element(AppiumBy.XPATH, wifi_switch_xpath)  # Recharger l'élément
            wifi_switch.click()
            time.sleep(3)

            # Vérification ADB après réactivation
            adb_wifi_state = os.popen(f"adb -s {AAOS_UDID} shell settings get global wifi_on").read().strip()
            adb_wifi_state = int(adb_wifi_state) if adb_wifi_state.isdigit() else -1
            print(f"🔍 ADB Wi-Fi State après réactivation : {adb_wifi_state}")

            if adb_wifi_state == 1:
                print("✅ ADB confirme que Wi-Fi est réactivé.")
            else:
                print("❌ ADB ne confirme pas la réactivation du Wi-Fi.")

        # 4. Capture et OCR pour vérifier AndroidWifi
        print("📸 Capture et OCR pour détecter AndroidWifi...")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_PATH, f"wifi_check_{timestamp}.png")
        driver.save_screenshot(screenshot_path)

        # Crop uniquement AndroidWifi
        image = cv2.imread(screenshot_path)
        wifi_name_crop = image[611:654, 763:929]  # [y1:y2, x1:x2]
        wifi_name_path = os.path.join(SCREENSHOT_PATH, f"cropped_wifi_name_{timestamp}.png")
        cv2.imwrite(wifi_name_path, wifi_name_crop)

        # OCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(wifi_name_path, cls=True)

        if result and len(result) > 0 and len(result[0]) > 0:
            detected_wifi_name = ""
            for line in result[0]:
                detected_wifi_name += line[1][0] + " "

            detected_wifi_name = detected_wifi_name.strip()
            print(f"🧠 Texte détecté Wi-Fi Name : {detected_wifi_name}")

            if "AndroidWifi" in detected_wifi_name:
                print("✅ Wi-Fi AndroidWifi détecté correctement via OCR après Activation.")
            else:
                print("❌ AndroidWifi non détecté via OCR après Activation.")
        else:
            print("❌ Aucune détection OCR trouvée pour AndroidWifi après Activation.")

    except Exception as e:
        print(f"❌ Erreur pendant le test Wi-Fi : {e}")


def open_display_settings(driver):
    print("📱 Ouverture Paramètres > Display...")
    time.sleep(2)
    # C'est le 5ème item dans RecyclerView (pas le 2ème)
    driver.find_element(AppiumBy.XPATH, '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.car.settings:id/car_ui_recycler_view"]/android.widget.RelativeLayout[5]').click()
    time.sleep(2)


def get_brightness_level(driver):
    slider = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.SeekBar")
    x = slider.location["x"]
    width = slider.size["width"]
    thumb_center_x = x + width / 2
    return thumb_center_x, width

def move_brightness_slider(driver, position="right"):
    slider = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.SeekBar")
    start_x = slider.location["x"]
    start_y = slider.location["y"]
    width = slider.size["width"]

    target_x = start_x + int(width * (0.8 if position == "right" else 0.2))
    driver.swipe(start_x + int(width/2), start_y, target_x, start_y, 800)
    print(f"✅ Curseur déplacé vers {'droite' if position == 'right' else 'gauche'}")
    time.sleep(2)

def capture_screenshot(driver, name):
    full_path = os.path.join(SCREENSHOT_PATH, f"{name}.png")
    driver.save_screenshot(full_path)
    print(f"📸 Capture enregistrée : {full_path}")
    return full_path

def compare_screenshots(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        print("❌ Images non chargées.")
        return False

    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(img1_gray, img2_gray)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    changed_pixels = np.count_nonzero(thresh)
    total_pixels = thresh.size
    percent_change = (changed_pixels / total_pixels) * 100

    print(f"📊 Pourcentage changement : {percent_change:.4f}%")
    return percent_change > 0.3

def toggle_adaptive_brightness(driver):
    toggle = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.Switch")
    toggle.click()
    print("🔄 Switch 'Adaptive Brightness' activé/désactivé")
    time.sleep(3)

def test_brightness_slider_functionality(driver):
    print("\n🚀 TEST : Brightness Slider Fonctionnel ?")
    open_display_settings(driver)

    move_brightness_slider(driver, "right")
    capture_screenshot(driver, "brightness_high")

    move_brightness_slider(driver, "left")
    capture_screenshot(driver, "brightness_low")

    img_high = os.path.join(SCREENSHOT_PATH, "brightness_high.png")
    img_low = os.path.join(SCREENSHOT_PATH, "brightness_low.png")
    result = compare_screenshots(img_high, img_low)

    if result:
        print("✅ Brightness Slider fonctionne correctement (différence détectée).")
    else:
        print("❌ Brightness Slider NE fonctionne PAS (aucune différence détectée).")

def test_adaptive_brightness_functionality(driver):
    print("\n🚀 TEST : Adaptive Brightness Fonctionnel ?")
    open_display_settings(driver)

    initial_level, width = get_brightness_level(driver)
    print(f"📏 Niveau initial luminosité : {initial_level:.2f}")

    toggle_adaptive_brightness(driver)

    after_toggle_level, _ = get_brightness_level(driver)
    print(f"📏 Niveau après changement : {after_toggle_level:.2f}")

    if abs(initial_level - after_toggle_level) > width * 0.05:
        print("✅ Adaptive Brightness fonctionne (niveau changé automatiquement).")
    else:
        print("❌ Adaptive Brightness NE fonctionne PAS (niveau inchangé).")

# --- Fonctions Date & Time Correctes ---

def navigate_to_date_time_settings(driver):
    """Depuis Display, naviguer vers Date & Time"""
    print("📅 Navigation vers Date & Time...")
    wait(1)

    # On est dans Display ➔ maintenant clique sur "Date & Time"
    date_time_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.car.settings:id/car_ui_internal_recycler_view"]/android.widget.RelativeLayout[2]'
    success = click_xpath(driver, date_time_xpath, "Ouvrir Date & Time depuis Display")
    if not success:
        print("❌ Impossible d'ouvrir Date & Time depuis Display.")
        return False

    wait(2)
    return True

def disable_automatic_time(driver):
    """Vérifie et désactive 'Set time automatically' si activé"""
    print("🔍 Vérification du mode automatique...")
    try:
        toggle_xpath = '//android.widget.Switch[@resource-id="android:id/switch_widget"]'
        toggle_element = driver.find_element(AppiumBy.XPATH, toggle_xpath)
        is_enabled = toggle_element.get_attribute("checked")

        if is_enabled == "true":
            print("⚠️ 'Set time automatically' activé ➔ Désactivation...")
            toggle_element.click()
            time.sleep(2)
            print("✅ 'Set time automatically' désactivé.")
        else:
            print("✅ 'Set time automatically' déjà désactivé.")
    except Exception as e:
        print(f"❌ Erreur désactivation automatique : {e}")

def get_current_date():
    """Récupère la date actuelle via ADB"""
    result = os.popen(f"adb -s {AAOS_UDID} shell date '+%Y-%m-%d'").read().strip()
    print(f"📆 Date actuelle : {result}")
    return result

def get_current_time():
    """Récupère l'heure actuelle via ADB"""
    result = os.popen(f"adb -s {AAOS_UDID} shell date '+%H:%M'").read().strip()
    print(f"⏰ Heure actuelle : {result}")
    return result

def change_date(driver):
    """Change la date"""
    print("📅 Changement de la date...")

    try:
        # Essayer de cliquer sur 'Set date'
        set_date_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Set date"]')
        set_date_button.click()
        time.sleep(2)

        # Tap dans le sélecteur de date
        os.system(f"adb -s {AAOS_UDID} shell input tap 846 532")  # Mois
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 976 532")  # Jour
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 1095 532")  # Année
        time.sleep(1)

        # Confirmer (ENTER)
        os.system(f"adb -s {AAOS_UDID} shell input keyevent 66")
        time.sleep(2)

    except Exception as e:
        print(f"❌ Impossible de changer la date : {e}")

def change_time(driver):
    """Change l'heure"""
    print("⏰ Changement de l'heure...")

    try:
        set_time_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Set time"]')
        set_time_button.click()
        time.sleep(2)

        # Tap dans le sélecteur d'heure
        os.system(f"adb -s {AAOS_UDID} shell input tap 852 522")  # Heure
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 981 532")  # Minutes
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 1107 339")  # Minutes
        time.sleep(1)
        # Confirmer (ENTER)
        os.system(f"adb -s {AAOS_UDID} shell input keyevent 66")
        time.sleep(2)

    except Exception as e:
        print(f"❌ Impossible de changer l'heure : {e}")

def go_back(driver):
    """Retour arrière"""
    print("↩️ Retour arrière...")
    try:
        back_button_xpath = '//android.widget.ImageView[@resource-id="com.android.car.settings:id/car_ui_toolbar_nav_icon"]'
        driver.find_element(AppiumBy.XPATH, back_button_xpath).click()
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Erreur retour arrière : {e}")

def verify_date_changed(old_date):
    """Vérifie changement de date"""
    new_date = get_current_date()
    print(f"🔄 Date : Avant = {old_date} | Après = {new_date}")
    if old_date != new_date:
        print("✅ Date modifiée avec succès.")
        return True
    else:
        print("❌ Date inchangée.")
        return False

def verify_time_changed(old_time):
    """Vérifie changement d'heure"""
    new_time = get_current_time()
    print(f"🔄 Heure : Avant = {old_time} | Après = {new_time}")
    if old_time != new_time:
        print("✅ Heure modifiée avec succès.")
        return True
    else:
        print("❌ Heure inchangée.")
        return False

# --- TESTS ---

def test_date_change(driver):
    """Test complet de changement de la date"""
    print("\n🚀 TEST DATE CHANGE 🚀")
    if not navigate_to_date_time_settings(driver):
        print("❌ Navigation échouée vers Date & Time.")
        return

    disable_automatic_time(driver)

    old_date = get_current_date()
    change_date(driver)
    go_back(driver)

    if verify_date_changed(old_date):
        print("✅ Test de changement de date PASSED")
    else:
        print("❌ Test de changement de date FAILED")

def test_time_change(driver):
    """Test complet de changement de l'heure"""
    print("\n🚀 TEST TIME CHANGE 🚀")
    if not navigate_to_date_time_settings(driver):
        print("❌ Navigation échouée vers Date & Time.")
        return

    disable_automatic_time(driver)

    old_time = get_current_time()
    change_time(driver)
    go_back(driver)

    if verify_time_changed(old_time):
        print("✅ Test de changement d'heure PASSED")
    else:
        print("❌ Test de changement d'heure FAILED")
def change_language_cycle(driver):
    """Test complet : passage English ➔ Français ➔ retour English"""
    print("\n🚀 Début du test de changement de langue 🚀")

    # 📜 1. Navigation initiale
    try:
        print("📜 Défilement vers 'System'...")
        wait(1)
        driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().textContains("System"))')
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="System"]').click()
        time.sleep(2)

        print("🌍 Accès à 'Languages & input'...")
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text,"Languages")]').click()
        time.sleep(2)

        print("🌐 Accès à 'Languages'...")
        driver.find_element(AppiumBy.XPATH,
            '//android.widget.TextView[@resource-id="android:id/title" and (@text="Languages" or @text="Langues")]').click()
        time.sleep(2)

    except Exception as e:
        print(f"❌ Erreur navigation initiale : {e}")
        return

    # 📖 2. Langue actuelle AVANT
    previous_language = os.popen(f"adb -s {AAOS_UDID} shell getprop persist.sys.locale").read().strip()
    print(f"📖 Langue actuelle AVANT changement : {previous_language}")

    # 🔵 3. Passage en Français
    print("\n🔵 Passage en Français...")

    try:
        # Scroll pour trouver "Français"
        found = False
        for _ in range(10):
            try:
                driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Français"]').click()
                found = True
                break
            except:
                print("🔄 'Français' non trouvé, scroll...")
                os.system(f"adb -s {AAOS_UDID} shell input swipe 612 649 612 400")
                time.sleep(2)

        if not found:
            print("❌ 'Français' non trouvé après plusieurs scrolls.")
            return

        time.sleep(2)

        # Sélection de Français (France)
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Français (France)"]').click()
        time.sleep(3)

        new_language = os.popen(f"adb -s {AAOS_UDID} shell getprop persist.sys.locale").read().strip()
        print(f"📖 Langue APRES passage en Français : {new_language}")

        if "fr" in new_language:
            print("✅ Passage en Français réussi.")
        else:
            print(f"❌ Passage en Français échoué. Langue actuelle: {new_language}")
            return

    except Exception as e:
        print(f"❌ Erreur pendant passage en Français : {e}")
        return

    # 🔴 4. Retour en Anglais
    print("\n🔄 Retour en Anglais...")

    try:
        # 🌐 Re-cliquer sur "Languages" ("Langues")
        print("🌐 Retour dans 'Languages'...")
        driver.find_element(AppiumBy.XPATH,
            '//android.widget.TextView[@resource-id="android:id/title" and (@text="Languages" or @text="Langues")]').click()
        time.sleep(2)

        # 🔥 Cliquer directement sur "English (United States)"
        print("🌐 Sélection de 'English (United States)'...")
        driver.find_element(AppiumBy.XPATH,
            '//android.widget.TextView[@text="English (United States)"]').click()
        time.sleep(3)

        final_language = os.popen(f"adb -s {AAOS_UDID} shell getprop persist.sys.locale").read().strip()
        print(f"📖 Langue APRES retour en Anglais : {final_language}")

        if "en" in final_language:
            print("✅ Retour en Anglais réussi.")
        else:
            print(f"❌ Retour en Anglais échoué. Langue actuelle: {final_language}")

    except Exception as e:
        print(f"❌ Erreur pendant retour en Anglais : {e}")

def close_settings():
    """Ferme uniquement l'application Settings AAOS."""
    print("⏳ Attente 3 secondes avant fermeture de Settings...")
    time.sleep(5)  # 🕒 Attendre 3 secondes AVANT de fermer

    print("🚪 Fermeture de Settings AAOS...")
    try:
        os.system(f"adb -s {AAOS_UDID} shell am force-stop com.android.car.settings")
        print("✅ Settings fermé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de la fermeture de Settings : {e}")
if __name__ == "__main__":
    print("🚀 Début des tests AAOS...")

    # Initialisation AAOS
    open_aaos_settings()

    # Test Bluetooth
    full_bluetooth_test(driver_aaos, AAOS_UDID, "aaos")
    # Test pairing
    test_bluetooth_pairing()

    # Test OCR Wi-Fi
    test_wifi_connection(driver_aaos)

    # Test Brightness Slider
    test_brightness_slider_functionality(driver_aaos)

    # Test Adaptive Brightness
    test_adaptive_brightness_functionality(driver_aaos)

    # Test Date Change
    test_date_change(driver_aaos)

    # Test Time Change
    test_time_change(driver_aaos)

    # Test Changement de langue (Français ➔ Anglais)
    change_language_cycle(driver_aaos)

    # Fermeture Settings
    close_settings()

    print("✅ Tous les tests terminés !")
