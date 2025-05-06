*** Settings ***
Library    ../keywords/Tests_system.py
Library    ../keywords/Test_pairing_bluetooth.py

*** Test Cases ***

Test bluetooth toggle sync
    Run Test bluetooth toggle sync
Test pairing bluetooth
    Run Test pairing bluetooth
Test Hotspot Activation / Désactivation
    Run Test Hotspot Behavior

Test Mobile Network
    Run Test Mobile Network Behavior

Test Wi-Fi connectivity
    Run Test wifi connectivity

Test Wi-Fi disconnectivity
    Run Test wifi disconnectivity

Test forget Network
    Run Test forget network

Test loopback latency
   Run Test loopback latency   

Test wifi latency 
   Run Test wifi latency    

Test mobile network latency
   Run Test mobile network latency

Test brightness slider functionality
   Run Test brightness slider functionality   

Test adaptive brightness functionality
  Run Test adaptive brightness functionality   

Test Date change
  Run Test Date change  

Test Time change
  Run Test Time change  

Test Micro Input 
   Run Test micro Input  

Test Micro Output
   Run Test micro Output

Test Install/Uinstall Apks   
   Run Test install uninstall Apks

Test hvac temperature control 
    Run Test hvac temperature control   

Test hvac climatisation system (AC)
    Run Test hvac climatisation system (AC)
