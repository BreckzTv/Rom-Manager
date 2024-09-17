import webbrowser

banner =R'''
        
██████╗░░█████╗░███╗░░░███╗  ███╗░░░███╗░█████╗░███╗░░██╗░█████╗░░██████╗░███████╗██████╗░
██╔══██╗██╔══██╗████╗░████║  ████╗░████║██╔══██╗████╗░██║██╔══██╗██╔════╝░██╔════╝██╔══██╗
██████╔╝██║░░██║██╔████╔██║  ██╔████╔██║███████║██╔██╗██║███████║██║░░██╗░█████╗░░██████╔╝
██╔══██╗██║░░██║██║╚██╔╝██║  ██║╚██╔╝██║██╔══██║██║╚████║██╔══██║██║░░╚██╗██╔══╝░░██╔══██╗
██║░░██║╚█████╔╝██║░╚═╝░██║  ██║░╚═╝░██║██║░░██║██║░╚███║██║░░██║╚██████╔╝███████╗██║░░██║
╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝  ╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝╚═╝░░╚═╝░╚═════╝░╚══════╝╚═╝░░╚═╝

authour=BreckzTv V=1.1 Github:https://github.com/BreckzTv
'''

print(banner)


def konsolen(PS3, PS4, PS5, NDSI, NSW, WII):
    print(f"Verfügbare Konsolen: {PS3}, {PS4}, {PS5}, {NDSI}, {NSW}, {WII}")

def ps3_options():
    print('Firmware, Games, Roms, PKG, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/Roms/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Version:", "4.80", "4.81", "4.82")
        if input("Geben Sie die OFW Version ein: "):
            print("http://deu01.ps3.update.playstation.net/update/ps3/image/eu/2024_0227_3694eb3fb8d9915c112e6ab41a60c69f/PS3UPDAT.PUP")
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/sony-playstation-3")
        print("Vimmnet\nhttps://vimm.net/vault/PS3")
    elif detail == 'PKG':
        print("Stores, Apps, Media")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def ps4_options():
    print('Firmware, Games, PKG, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 11.0, 11.5)
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/sony-playstation-4")
    elif detail == 'PKG':
        print("Stores, Apps, Media")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def ps5_options():
    print('Firmware, Games, PKG, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 23.0, 23.5)
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/sony-playstation-5")
    elif detail == 'PKG':
        print("Stores, Apps, Media")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def ndsi_options():
    print('Firmware, Games, Roms, Ordner, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/Roms/Ordner/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 11.0, 11.5)
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/nintendo-ds")
        print("Vimmnet\nhttps://vimm.net/vault/DS")
    elif detail == 'Roms':
        print("Hier sind einige Rom-Optionen.")
    elif detail == 'Ordner':
        ordner_option = input("Wählen Sie einen Ordner (Spiele/Daten/Supercard): ").strip()
        if ordner_option == 'Spiele':
            print(r"E:\Geräte\Nintendo\Nintendo Ds\DSTWO-Copy\Gute Games")
        elif ordner_option == 'Daten':
            print(r"E:\Geräte\Nintendo\Nintendo Ds")
        elif ordner_option == 'Supercard':
            print(r"E:\Geräte\Nintendo\Nintendo Ds\DSTWO-Copy")
        else:
            print("Unbekannter Ordner.")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def nsw_options():
    print('Firmware, Games, Roms, PKG, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/Roms/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 16.0, 16.1)
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/nintendo-switch")
    elif detail == 'Roms':
        print("Hier sind einige Rom-Optionen für die Switch.")
    elif detail == 'PKG':
        print("Stores, Apps, Media für Nintendo Switch.")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def wii_options():
    print('Firmware, Games, Roms, PKG, Help')
    detail = input('Geben Sie eine Option ein (Firmware/Games/Roms/PKG/Help): ').strip()

    if detail == 'Firmware':
        print("Firmwares: ", 4.3, 4.4)
    elif detail == 'Games':
        print("Romspure.cc\nhttps://romspure.cc/roms/nintendo-wii")
    elif detail == 'Roms':
        print("Hier sind einige Rom-Optionen für die Nintendo Wii.")
    elif detail == 'PKG':
        print("Stores, Apps, Media für Nintendo Wii.")
    elif detail == 'Help':
        print("Hilfe: Hier sind einige Optionen, die Sie verwenden können.")
    else:
        print("Unbekannte Option.")

def main():
    konsolen('PS3', 'PS4', 'PS5', "NDSI", "NSW", "WII")

    while True:
        konsole = input("Geben Sie eine Konsole ein: ").strip()

        if konsole == 'PS3':
            ps3_options()
        elif konsole == 'PS4':
            ps4_options()
        elif konsole == 'PS5':
            ps5_options()
        elif konsole == 'NDSI':
            ndsi_options()
        elif konsole == 'NSW':
            nsw_options()
        elif konsole == 'WII':
            wii_options()
        else:
            print("Unbekannte Konsole. Versuchen Sie es erneut.")
        
        if input("Möchten Sie eine weitere Konsole eingeben? (ja/nein): ").strip().lower() != 'ja':
            break

if __name__ == "__main__":
    main()
