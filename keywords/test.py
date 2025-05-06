import subprocess
import time

def detect_avd_by_type(target_type):
    result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True)
    avds = result.stdout.strip().splitlines()

    keywords = {
        "phone": ["pixel", "nexus", "phone", "default"],
    }

    for avd in avds:
        name = avd.lower()
        for keyword in keywords[target_type]:
            if keyword in name:
                print(f"[INFO] AVD détecté pour {target_type} : {avd}")
                return avd

    raise ValueError(f"[ERROR] Aucun AVD trouvé pour le type : {target_type}")

def start_avd_by_type(target_type):
    try:
        avd_name = detect_avd_by_type(target_type)
        print(f"[INFO] Lancement de l'AVD '{avd_name}' pour type {target_type}")
        subprocess.Popen(["emulator", "-avd", avd_name])
        time.sleep(15)
    except Exception as e:
        print(f"[ERROR] Échec lancement AVD {target_type} : {e}")

def stop_avd_by_type(target_type):
    try:
        print(f"\n[Fermeture AVD] Type demandé : {target_type.upper()}")
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        for line in lines:
            if "emulator" in line and "device" in line:
                emulator_uid = line.split()[0]
                result = subprocess.run(["adb", "-s", emulator_uid, "emu", "avd", "name"],
                                        capture_output=True, text=True)
                avd_name = result.stdout.strip().lower()
                if target_type in avd_name:
                    print(f"[INFO] AVD détecté : {avd_name} ({emulator_uid}) ➤ arrêt en cours...")
                    subprocess.run(["adb", "-s", emulator_uid, "emu", "kill"])
                    print(f"[OK] Fermeture réussie de {avd_name}")
                    return
        print(f"[WARN] Aucun AVD de type '{target_type}' n’a été trouvé ou est déjà éteint.")

    except Exception as e:
        print(f"[ERROR] Fermeture AVD {target_type.upper()} : {e}")
