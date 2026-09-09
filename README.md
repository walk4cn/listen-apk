# 英语课文点读台（安卓 APK）

二年级女孩用的英语课文点读 App：把课文音频和网页点读台一起打包进安卓安装包，**完全离线**、不依赖浏览器，手机竖屏 / 平板横屏自适应。

## 功能特性

- **点读台网页**：按单元折叠的课文列表，点任意一条即播放对应 mp3；保留原始英文文件名（不翻译、不重命名）。
- **儿童向界面**：粉紫糖果色、圆角卡片、内联 SVG 图标（不用 emoji），已听条目显示绿色小星星「集贴纸」。
- **播放控制**：上下曲、进度条拖动 seek、后退 15 秒、倍速 0.5–1.5×、单曲循环、自动连播（默认关闭，可开关）。
- **进度记录**：已听标记、上次听到位置存 `localStorage`，重开自动续上。
- **离线音频**：51 个课文 mp3 全部打进 APK 的 `assets/`，无任何网络依赖。
- **自适应方向**：运行时检测屏幕宽度（手机 `portrait` / 平板 `sensorLandscape`），旋转不重载。
- **零权限**：不需要联网、存储、相机等任何系统权限。

## 目录结构

```
listen-apk/
├── app/
│   └── src/main/
│       ├── assets/            # index.html + 51 个课文 mp3（全部打包进 APK）
│       ├── java/com/kidlisten/app/MainActivity.java   # WebView 壳 + mp3 的 Range/206 分发
│       └── res/               # 自适应图标（mipmap-anydpi-v26 + 各密度 PNG 兜底）
├── _gen_res.py                # 图标/资源生成脚本
├── build.gradle / settings.gradle
└── listen.keystore            # 发布签名（已被 .gitignore 排除，不会进仓库）
```

> **进度条 seek 的关键修复**：安卓 `WebViewAssetLoader` 不支持 HTTP Range，导致本地 mp3 在 WebView 里无法拖动进度。修复方式是 `MainActivity.shouldInterceptRequest` 对 `*.mp3` 自写 `serveAudio()`，按 `Range` 头返回 `206 + Content-Range + Accept-Ranges`；页面层 `effDur()` 用 `isFinite` 守卫 + `seekable` 兜底处理 VBR mp3 的 `duration=Infinity`。

## 构建（本地工具链）

环境要求：JDK 17、Android SDK（platform-tools / platforms;android-34 / build-tools;34.0.0）、Gradle 8.7。

本项目工具链隔离装在：

```
C:\Users\Lenovo\.workbuddy\binaries\android\   # jdk-17 / gradle-8.7 / cmdline-tools / sdk
```

一键构建 release APK：

```bash
cd listen-apk
export JAVA_HOME="/C/Users/Lenovo/.workbuddy/binaries/android/jdk-17"
export ANDROID_HOME="/C/Users/Lenovo/.workbuddy/binaries/android/sdk"
export PATH="$JAVA_HOME/bin:$PATH"
/C/Users/Lenovo/.workbuddy/binaries/android/gradle-8.7/bin/gradle assembleRelease
# 产物：app/build/outputs/apk/release/app-release.apk
```

> ⚠️ 工程路径**不能含空格**（如 `Default Project` 会让 Gradle 的 .bat 参数解析炸掉）。本工程已放在无空格路径下。

## 更新课文 / 页面后重打包

1. 用工作区的 `build.py` 重新生成 `index.html`（入口是桌面 `课文音频` 目录的 51 个 mp3）。
2. 把新的 `index.html` 及 mp3 覆盖到 `app/src/main/assets/`。
3. 重新 `assembleRelease`。

> **签名一致性**：更新包必须用同一个 `listen.keystore` 签名才能覆盖安装。密钥已排除在 git 外，请单独保管。

## 自定义页面（可选）

页面由工作区 `C:\Users\Lenovo\Documents\Default Project\listen\build.py` 生成，
顶栏标题、配色、分组逻辑都在该脚本里；改完重新生成 `index.html` 再拷进 `assets/` 即可。
图标由 `icon.py`（PIL 绘制粉紫圆角 + 白色耳机 + ABC）生成。

## 隐私说明

- 安装包离线运行，音频与数据都在本机，无服务器端存储、无上传。
- 进度仅存于 App 内 `localStorage`，清除 App 数据即清空。

## 版本

- v1.7（versionCode 8）：修复进度条拖动弹回开头（壳层 Range/206 分发 + 206 Content-Length 加固）。
- v1.1：手机竖屏 / 平板横屏运行时自适应。
- v1.0：首版 WebView 壳 + 离线音频。
