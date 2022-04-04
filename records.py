import pickle
import os
import random
import tkinter as tk
from tkinter import filedialog

from settings import Settings

class SaveData:
    def __init__(self):
        self.seed = 0
        self.gamemode = 1
        self.changes = {}
        self.dy = 0
        self.flying = False
        self.inventory = [['', 0] for _ in range(70)]
        self.block = 0
        self.max_health = 20
        self.health = 20
        self.sector = None
        self.position = (0, None, 0)
        self.respwan = (0, None, 0)

    def save(self, name):
        with open(f'records/{name}.mtr', mode='wb') as f:
            pickle.dump(self, f)


def ask_open():
    data = {}
    root = tk.Tk()

    root.title('选择存档')
    root.geometry('400x400')
    root.resizable(False, False)

    def do_open():
        filepath = filedialog.askopenfilename(title='导入', filetypes=[('世界存档', '.mtr')])
        with open(filepath, 'rb') as fi, open(f"records/{filepath.split('/')[-1]}", 'wb') as fo:
            fo.write(fi.read())
        update()

    def do_save():
        selected = lb.curselection()
        if len(selected) == 1:
            text = lb.get(selected)
            filepath = filedialog.asksaveasfilename(title='导出', filetypes=[('世界存档', '.mtr')])
            if not filepath.endswith('.mtr'):
                filepath += '.mtr'
            with open(f'records/{text}.mtr', mode='rb') as fi, open(filepath, mode='wb') as fo:
                fo.write(fi.read())

    def do_load():
        selected = lb.curselection()
        if len(selected) == 1:
            text = lb.get(selected)
            with open(f'records/{text}.mtr', mode='rb') as f:
                savedata = pickle.load(f)
                data['name'] = text
                data['savedata'] = savedata
                root.destroy()

    def do_new():
        root.attributes('-disabled', True)
        top = tk.Toplevel(root)

        def exit_window():
            root.attributes('-disabled', False)
            top.destroy()

        def do_random():
            etr2.delete(0, 'end')
            etr2.insert('end', str(random.randint(10, 1000000)))

        def do_complete():
            name = etr1.get()
            if not os.path.exists(f'records/{name}.mtr'):
                savedata = SaveData()
                savedata.seed = int(etr2.get())
                savedata.gamemode = {'生存模式': 1, '创造模式': 2}[om_value.get()]
                savedata.save(name)
                update()
                exit_window()

        top.geometry('300x130')
        top.title('新建存档')
        top.focus_set()
        top.transient(root)
        top.resizable(False, False)
        top.protocol('WM_DELETE_WINDOW', exit_window)

        tk.Label(top, text='世界名称：').place(x=0, y=0)
        etr1 = tk.Entry(top)
        etr1.place(x=80, y=0, width=220)
        tk.Label(top, text='种子：').place(x=0, y=30)
        etr2 = tk.Entry(top)
        etr2.place(x=50, y=30, width=200)
        do_random()
        btn1 = tk.Button(top, text='随机', command=do_random)
        btn1.place(x=250, y=30, width=50, height=21)
        tk.Label(top, text='世界模式：').place(x=0, y=60)
        om_value = tk.StringVar()
        om_value.set('生存模式')
        om = tk.OptionMenu(top, om_value, '生存模式', '创造模式')
        om.place(x=120, y=58, width=140, height=27)
        btn2 = tk.Button(top, text='完成(C)', underline=3, command=do_complete)
        btn2.place(x=100, y=95, width=100, height=30)

        top.mainloop()
    
    def do_delete():
        selected = lb.curselection()
        if len(selected) == 1:
            text = lb.get(selected)
            os.remove(f'records/{text}.mtr')
            update()

    def update():
        lb.delete(0, 'end')
        for file in os.listdir('./records'):
            if file.endswith('.mtr'):
                lb.insert('end', file[:-4])

    menu = tk.Menu(root)
    file_menu = tk.Menu(menu, tearoff=False)
    file_menu.add_command(label='导入(O)', underline=3, command=do_open)
    file_menu.add_command(label='导出(S)', underline=3, command=do_save)
    menu.add_cascade(label='文件(F)', underline=3, menu=file_menu)
    root.config(menu=menu)

    sb = tk.Scrollbar(root)
    sb.place(x=380, y=0, width=20, height=370)
    lb = tk.Listbox(root, yscrollcommand=sb.set)
    lb.place(x=0, y=0, width=380, height=370)
    sb.config(command=lb.yview)

    btn1 = tk.Button(root, text='加载存档(L)', underline=5, command=do_load)
    btn1.place(x=25, y=370, width=100, height=30)
    btn2 = tk.Button(root, text='新建存档(N)', underline=5, command=do_new)
    btn2.place(x=150, y=370, width=100, height=30)
    btn3 = tk.Button(root, text='删除存档(D)', underline=5, command=do_delete)
    btn3.place(x=275, y=370, width=100, height=30)

    update()

    root.mainloop()

    return data

def save_record(name):
    win = Settings.window
    data = SaveData()
    data.seed = win.model.seed
    data.gamemode = Settings.gamemode
    data.changes = win.changes
    data.dy = win.dy
    data.flying = win.flying
    data.inventory = win.inventory
    data.block = win.block
    data.max_health = win.max_health
    data.health = win.health
    data.sector = win.sector
    data.position = win.position
    data.respwan = win.respwan
    data.save(name)


if __name__ == '__main__':
    data = ask_open()
    print(data)
