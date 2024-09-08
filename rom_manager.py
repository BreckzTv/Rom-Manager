import webbrowser

banner =R'''
        
██████╗░░█████╗░███╗░░░███╗  ███╗░░░███╗░█████╗░███╗░░██╗░█████╗░░██████╗░███████╗██████╗░
██╔══██╗██╔══██╗████╗░████║  ████╗░████║██╔══██╗████╗░██║██╔══██╗██╔════╝░██╔════╝██╔══██╗
██████╔╝██║░░██║██╔████╔██║  ██╔████╔██║███████║██╔██╗██║███████║██║░░██╗░█████╗░░██████╔╝
██╔══██╗██║░░██║██║╚██╔╝██║  ██║╚██╔╝██║██╔══██║██║╚████║██╔══██║██║░░╚██╗██╔══╝░░██╔══██╗
██║░░██║╚█████╔╝██║░╚═╝░██║  ██║░╚═╝░██║██║░░██║██║░╚███║██║░░██║╚██████╔╝███████╗██║░░██║
╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝  ╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝╚═╝░░╚═╝░╚═════╝░╚══════╝╚═╝░░╚═╝

authour=BreckzTv V=1.0 Github:https://github.com/BreckzTv
'''

print(banner)

def Konsolen(PS3, PS4, PS5):
    print(f"Verfügbare Konsolen: {PS3}, {PS4}, {PS5}")

def PS3():
    print("Firmware", "Games", "help")

Konsolen('PS3', 'PS4', 'PS5')

konsole = input("Geben Sie eine Konsole ein: ").strip()

if konsole == 'PS3':
    print('Firmware, Games, PKG, Help')

    detail = input('Geben Sie eine Option ein (Firmware/Games/PKG/Help): ').strip()
    
    if detail == 'Firmware':
        print("Version:", "4.80", "4.81", "4.82")
        if input("Geben sie OFW Version ein"):
            print("http://deu01.ps3.update.playstation.net/update/ps3/image/eu/2024_0227_3694eb3fb8d9915c112e6ab41a60c69f/PS3UPDAT.PUP")
    elif detail == 'Games':
        #Gaming Urls für PS3
        print("Romspure.cc")
        print ('https://romspure.cc/roms/sony-playstation-3')
        print("Vimmnet")
        print ('https://vimm.net/vault/PS3')
        
    elif detail == 'PKG':
        print("Stores, Apps, Media")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option. Drücken Sie eine Taste zum Beenden.")
else:
    print("Unbekannte Konsole. Drücken Sie eine Taste zum Beenden.")

if konsole == 'PS4':
    print('Firmware, Games, PKG, Help')

    detail = input('Geben Sie eine Option ein (Firmware/Games/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 11.0, 11.5)
    elif detail == 'Games':
        #Gaming Urls für PS3
        print("Romspure.cc")
        print ('https://romspure.cc/roms/sony-playstation-4')
        
    elif detail == 'PKG':
        print("Stores, Apps, Media")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option. Drücken Sie eine Taste zum Beenden.")
else:
    print("Unbekannte Konsole. Drücken Sie eine Taste zum Beenden.")

if konsole =='PS5':
    print("update coming soon!")