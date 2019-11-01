import os
import time
import random
import string
import subprocess
from Tkinter import Tk, Label, Button, Entry, StringVar


class LauncherGUI:
    def __init__(self, master):
        self.master = master
        master.title("Broadcast Game")
        if os.path.exists('certabo.ico'):
            master.iconbitmap('certabo.ico')

        self.player1_label = Label(master, text="Player 1:")
        self.player1_var = StringVar(value='White')
        self.player1_entry = Entry(master, textvariable=self.player1_var, width=25)
        self.player1_label.grid(row=1, column=1, padx=(30, 0), pady=(20, 5))
        self.player1_entry.grid(row=1, column=2, padx=(5, 30), pady=(20, 5), sticky='w', columnspan=10)

        self.player2_label = Label(master, text="Player 2:")
        self.player2_var = StringVar(value='Black')
        self.player2_entry = Entry(master, textvariable=self.player2_var, width=25)
        self.player2_label.grid(row=2, column=1, padx=(30, 0), pady=(5, 20))
        self.player2_entry.grid(row=2, column=2, padx=(5, 30), pady=(5, 20), sticky='w', columnspan=10)

        self.gameid_label = Label(master, text="Game ID:")
        default_value = ''.join(random.choice(string.digits[1:]) for _ in xrange(3))
        self.gameid_var = StringVar(value=default_value)
        self.gameid_var.trace('w', lambda *args: self.validate_gameid())
        self.gameid_entry = Entry(master, textvariable=self.gameid_var, width=4)
        self.gameid_label.grid(row=3, column=1, padx=(30, 0), pady=(5, 5))
        self.gameid_entry.grid(row=3, column=2, padx=(5, 30), pady=(5, 5), sticky='w')

        self.gamekey_label = Label(master, text="Game Key:")
        self.gamekey_label.grid(row=4, column=1, padx=(30, 0), pady=(5, 20))
        self.gamekey_entries = []
        self.gamekey_vars = []
        for i, width in enumerate((8, 4, 4, 4, 12)):
            default_value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(width))
            self.gamekey_vars.append(StringVar(value=default_value))
            self.gamekey_vars[i].trace('w', lambda nm, idx, mode, _i=i, _width=width: self.validate_gamekey(_i, _width))
            gamekey_entry = Entry(master, textvariable=self.gamekey_vars[i], width=int(width*1.5))
            if i < 4:
                gamekey_entry.grid(row=4, column=i * 2 + 2, padx=(5, 5), pady=(5, 20), sticky='w')
                Label(master, text='-').grid(row=4, column=i * 2 + 3, pady=(5, 20))
            else:
                gamekey_entry.grid(row=4, column=i * 2 + 2, padx=(5, 30), pady=(5, 20), sticky='w')
            self.gamekey_entries.append(gamekey_entry)

        self.launch_button = Button(master, text='Launch', command=self.launch)
        self.launch_button.grid(row=5, column=0, columnspan=11, sticky='we', padx=(200), pady=(0, 20))

    def validate_gameid(self):
        id = self.gameid_var.get()
        id = ''.join(c for c in id if c in string.digits)
        self.gameid_var.set(id[:3])

    def validate_gamekey(self, i, w):
        key = self.gamekey_vars[i].get()
        if len(key) > w:
            self.gamekey_vars[i].set(key[:w])
            if i < 4:
                self.gamekey_entries[i+1].focus()

        elif not len(key) and i > 0:
            self.gamekey_entries[i-1].focus()

    def launch(self):
        game_id = self.gameid_var.get()
        game_key = '-'.join(key.get() for key in self.gamekey_vars)
        print(id, game_key)
        # process = ['python.exe', 'run.py', '--robust', '--publish', 'https://broadcast.certabo.com/',
        #            '--game-id', game_id, '--game-key=' + game_key]
        process = ['run.exe', '--robust', '--publish', 'https://broadcast.certabo.com/',
                   '--game-id', game_id, '--game-key=' + game_key]
        subprocess.Popen(process)
        # time.sleep(3)
        # root.destroy()


root = Tk()
my_gui = LauncherGUI(root)
root.mainloop()
