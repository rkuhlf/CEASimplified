@REM Using -F makes it a one file application
pyinstaller --icon rocket.ico -F -w main.py

set originalPath=dist


copy rocket.ico %originalPath%\rocket.ico

robocopy FCEA %originalPath%\FCEA /E

robocopy CleanCEAData %originalPath%\CEAData /E

cd %originalPath%

rename main.exe CEASimplified.exe

cd ..

rmdir ..\Builds\CEASimplified /S /Q

move %originalPath% ..\Builds\CEASimplified

@REM Necessary if you are not doing a one file build (I think)
@REM rmdir dist