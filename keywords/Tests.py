from appium_driver_factory import driver_factory

print("🚀 Initialisation des drivers...")
driver_factory.initialize_drivers()

print("📱 Driver PHONE :", driver_factory.get_driver("phone"))
print("🚗 Driver AUTOMOTIVE :", driver_factory.get_driver("automotive"))

print("📱 UID PHONE :", driver_factory.get_emulator_uid("phone"))
print("🚗 UID AUTOMOTIVE :", driver_factory.get_emulator_uid("automotive"))

print("✅ Test terminé.")
