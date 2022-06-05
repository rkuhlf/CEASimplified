pyinstaller --onefile -w main.py

copy rocket.ico dist\rocket.ico

robocopy FCEA dist/FCEA /E

robocopy CleanCEAData dist/CEAData /E

cd dist

rename main.exe CEASimplified.exe

cd ..

rmdir ..\Builds\CEASimplified /S /Q

move dist ..\Builds\CEASimplified
