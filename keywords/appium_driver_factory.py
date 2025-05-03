import subprocess
import time
from appium.options.common import AppiumOptions
from appium.webdriver import Remote
from selenium.common.exceptions import WebDriverException

class AppiumDriverFactory:
    def __init__(self):
        self.drivers = {}      
        self.emulators = {}    

    def get_available_emulators(self):
        try:
            result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, check=True)
            output = result.stdout
            emulators = []

            for line in output.splitlines():
                if 'emulator' in line and 'device' in line:
                    parts = line.split()
                    udid = parts[0]
                    model = ''
                    for part in parts:
                        if part.startswith("model:"):
                            model = part.split(":")[1]
                    emulators.append((udid, model))

            if not emulators:
                raise RuntimeError("Aucun émulateur détecté. Vérifiez 'adb devices'.")

            return emulators
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors de l'exécution de 'adb devices' : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération des émulateurs : {e}")

    def wait_for_shell_ready(self, emulator_uid, timeout=60):
        print(f"⏳ Attente que {emulator_uid} réponde à 'adb shell'...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['adb', '-s', emulator_uid, 'shell', 'getprop', 'sys.boot_completed'],
                    capture_output=True, text=True, check=True
                )
                if result.stdout.strip() == "1":
                    print(f"✅ {emulator_uid} est prêt.")
                    return
            except subprocess.CalledProcessError:
                pass
            time.sleep(2)
        raise TimeoutError(f"❌ {emulator_uid} ne répond pas à adb shell après {timeout} secondes.")

    def detect_emulator_type(self, emulator_uid, model):
        if "car" in model.lower():
            return "automotive"
        elif "phone" in model.lower() or "gphone" in model.lower():
            return "phone"
        else:
            print(f"❓ Modèle inconnu : {model}, supposition 'phone'")
            return "phone"

    def setup_driver(self, emulator_uid, emulator_type, app_package=None, app_activity=None):
        options = AppiumOptions()
        options.set_capability("platformName", "Android")
        options.set_capability("deviceName", emulator_uid)
        options.set_capability("automationName", "UiAutomator2")
        options.set_capability("adbExecTimeout", 60000)
        if app_package and app_activity:
            options.set_capability("appPackage", app_package)
            options.set_capability("appActivity", app_activity)

        if emulator_type == 'automotive':
            options.set_capability("appium:deviceType", "automotive")

        try:
            self.wait_for_shell_ready(emulator_uid) 
            driver = Remote("http://127.0.0.1:4723", options=options)
            time.sleep(5)
            return driver
        except WebDriverException as e:
            raise RuntimeError(f"Échec de la création du driver pour {emulator_uid} : {e}")

    def initialize_drivers(self, default_app_package=None, default_app_activity=None):
        if self.drivers:
            print("Drivers déjà initialisés, réutilisation.")
            return

        emulators = self.get_available_emulators()
        for emulator_uid, model in emulators:
            emulator_type = self.detect_emulator_type(emulator_uid, model)
            if emulator_type in ['phone', 'automotive']:
                self.wait_for_shell_ready(emulator_uid)
                driver = self.setup_driver(emulator_uid, emulator_type, default_app_package, default_app_activity)
                self.drivers[emulator_type] = driver
                self.emulators[emulator_type] = emulator_uid
                print(f"✅ Driver initialisé pour {emulator_type} avec UID {emulator_uid}")
            else:
                print(f"⚠️ Type d'émulateur inconnu pour {emulator_uid}, ignoré.")

    def initialize_driver_for_type(self, emulator_type):
        if emulator_type in self.drivers:
            print(f"🔁 Driver déjà initialisé pour {emulator_type}, on le réutilise.")
            return

        emulators = self.get_available_emulators()
        for emulator_uid, model in emulators:
            detected_type = self.detect_emulator_type(emulator_uid, model)
            if detected_type == emulator_type:
                self.wait_for_shell_ready(emulator_uid)
                driver = self.setup_driver(emulator_uid, emulator_type)
                self.drivers[emulator_type] = driver
                self.emulators[emulator_type] = emulator_uid
                print(f"✅ Driver initialisé pour {emulator_type} avec UID {emulator_uid}")
                return

        raise RuntimeError(f"❌ Aucun émulateur de type {emulator_type} détecté.")

    def start_new_activity(self, emulator_type, app_package, app_activity):
        driver = self.get_driver(emulator_type)
        if not driver:
            raise RuntimeError(f"Aucun driver trouvé pour le type {emulator_type}")
        try:
            driver.start_activity(app_package, app_activity)
            time.sleep(3)
            print(f"Nouvelle activité lancée : {app_package}/{app_activity}")
        except WebDriverException as e:
            raise RuntimeError(f"Erreur lors du lancement de l'activité {app_package}/{app_activity} : {e}")

    def get_driver(self, emulator_type):
        return self.drivers.get(emulator_type)

    def get_emulator_uid(self, emulator_type):
        return self.emulators.get(emulator_type)

    def quit_drivers(self):
        for driver in self.drivers.values():
            try:
                driver.quit()
            except Exception as e:
                print(f"Erreur lors de la fermeture du driver : {e}")
        self.drivers.clear()
        self.emulators.clear()
        print("🧹 Tous les drivers ont été fermés.")



driver_factory = AppiumDriverFactory()
