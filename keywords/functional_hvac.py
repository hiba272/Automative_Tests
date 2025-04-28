import os
import time
import cv2
from paddleocr import PaddleOCR
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.common import AppiumOptions
import numpy as np
from ultralytics import YOLO    
ocr = PaddleOCR(use_angle_cls=True, lang='en')
driver = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCREENSHOT_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "screenshots_hvac"))
MODEL_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "yolo_model", "best.pt"))
CAPTURE_PATH = os.path.join(SCREENSHOT_DIR, "capture_auto.png")

# ======================= SETUP APPIUM =======================
def setup_appium():
    
    global driver
    print("[🚗] Initialisation Appium...")
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "emulator-5554")
    options.set_capability("automationName", "UiAutomator2")
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    time.sleep(2)

# ======================= OUVERTURE BARRE DE CLIMATISATION =======================
def ouvrir_barre_climatisation():
    print("📌 Ouverture de la barre de climatisation...")
    os.system("adb shell input tap 740 749")
    time.sleep(2)

# ======================= TEST TEMPERATURE GAUCHE (OCR) =======================

def get_temp_from_screenshot(image_path, crop_coords):
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Image introuvable : {image_path}")
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
        print("⚠️ OCR n’a rien détecté.")
        return None

    candidates = []
    for line in result[0]:
        text = line[1][0]
        print(f"[🧠 OCR détecté] : {text}")
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
        print(f"🌡 Température détectée par OCR : {selected}°")
        return selected

    print("⚠️ Aucun nombre plausible détecté.")
    return None

def capture_temp(file_name, crop_coords, driver):
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
    path = os.path.join(SCREENSHOT_DIR, file_name)
    result = driver.save_screenshot(path)
    if not result:
        print(f"❌ Échec de capture : {path}")
        return None
    print(f"📸 Capture enregistrée : {path}")
    return get_temp_from_screenshot(path, crop_coords)

def executer_test_temperature_gauche():
    print("🧪 TEST T01 — Température GAUCHE (OCR + Crop)")
    global driver

    crop_coords = (32, 268, 96, 356)  # x, y, w, h

    plus_btn_xpath = '//android.widget.ImageView[@resource-id="com.android.systemui:id/hvac_increase_button"][1]'
    minus_btn_xpath = '//android.widget.ImageView[@resource-id="com.android.systemui:id/hvac_decrease_button"][1]'

    initial = capture_temp("initial.png", crop_coords, driver)
    if initial is None:
        print("❌ OCR ÉCHEC – Température initiale non détectée.")
        return

    try:
        plus = driver.find_element(AppiumBy.XPATH, plus_btn_xpath)
        for _ in range(3):
            plus.click()
            time.sleep(1.5)
    except Exception as e:
        print(f"❌ ERREUR bouton + : {e}")
        return

    after_plus = capture_temp("after_plus.png", crop_coords, driver)
    if after_plus is None:
        return

    try:
        minus = driver.find_element(AppiumBy.XPATH, minus_btn_xpath)
        for _ in range(2):
            minus.click()
            time.sleep(1.5)
    except Exception as e:
        print(f"❌ ERREUR bouton - : {e}")
        return

    after_minus = capture_temp("after_minus.png", crop_coords, driver)
    if after_minus is None:
        return

    print(f"🌡 Initiale : {initial}°, + : {after_plus}°, - : {after_minus}°")
    if after_plus > initial and after_minus < after_plus:
        print("✅ TEST T01 RÉUSSI")
    else:
        print("❌ TEST T01 ÉCHOUÉ")
# ======================= TEST TEMPERATURE DROITE (APPIUM) =======================
def get_temperature_droite():
    try:
        elements = driver.find_elements(AppiumBy.ID, "com.android.systemui:id/hvac_temperature_text")
        if len(elements) > 1:
            temp_text = elements[1].text.replace("°", "").strip()
            temp = int(temp_text)
            print(f"🌡 Température actuelle (droite) : {temp}°")
            return temp
        return int(driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "°")]').text.replace("°", "").strip())
    except Exception as e:
        print(f"❌ Erreur température droite : {e}")
        return -1

def augmenter_temperature_droite():
    print("🔼 Augmentation température DROITE (x3)...")
    for _ in range(3):
        os.system("adb shell input tap 1329 314")
        time.sleep(1.5)

def diminuer_temperature_droite():
    print("🔽 Diminution température DROITE (x2)...")
    for _ in range(2):
        os.system("adb shell input tap 1332 577")
        time.sleep(1.5)

def verifier_changement_temperature(ancienne, nouvelle, action):
    if action == "augmentation" and nouvelle > ancienne:
        print("✅ Température augmentée.")
        return True
    elif action == "diminution" and nouvelle < ancienne:
        print("✅ Température diminuée.")
        return True
    print("❌ Aucun changement détecté.")
    return False

def executer_test_temperature_droite():
    print("\n🧪 TEST T02 — Température DROITE (Appium)")
    initial = get_temperature_droite()
    if initial == -1: return

    augmenter_temperature_droite()
    apres_plus = get_temperature_droite()
    if not verifier_changement_temperature(initial, apres_plus, "augmentation"): return

    diminuer_temperature_droite()
    apres_moins = get_temperature_droite()
    verifier_changement_temperature(apres_plus, apres_moins, "diminution")

# ======================= TEST AUTO (APPIUM + YOLO) =======================
def test_bouton_auto_verifie_yolo():
    print("🧪 TEST T03 — Bouton AUTO HVAC + Vérification visuelle YOLO")
    try:
        auto_button = driver.find_element(AppiumBy.XPATH, '//android.widget.ImageButton[@resource-id="com.android.systemui:id/auto_button"]')
        etat_initial = auto_button.get_attribute("selected")

        if etat_initial == "true":
            print("⚠️ AUTO est activé. Tentative de désactivation...")
            auto_button.click()
            time.sleep(2)
        else:
            print("ℹ️ AUTO est désactivé. Tentative d’activation...")
            auto_button.click()
            time.sleep(2)

        # Détection visuelle
        print("🔍 Prédiction de l’état du bouton AUTO via YOLO...")
        os.system(f"adb shell screencap -p /sdcard/capture.png")
        os.system(f"adb pull /sdcard/capture.png {CAPTURE_PATH}")

        model = YOLO(MODEL_PATH)
        results = model(CAPTURE_PATH)[0]
        classes = results.names
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = classes[cls_id]
            conf = float(box.conf[0])
            print(f"🔎 {label} détecté avec confiance {conf:.2f}")
            if conf > 0.7 and label in ["auto_enabled", "auto_disabled"]:
                print(f"🎯 État visuel détecté après clic : {label.upper()}")
                return
        print("⚠️ Aucun état fiable détecté visuellement.")

    except Exception as e:
        print(f"❌ ERREUR : Impossible d’interagir avec le bouton AUTO.\n{e}")
# ======================= TEST AC (APPIUM + YOLO) =======================        

def activer_desactiver_climatisation():
    """ Active ou désactive la climatisation en fonction de son état actuel """
    print("🔄 Changement de l'état AC...")

    try:
        ac_button = driver.find_element(AppiumBy.XPATH, '//android.widget.ImageButton[@resource-id="com.android.systemui:id/ac_button"]')
        ac_actif = ac_button.get_attribute("selected") == "true"

        if ac_actif:
            print("🔵 AC est actuellement ACTIVÉ, désactivation...")
        else:
            print("🟢 AC est actuellement DÉSACTIVÉ, activation...")

        ac_button.click()  # Basculer l'état d'AC
        time.sleep(2)

        # Vérifier l'état après le clic
        nouvel_etat = ac_button.get_attribute("selected") == "true"

        if nouvel_etat != ac_actif:
            print("✅ Changement de l'état AC réussi.")
        else:
            print("❌ Aucun changement détecté, AC n'a pas été modifié correctement.")
    except Exception as e:
        print(f"⚠️ Erreur lors du changement de l'AC : {e}")


# ======================= FERMETURE =======================
def fermer_barre_climatisation():
    """ Ferme la barre de climatisation en retapant sur la même zone que l'ouverture. """
    print("📌 Fermeture de la barre de climatisation...")
    os.system("adb shell input tap 740 749")
    time.sleep(2)

def fermer_appium():
    if driver:
        driver.quit()
        print("📴 Appium fermé.")

# ---------- MAIN ----------
if __name__ == "__main__":
    setup_appium()
    ouvrir_barre_climatisation()
    executer_test_temperature_gauche()
    executer_test_temperature_droite()
    test_bouton_auto_verifie_yolo()
    activer_desactiver_climatisation()
    fermer_barre_climatisation()
    fermer_appium()
