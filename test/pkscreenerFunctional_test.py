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
# pytest --cov --cov-report=html:coverage_re

import os
import shutil
import sys
import warnings

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import pytest

try:
    shutil.copyfile("pkscreener/.env.dev", ".env.dev")
    sys.path.append(os.path.abspath("pkscreener"))
except Exception:
    print("This test must be run from the root of the project!")
from requests_cache import CachedSession

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.globals as globals
from pkscreener.classes import VERSION, Changelog
from pkscreener.classes.log import default_logger
from pkscreener.classes.MenuOptions import MenuRenderStyle, menus
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.globals import main
from pkscreener.pkscreenercli import argParser, disableSysOut

session = CachedSession("pkscreener_cache", cache_control=True)
last_release = 0
configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
configManager.default_logger = default_logger()
disableSysOut(input=False)


def cleanup():
    # configManager.deleteFileWithPattern(pattern='*.pkl')
    configManager.deleteFileWithPattern(pattern="*.png")
    configManager.deleteFileWithPattern(pattern="*.xlsx")
    configManager.deleteFileWithPattern(pattern="*.html")


def test_if_changelog_version_changed():
    global last_release
    v = Changelog.changelog().split("]")[1].split("[")[-1]
    v = str(v).replace("v", "")
    assert float(v) >= float(last_release)
    assert f"v{str(last_release)}" in Changelog.changelog()
    assert f"v{str(VERSION)}" in Changelog.changelog()


def test_if_release_version_incremented():
    global last_release
    r = fetcher.fetchURL("https://api.github.com/repos/pkjmesra/PKScreener/releases/latest", stream=True)
    try:
        tag = r.json()["tag_name"]
        version_components = tag.split(".")
        major_minor = ".".join([version_components[0], version_components[1]])
        last_release = float(major_minor)
    except Exception:
        if r.json()["message"] == "Not Found":
            last_release = 0
    assert float(VERSION) >= last_release


def test_configManager():
    configManager.getConfig(ConfigManager.parser)
    assert configManager.duration is not None
    assert configManager.period is not None
    assert configManager.consolidationPercentage is not None

def test_option_B_10_0_1(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["B","10","0","1","SBIN,IRFC","Y","\n"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","B:10:0:1:SBIN,IRFC"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    assert (globals.screenResultsCounter.value >= 0)

def test_option_D(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["Y"])
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","X:12:2","-d"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""

def test_option_E(mocker, capsys):
    mocker.patch(
        "builtins.input",
        side_effect=[
            "E",
            str(configManager.period),
            str(configManager.daysToLookback),
            str(configManager.duration),
            str(configManager.minLTP),
            str(configManager.maxLTP),
            str(configManager.volumeRatio),
            str(configManager.consolidationPercentage),
            "y",
            "y",
            "y",
            "n",
            "n",
            str(configManager.generalTimeout),
            str(configManager.longTimeout),
            str(configManager.maxNetworkRetryCount),
            str(configManager.backtestPeriod),
            "\n"
        ],
    )
    args = argParser.parse_known_args(args=["-e","-t", "-p","-a","Y"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == 0 or err == ""

def test_option_Y(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["Y","\n"])
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","Y"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""

def test_option_H(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["H","\n"])
    args = argParser.parse_known_args(args=["-e","-a","N","-t","-p"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_nifty_prediction(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["X", "N"])
    args = argParser.parse_known_args(args=["-e","-a","Y","-t","-p"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_T(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["T","\n"])
    args = argParser.parse_known_args(args=["-e","-a","Y","-t","-p"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    # Revert to the original state
    mocker.patch("builtins.input", side_effect=["-e","T","\n"])
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_U(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["U", "Z", "Y", "\n"])
    args = argParser.parse_known_args(args=["-e","-a","N","-t","-p","-o","U"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_X_0(mocker):
    cleanup()
    mocker.patch(
        "builtins.input", side_effect=["X", "0", "0", globals.TEST_STKCODE, "y"]
    )
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","X:0:0:" + globals.TEST_STKCODE])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) == 1

def test_option_X_0_input(mocker):
    cleanup()
    mocker.patch(
        "builtins.input", side_effect=["X", "0", "0", globals.TEST_STKCODE, "y"]
    )
    args = argParser.parse_known_args(args=["-e","-a","Y"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) == 1

def test_option_X_1_0(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "0", "y"])
    args = argParser.parse_known_args(args=["-e", "-t","-p","-a","Y","-o","X:1:0"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "1", "y"])
    args = argParser.parse_known_args(args=["-e", "-t","-p","-a","Y","-o","X:1:1"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "2", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:2"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "3", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:3"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "4", "5", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:4:5"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "5", "10", "90", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:5:10:90"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "1", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:1"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "2", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:2"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "3", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:3"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "4", "50", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:4:50"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_6_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "5", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:5"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_6_6(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "6", "4", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:6:6:4"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_1_7(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "1", "7", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:7:1:7"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_2_7(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "2", "7", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:7:2:7"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_3_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "3", "1", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:7:3:1"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "4", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:7:4"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "5", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:7:5"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_6(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "6", "y","\n","\n"])
    args = argParser.parse_known_args(args=["-e","-t","-p"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_8(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "8", "-100","150","y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:8:-100:150"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_9_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "9", "3", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:9:3"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_10(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "10", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:10"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_11(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "11", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:11"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_12(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "12", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:12"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_13(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "13", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:13"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_14(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "14", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:1:14"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_8_15(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "8", "15", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:8:15"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0

def test_option_X_8_16(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "8", "16", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:8:16"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0

def test_option_X_8_17(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "8", "17", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:8:17"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0

def test_option_X_8_18(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "8", "18", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:8:18"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0

def test_option_X_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["X", "Z", ""])
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","X:Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_X_12_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "1", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:12:1"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0

def test_option_X_12_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["X", "12", "Z", ""])
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","X:12:Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""

def test_option_X_14_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "14", "1", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:14:1"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_W(mocker):
    cleanup()
    sample = {"Stock Code": ["SBIN", "INFY", "TATAMOTORS", "ITC"]}
    sample_data = pd.DataFrame(sample, columns=["Stock Code"])
    sample_data.to_excel(os.path.join(os.getcwd(),"watchlist.xlsx"), index=False, header=True)
    mocker.patch("builtins.input", side_effect=["X", "W", "y"])
    args = argParser.parse_known_args(args=["-e","-t","-p","-a","Y","-o","X:W:0"])[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["Z", ""])
    args = argParser.parse_known_args(args=["-e","-a","Y","-o","Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_ota_updater():
    OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
    if OTAUpdater.checkForUpdate.url is not None:
        assert (
            "exe" in OTAUpdater.checkForUpdate.url
            or "bin" in OTAUpdater.checkForUpdate.url
            or "run" in OTAUpdater.checkForUpdate.url
        )


def test_release_readme_urls():
    global last_release
    f = open("pkscreener/release.md", "r")
    contents = f.read()
    f.close()
    failUrl = [
        f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli.bin",
        f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli.exe",
    ]
    passUrl = [
        f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli.bin",
        f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli.exe",
    ]
    if float(VERSION) > float(last_release):
        for url in failUrl:
            assert url not in contents
    for url in passUrl:
        assert url in contents

def listedMenusFromRendering(selectedMenu=None, skipList=[]):
    m = menus()
    return m, m.renderForMenu(
            selectedMenu=selectedMenu,
            skip=skipList,
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )

def test_option_X_12_all(mocker, capsys):
    m ,_ = listedMenusFromRendering()
    x = m.find("X")
    m ,_ = listedMenusFromRendering(x)
    x = m.find("12")
    skipList =["0","Z","M"]
    NA_Counter = 19
    Last_Counter = 42
    menuCounter = NA_Counter
    while menuCounter <= Last_Counter:
        skipList.extend([str(menuCounter)])
        menuCounter += 1
    m, cmds = listedMenusFromRendering(x, skipList=skipList)
    argsList =[]
    for cmd in cmds:
        startupOption = "X:12"
        key = cmd.menuKey.upper()
        startupOption = f"{startupOption}:{key}"
        if str(key) in ["6","7"]:
            x = m.find(key)
            _, cmds1 = listedMenusFromRendering(x,skipList=skipList)
            for cmd1 in cmds1:
                key1 = cmd1.menuKey.upper()
                startupOption = f"{startupOption}:{key1}:D:D"
                args = argParser.parse_known_args(args=["-e","-p","-t","-a","Y","-o",startupOption])[0]
                argsList.extend([args])
        else:
            startupOption = f"{startupOption}:D:D"
            args = argParser.parse_known_args(args=["-e","-p","-t","-a","Y","-o",startupOption])[0]
            argsList.extend([args])
    for arg in argsList:
        main(userArgs=arg)
        out, err = capsys.readouterr()
        assert err == ""