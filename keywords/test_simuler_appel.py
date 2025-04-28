import subprocess
import time
import os
from appium import webdriver
from appium.options.common import AppiumOptions
from paddleocr import PaddleOCR

# 📱 Driver Appium global
driver = None
ocr = PaddleOCR(use_angle_cls=True, lang='en')
CAPTURE_PATH = "screenshot_incoming_call.png"

# ======================= SETUP APPIUM =======================

def setup_appium():
    global driver
    if driver is None:
        print("🚀 Démarrage session Appium...")
        options = AppiumOptions()
        options.set_capability("platformName", "Android")
        options.set_capability("deviceName", "Android Emulator")
        options.set_capability("automationName", "UiAutomator2")
        options.set_capability("noReset", True)
        driver = webdriver.Remote(command_executor="http://127.0.0.1:4723", options=options)
        time.sleep(5)
        print("✅ Session Appium démarrée.")

# ======================= FERMER APPIUM =======================

def fermer_appium():
    global driver
    if driver:
        driver.quit()
        driver = None
        print("📴 Session Appium fermée proprement.")

# ======================= SIMULATION + OCR DETECTION =======================

def test_simuler_et_verifier_appel(numero="123456"):
    print(f"\n📞 Simulation d'appel entrant depuis {numero}...")

    try:
        # 1️⃣ Lancer l'appel simulé
        result = subprocess.run(
            ["adb", "emu", "gsm", "call", numero],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Échec de la simulation d'appel : {result.stderr}")
            return

        print("✅ Appel simulé avec succès.")

        # 2️⃣ Attendre un peu pour que l'appel arrive
        time.sleep(3)

        # 3️⃣ Capture d'écran complète
        subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/capture.png"])
        subprocess.run(["adb", "pull", "/sdcard/capture.png", CAPTURE_PATH])
        print("📸 Capture d'écran sauvegardée.")

        # 4️⃣ Analyse OCR sur tout l'écran
        result = ocr.ocr(CAPTURE_PATH, cls=True)
        detected_texts = [line[1][0] for block in result for line in block]
        print(f"🧠 Textes détectés : {detected_texts}")

        # 5️⃣ Vérification si "Incoming call" apparaît
        incoming_call_detected = any("incoming call" in text.lower() for text in detected_texts)

        if incoming_call_detected:
            print("✅ Appel entrant détecté par OCR ! 🎯")
        else:
            print("❌ Appel entrant NON détecté par OCR.")

        time.sleep(2)

        # 6️⃣ Raccrocher l'appel simulé
        subprocess.run(["adb", "emu", "gsm", "cancel", numero])
        print("📴 Appel simulé terminé (raccroché).")

    except Exception as e:
        print(f"❌ Erreur inattendue lors du test d'appel : {e}")

# ======================= MAIN =======================

if __name__ == "__main__":
    setup_appium()
    test_simuler_et_verifier_appel("123456")
    fermer_appium()
