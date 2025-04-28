import subprocess

def detect_devices():
    """
    Détecte automatiquement quel device est le Phone et quel est l'AAOS Emulator.
    Retourne : (AAOS_UDID, PHONE_UDID)
    """
    try:
        # 🔎 1. Liste tous les devices ADB connectés
        devices_output = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True).stdout
        lines = devices_output.strip().split("\n")[1:]  # On saute la première ligne "List of devices attached"
        device_ids = [line.split("\t")[0] for line in lines if "device" in line]

        AAOS_UDID = None
        PHONE_UDID = None

        print("🔍 Détection des devices en cours...")

        # 🔎 2. Vérifie chaque device
        for udid in device_ids:
            packages = subprocess.run(["adb", "-s", udid, "shell", "pm", "list", "packages"], capture_output=True, text=True).stdout

            if "com.android.car.settings" in packages:
                AAOS_UDID = udid
                print(f"🚗 Détecté comme AAOS Emulator : {udid}")
            elif "com.google.android.apps.maps" in packages or "com.google.android.apps.messaging" in packages:
                PHONE_UDID = udid
                print(f"📱 Détecté comme Phone Emulator : {udid}")
            else:
                print(f"⚠️ Device {udid} non catégorisé.")

        # 🔎 3. Résultat final
        if not AAOS_UDID:
            print("❌ Aucun AAOS Emulator détecté.")
        if not PHONE_UDID:
            print("❌ Aucun Phone Emulator détecté.")

        return AAOS_UDID, PHONE_UDID

    except Exception as e:
        print(f"❌ Erreur lors de la détection : {e}")
        return None, None

# ===========================
# ▶️ Utilisation
# ===========================

if __name__ == "__main__":
    aaos, phone = detect_devices()
    print("\n📋 Résultat Final :")
    print(f"AAOS_UDID  ➔ {aaos}")
    print(f"PHONE_UDID ➔ {phone}")
