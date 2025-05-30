from setuptools import setup

APP = ['main.py']
DATA_FILES = ['logo.png']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'cxf2lab.icns',
    'packages': ['tkinterdnd2', 'colormath', 'PIL'],
    'plist': {
        'CFBundleName': 'CXF2Lab',
        'CFBundleDisplayName': 'CXF → Lab Converter',
        'CFBundleIdentifier': 'com.upak.cxf2lab',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
