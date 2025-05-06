import subprocess
import time
import shutil
import socket
from emulator_manager import start_avd_by_type
from appium_driver_factory import driver_factory
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from appium.options.common import AppiumOptions

def wait(seconds):
    print(f"⏳ Attente {seconds} secondes...")
    time.sleep(seconds)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def find_free_port(start_port=4723, max_tries=10):
    for i in range(max_tries):
        port = start_port + i
        if not is_port_in_use(port):
            return port
    raise RuntimeError("⛔ Aucun port libre trouvé.")

def start_appium_on_free_port(start_port=4723):
    appium_path = shutil.which("appium")
    if appium_path is None:
        raise RuntimeError("⛔ Appium non trouvé. Exécute : npm install -g appium")

    free_port = find_free_port(start_port)
    print(f"🚀 Lancement Appium Server sur le port {free_port}...")
    subprocess.Popen([appium_path, "-p", str(free_port), "--base-path", "/wd/hub"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    return free_port

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
        print(f"⏳ En attente d'un émulateur de type {emulator_type}...")
        time.sleep(5)
    raise RuntimeError(f"⛔ Aucun émulateur {emulator_type} détecté après {timeout}s.")

def open_phone_settings_and_navigate():
    print("📱 Démarrage et configuration téléphone...")
    start_avd_by_type("phone")
    phone_uid = wait_for_emulator_of_type("phone")

    # 🚀 Lancer Appium sur port libre (≠ de 4723 si déjà utilisé)
    appium_port = start_appium_on_free_port(4723)

    # 🧠 Créer un driver Appium manuellement (pas via driver_factory ici)
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "Android Emulator")
    options.set_capability("automationName", "UiAutomator2")
    options.set_capability("noReset", True)

    driver = webdriver.Remote(f"http://127.0.0.1:{appium_port}/wd/hub", options=options)

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

# 🟢 Lance le scénario
open_phone_settings_and_navigate()
