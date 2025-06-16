# gui.py
import PySimpleGUI as sg, time
from backend import TrackerDB

def format_ts(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def main():
    db = TrackerDB()
    current = None
    start_time = 0
    last_backup = time.time()
    BACKUP_INTERVAL = 600  # cada 10 minutos

    sg.theme("LightBlue2")

    layout = [
        [sg.Input(key="-DESC-", expand_x=True),
         sg.Button("Iniciar", key="-TOGGLE-"),
         sg.Button("Eliminar", key="-DEL-"),
         sg.Button("Exportar CSV", key="-EXP-")],
        [sg.Table(key="-TABLE-", values=[], headings=["ID","Desc","Inicio","Fin","Dur(s)"],
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                  expand_x=True, expand_y=True)],
        [sg.Text("Cronómetro:"), sg.Text("00:00:00", key="-TIMER-")]
    ]

    window = sg.Window("Time Tracker", layout, resizable=True, finalize=True)
    window.timer_start(1000, key="-TICK-")

    update_table(window, db)

    while True:
        event, vals = window.read()
        if event == sg.WIN_CLOSED:
            break

        now = time.time()
        if now - last_backup >= BACKUP_INTERVAL:
            db.auto_backup()
            last_backup = now

        if event == "-TICK-" and current:
            elapsed = int(time.time() - start_time)
            window["-TIMER-"].update(time.strftime("%H:%M:%S", time.gmtime(elapsed)))

        if event == "-TOGGLE-":
            if not current:
                desc = vals["-DESC-"] or "Sin descripción"
                current = db.start_entry(desc)
                start_time = time.time()
                window["-TOGGLE-"].update("Detener")
            else:
                db.stop_entry(current)
                current = None
                window["-TOGGLE-"].update("Iniciar")
                window["-TIMER-"].update("00:00:00")
                update_table(window, db)

        elif event == "-TABLE-":
            sel = vals["-TABLE-"]
            if sel:
                row = window["-TABLE-"].get()[sel[0]]
                window["-DESC-"].update(row[1])

        elif event == "-DEL-":
            sel = vals["-TABLE-"]
            if sel:
                db.delete_entry(window["-TABLE-"].get()[sel[0]][0])
                update_table(window, db)

        elif event == "-EXP-":
            path = sg.popup_get_file("Guardar CSV", save_as=True,
                                     file_types=(("CSV","*.csv"),),
                                     defaultextension=".csv")
            if path:
                db.export_csv(path)
                sg.popup("Exportado a", path)

    window.close()

def update_table(win, db):
    data = []
    for id_, d, s, e in db.get_entries():
        dur = int(((e or time.time()) - s))
        data.append([id_, d, format_ts(s), format_ts(e) if e else "-", dur])
    win["-TABLE-"].update(values=data)
