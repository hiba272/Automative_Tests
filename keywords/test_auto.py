import subprocess
import time
from appium_driver_factory import driver_factory
from appium.webdriver.common.appiumby import AppiumBy

def wait(seconds):
    print(f"⏳ Attente {seconds} secondes...")
    time.sleep(seconds)

def click_xpath(driver, xpath, description="", timeout=15):
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
    
    # Debug: print tous les textes visibles si échec
    elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    print("📋 Éléments visibles à l'écran :")
    for el in elements:
        try:
            print(" •", el.text)
        except:
            pass

    return False

def pair_new_device_on_aaos():
    print("🔗 Démarrage du Pairing AAOS...")

    driver = driver_factory.get_driver("automotive")
    if driver is None:
        print("ℹ️ Initialisation du driver automotive...")
        driver_factory.initialize_driver_for_type("automotive")
        driver = driver_factory.get_driver("automotive")

    if driver is None:
        raise RuntimeError("❌ Driver automotive non récupéré.")

    emulator_uid = driver_factory.get_emulator_uid("automotive")
    print("📲 Navigation vers Settings AAOS...")
    subprocess.run(["adb", "-s", emulator_uid, "shell", "am", "start", "-n", "com.android.car.settings/.Settings_Launcher_Homepage"])
    wait(5)

    pair_new_device_xpath = '//android.widget.TextView[@text="Pair new device"]'
    phone_device_xpath = '//android.view.ViewGroup[@resource-id="com.android.car.settings:id/multi_action_preference_first_action_container"]'
    pair_button_xpath = '//android.widget.Button[@resource-id="android:id/button1"]'

    if click_xpath(driver, pair_new_device_xpath, "Ouvrir Pair New Device"):
        wait(1)
        if click_xpath(driver, phone_device_xpath, "Sélectionner sdk_gphone64_x86_64"):
            wait(1)
            if click_xpath(driver, pair_button_xpath, "Cliquer sur Pair AAOS"):
                wait(1)
                print("✅ Pairing terminé avec succès !")
            else:
                print("❌ Échec au clic sur Pair AAOS")
        else:
            print("❌ Échec à sélectionner sdk_gphone64_x86_64")
    else:
        print("❌ Échec à ouvrir Pair New Device")

# Lancer la fonction
pair_new_device_on_aaos()
