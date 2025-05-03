import subprocess
import time
from emulator_manager import start_avd_by_type
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

# Vérification explicite pour s'assurer que l'émulateur est détecté
def wait_for_emulator_of_type(emulator_type, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()[1:]
        for line in lines:
            if "device" in line and "emulator" in line:
                uid = line.split()[0]
                if emulator_type == "phone" and ("gphone" in line or "model:sdk_gphone" in line):
                    print(f"✅ Émulateur PHONE détecté : {uid}")
                    return uid
                elif emulator_type == "automotive" and ("gcar" in line or "model:car" in line):
                    print(f"✅ Émulateur AUTOMOTIVE détecté : {uid}")
                    return uid
        print(f"⏳ En attente d'un émulateur de type {emulator_type}...")
        time.sleep(5)
    raise RuntimeError(f"⛔ Aucun émulateur de type {emulator_type} détecté après {timeout} secondes.")



def open_phone_settings_and_navigate():
    print("📱 Démarrage et configuration téléphone...")
    start_avd_by_type("phone")

    phone_uid = wait_for_emulator_of_type("phone")


    driver_factory.initialize_driver_for_type("phone")
    driver = driver_factory.get_driver("phone")

    if not driver or not phone_uid:
        raise RuntimeError("❌ Driver ou UID du téléphone non récupéré.")

    driver.press_keycode(3)
    wait(1)

    subprocess.run(["adb", "-s", phone_uid, "shell", "am", "start", "-a", "android.settings.SETTINGS"])
    wait(2)

    connected_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.settings:id/recycler_view"]/android.widget.LinearLayout[3]'
    click_xpath(driver, connected_xpath, "Ouvrir Connected Devices")
    wait(3)

    pair_xpath = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.settings:id/recycler_view"]/android.widget.LinearLayout[1]'
    click_xpath(driver, pair_xpath, "Ouvrir Pair New Devices")
    wait(3)

    return driver, phone_uid


open_phone_settings_and_navigate()



