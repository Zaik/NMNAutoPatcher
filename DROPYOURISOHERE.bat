:: Nordic Melee Netplay Build v1 created by Anutim
:: xdelta program created by Josh Macdonald
:: This script created by DRGN.
:: Script version 2.1

@echo off

set version=01
set betaMD5=e4 62 f7 f3 46 97 8a 9c 4f a6 79 ea 15 ab de 53
set certUtilExists=true
set originalISO=%~1

	:: First, ensure a file was provided to the script.

if NOT "%originalISO%"=="" goto :sourceProvided

echo.
echo  To use this, drag-and-drop your Vanilla PAL ISO or Nordic Melee Netplay Build iso (any version, not Melee Netplay Community Build though)  onto the batch file.
echo.
echo  (That is, the actual file icon in the folder, not this window.)
echo.
goto exit

:sourceProvided
::Confirm existence of the relevant utilities, CertUtil last so we can skip it if desired
where xdelta3-x86_64-3.0.10.exe >nul 2>nul
if not %ERRORLEVEL%==0 goto :missingXDelta

where CertUtil >nul 2>nul
if %ERRORLEVEL%==0 goto :obtainPatches

set certUtilExists=false

echo.
echo  The hash checking utility (CertUtil) was not found installed on your system.
echo  It is highly advised to not execute the auto-patcher without this, as you will have
echo  to provide information on what patched to apply, and the resulting ISOs will not be
echo  verifiable
set /p continue=- Continue anyway? (y/n): 
if %continue%==n goto exit
if %continue%==no goto exit
goto :obtainPatches

:missingXDelta
echo.
echo  You do not have xDelta on your user path, it SHOULD have been bundled with this script
echo  Check that you're executing this script from the correct directory
echo  This utility requires "xdelta3-x86_64-3.0.10.exe" to run
goto exit

:obtainPatches
echo.
echo  Now attempting to obtain the latest patchinfo file from the server
echo  Starting python script...
python35 obtain_patch_info.py || goto :failedObtainPatches
echo  Patches succesfully obtained!
goto :checkPatchExistance

:failedObtainPatches
echo  Failed to obtain the latest patches. If you already have the patchinfo file and
echo  the xdelta files, you can continue patching to the version you already have.
echo  Would you like to continue with already existing patchinfo?
echo  (will fail if you do not have the files)
set /p continue=- (y/n): 
if %continue%==n goto exit
if %continue%==no goto exit

:checkPatchExistance
echo  Now attempting to read and apply patches
python35 read_and_apply_patch_info.py "%originalISO%" "%certUtilExists%" || goto :failedApply
echo  Succesfull! You should now have the latest version of NMNB!
goto exit

:failedApply
echo  Something went wrong while reading or applying patches
echo  This is most likely due to missing patches or incorrect checksums
echo  but check the output from the python script for more details.
goto exit

:exit
echo  Press any key to exit. . . && pause > nul