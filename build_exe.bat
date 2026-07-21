@echo off
setlocal EnableDelayedExpansion

echo Checking for virtual environment...

if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment: .venv
    call ".venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment: venv
    call "venv\Scripts\activate.bat"
) else (
    echo ⚠️ No virtual environment found. Using system Python.
)

echo Cleaning old build files...
powershell -Command "Remove-Item -Recurse -Force build, dist, QApplication.spec -ErrorAction SilentlyContinue"

echo Checking for PyInstaller...
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo Building ValScanner executable...
pyinstaller --onefile --windowed ^
    --name ValScanner ^
    --icon=assets/logoone.ico ^
    --add-data "core;core" ^
    --hidden-import=aiohappyeyeballs ^
    --hidden-import=aiohttp ^
    --hidden-import=aiosignal ^
    --hidden-import=asyncio ^
    --hidden-import=attrs ^
    --hidden-import=certifi ^
    --hidden-import=charset_normalizer ^
    --hidden-import=cryptography ^
    --hidden-import=cryptography.hazmat.primitives.serialization.pkcs12 ^
    --hidden-import=frozenlist ^
    --hidden-import=idna ^
    --hidden-import=msgspec ^
    --hidden-import=multidict ^
    --hidden-import=PIL ^
    --hidden-import=propcache ^
    --hidden-import=PySide6 ^
    --hidden-import=PySide6_Addons ^
    --hidden-import=PySide6_Essentials ^
    --hidden-import=qasync ^
    --hidden-import=qtawesome ^
    --hidden-import=requests ^
    --hidden-import=shiboken6 ^
    --hidden-import=superqt ^
    --hidden-import=urllib3 ^
    --hidden-import=yarl ^
    --hidden-import=websockets ^
	--hidden-import=xml.etree.ElementTree ^
	--hidden-import=aiofiles ^
    --collect-data=qtawesome ^
    frontend/QApplication.py

echo.
echo ✅ Build complete!
pause
