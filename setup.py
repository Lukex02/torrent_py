from cx_Freeze import setup, Executable

application_exe = Executable(
    script="main.py",
    target_name="MMT_Torrent_Py.exe"
)

tracker_exe = Executable(
    script="tracker.py",
    target_name="MMT_Tracker.exe"
)


setup (
    name="Torrent Python",
    version="5.0",
    description="Torrent application using python with private tracker",
    executables=[application_exe, tracker_exe],
)