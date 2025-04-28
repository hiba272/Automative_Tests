import subprocess


test_files = [
    "tests/functional_hvac.robot",
    "tests/functional_maps.robot",
    "tests/Functional_test_system.robot",
    "tests/Test_apk_install.robot",
    "tests/test_audio.robot",
    "tests/Test_micro_Input.robot",
    "tests/test_simuler_appel.robot",
    "tests/Test_system_notification.robot",
    "tests/Tests_Execitions.robot"
]

for test in test_files:
    print(f"🚀 Exécution de {test}...")
    subprocess.run(["robot", test])
    print(f"✅ Terminé {test}\n")
