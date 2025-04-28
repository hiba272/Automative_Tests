import time
import os
import pyaudio
import wave
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import subprocess

# 📱 Paramètres généraux
AAOS_UDID = "emulator-5554"
APPIUM_SERVER_URL = "http://127.0.0.1:4723"
DURATION = 10
SEUIL_DB = -40
SEUIL_DUREE_ACTIVE = 0.5
SEUIL_PIC_DB = 20
SEUIL_NB_PICS = 10
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

driver = None

# ======================= SESSION SETUP =======================
def setup_driver():
    global driver
    if driver is None:
        options = AppiumOptions()
        options.set_capability("platformName", "Android")
        options.set_capability("deviceName", "Android Emulator")
        options.set_capability("udid", AAOS_UDID)
        options.set_capability("automationName", "UiAutomator2")
        options.set_capability("noReset", True)
        driver = webdriver.Remote(command_executor=APPIUM_SERVER_URL, options=options)
        time.sleep(5)

# ======================= MEDIA PLAYER CONTROL =======================
def ouvrir_media_player():
    global driver
    print("🚀 Ouverture du launcher AAOS...")
   
    subprocess.run(
    ["adb", "-s", AAOS_UDID, "shell", "monkey", "-p", "com.android.car.carlauncher", "-c", "android.intent.category.LAUNCHER", "1"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    shell=True
    )

    time.sleep(3)

    try:
        print("🎵 Clic sur l'icône Local Media Player...")
        media_player_icon = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Local Media Player")')
        media_player_icon.click()
        print("✅ Local Media Player ouvert.")
    except Exception:
        print("❌ Erreur : Impossible de trouver l'icône Local Media Player.")
        raise

    time.sleep(3)

def cliquer_si_cancel():
    global driver
    print("🔚 Vérification présence du bouton 'Cancel'...")
    try:
        cancel_button = driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@resource-id='android:id/button2']")
        if cancel_button.is_displayed():
            cancel_button.click()
            print("✅ 'Cancel' cliqué.")
        else:
            print("⚠️ Le bouton 'Cancel' n'est pas affiché.")
    except NoSuchElementException:
        print("⚠️ Aucun bouton 'Cancel' trouvé.")

def entrer_dans_ringtones():
    global driver
    try:
        print("🎵 Sélection de la catégorie Ringtones...")
        item_ringtone = driver.find_element(AppiumBy.XPATH, "(//android.view.ViewGroup[@resource-id='com.android.car.media:id/item_container'])[1]")
        item_ringtone.click()
        print("✅ Première catégorie ouverte (Ringtones).")
    except Exception as e:
        print(f"❌ Erreur lors de la sélection du container : {e}")
        raise

def selectionner_et_lancer_andromeda():
    global driver
    try:
        print("🎵 Attente de l'élément 'Andromeda'...")
        sonnerie = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Andromeda")'))
        )
        sonnerie.click()
        print("✅ 'Andromeda' sélectionnée.")
        time.sleep(1)
        driver.press_keycode(66)  # KEYCODE_ENTER pour lire
        print("🎶 Lecture de la sonnerie lancée.")
    except Exception as e:
        print(f"❌ Erreur lors de la sélection/lancement de la sonnerie : {e}")
        raise

# ======================= AUDIO CAPTURE =======================
def enregistrer_audio(filename):
    print(f"🎧 Enregistrement audio dans {filename} ...")
    p = pyaudio.PyAudio()
    device_index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            name = info["name"].lower()
            if "microphone" in name or "input" in name or "default" in name:
                device_index = i
                print(f"🌟 Micro sélectionné : [{i}] {info['name']}")
                break
    if device_index is None:
        print("❌ Aucun micro détecté.")
        p.terminate()
        return

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * DURATION)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"✅ Fichier audio sauvegardé : {filename}")

# ======================= AUDIO ANALYSIS =======================
def analyser_audio_precis(file_path, image_name):
    if not os.path.exists(file_path):
        print("❌ Fichier audio introuvable.")
        return 0, 0, 0, 0

    with wave.open(file_path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
        framerate = wf.getframerate()

    audio_filtre = scipy.signal.sosfilt(scipy.signal.butter(10, 100, 'hp', fs=framerate, output='sos'), audio)

    rms_global = np.sqrt(np.mean(audio_filtre**2))
    db_global = 20 * np.log10(rms_global) if rms_global > 0 else -100

    chunk_size = int(framerate * 0.1)
    active_chunks = 0
    total_chunks = len(audio_filtre) // chunk_size
    nb_pics_forts = 0

    for i in range(total_chunks):
        chunk = audio_filtre[i*chunk_size:(i+1)*chunk_size]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms) if rms > 0 else -100
        if db > SEUIL_DB:
            active_chunks += 1
        if db > SEUIL_PIC_DB:
            nb_pics_forts += 1

    duree_active = active_chunks * 0.1

    plt.figure(figsize=(14, 5))
    plt.plot(audio_filtre, color='green' if duree_active >= SEUIL_DUREE_ACTIVE else 'red')
    plt.title(f"Signal Audio : {file_path}")
    plt.xlabel("Échantillons")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(image_name)
    plt.close()

    return rms_global, db_global, duree_active, nb_pics_forts

def revenir_launcher():
    global driver
    print("🚀 Retour à l'interface des applications (Car Launcher)...")
    try:
        driver.press_keycode(4)
        time.sleep(1)
        driver.press_keycode(4)
        time.sleep(2)
        driver.press_keycode(4)
        subprocess.run(
        ["adb", "-s", AAOS_UDID, "shell", "monkey", "-p", "com.android.car.carlauncher", "-c", "android.intent.category.LAUNCHER", "1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True
        )

        time.sleep(2)
        print("✅ Interface des apps affichée.")
    except Exception as e:
        print(f"❌ Erreur lors du retour à l'interface des apps : {e}")

def fermer_driver():
    global driver
    if driver:
        driver.quit()
        driver = None
        print("🚪 Appium fermé proprement.")


# ======================= MAIN =======================
def main():
    driver = setup_driver()
    ouvrir_media_player(driver)
    cliquer_si_cancel(driver)
    entrer_dans_ringtones(driver)
    selectionner_et_lancer_andromeda(driver)

    print("\n🎧 Capture AVANT Stop...")
    enregistrer_audio("before_stop.wav")

    print("\n🚨 Envoi commande STOP...")
   
    subprocess.run(
    ["adb", "-s", "emulator-5554", "shell", "input", "keyevent", "127"],
    shell=True
     )

    time.sleep(1)

    print("\n🎧 Capture APRÈS Stop...")
    enregistrer_audio("after_stop.wav")

    print("\n📊 Analyse des audios...")
    before_rms, before_db, before_duree, before_pics = analyser_audio_precis("before_stop.wav", "before_stop.png")
    after_rms, after_db, after_duree, after_pics = analyser_audio_precis("after_stop.wav", "after_stop.png")

    # 🎯 Nouvelle logique de conclusion 
    if before_pics >= SEUIL_NB_PICS:
        conclusion = "✅ Son détecté dans l'émulateur."
    else:
        conclusion = "✅ Son non détecté dans l'émulateur."

    rapport = f"""
✨ RAPPORT AUDIO
=====================

Avant Stop :
------------
Niveau RMS : {before_rms:.2f}
Niveau sonore (dB) : {before_db:.2f}
Durée avec son (> {SEUIL_DB} dB) : {before_duree:.2f} sec
Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {before_pics}

Après Stop :
------------
Niveau RMS : {after_rms:.2f}
Niveau sonore (dB) : {after_db:.2f}
Durée avec son (> {SEUIL_DB} dB) : {after_duree:.2f} sec
Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {after_pics}

Conclusion :
------------
{conclusion}
"""
    print(rapport)

    with open("rapport_audio.txt", "w", encoding="utf-8") as f:
        f.write(rapport)

    # 🛠 Ici on revient proprement à l'interface des apps
    revenir_launcher(driver)

    # 🛠 Puis on ferme la session Appium
    driver.quit()

# ▶️ Lancement
if __name__ == "__main__":
    main()
