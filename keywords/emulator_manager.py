import subprocess
import time
def detect_avd_by_type(target_type):
    result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True)
    avds = result.stdout.strip().splitlines()

    keywords = {
        "phone": ["pixel", "nexus", "phone", "default"],
        "automotive": ["auto", "car", "automotive"]
    }

    for avd in avds:
        name = avd.lower()
        for keyword in keywords[target_type]:
            if keyword in name:
                print(f"🔍 AVD détecté pour {target_type} : {avd}")
                return avd

    raise ValueError(f"Aucun AVD trouvé pour le type : {target_type}")

def start_avd_by_type(target_type):

    try:
        avd_name = detect_avd_by_type(target_type)
        print(f"Démarrage de l'AVD '{avd_name}' pour type {target_type}")
        subprocess.Popen(["emulator", "-avd", avd_name])
        time.sleep(5)
    except Exception as e:
        print(f"Erreur lors du démarrage AVD ({target_type}) : {e}")

def stop_avd_by_type(target_type):

    try:
        print(f"\n[Fermeture AVD] Type demandé : {target_type.upper()}")

        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        keywords = {
            "phone": ["pixel", "nexus", "phone", "default"],
            "automotive": ["auto", "car", "automotive"]
        }


        for line in lines:
            if "emulator" in line and "device" in line:
                emulator_uid = line.split()[0]
                result = subprocess.run(["adb", "-s", emulator_uid, "emu", "avd", "name"],
                                        capture_output=True, text=True)
                avd_name = result.stdout.strip().splitlines()[0].lower()

                for keyword in keywords[target_type]:
                    if keyword in avd_name:
                        print(f"AVD détecté : {avd_name} ({emulator_uid}) ➤ correspond à '{target_type}'")
                        subprocess.run(["adb", "-s", emulator_uid, "emu", "kill"])
                        print(f"Fermeture réussie ➤ {avd_name} ({emulator_uid}) éteint proprement.")
                        return

        print(f"Aucun AVD de type '{target_type}' n’a été trouvé ou déjà fermé.")

    except Exception as e:
        print(f"Erreur lors de la fermeture de l’AVD {target_type.upper()} : {e}")
