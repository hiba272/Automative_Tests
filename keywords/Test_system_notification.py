import os
import time
import cv2
from paddleocr import PaddleOCR
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.common import AppiumOptions
import subprocess
# Initialisation du driver global
driver = None

def setup_appium():
    """ Configure et démarre une session Appium """
    global driver
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "emulator-5554")
    options.set_capability("automationName", "UiAutomator2")
    options.set_capability("appPackage", "com.android.systemui")
    options.set_capability("appActivity", ".notetask.LaunchNotesRoleSettingsTrampolineActivity")

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    time.sleep(3)

def open_notifications():
    """ Ouvre le panneau des notifications """
    print("📩 Ouverture du panneau des notifications...")
    driver.open_notifications()
    time.sleep(2)

def check_notification_with_appium():
    """ Vérifie la présence d'une notification via Appium """
    print("🔄 Vérification des notifications via Appium...")
    try:
        notifications = driver.find_elements(AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Notification")]')
        if notifications:
            print("✅ Notification détectée avec Appium !")
            return True
        else:
            print("❌ Aucune notification détectée via Appium.")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification Appium : {e}")
        return False

def check_notification_with_adb():
    """ Vérifie la présence d'une notification via ADB """
    print("🔄 Vérification des notifications via ADB...")
    try:
        result = os.popen("adb shell dumpsys notification").read()
        if "Notification" in result or "notification" in result:
            print("✅ Notification détectée avec ADB !")
            return True
        else:
            print("❌ Aucune notification trouvée via ADB.")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'utilisation d'ADB : {e}")
        return False

def check_notification_with_ocr():
    """ Vérifie la présence d'une notification via OCR (PaddleOCR) """
    print("🔄 Vérification des notifications via OCR (PaddleOCR)...")
    try:
        # Capture l'écran du téléphone
        screenshot_device_path = "/sdcard/notification.png"
        screenshot_local_path = "notification.png"

        os.system(f"adb shell screencap -p {screenshot_device_path}")
        os.system(f"adb pull {screenshot_device_path} {screenshot_local_path}")

        img = cv2.imread(screenshot_local_path)

        # Utiliser PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(img, cls=True)

        extracted_text = ""
        for line in result[0]:
            extracted_text += line[1][0] + " "

        print("🔍 Texte extrait OCR : ", extracted_text.strip())

        if "Notification" in extracted_text or "notification" in extracted_text:
            print("✅ Notification détectée avec PaddleOCR !")
            return True
        else:
            print("❌ Aucune notification détectée via OCR.")
            return False
    except Exception as e:
        print(f"❌ Erreur OCR : {e}")
        return False

def capture_screenshot(filename):
    """ Capture et enregistre une capture d'écran """
    print(f"📸 Capture écran : {filename}...")
    try:
        os.system("adb shell mkdir -p /sdcard/captures/")
        full_path_device = f"/sdcard/captures/{filename}"
        full_path_local = filename
        os.system(f"adb shell screencap -p {full_path_device}")
        os.system(f"adb pull {full_path_device} {full_path_local}")
        print(f"✅ Screenshot sauvegardé localement : {full_path_local}")
    except Exception as e:
        print(f"❌ Erreur capture écran : {e}")

def close_notifications():
    """ Ferme le panneau des notifications en simulant un TAP aux coordonnées (852, 749) """
    print("🚪 Fermeture du panneau des notifications par TAP aux coordonnées (852, 749)...")
    try:
        os.system(f"adb shell input tap 852 749")
        time.sleep(2)
        print("✅ Panneau des notifications fermé avec un tap.")
    except Exception as e:
        print(f"❌ Erreur lors du TAP pour fermeture : {e}")

def close_app():
    """ Ferme la session Appium """
    global driver
    if driver:
        driver.quit()
        print("🚪 Appium fermé proprement.")
if __name__ == "__main__":
    setup_appium()
    open_notifications()

    check_notification_with_adb()
    check_notification_with_ocr()

    capture_screenshot("notification_test_final.png")
    close_notifications()
    close_app()
