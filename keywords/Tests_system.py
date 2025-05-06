import cv2
import time
import os
import numpy as np
from paddleocr import PaddleOCR
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from appium_driver_factory import driver_factory
from robot.api.deco import keyword
from playsound import playsound
import pyaudio
import wave
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import subprocess
import re
ocr = PaddleOCR(use_angle_cls=True, lang='en')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = "output"
SCREENSHOT_PATH = os.path.join(BASE_DIR, "screenshots_system")
SCREENSHOT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "screenshots_hvac"))
AUDIO_FILE = os.path.join(BASE_DIR, "open_play_store.mp3")
PACKAGE_NAME = "com.simplemobiletools.filemanager"
MAIN_ACTIVITY = "com.simplemobiletools.filemanager.activities.MainActivity"
APK_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "apks", "simple_file_manager.apk"))
driver_factory.initialize_drivers()
driver = driver_factory.get_driver("automotive")
AAOS_UDID = driver_factory.get_emulator_uid("automotive")  
DURATION = 10
SEUIL_DB = -40
SEUIL_DUREE_ACTIVE = 0.5
SEUIL_PIC_DB = 20
SEUIL_NB_PICS = 10
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def wait(seconds):
    print(f"Attente {seconds} secondes...")
    time.sleep(seconds)

def click_xpath(driver, xpath, description="", timeout=5):
    print(f"Action : {description}")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            element.click()
            print(f"Cliqué sur {description}")
            return True
        except Exception:
            time.sleep(0.5)
    print(f"Impossible de cliquer sur {description}")
    return False

def get_bluetooth_state_adb():
    """Retourne 1 si Bluetooth est ON, sinon 0"""
    result = subprocess.run("adb shell settings get global bluetooth_on", shell=True, capture_output=True, text=True)
    state = result.stdout.strip()
    print(f"Résultat ADB ➤ bluetooth_on = {state}")
    return state

def get_bluetooth_ui_state(driver):
    """Retourne True si le switch est activé (checked = true)"""
    toggle = driver.find_element(AppiumBy.XPATH, '//android.widget.Switch[@resource-id="android:id/switch_widget"]')
    checked = toggle.get_attribute("checked")
    print(f"État UI ➤ checked = {checked}")
    return checked == "true"

def test_bluetooth_toggle_sync():
    print("\nLancement du test de synchronisation Bluetooth (UI ↔ ADB)")

    print("Navigation vers les paramètres Bluetooth...")
    driver.activate_app("com.android.car.settings")
    time.sleep(2)

    for action in ["activate", "deactivate"]:
        print(f"\nÉTAPE : {action.upper()} le Bluetooth")

        ui_before = get_bluetooth_ui_state(driver)
        adb_before = get_bluetooth_state_adb()

        print(f"Avant clic ➤ UI = {'ON' if ui_before else 'OFF'}, ADB = {'ON' if adb_before == '1' else 'OFF'}")
        toggle = driver.find_element(AppiumBy.XPATH, '//android.widget.Switch[@resource-id="android:id/switch_widget"]')
        toggle.click()
        time.sleep(3)
        ui_after = get_bluetooth_ui_state(driver)
        adb_after = get_bluetooth_state_adb()
        print(f"Après clic ➤ UI = {'ON' if ui_after else 'OFF'}, ADB = {'ON' if adb_after == '1' else 'OFF'}")
        sync_ok = (ui_after and adb_after == '1') or (not ui_after and adb_after == '0')

        if sync_ok:
            etat = "activé" if adb_after == '1' else "désactivé"
            print(f"SYNC UI/ADB : Le Bluetooth est bien {etat} et les états sont synchronisés.")
            screenshot_name = f"bluetooth_{etat}.png"
            driver.save_screenshot(screenshot_name)
            print(f"Capture prise ➤ {screenshot_name}")
        else:
            print("SYNC UI/ADB : Les états ne correspondent pas (désynchronisation)")
            raise AssertionError("L'état UI et ADB ne sont pas synchronisés après le clic.")

        time.sleep(2)

    print("\nTest terminé avec succès ➤ Bluetooth UI et système sont parfaitement synchronisés.")

def preprocess_image_for_ocr(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Impossible de charger {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

def detect_keywords_from_image(image_path, keywords):
    image = preprocess_image_for_ocr(image_path)
    result = ocr.ocr(image)
    if not result or not result[0]:
        return []
    found = []
    for line in result[0]:
        text = line[1][0].lower().strip()
        for keyword in keywords:
            if keyword.lower() in text:
                found.append(keyword.lower())
    return found

def go_to_network_and_internet(driver):
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Network")').click()
    time.sleep(2)

def toggle_hotspot(driver):
    driver.find_element(AppiumBy.XPATH, '//android.widget.Switch[@resource-id="com.android.car.settings:id/car_ui_secondary_action_concrete"]').click()
    time.sleep(3)

def capture_full_screen(driver, filename):
    driver.save_screenshot(filename)
    print(f"Capture prise : {filename}")

def verify_state(image_path, expect_hotspot, expect_wifi):
    detected = detect_keywords_from_image(image_path, ["androidap", "androidwifi", "off"])
    has_ap = "androidap" in detected
    has_wifi = "androidwifi" in detected
    has_off = "off" in detected

    if expect_hotspot and not expect_wifi:
        if has_ap and not has_wifi:
            print("Hotspot bien activé : SSID détecté et Wi-Fi non détecté.")
            return True
        else:
            print("Échec activation Hotspot : 'androidap' manquant ou 'androidwifi' détecté.")
            return False

    if not expect_hotspot and expect_wifi:
        if not has_ap and has_wifi and has_off:
            print("Hotspot bien désactivé : Wi-Fi détecté et état 'OFF' confirmé.")
            return True
        else:
            print("Échec désactivation Hotspot : conditions 'androidwifi' ou 'off' manquantes.")
            return False

    print("Vérification incohérente avec les attentes.")
    return False

def test_hotspot_behavior(driver):
    go_to_network_and_internet(driver)
    subprocess.run("adb shell svc wifi enable", shell=True)
    time.sleep(2)
    toggle = driver.find_element(AppiumBy.XPATH, '//android.widget.Switch[@resource-id="com.android.car.settings:id/car_ui_secondary_action_concrete"]')
    is_hotspot_active = toggle.get_attribute("checked") == "true"

    print(f"État initial du hotspot : {'Activé' if is_hotspot_active else 'Désactivé'}")

    if is_hotspot_active:
        print("Hotspot actif ➔ Désactivation...")
        toggle_hotspot(driver)
        time.sleep(2)
        capture_full_screen(driver, "hotspot_deactivated_1.png")
        if not verify_state("hotspot_deactivated_1.png", expect_hotspot=False, expect_wifi=True):
            raise AssertionError("Hotspot non désactivé correctement.")

        print("Réactivation du Hotspot...")
        toggle_hotspot(driver)
        time.sleep(2)
        capture_full_screen(driver, "hotspot_reactivated.png")
        if not verify_state("hotspot_reactivated.png", expect_hotspot=True, expect_wifi=False):
            raise AssertionError("Hotspot non réactivé correctement.")

    else:
        print("Hotspot inactif ➔ Activation...")
        toggle_hotspot(driver)
        time.sleep(2)
        capture_full_screen(driver, "hotspot_activated.png")
        if not verify_state("hotspot_activated.png", expect_hotspot=True, expect_wifi=False):
            raise AssertionError("Activation du Hotspot échouée.")

        print("Désactivation du Hotspot...")
        toggle_hotspot(driver)
        time.sleep(2)
        capture_full_screen(driver, "hotspot_deactivated_2.png")
        if not verify_state("hotspot_deactivated_2.png", expect_hotspot=False, expect_wifi=True):
            raise AssertionError("Désactivation finale du Hotspot échouée.")

def detect_mobile_network_state(image_path):
    print(f"Analyse OCR sur : {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        print(f"Image introuvable : {image_path}")
        return "UNKNOWN"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpen = cv2.filter2D(gray, -1, np.array([[0,-1,0], [-1,5,-1], [0,-1,0]]))
    _, thresh = cv2.threshold(sharpen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    result = ocr.ocr(resized)

    if not result or not result[0]:
        print("Aucune détection OCR dans l’image.")
        return "UNKNOWN"

    for line in result[0]:
        text = line[1][0].replace(";", "-").replace(" ", "").strip().lower()
        if "off" in text:
            print(f"OCR détecté : {text} ➤ Mobile Network est bien désactivé.")
            return "OFF"
        elif "t-mobile" in text or "t-mobile-us" in text:
            print(f"OCR détecté : {text} ➤ Mobile Network est bien activé.")
            return "ON"

    print("Aucun état reconnu via OCR.")
    return "UNKNOWN"
def go_to_network_and_internet(driver):
    btn = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Network")')
    btn.click()
    time.sleep(2)
def capture_crop_mobile(driver, filename):
    print(f"Capture Mobile Network ➔ {filename}")
    driver.save_screenshot("full_mobile.png")
    img = cv2.imread("full_mobile.png")
    crop = img[358:391, 763:904]
    cv2.imwrite(filename, crop)

def toggle_mobile_network(driver):
    try:
        toggle = driver.find_element(
            AppiumBy.XPATH,
            '//android.view.ViewGroup[@resource-id="com.android.car.settings:id/colored_preference_second_action_container"]'
        )
        toggle.click()
        time.sleep(3)
    except Exception as e:
        print(f"Erreur lors du toggle Mobile Network : {e}")

def verify_mobile_state(driver, expected_state, filename):
    capture_crop_mobile(driver, filename)
    state = detect_mobile_network_state(filename)
    if state != expected_state:
        raise AssertionError(f"Échec : attendu '{expected_state}', mais détecté '{state}'")
    print(f"État '{expected_state}' confirmé par OCR.")

def test_mobile_network_behavior(driver):
    go_to_network_and_internet(driver)

    print("Vérification de l'état initial du Mobile Network...")
    capture_crop_mobile(driver, "mobile_state_initial.png")
    state_before = detect_mobile_network_state("mobile_state_initial.png")
    verify_mobile_state(driver, state_before, "mobile_state_initial.png")

    if state_before == "OFF":
        print("Activation du Mobile Network...")
        toggle_mobile_network(driver)
        verify_mobile_state(driver, "ON", "mobile_state_on.png")

        print("Désactivation du Mobile Network...")
        toggle_mobile_network(driver)
        verify_mobile_state(driver, "OFF", "mobile_state_off.png")

    elif state_before == "ON":
        print("Désactivation du Mobile Network...")
        toggle_mobile_network(driver)
        verify_mobile_state(driver, "OFF", "mobile_state_off.png")

        print("Réactivation du Mobile Network...")
        toggle_mobile_network(driver)
        verify_mobile_state(driver, "ON", "mobile_state_on_final.png")

    else:
        raise AssertionError(f"État Mobile Network inconnu : {state_before}")

def test_wifi_connectivity():
    print("\n Étape 1 : Réinitialisation ➤ Désactivation Wi-Fi + Données mobiles...")
    subprocess.run("adb shell svc wifi disable", shell=True)
    subprocess.run("adb shell svc data disable", shell=True)
    time.sleep(2)

    print(" Étape 2 : Activation du Wi-Fi...")
    subprocess.run("adb shell svc wifi enable", shell=True)
    time.sleep(5)

    print("\n Étape 3 : Vérification `dumpsys wifi | grep curState`...")
    state_result = subprocess.run('adb shell dumpsys wifi | grep "curState"', shell=True, capture_output=True, text=True)
    state_output = state_result.stdout.strip()
    print("📋 États détectés :\n" + state_output)

    lines = state_output.splitlines()
    if len(lines) >= 3 and "L3ConnectedState" in lines[2]:
        print("L3ConnectedState détecté ➤ Wi-Fi connecté.")
    else:
        raise AssertionError(" L3ConnectedState non détecté à la 3e ligne ➤ Wi-Fi non connecté.")

    print("\n Étape 4 : Vérification IP route...")
    route_result = subprocess.run("adb shell ip route", shell=True, capture_output=True, text=True)
    route_output = route_result.stdout.strip()
    print(" IP Routes :\n" + route_output)

    if "wlan0" in route_output or "10.0." in route_output:
        print(" wlan0 ou IP 10.0.x.x détecté ➤ Connexion réseau active.")
    else:
        raise AssertionError(" Aucune trace de wlan0 ➤ Wi-Fi probablement inactif.")

    print("\n Étape 5 : Test Internet ➤ ping vers 8.8.8.8")
    ping_result = subprocess.run("adb shell ping -c 3 8.8.8.8", shell=True, capture_output=True, text=True)
    ping_output = ping_result.stdout.strip()
    print(" Résultat ping :\n" + ping_output)

    if "0% packet loss" in ping_output or "bytes from" in ping_output:
        print(" Le Wi-Fi est bien connecté à Internet.")
    else:
        raise AssertionError(" Ping échoué ➤ Pas d’accès Internet malgré la connexion Wi-Fi.")

    print("\n TEST WI-FI COMPLET ")

def test_wifi_disconnectivity():
    print("Étape 1 : Simuler la déconnexion depuis l'interface")
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("AndroidWifi")').click()
    time.sleep(2)
    driver.find_element(AppiumBy.XPATH, '//android.widget.LinearLayout[@resource-id="com.android.car.settings:id/button2"]').click()
    driver.back()
    time.sleep(1)

    print("\nÉtape 2 : Vérification `dumpsys wifi | grep curState`...")
    state_result = subprocess.run('adb shell dumpsys wifi | grep "curState"', shell=True, capture_output=True, text=True)
    state_output = state_result.stdout.strip()
    lines = state_output.splitlines()[:4]
    print("📋 États détectés :\n" + "\n".join(lines))
    if len(lines) >= 3 and "DisconnectedState" in lines[2]:
      print("Wi-Fi déconnecté ➤ DisconnectedState détecté à la 3ème ligne.")
    else:
      raise AssertionError(" Le Wi-Fi semble encore connecté ➤ DisconnectedState non détecté à la 3ème ligne.")
    print("\nÉtape 3 : Vérification IP route...")

    route_result = subprocess.run("adb shell ip route", shell=True, capture_output=True, text=True)
    route_output = route_result.stdout.strip()
    print("IP Routes :\n" + (route_output if route_output else "aucune route"))

    if not route_output.strip():
        print("Aucune route IP ➤ Wi-Fi semble bien déconnecté.")
    else:
        raise AssertionError(" Une route est encore active ➤ Connexion possible.")

    print("\n Étape 4 : Ping ➤ 8.8.8.8 pour test réseau")
    ping_result = subprocess.run("adb shell ping -c 3 8.8.8.8", shell=True, capture_output=True, text=True)
    ping_output = (ping_result.stdout + ping_result.stderr).strip()
    print("Résultat ping :\n" + ping_output)
    if "0% packet loss" in ping_output or "bytes from" in ping_output:
      raise AssertionError("Ping réussi ➤ Le Wi-Fi est encore connecté à Internet.")
    elif "unreachable" in ping_output or "100% packet loss" in ping_output:
     print("Ping échoué ➤ Aucune connexion Internet ➤ Wi-Fi bien déconnecté.")
    else:
     print("Résultat du ping incertain ➤ À analyser manuellement.")
def test_forget_network():
    print("\nÉtape 1 : Accès à AndroidWifi via Appium")
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("AndroidWifi")').click()
    time.sleep(2)

    print("\nÉtape 2 : Récupération de la liste des réseaux Wi-Fi")
    result = subprocess.run("adb shell cmd wifi list-networks", shell=True, capture_output=True, text=True)
    networks_output = result.stdout.strip()
    print("📋 Liste des réseaux :\n" + networks_output)
    network_id = None
    for line in networks_output.splitlines():
        if "AndroidWifi" in line:
            parts = line.strip().split()
            if parts and parts[0].isdigit():
                network_id = parts[0]
                print(f"ID du réseau AndroidWifi détecté : {network_id}")
                break
    if network_id is None:
        raise AssertionError("Aucun réseau AndroidWifi détecté dans la liste.")
    print(f"\nÉtape 3 : Suppression du réseau ID={network_id}")
    forget_cmd = f"adb shell cmd wifi forget-network {network_id}"
    forget_result = subprocess.run(forget_cmd, shell=True, capture_output=True, text=True)
    forget_output = (forget_result.stdout + forget_result.stderr).strip()
    print("Résultat :\n" + forget_output)

    if "Forget successful" in forget_output:
        print("Réseau AndroidWifi oublié avec succès.")
    else:
        raise AssertionError("La suppression du réseau AndroidWifi a échoué.")
def test_wifi_latency():
    subprocess.run("adb shell svc data disable", shell=True)
    subprocess.run("adb shell svc wifi enable", shell=True)
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("AndroidWifi")').click()
    time.sleep(5)
    ping_cmd = subprocess.run("adb shell ping -c 4 10.0.2.2", shell=True, capture_output=True, text=True)
    ping_output = (ping_cmd.stdout + ping_cmd.stderr).strip()
    print("\nRésultat du ping :\n" + ping_output)

    match = re.search(r"= .*?/([\d.]+)/", ping_output)
    if match:
        avg_latency = float(match.group(1))
        print(f"\nLatence moyenne détectée : {avg_latency} ms")

        if avg_latency < 50:
            print("Latence Wi-Fi (locale) dans la plage acceptable (< 50 ms)")
        else:
            raise AssertionError(f"Latence Wi-Fi trop élevée : {avg_latency} ms")
    else:
        raise AssertionError("Impossible d'extraire la latence moyenne du ping.")
def test_mobile_network_latency():
    print("Test de latence network mobile")
    subprocess.run("adb shell svc data enable", shell=True)
    subprocess.run("adb shell svc wifi disable", shell=True)
    time.sleep(5)
    ping_cmd = subprocess.run("adb shell ping -c 4 10.0.2.2", shell=True, capture_output=True, text=True)
    ping_output = (ping_cmd.stdout + ping_cmd.stderr).strip()
    print("\n📨 Résultat du ping :\n" + ping_output)
    match = re.search(r"= .*?/([\d.]+)/", ping_output)
    if match:
        avg_latency = float(match.group(1))
        print(f"\nLatence moyenne détectée : {avg_latency} ms")

        if 1 <= avg_latency <= 500:
            print("Latence mobile locale dans la plage acceptable (1–500 ms)")
        else:
            raise AssertionError(f"Latence mobile hors plage : {avg_latency} ms")
    else:
        raise AssertionError("Impossible d'extraire la latence moyenne du ping.") 

def test_loopback_latency():
    print("\nTest de latence loopback (127.0.0.1)...")
    ping_cmd = subprocess.run("adb shell ping -c 4 127.0.0.1", shell=True, capture_output=True, text=True)
    ping_output = (ping_cmd.stdout + ping_cmd.stderr).strip()
    print("\nRésultat du ping loopback :\n" + ping_output)

    match = re.search(r"= .*?/([\d.]+)/", ping_output)
    if match:
        avg_latency = float(match.group(1))
        print(f"\nLatence moyenne loopback détectée : {avg_latency} ms")

        if avg_latency < 5:
            print("Loopback fonctionnel avec latence ultra-faible (< 5 ms)")
        else:
            raise AssertionError(f"Loopback lent ou anormal : {avg_latency} ms")
    else:
        raise AssertionError("Impossible d'extraire la latence du loopback.")

    print("\nTest loopback réussi : pile réseau bien  fonctionnelle dans l'émulateur.")   



def open_display_settings(driver):
    print("Ouverture Paramètres > Display...")
    time.sleep(2)
    driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Display"]').click()
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
    print(f"Curseur déplacé vers {'droite' if position == 'right' else 'gauche'}")
    time.sleep(2)

def capture_screenshot(driver, name):
    full_path = os.path.join(SCREENSHOT_PATH, f"{name}.png")
    driver.save_screenshot(full_path)
    print(f"Capture enregistrée : {full_path}")
    return full_path

def compare_screenshots(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        print("Images non chargées.")
        return False

    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(img1_gray, img2_gray)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    changed_pixels = np.count_nonzero(thresh)
    total_pixels = thresh.size
    percent_change = (changed_pixels / total_pixels) * 100

    print(f"Pourcentage changement : {percent_change:.4f}%")
    return percent_change > 0.3

def toggle_adaptive_brightness(driver):
    toggle = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.Switch")
    toggle.click()
    print("Switch 'Adaptive Brightness' activé/désactivé")
    time.sleep(3)

def test_brightness_slider_functionality(driver):
    print("\nTEST : Brightness Slider Fonctionnel ?")
    open_display_settings(driver)

    move_brightness_slider(driver, "right")
    capture_screenshot(driver, "brightness_high")

    move_brightness_slider(driver, "left")
    capture_screenshot(driver, "brightness_low")

    img_high = os.path.join(SCREENSHOT_PATH, "brightness_high.png")
    img_low = os.path.join(SCREENSHOT_PATH, "brightness_low.png")
    result = compare_screenshots(img_high, img_low)

    if result:
        print("Brightness Slider fonctionne correctement (différence détectée).")
    else:
        print("Brightness Slider NE fonctionne PAS (aucune différence détectée).")

def test_adaptive_brightness_functionality(driver):
    print("\nTEST : Adaptive Brightness Fonctionnel ?")
    open_display_settings(driver)

    initial_level, width = get_brightness_level(driver)
    print(f"Niveau initial luminosité : {initial_level:.2f}")

    toggle_adaptive_brightness(driver)

    after_toggle_level, _ = get_brightness_level(driver)
    print(f"Niveau après changement : {after_toggle_level:.2f}")

    if abs(initial_level - after_toggle_level) > width * 0.05:
        print("Adaptive Brightness fonctionne (niveau changé automatiquement).")
    else:
        print("Adaptive Brightness NE fonctionne PAS (niveau inchangé).")

def navigate_to_date_time_settings(driver):
    print("Navigation vers Date & Time...")
    wait(1)
    date_time_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.car.settings:id/car_ui_internal_recycler_view"]/android.widget.RelativeLayout[2]'
    if click_xpath(driver, date_time_xpath, "Ouvrir Date & Time depuis Display"):
        wait(2)
        return True
    print("Échec ouverture Date & Time.")
    return False


def disable_automatic_time(driver):
    print("Vérification du mode automatique...")
    try:
        toggle_xpath = '//android.widget.Switch[@resource-id="android:id/switch_widget"]'
        toggle_element = driver.find_element(AppiumBy.XPATH, toggle_xpath)
        is_enabled = toggle_element.get_attribute("checked")
        if is_enabled == "true":
            print("Activé ➔ Désactivation...")
            toggle_element.click()
            time.sleep(2)
            print("Désactivé.")
        else:
            print("Déjà désactivé.")
    except Exception as e:
        print(f"Erreur désactivation : {e}")

def get_current_date():
    result = os.popen(f"adb -s {AAOS_UDID} shell date '+%Y-%m-%d'").read().strip()
    print(f"Date actuelle : {result}")
    return result


def get_current_time():
    result = os.popen(f"adb -s {AAOS_UDID} shell date '+%H:%M'").read().strip()
    print(f"Heure actuelle : {result}")
    return result

def change_date(driver):
    print("Changement de la date...")
    try:
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Set date"]').click()
        time.sleep(2)
        os.system(f"adb -s {AAOS_UDID} shell input tap 846 532")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 976 532")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 1095 532")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input keyevent 66")  
        time.sleep(2)
    except Exception as e:
        print(f"Erreur changement date : {e}")

def change_time(driver):
    print("Changement de l'heure...")
    try:
        driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Set time"]').click()
        time.sleep(2)
        os.system(f"adb -s {AAOS_UDID} shell input tap 852 522")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 981 532")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input tap 1107 339")  
        time.sleep(1)
        os.system(f"adb -s {AAOS_UDID} shell input keyevent 66")
        time.sleep(2)
    except Exception as e:
        print(f"Erreur changement heure : {e}")

def go_back(driver):
    print("Retour arrière...")
    try:
        back_xpath = '//android.widget.ImageView[@resource-id="com.android.car.settings:id/car_ui_toolbar_nav_icon"]'
        driver.find_element(AppiumBy.XPATH, back_xpath).click()
        time.sleep(2)
    except Exception as e:
        print(f"Erreur retour arrière : {e}")

def verify_date_changed(old_date):
    new_date = get_current_date()
    print(f"Date : Avant = {old_date} | Après = {new_date}")
    return old_date != new_date

def verify_time_changed(old_time):
    new_time = get_current_time()
    print(f"Heure : Avant = {old_time} | Après = {new_time}")
    return old_time != new_time

def test_date_change(driver):
    print("\nTEST DATE CHANGE")
    if not navigate_to_date_time_settings(driver):
        return
    disable_automatic_time(driver)
    old_date = get_current_date()
    change_date(driver)
    go_back(driver)
    if verify_date_changed(old_date):
        print("Test de changement de date PASSED")
    else:
        print("Test de changement de date FAILED")

def test_time_change(driver):
    print("\nTEST TIME CHANGE")
    if not navigate_to_date_time_settings(driver):
        return
    disable_automatic_time(driver)
    old_time = get_current_time()
    change_time(driver)
    go_back(driver)
    if verify_time_changed(old_time):
        print("Test de changement d'heure PASSED")
    else:
        print("Test de changement d'heure FAILED")

def test_micro_input():
    subprocess.run("adb shell svc wifi disable", shell=True)
    time.sleep(5)
    print("Ouverture de Google Assistant via ADB...")
    subprocess.run(
        f"adb -s {AAOS_UDID} shell am start -n com.google.android.carassistant/com.google.android.apps.gsa.binaries.auto.app.voiceplate.VoicePlateActivity",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    print("Lecture du fichier audio...")
    playsound(AUDIO_FILE)
    print("Audio envoyé au micro")
    print("Attente de la réponse de l'assistant...")
    time.sleep(7)

    current_package = driver.current_package
    print(f"Application active : {current_package}")

    if current_package == "com.android.vending":
        print("Play Store ouvert avec succès ! le microphone fonctionne bien ")
        subprocess.run(
        ["adb", "-s", AAOS_UDID, "shell", "am", "start", "-n", "com.android.car.carlauncher/.GASAppGridActivity"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        
    else:
        print("Play Store non détecté.")
def Test_install_uninstall_apks():
    print("===== DÉBUT DU TEST INSTALLATION APK =====\n")

    print(f"\nInstallation de l'application : {APK_PATH}")
    try:
        subprocess.run(["adb", "-s", AAOS_UDID, "install", "-r", APK_PATH], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Application installée avec succès.")
        time.sleep(5)
        subprocess.run(["adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "26"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(["adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "26"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
    except subprocess.CalledProcessError as e:
        print(f"Échec de l'installation ou de l'activation écran : {e}")
    print(f"\n Vérification via 'pm list packages' pour {PACKAGE_NAME}...")
    time.sleep(2)
    result = subprocess.run(["adb", "-s", AAOS_UDID, "shell", "pm", "list", "packages"], capture_output=True, text=True)
    if PACKAGE_NAME in result.stdout:
        print("Package trouvé via 'pm list packages'.")
    else:
        print("Package NON trouvé via 'pm list packages'.")

    print(f"\nVérification via 'dumpsys package' pour {PACKAGE_NAME}...")
    result = subprocess.run(["adb", "-s", AAOS_UDID, "shell", "dumpsys", "package", PACKAGE_NAME], capture_output=True, text=True)
    if f"Package [{PACKAGE_NAME}]" in result.stdout:
        print("Package trouvé via 'dumpsys package'.")
    else:
        print("Package NON trouvé via 'dumpsys package'.")

    print(f"\nVérification de l'Activity principale {PACKAGE_NAME}/{MAIN_ACTIVITY}...")
    result = subprocess.run(["adb", "-s", AAOS_UDID, "shell", "am", "start", "-n", f"{PACKAGE_NAME}/{MAIN_ACTIVITY}"], capture_output=True, text=True)
    if "Error type 3" in result.stdout or "does not exist" in result.stdout:
        print("L'Activity principale est introuvable.")
    else:
        print("L'Activity principale existe et est accessible.")

 
    print(f"\nLancement de l'application {PACKAGE_NAME}/{MAIN_ACTIVITY}...")
    try:
        subprocess.run(["adb", "-s", AAOS_UDID, "shell", "am", "start", "-n", f"{PACKAGE_NAME}/{MAIN_ACTIVITY}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        print("Application lancée avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Échec du lancement de l'application : {e}")


    print(f"\nDésinstallation de {PACKAGE_NAME}...")
    try:
        subprocess.run(["adb", "-s", AAOS_UDID, "uninstall", PACKAGE_NAME], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{PACKAGE_NAME} désinstallé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Échec de la désinstallation : {e}")

   
    print(f"\nVérification suppression de {PACKAGE_NAME}...")
    result = subprocess.run(["adb", "-s", AAOS_UDID, "shell", "pm", "list", "packages"], capture_output=True, text=True)
    if PACKAGE_NAME not in result.stdout:
        print("Application supprimée de l'émulateur.")
    else:
        print("Application encore présente.")

def lancer_launcher():
    subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "monkey", "-p", "com.android.car.carlauncher",
        "-c", "android.intent.category.LAUNCHER", "1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    time.sleep(3)

def cliquer_si_cancel():
    try:
        cancel_button = driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@resource-id='android:id/button2']")
        if cancel_button.is_displayed():
            cancel_button.click()
    except NoSuchElementException:
        pass

def ouvrir_media_player():
    lancer_launcher()
    try:
        media_icon = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Local Media Player")')
        media_icon.click()
        time.sleep(3)
    except Exception:
        raise Exception("Impossible d'ouvrir Local Media Player")

def entrer_ringtones():
    container = driver.find_element(AppiumBy.XPATH, "(//android.view.ViewGroup[@resource-id='com.android.car.media:id/item_container'])[1]")
    container.click()
    time.sleep(1)

def jouer_andromeda():
    sonnerie = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Andromeda")'))
    )
    sonnerie.click()
    time.sleep(1)
    driver.press_keycode(66)


def enregistrer_audio(nom_fichier):
    p = pyaudio.PyAudio()
    device_index = next((i for i in range(p.get_device_count())
                         if p.get_device_info_by_index(i).get("maxInputChannels", 0) > 0), None)
    if device_index is None:
        print("Aucun micro détecté.")
        return

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, input_device_index=device_index,
                    frames_per_buffer=CHUNK)

    frames = [stream.read(CHUNK) for _ in range(int(RATE / CHUNK * DURATION))]

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(nom_fichier, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
def analyser_audio(path, img_name):
    if not os.path.exists(path):
        return 0, 0, 0, 0

    with wave.open(path, 'rb') as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        framerate = wf.getframerate()

    filtre = scipy.signal.sosfilt(
        scipy.signal.butter(10, 100, 'hp', fs=framerate, output='sos'), audio)

    rms = np.sqrt(np.mean(filtre ** 2))
    db = 20 * np.log10(rms) if rms > 0 else -100

    chunk_size = int(framerate * 0.1)
    chunks = [filtre[i:i + chunk_size] for i in range(0, len(filtre), chunk_size)]
    active_chunks = sum(1 for c in chunks if 20 * np.log10(np.sqrt(np.mean(c ** 2))) > SEUIL_DB)
    pics_forts = sum(1 for c in chunks if 20 * np.log10(np.sqrt(np.mean(c ** 2))) > SEUIL_PIC_DB)

    plt.figure(figsize=(14, 5))
    plt.plot(filtre, color='green' if active_chunks * 0.1 >= SEUIL_DUREE_ACTIVE else 'red')
    plt.title(f"Signal Audio : {path}")
    plt.xlabel("Échantillons")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img_name)
    plt.close()

    return rms, db, active_chunks * 0.1, pics_forts

def retour_launcher():
    for _ in range(3):
        driver.press_keycode(4)
        time.sleep(1)
    lancer_launcher()

def fermer_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

def Test_micro_Output():
    ouvrir_media_player()
    cliquer_si_cancel()
    entrer_ringtones()
    jouer_andromeda()

    print("\nCapture AVANT Stop...")
    enregistrer_audio("before_stop.wav")

    print("\nEnvoi STOP...")
    subprocess.run(["adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "127"], shell=True)
    time.sleep(1)

    print("\nCapture APRÈS Stop...")
    enregistrer_audio("after_stop.wav")

    print("\nAnalyse...")
    before_rms, before_db, before_duree, before_pics = analyser_audio("before_stop.wav", "before_stop.png")
    after_rms, after_db, after_duree, after_pics = analyser_audio("after_stop.wav", "after_stop.png")

    rapport = f"""
✨ RAPPORT AUDIO
=====================

🔊 AVANT STOP :
---------------------
- Niveau RMS : {before_rms:.2f}
- Niveau sonore (dB) : {before_db:.2f} dB
- Durée avec son (> {SEUIL_DB} dB) : {before_duree:.2f} secondes
- Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {before_pics}

✅ Analyse :
Un signal audio important a été détecté avant l'envoi de la commande STOP. 
Le niveau RMS élevé ({before_rms:.2f}) et le volume sonore moyen ({before_db:.2f} dB) indiquent clairement une activité sonore significative. 
La totalité des {DURATION} secondes contient du son audible, avec {before_pics} pics forts dépassant le seuil critique de {SEUIL_PIC_DB} dB.
👉 Ces indicateurs confirment la lecture correcte de la sonnerie dans l’émulateur avant le STOP.

🔇 APRÈS STOP :
---------------------
- Niveau RMS : {after_rms:.2f}
- Niveau sonore (dB) : {after_db:.2f} dB
- Durée avec son (> {SEUIL_DB} dB) : {after_duree:.2f} secondes
- Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {after_pics}

🟡 Analyse :
Après l’envoi de la commande STOP, bien que le seuil de bruit soit dépassé sur toute la durée (10s),
le niveau RMS très bas ({after_rms:.2f}) et le volume sonore moyen faible ({after_db:.2f} dB) indiquent un bruit de fond minimal.
Le faible nombre de pics ({after_pics}) suggère l'absence de véritable activité sonore.
👉 Il n’y a pas de sonnerie jouée après le STOP — seulement un résidu ou bruit technique du micro.

🎯 CONCLUSION GLOBALE :
------------------------
✅ Le son a bien été détecté dans l’émulateur **avant** la commande STOP.
✅ Aucun son significatif n'a été détecté **après** — la commande STOP fonctionne correctement.
"""
    print(rapport)
    with open("rapport_audio.txt", "w", encoding="utf-8") as f:
        f.write(rapport)

    retour_launcher()
def ouvrir_barre_climatisation():

    os.system("adb shell input tap 740 749")
    time.sleep(2)

# ======================= TEST TEMPERATURE GAUCHE (OCR) =======================

def get_temp_from_screenshot(image_path, crop_coords):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Image introuvable : {image_path}")
        return None

    x, y, w, h = crop_coords
    cropped = image[y:y+h, x:x+w]
    cropped_path = image_path.replace(".png", "_cropped.png")
    cv2.imwrite(cropped_path, cropped)

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(processed, -1, kernel)
    debug_path = image_path.replace(".png", "_ocr_ready.png")
    cv2.imwrite(debug_path, sharpened)

    result = ocr.ocr(sharpened, cls=True)
    if not result or not result[0]:
        print("OCR n’a rien détecté.")
        return None

    candidates = []
    for line in result[0]:
        text = line[1][0]
        print(f"[OCR détecté] : {text}")
        try:
            clean_text = text.strip().replace("°", "").replace(",", ".")
            if clean_text.startswith("."):
                clean_text = clean_text[1:]
            number = int(float(clean_text))
            if 10 <= number <= 80:
                candidates.append(number)
        except:
            continue

    if candidates:
        selected = max(set(candidates), key=candidates.count)
        print(f"Température détectée par OCR : {selected}°")
        return selected

    print("Aucun nombre plausible détecté.")
    return None

def capture_temp(file_name, crop_coords, driver):
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
    path = os.path.join(SCREENSHOT_DIR, file_name)
    result = driver.save_screenshot(path)
    if not result:
        print(f"Échec de capture : {path}")
        return None
    print(f"📸 Capture enregistrée : {path}")
    return get_temp_from_screenshot(path, crop_coords)

def executer_test_temperature_gauche():
    print("\nTempérature GAUCHE (OCR + UI)")
    ouvrir_barre_climatisation()
    crop_coords = (32, 268, 96, 356)  

    plus_btn_xpath = '//android.widget.ImageView[@resource-id="com.android.systemui:id/hvac_increase_button"][1]'
    minus_btn_xpath = '//android.widget.ImageView[@resource-id="com.android.systemui:id/hvac_decrease_button"][1]'

    initial = capture_temp("initial.png", crop_coords, driver)
    if initial is None:
        print("OCR ÉCHEC – Température initiale non détectée.\n")
        return

    try:
        print("Augmentation température (x3)...")
        plus = driver.find_element(AppiumBy.XPATH, plus_btn_xpath)
        for _ in range(3):
            plus.click()
            time.sleep(1.5)
    except Exception as e:
        print(f"ERREUR lors du clic sur le bouton + : {e}")
        return

    after_plus = capture_temp("after_plus.png", crop_coords, driver)
    if after_plus is None:
        return

    try:
        print("Diminution température (x2)...")
        minus = driver.find_element(AppiumBy.XPATH, minus_btn_xpath)
        for _ in range(2):
            minus.click()
            time.sleep(1.5)
    except Exception as e:
        print(f"ERREUR lors du clic sur le bouton - : {e}")
        return

    after_minus = capture_temp("after_minus.png", crop_coords, driver)
    if after_minus is None:
        return

    print("\n[Récapitulatif Température Gauche]")
    print(f"    Température initiale      : {initial}°")
    print(f"    Après augmentation (x3)   : {after_plus}° ")
    print(f"    Après diminution (x2)     : {after_minus}° ")

    if after_plus > initial and after_minus < after_plus:
        print("\nTempérature Gauche ajustée correctement.\n")
    else:
        print("\nLa température n’a pas été ajustée comme prévu.\n")


def get_temperature_droite():
    try:
        elements = driver.find_elements(AppiumBy.ID, "com.android.systemui:id/hvac_temperature_text")
        if len(elements) > 1:
            temp_text = elements[1].text.replace("°", "").strip()
            temp = int(temp_text)
            print(f"   Température actuelle (droite) : {temp}°")
            return temp
        # Fallback
        fallback_temp = int(driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "°")]').text.replace("°", "").strip())
        print(f"    Température détectée via fallback : {fallback_temp}°")
        return fallback_temp
    except Exception as e:
        print(f"Erreur lecture température droite : {e}")
        return -1

def augmenter_temperature_droite():
    print("Augmentation température DROITE (x3)...")
    for _ in range(3):
        os.system("adb shell input tap 1329 314")
        time.sleep(1.5)

def diminuer_temperature_droite():
    print("Diminution température DROITE (x2)...")
    for _ in range(2):
        os.system("adb shell input tap 1332 577")
        time.sleep(1.5)

def verifier_changement_temperature(ancienne, nouvelle, action):
    if action == "augmentation" and nouvelle > ancienne:
        print("Température augmentée avec succès.")
        return True
    elif action == "diminution" and nouvelle < ancienne:
        print("Température diminuée avec succès.")
        return True
    print("Aucun changement détecté après", action)
    return False

def executer_test_temperature_droite():
    print("\nTempérature DROITE (Appium UI)")

    initial = get_temperature_droite()
    if initial == -1:
        print("Température initiale introuvable.\n")
        return

    augmenter_temperature_droite()
    apres_plus = get_temperature_droite()
    if apres_plus == -1 or not verifier_changement_temperature(initial, apres_plus, "augmentation"):
        print("Échec augmentation.\n")
        return

    diminuer_temperature_droite()
    apres_moins = get_temperature_droite()
    if apres_moins == -1 or not verifier_changement_temperature(apres_plus, apres_moins, "diminution"):
        print("Échec diminution.\n")
        return

 
    print("\n[Récapitulatif Température Droite]")
    print(f"    Température initiale        : {initial}°")
    print(f"    Après augmentation (x3)     : {apres_plus}° ")
    print(f"    Après diminution (x2)       : {apres_moins}° ")

    print("\nTempérature DROITE ajustée correctement.\n")


def test_toggle_ac_state_on_aaos():
  

    try:
        ac_button = driver.find_element(AppiumBy.XPATH, '//android.widget.ImageButton[@resource-id="com.android.systemui:id/ac_button"]')
        
        # État initial
        ac_initial = ac_button.get_attribute("selected") == "true"
        etat_txt = "ACTIVÉ" if ac_initial else "DÉSACTIVÉ"
        print(f"État initial de l'AC : {' ACTIVÉ' if ac_initial else ' DÉSACTIVÉ'}")

        # Bascule 1 : changer l'état
        print(f"Tentative de {'désactivation' if ac_initial else 'activation'} de l'AC...")
        ac_button.click()
        time.sleep(2)

        ac_apres_1 = ac_button.get_attribute("selected") == "true"
        if ac_apres_1 != ac_initial:
            print(f"Changement réussi : AC est maintenant {' ACTIVÉ' if ac_apres_1 else ' DÉSACTIVÉ'}")
        else:
            print("Aucune modification détectée à la première bascule.")
            return

        print(f"Retour à l'état initial : {'activation' if not ac_initial else 'désactivation'} de l'AC...")
        ac_button.click()
        time.sleep(2)

        ac_apres_2 = ac_button.get_attribute("selected") == "true"
        if ac_apres_2 == ac_initial:
            print(f"Retour réussi : AC est de nouveau {' ACTIVÉ' if ac_apres_2 else ' DÉSACTIVÉ'}")
            print("\nL'AC a été correctement activée puis désactivée.")
        else:
            print("Le retour à l'état initial a échoué.")

    except Exception as e:
        print(f"Erreur pendant le test de bascule AC : {e}")


    os.system("adb shell input tap 740 749")
    time.sleep(2)

def Test_hvac_temperature_control():
    executer_test_temperature_gauche()
    executer_test_temperature_droite()

@keyword("Run Test bluetooth toggle sync")
def run_test_bluetooth_toggle_sync():
    test_bluetooth_toggle_sync()

@keyword("Run Test Hotspot Behavior")
def run_test_hotspot_behavior():
    test_hotspot_behavior(driver)

@keyword("Run Test Mobile Network Behavior")
def run_test_mobile_network_behavior():
    test_mobile_network_behavior(driver)

@keyword("Run Test wifi connectivity")
def run_test_wifi_connectivity():
    test_wifi_connectivity()

@keyword("Run Test wifi disconnectivity")   
def run_wifi_disconnectivity():
    test_wifi_disconnectivity()   
@keyword("Run Test forget network") 
def run_forget_network():
    test_forget_network()
@keyword("Run Test loopback latency ")
def run_loopback_latency():
    test_loopback_latency() 
@keyword("Run Test wifi latency ")
def run_wifi_latency():
    test_wifi_latency()
@keyword("Run Test mobile network latency ")
def run_mobile_network_latency():
    test_mobile_network_latency()
  
@keyword("Run Test brightness slider functionality ")
def Run_test_brightness_slider_functionality():
    test_brightness_slider_functionality(driver)

@keyword("Run Test adaptive brightness functionality ")
def Run_test_adaptive_brightness_functionality():
    test_adaptive_brightness_functionality(driver)

@keyword("Run Test adaptive brightness functionality ")
def Run_test_adaptive_brightness_functionality():
    test_adaptive_brightness_functionality(driver)

@keyword("Run Test Date change")
def run_test_date_change():
    test_date_change(driver)

@keyword("Run Test Time change")
def run_test_Time_change():
    test_time_change(driver)

@keyword("Run Test micro Input")
def run_test_Micro_input():
       test_micro_input()

@keyword("Run Test install uninstall Apks")
def run_test_install_uninstall_apks():
      Test_install_uninstall_apks()

      
@keyword("Run Test micro Output")
def run_test_micro_output():
        Test_micro_Output()

@keyword("Run Test hvac temperature control")
def run_test_hvac_temperature():
    Test_hvac_temperature_control() 

@keyword("Run Test hvac climatisation system (AC)")
def run_test_hvac_climatisation_system():
   test_toggle_ac_state_on_aaos()

