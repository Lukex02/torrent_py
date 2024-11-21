from cx_Freeze import setup, Executable

setup (
    name="Torrent Python",
    version="4.2",
    description="",
    executables=[Executable("main.py",
                 target_name="MMT_Torrent_Py")
                 ],
)