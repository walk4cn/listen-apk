# -*- coding: utf-8 -*-
r"""
一键重建「英语课文点读台」APK
链条：重新生成页面 -> 同步进 assets -> gradle 构建签名 APK -> 拷出成品

用法（在 Git Bash / PowerShell 均可）：
    python rebuild_apk.py
成品落在：C:\Users\Lenovo\Documents\Default Project\listen\英语课文点读台.apk
"""
import os
import sys
import glob
import shutil
import subprocess

# ---------- 路径（含中文，Python 原生支持）----------
DESKTOP_AUDIO = r"C:\Users\Lenovo\Desktop\课文音频"                       # 51 个 mp3 源目录
WORKSPACE     = r"C:\Users\Lenovo\Documents\Default Project\listen"       # build.py 与成品 APK 所在
PROJECT       = r"C:\Users\Lenovo\.workbuddy\projects\listen-apk"        # 安卓工程（无空格路径）
TOOLCHAIN     = r"C:\Users\Lenovo\.workbuddy\binaries\android"
JAVA_HOME     = os.path.join(TOOLCHAIN, "jdk-17")
ANDROID_HOME  = os.path.join(TOOLCHAIN, "sdk")
GRADLE_BAT    = os.path.join(TOOLCHAIN, "gradle-8.7", "bin", "gradle.bat")

BUILD_PY  = os.path.join(WORKSPACE, "build.py")
ASSETS    = os.path.join(PROJECT, "app", "src", "main", "assets")
APK_OUT   = os.path.join(PROJECT, "app", "build", "outputs", "apk", "release")
APK_DST   = os.path.join(WORKSPACE, "英语课文点读台.apk")

PY = sys.executable  # 用运行本脚本的解释器去跑 build.py（只需标准库）


def step(n, msg):
    print("\n=== [%d/4] %s ===" % (n, msg))


def run(cmd, cwd=None, env=None):
    print(">>> " + (cmd if isinstance(cmd, str) else " ".join(cmd)))
    return subprocess.run(cmd, cwd=cwd, env=env, shell=isinstance(cmd, str))


def main():
    # 0. 前置检查
    for p in (DESKTOP_AUDIO, BUILD_PY, PROJECT, GRADLE_BAT, JAVA_HOME, ANDROID_HOME):
        if not os.path.exists(p):
            print("缺少路径，请检查：", p)
            sys.exit(1)

    # 1. 重新生成 index.html
    step(1, "重新生成 index.html（build.py -> 桌面音频目录）")
    r = run([PY, BUILD_PY])
    if r.returncode != 0:
        print("build.py 执行失败"); sys.exit(r.returncode)
    src_html = os.path.join(DESKTOP_AUDIO, "index.html")
    if not os.path.exists(src_html):
        print("未生成 index.html：", src_html); sys.exit(1)

    # 2. 同步 assets：index.html + 全部 mp3
    step(2, "同步 assets（index.html + 51 个 mp3）")
    os.makedirs(ASSETS, exist_ok=True)
    shutil.copy2(src_html, os.path.join(ASSETS, "index.html"))
    copied = 0
    for fn in os.listdir(DESKTOP_AUDIO):
        if fn.lower().endswith(".mp3"):
            shutil.copy2(os.path.join(DESKTOP_AUDIO, fn), os.path.join(ASSETS, fn))
            copied += 1
    print("    已拷贝 index.html + %d 个 mp3 到 assets" % copied)

    # 3. 构建 release APK（沿用 listen.keystore 签名）
    step(3, "gradle assembleRelease（约 1-2 分钟）")
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["PATH"] = os.path.join(JAVA_HOME, "bin") + os.pathsep + env.get("PATH", "")
    r = run('"%s" assembleRelease --no-daemon' % GRADLE_BAT, cwd=PROJECT, env=env)
    if r.returncode != 0:
        print("构建失败，exit=%d" % r.returncode); sys.exit(r.returncode)

    # 4. 拷出成品 APK
    step(4, "拷出成品 APK")
    apks = glob.glob(os.path.join(APK_OUT, "*.apk"))
    if not apks:
        print("未找到产物 APK：", APK_OUT); sys.exit(1)
    apks.sort(key=os.path.getmtime, reverse=True)
    shutil.copy2(apks[0], APK_DST)
    size = os.path.getsize(APK_DST) / 1024.0 / 1024.0
    print("    完成 -> %s  (%.1f MB)" % (APK_DST, size))
    print("\n全部完成 ✅")


if __name__ == "__main__":
    main()
