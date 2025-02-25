"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
"""
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   21/04/2021
 *  Description         :   Class for handling OTA updates
"""

import platform
import subprocess
import sys
from datetime import timedelta

from requests_cache import CachedSession

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes import VERSION
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger

session = CachedSession(
    "pkscreener_cache",
    expire_after=timedelta(days=1),
    stale_if_error=True,
)


class OTAUpdater:
    developmentVersion = "d"
    _configManager = ConfigManager.tools()
    _tools = Fetcher.tools(_configManager)
    configManager = _configManager 
    fetcher = _tools
    # Download and replace exe through other process for Windows
    def updateForWindows(url):
        batFile = (
            """@echo off
color a
echo [+] pkscreener Software Updater!
echo [+] Downloading Software Update...
echo [+] This may take some time as per your Internet Speed, Please Wait...
curl -o pkscreenercli.exe -L """
            + url
            + """
echo [+] Newly downloaded file saved in %cd%
echo [+] Software Update Completed! Run'pkscreenercli.exe' again as usual to continue..
pause
del updater.bat & exit
        """
        )
        f = open("updater.bat", "w")
        f.write(batFile)
        f.close()
        subprocess.Popen("start updater.bat", shell=True)
        sys.exit(0)

    # Download and replace bin through other process for Linux
    def updateForLinux(url):
        bashFile = (
            """#!/bin/bash
echo ""
echo "[+] Starting PKScreener updater, Please Wait..."
sleep 3
echo "[+] pkscreener Software Updater!"
echo "[+] Downloading Software Update..."
echo "[+] This may take some time as per your Internet Speed, Please Wait..."
wget -q """
            + url
            + """ -O pkscreenercli.bin
echo "[+] Newly downloaded file saved in $(pwd)"
chmod +x pkscreenercli.bin
echo "[+] Update Completed! Run 'pkscreenercli.bin' again as usual to continue.."
rm updater.sh
        """
        )
        f = open("updater.sh", "w")
        f.write(bashFile)
        f.close()
        subprocess.Popen("bash updater.sh", shell=True)
        sys.exit(0)

        # Download and replace run through other process for Mac

    def updateForMac(url):
        bashFile = (
            """#!/bin/bash
echo ""
echo "[+] Starting PKScreener updater, Please Wait..."
sleep 3
echo "[+] pkscreener Software Updater!"
echo "[+] Downloading Software Update..."
echo "[+] This may take some time as per your Internet Speed, Please Wait..."
curl -o pkscreenercli.run -L """
            + url
            + """
echo "[+] Newly downloaded file saved in $(pwd)"
chmod +x pkscreenercli.run
echo "[+] Update Completed! Run 'pkscreenercli.run' again as usual to continue.."
rm updater.sh
        """
        )
        f = open("updater.sh", "w")
        f.write(bashFile)
        f.close()
        subprocess.Popen("bash updater.sh", shell=True)
        sys.exit(0)

    # Parse changelog from release.md
    def showWhatsNew():
        url = "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/release.md"
        md = OTAUpdater.fetcher.fetchURL(url)
        txt = md.text
        txt = txt.split("New?")[1]
        txt = txt.split("## Older Releases")[0]
        txt = txt.replace("* ", "- ").replace("`", "").strip()
        return txt + "\n"
    
    def get_latest_release_info():
        resp = OTAUpdater.fetcher.fetchURL("https://api.github.com/repos/pkjmesra/PKScreener/releases/latest")
        if "Windows" in platform.system():
            OTAUpdater.checkForUpdate.url = resp.json()["assets"][1][
                    "browser_download_url"
                ]
            size = int(resp.json()["assets"][1]["size"] / (1024 * 1024))
        elif "Darwin" in platform.system():
            OTAUpdater.checkForUpdate.url = resp.json()["assets"][2][
                    "browser_download_url"
                ]
            size = int(resp.json()["assets"][2]["size"] / (1024 * 1024))
        else:
            OTAUpdater.checkForUpdate.url = resp.json()["assets"][0][
                    "browser_download_url"
                ]
            size = int(resp.json()["assets"][0]["size"] / (1024 * 1024))
        return resp,size

    # Check for update and download if available
    def checkForUpdate(VERSION=VERSION, skipDownload=False):
        OTAUpdater.checkForUpdate.url = None
        resp = None
        try:
            now_components = str(VERSION).split(".")
            now_major_minor = ".".join([now_components[0], now_components[1]])
            now = float(now_major_minor)
            resp, size = OTAUpdater.get_latest_release_info()
            tag = resp.json()["tag_name"]
            version_components = tag.split(".")
            major_minor = ".".join([version_components[0], version_components[1]])
            last_release = float(major_minor)
            prod_update = False
            if last_release > now:
                prod_update = True
            elif last_release == now and (
                len(now_components) < len(version_components)
            ):
                # Must be the weekly update over the last major.minor update
                prod_update = True
            elif last_release == now and (
                len(now_components) == len(version_components)
            ):
                if float(now_components[2]) < float(version_components[2]):
                    prod_update = True
                elif float(now_components[2]) == float(version_components[2]):
                    if float(now_components[3]) < float(version_components[3]):
                        prod_update = True
            if prod_update:
                print(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] What's New in this Update?\n"
                    + OTAUpdater.showWhatsNew()
                    + colorText.END
                )
                if skipDownload:
                    return
                action = str(
                    input(
                        colorText.BOLD
                        + colorText.GREEN
                        + (
                            "\n[+] New Software update (v%s) available. Download Now (Size: %dMB)? [Y/N]: "
                            % (str(resp.json()["tag_name"]), size)
                        )
                    )
                ).lower()
                if action == "y":
                    try:
                        if "Windows" in platform.system():
                            OTAUpdater.updateForWindows(OTAUpdater.checkForUpdate.url)
                        elif "Darwin" in platform.system():
                            OTAUpdater.updateForMac(OTAUpdater.checkForUpdate.url)
                        else:
                            OTAUpdater.updateForLinux(OTAUpdater.checkForUpdate.url)
                    except Exception as e:
                        default_logger().debug(e, exc_info=True)
                        print(
                            colorText.BOLD
                            + colorText.WARN
                            + "[+] Error occured while updating!"
                            + colorText.END
                        )
                        raise (e)
            elif not prod_update:
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + (
                        "[+] This version (v%s) is in Development mode and unreleased!"
                        % VERSION
                    )
                    + colorText.END
                )
                return OTAUpdater.developmentVersion
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            if OTAUpdater.checkForUpdate.url is not None:
                print(
                    colorText.BOLD
                    + colorText.BLUE
                    + (
                        "[+] Download update manually from %s\n"
                        % OTAUpdater.checkForUpdate.url
                    )
                    + colorText.END
                )
            else:
                OTAUpdater.checkForUpdate.url = "[+] No exe/bin/run file as an update available!"
            if resp is not None and resp.json()["message"] == "Not Found":
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + OTAUpdater.checkForUpdate.url
                    + colorText.END
                )
            print(e)
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Failure while checking update!"
                + colorText.END
            )
        return
