import time
import os
from playsound import playsound
from appium import webdriver
from appium.options.common import AppiumOptions
import subprocess

# 📱 Paramètres généraux
AAOS_UDID = "emulator-5554"
APPIUM_SERVER_URL = "http://127.0.0.1:4723"
AUDIO_FILE = "open_play_store.mp3"
ATTENTE_ASSISTANT = 7  # secondes pour laisser Assistant répondre

# Driver global
driver = None

def setup_appium():
    """Configure et lance une session Appium."""
    global driver
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "Android Emulator")
    options.set_capability("udid", AAOS_UDID)
    options.set_capability("automationName", "UiAutomator2")
    options.set_capability("noReset", True)
    driver = webdriver.Remote(command_executor=APPIUM_SERVER_URL, options=options)
    time.sleep(5)

def ouvrir_google_assistant():
    """Force l'ouverture de Google Assistant via ADB."""
    print("🚀 Ouverture de Google Assistant via ADB...")
    subprocess.run(
    f"adb -s {AAOS_UDID} shell am start -n com.google.android.carassistant/com.google.android.apps.gsa.binaries.auto.app.voiceplate.VoicePlateActivity",
    shell=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
    time.sleep(3)

def envoyer_audio_open_play_store():
    """Joue l'audio pour commander l'ouverture du Play Store."""
    print("🎙️ Lecture du fichier audio...")
    playsound(AUDIO_FILE)
    print("✅ Audio envoyé au micro")

def verifier_play_store():
    """Vérifie si le Play Store est ouvert."""
    current_package = driver.current_package
    print(f"🛠️ Application active : {current_package}")
    return current_package == "com.android.vending"

def close_appium():
    """Ferme proprement la session Appium."""
    global driver
    if driver:
        driver.quit()
        print("🚪 Appium fermé proprement.")
if __name__ == "__main__":
    setup_appium()
    ouvrir_google_assistant()
    envoyer_audio_open_play_store()
    time.sleep(ATTENTE_ASSISTANT)
    if verifier_play_store():
        print("✅ Play Store ouvert avec succès !")
    else:
        print("❌ Play Store non détecté.")
    close_appium()
