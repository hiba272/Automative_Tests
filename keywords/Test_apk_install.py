import subprocess
import time
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APK_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "apks", "simple_file_manager.apk"))
AAOS_UDID = "emulator-5554"
PACKAGE_NAME = "com.simplemobiletools.filemanager"
MAIN_ACTIVITY = "com.simplemobiletools.filemanager.activities.MainActivity"
def installer_application(apk_path):
    print(f"\n📦 Installation de l'application : {apk_path}")
    try:
        subprocess.run([
            "adb", "-s", AAOS_UDID, "install", "-r", apk_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("✅ Application installée avec succès.")
        print("⏳ Attente de 5 secondes avant Power Off...")
        time.sleep(5)

        print("📴 Power OFF (éteindre l'écran)...")
        subprocess.run([
            "adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "26"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        print("📳 Power ON (rallumer l'écran)...")
        subprocess.run([
            "adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "26"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("✅ Écran rallumé.")
        print("⏳ Attente de 5 secondes pour affichage des apps...")
        time.sleep(5)

    except subprocess.CalledProcessError as e:
        print(f"❌ Échec de l'installation ou de l'activation écran : {e}")

# 🔎 Vérification via 'pm list packages'
def verifier_installation_pm(package_name):
    print(f"\n🔎 Vérification via 'pm list packages' pour {package_name}...")
    time.sleep(2)
    result = subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "pm", "list", "packages"
    ], capture_output=True, text=True)

    if package_name in result.stdout:
        print("✅ Package trouvé via 'pm list packages'.")
    else:
        print("❌ Package NON trouvé via 'pm list packages'.")

# 🔎 Vérification via 'dumpsys package'
def verifier_installation_dumpsys(package_name):
    print(f"\n🔎 Vérification via 'dumpsys package' pour {package_name}...")
    time.sleep(2)
    result = subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "dumpsys", "package", package_name
    ], capture_output=True, text=True)

    if f"Package [{package_name}]" in result.stdout:
        print("✅ Package trouvé via 'dumpsys package'.")
    else:
        print("❌ Package NON trouvé via 'dumpsys package'.")

# 🔎 Vérification de l'Activity principale
def verifier_activity(package_name, activity_name):
    print(f"\n🔎 Vérification de l'Activity principale {package_name}/{activity_name}...")
    time.sleep(2)
    result = subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "am", "start", "-n", f"{package_name}/{activity_name}"
    ], capture_output=True, text=True)

    if "Error type 3" in result.stdout or "does not exist" in result.stdout:
        print("❌ L'Activity principale est introuvable.")
    else:
        print("✅ L'Activity principale existe et est accessible.")

# 🚀 Lancer l'application
def lancer_application(package_name, activity_name):
    print(f"\n🚀 Lancement de l'application {package_name}/{activity_name}...")
    time.sleep(2)
    try:
        subprocess.run([
            "adb", "-s", AAOS_UDID, "shell", "am", "start", "-n", f"{package_name}/{activity_name}"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Application lancée avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec du lancement de l'application : {e}")

# 🐃 Désinstaller l'application
def desinstaller_application(package_name):
    print(f"\n🐃 Désinstallation de {package_name}...")
    time.sleep(2)
    try:
        subprocess.run([
            "adb", "-s", AAOS_UDID, "uninstall", package_name
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ {package_name} désinstallé avec succès.")
        verifier_desinstallation(package_name)
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec de la désinstallation : {e}")

# 🔎 Vérifier suppression
def verifier_desinstallation(package_name):
    print(f"\n🔎 Vérification suppression de {package_name}...")
    time.sleep(2)
    result = subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "pm", "list", "packages"
    ], capture_output=True, text=True)

    if package_name not in result.stdout:
        print("✅ Application supprimée de l'émulateur.")
    else:
        print("❌ Application encore présente.")

# 🏁 Main
if __name__ == "__main__":
    print("===== 🔄 DÉBUT DU TEST INSTALLATION APK =====\n")

    installer_application(APK_PATH)
    verifier_installation_pm(PACKAGE_NAME)
    verifier_installation_dumpsys(PACKAGE_NAME)
    verifier_activity(PACKAGE_NAME, MAIN_ACTIVITY)

    print("\n===== 🚀 LANCEMENT DE L'APPLICATION =====\n")
    lancer_application(PACKAGE_NAME, MAIN_ACTIVITY)

    print("\n===== 🐃 DÉSINSTALLATION DE L'APPLICATION =====\n")
    desinstaller_application(PACKAGE_NAME)

    print("\n===== 🏁 TEST TERMINÉ =====")