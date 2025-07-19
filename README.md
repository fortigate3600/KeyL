# KeyL

This program records keystrokes on Linux machine and sends them to a telegram bot, until the attacker send the `/kill` command so the program delete itself from the target's machine.

It require root access to the target.

## Disclaimer:
This project of a Key Logger is for **educational purposes**, it has been created only with my mere knowledge. Do **not** deploy or use this code on any system without explicit permission from the owner. Misuse of this software may violate laws and going to jail for stupid reasons it's dumb.

## How2UseIt
Before starting you need to configure some stuff. Here's how:

### Go on your0 Linux machine:
1. ```git clone https://github.com/fortigate3600/KeyL.git```

   `cd KeyL`

2. **Set Your Telegram Token**  
   Go on telegram, get a bot and put its token in `config.py` \
   Then create a channel called "@channelName" and put it `config.py` as well \
   after that add your mod to the channel as an admin
   > If you’re unsure how to do it, it's trivial stuff just ask ChatGPT.

3. **Customize Logger Behavior (Optional)**  
   If you're geek enough you can configure the logger by modifying flags inside `KeyL.py`. \
   Be aware that I configure the software with an italian layout \
   Other than that, every keyboard is slightly different (even with the same layout), so there might be some typos.

4. execute `ifconfig` to get yout ip, it is gonna be usefull later

5. `pyinstaller --onefile --name mykeyl KeyL.py`
   > if you don't have it `pip3 install pyinstaller` \
    try again `pyinstaller --onefile --name mykeyl KeyL.py`

   > if you get something like "this environment is externally managed" do this: \
    `sudo apt install python3.13-venv` \
    `python3 -m venv /tmp/venv` \
    `/tmp/venv/bin/pip3 install pyinstaller` \
    `/tmp/venv/bin/pyinstaller --onefile --name mykeyl KeyL.py`
   
   > eventually if request is problematic: \
    `/tmp/venv/bin/pyinstaller --onefile --hidden-import=requests --name mykeyl KeyL.py`

6. `python3 -m http.server 9001`

### Now on the target machine:

Now you have two options:
1. Inject and execute (with root priviledges) the `make.sh` file.

2. Create a root shell with `sudo su` paste and execute the content of `toBePasted.txt` (easier).

In both cases you have to modify the <IP> near the end with your IP, taken before with `ifconfig`

### Important:

To stop the keylogger on a specific machine remotely,
send the command `/kill <machine_id>` to the Telegram bot.

## How it works
<img width="800" height="400" alt="465618311-aac92346-7d68-4f4b-8460-fb7a1a382a45" src="https://github.com/user-attachments/assets/05f44a28-d6b6-466f-bd12-dc148bd0bd8c" />

The persistence mechanism is simple (and quite weak): when the machine is boot a serice launch it.
I have hidden the files in the /root/ directory. I could have made it stealthier, but this project is just for academic purposes.

Once the main program calls KillSwitch.sh, the latter delete every file concerning us and the service.

Now, let’s dive into what the code does.

## Code

It monitors every keypress and stores each key in a buffer. Once the buffer reaches a certain threshold, it sends the content to a chat using Telegram bot.

Specifically, the monitorShift() function checks whether the Shift key is being held down and communicates this through a global flag to monitorKeys(), which logs the pressed keys. If necessary, the keys are passed through a dictionary to convert them to their uppercase equivalents.




