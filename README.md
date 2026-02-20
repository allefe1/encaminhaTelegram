# 🌑 DarkoGram

DarkoGram is a modern, minimalist desktop application for cloning and backing up Telegram channels.

![DarkoGram UI](https://via.placeholder.com/800x500?text=DarkoGram+Modern+UI)

## ✨ Features

- **Modern UI**: Clean, responsive interface built with Flet.
- **Easy Cloning**: Clone all messages from Channel A to Channel B.
- **Background Processing**: Non-blocking operations with live progress updates.
- **Secure**: Runs locally on your machine using your own API credentials.

## 📦 Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up your `.env` file (see `.env.example`).

## 🚀 Usage

Run the application:

```bash
python main.py
```

## 🛠️ Structure

-   `src/ui`: Interface code (Flet).
-   `src/core`: Backend logic (Pyrogram).
-   `src/utils`: Helper functions.

## 📝 License

Educational purpose only.
