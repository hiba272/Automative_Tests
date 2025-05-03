import subprocess
import time
from emulator_manager import start_avd_by_type
from appium_driver_factory import driver_factory
from appium.webdriver.common.appiumby import AppiumBy

def wait(seconds):
    print(f"⏳ Attente {seconds} secondes...")
    time.sleep(seconds)

def click_xpath(driver, xpath, description="", timeout=20):
    print(f"🔱 Action : {description}")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            element.click()
            print(f"✅ Cliqué sur {description}")
            return True
        except Exception as e:
            time.sleep(0.5)
    print(f"❌ XPATH non trouvé ou non cliquable après timeout : {description}")
    import subprocess
import time



def open_phone_settings_and_navigate():
    print("📱 Démarrage et configuration téléphone...")
    start_avd_by_type("phone")
    attendre_emulateur_pret("emulator-5554")

    driver_factory.initialize_drivers()
    driver = driver_factory.get_driver("phone")
    phone_uid = driver_factory.get_emulator_uid("phone")

    if not driver or not phone_uid:
        raise RuntimeError("❌ Driver ou UID du téléphone non récupéré.")

    print("⚙️ Fermeture forcée et ouverture des paramètres...")
    subprocess.run(["adb", "-s", phone_uid, "shell", "am", "force-stop", "com.android.settings"])
    subprocess.run(["adb", "-s", phone_uid, "shell", "am", "start", "-n", "com.android.settings/.Settings"])
    wait(3)

    with open("dump.xml", "w", encoding="utf-8") as f:
     f.write(driver.page_source)
    print("📄 Dump enregistré dans dump.xml.")
    current_activity = driver.current_activity
    print("📺 Activité actuelle :", current_activity)

    click_xpath(driver, '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.android.settings:id/recycler_view"]/android.widget.LinearLayout[3]', "Cliquer sur 'Connected devices'")
    wait(2)

    click_xpath(driver, '//android.widget.TextView[@text="Pair new device"]', "Cliquer sur 'Pair new device'")
    wait(2)

    return driver, phone_uid

def attendre_emulateur_pret(phone_uid, timeout=120):
    print(f"⏳ Attente que l'émulateur {phone_uid} soit prêt...")
    debut = time.time()
    while time.time() - debut < timeout:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if phone_uid in result.stdout and "device" in result.stdout:
            print(f"✅ Émulateur {phone_uid} détecté par ADB.")
            return True
        time.sleep(5)
    raise TimeoutError(f"⛔️ Émulateur {phone_uid} non détecté par ADB après {timeout} secondes.")


if __name__ == "__main__":
    open_phone_settings_and_navigate()
   