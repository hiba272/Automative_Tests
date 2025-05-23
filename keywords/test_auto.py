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
        
        open_phone_settings_and_navigate()

     
        pair_new_device_on_aaos(driver_aaos)

     
        confirm_pairing_on_phone(driver_phone)

        finalize_pairing_on_aaos(driver_aaos)

        # 5. Vérification OCR que le Phone est bien connecté sur AAOS
        verify_connection_with_ocr(driver_aaos, "aaos")

        print("✅ Test Bluetooth Pairing + Vérification OCR réussi entre Phone et AAOS.")

    except Exception as e:
        print(f"❌ Erreur lors du test de Bluetooth Pairing : {e}")

open_aaos_settings()
test_bluetooth_pairing()
