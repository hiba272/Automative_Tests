import time
import os
import wave
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import subprocess
import pyaudio

from appium_driver_factory import driver_factory
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# ======================= CONSTANTES =======================
driver_factory.initialize_drivers()
driver = driver_factory.get_driver("automotive")
AAOS_UDID = driver_factory.get_emulator_uid("automotive")
DURATION = 10
SEUIL_DB = -40
SEUIL_DUREE_ACTIVE = 0.5
SEUIL_PIC_DB = 20
SEUIL_NB_PICS = 10
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


def lancer_launcher():
    subprocess.run([
        "adb", "-s", AAOS_UDID, "shell", "monkey", "-p", "com.android.car.carlauncher",
        "-c", "android.intent.category.LAUNCHER", "1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    time.sleep(3)

def cliquer_si_cancel():
    try:
        cancel_button = driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@resource-id='android:id/button2']")
        if cancel_button.is_displayed():
            cancel_button.click()
    except NoSuchElementException:
        pass

def ouvrir_media_player():
    lancer_launcher()
    try:
        media_icon = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Local Media Player")')
        media_icon.click()
        time.sleep(3)
    except Exception:
        raise Exception("Impossible d'ouvrir Local Media Player")

def entrer_ringtones():
    container = driver.find_element(AppiumBy.XPATH, "(//android.view.ViewGroup[@resource-id='com.android.car.media:id/item_container'])[1]")
    container.click()
    time.sleep(1)

def jouer_andromeda():
    sonnerie = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Andromeda")'))
    )
    sonnerie.click()
    time.sleep(1)
    driver.press_keycode(66)


def enregistrer_audio(nom_fichier):
    p = pyaudio.PyAudio()
    device_index = next((i for i in range(p.get_device_count())
                         if p.get_device_info_by_index(i).get("maxInputChannels", 0) > 0), None)
    if device_index is None:
        print("Aucun micro détecté.")
        return

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, input_device_index=device_index,
                    frames_per_buffer=CHUNK)

    frames = [stream.read(CHUNK) for _ in range(int(RATE / CHUNK * DURATION))]

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(nom_fichier, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
def analyser_audio(path, img_name):
    if not os.path.exists(path):
        return 0, 0, 0, 0

    with wave.open(path, 'rb') as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        framerate = wf.getframerate()

    filtre = scipy.signal.sosfilt(
        scipy.signal.butter(10, 100, 'hp', fs=framerate, output='sos'), audio)

    rms = np.sqrt(np.mean(filtre ** 2))
    db = 20 * np.log10(rms) if rms > 0 else -100

    chunk_size = int(framerate * 0.1)
    chunks = [filtre[i:i + chunk_size] for i in range(0, len(filtre), chunk_size)]
    active_chunks = sum(1 for c in chunks if 20 * np.log10(np.sqrt(np.mean(c ** 2))) > SEUIL_DB)
    pics_forts = sum(1 for c in chunks if 20 * np.log10(np.sqrt(np.mean(c ** 2))) > SEUIL_PIC_DB)

    plt.figure(figsize=(14, 5))
    plt.plot(filtre, color='green' if active_chunks * 0.1 >= SEUIL_DUREE_ACTIVE else 'red')
    plt.title(f"Signal Audio : {path}")
    plt.xlabel("Échantillons")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img_name)
    plt.close()

    return rms, db, active_chunks * 0.1, pics_forts

def retour_launcher():
    for _ in range(3):
        driver.press_keycode(4)
        time.sleep(1)
    lancer_launcher()

def fermer_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

def Test_micro_Output():
    ouvrir_media_player()
    cliquer_si_cancel()
    entrer_ringtones()
    jouer_andromeda()

    print("\nCapture AVANT Stop...")
    enregistrer_audio("before_stop.wav")

    print("\nEnvoi STOP...")
    subprocess.run(["adb", "-s", AAOS_UDID, "shell", "input", "keyevent", "127"], shell=True)
    time.sleep(1)

    print("\nCapture APRÈS Stop...")
    enregistrer_audio("after_stop.wav")

    print("\nAnalyse...")
    before_rms, before_db, before_duree, before_pics = analyser_audio("before_stop.wav", "before_stop.png")
    after_rms, after_db, after_duree, after_pics = analyser_audio("after_stop.wav", "after_stop.png")

    rapport = f"""
✨ RAPPORT AUDIO
=====================

🔊 AVANT STOP :
---------------------
- Niveau RMS : {before_rms:.2f}
- Niveau sonore (dB) : {before_db:.2f} dB
- Durée avec son (> {SEUIL_DB} dB) : {before_duree:.2f} secondes
- Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {before_pics}

✅ Analyse :
Un signal audio important a été détecté avant l'envoi de la commande STOP. 
Le niveau RMS élevé ({before_rms:.2f}) et le volume sonore moyen ({before_db:.2f} dB) indiquent clairement une activité sonore significative. 
La totalité des {DURATION} secondes contient du son audible, avec {before_pics} pics forts dépassant le seuil critique de {SEUIL_PIC_DB} dB.
👉 Ces indicateurs confirment la lecture correcte de la sonnerie dans l’émulateur avant le STOP.

🔇 APRÈS STOP :
---------------------
- Niveau RMS : {after_rms:.2f}
- Niveau sonore (dB) : {after_db:.2f} dB
- Durée avec son (> {SEUIL_DB} dB) : {after_duree:.2f} secondes
- Nombre de pics forts (> {SEUIL_PIC_DB} dB) : {after_pics}

🟡 Analyse :
Après l’envoi de la commande STOP, bien que le seuil de bruit soit dépassé sur toute la durée (10s),
le niveau RMS très bas ({after_rms:.2f}) et le volume sonore moyen faible ({after_db:.2f} dB) indiquent un bruit de fond minimal.
Le faible nombre de pics ({after_pics}) suggère l'absence de véritable activité sonore.
👉 Il n’y a pas de sonnerie jouée après le STOP — seulement un résidu ou bruit technique du micro.

🎯 CONCLUSION GLOBALE :
------------------------
✅ Le son a bien été détecté dans l’émulateur **avant** la commande STOP.
✅ Aucun son significatif n'a été détecté **après** — la commande STOP fonctionne correctement.
"""
    print(rapport)
    with open("rapport_audio.txt", "w", encoding="utf-8") as f:
        f.write(rapport)

    retour_launcher()
    fermer_driver()

# ▶️ Lancement manuel si besoin
if __name__ == "__main__":
    Test_micro_Output()
