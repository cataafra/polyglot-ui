from gui.splash_screen import SplashScreen
from config.logger import setup_logger
from config.config import config

if __name__ == "__main__":
    setup_logger()

    app = SplashScreen(debug=config.getboolean("general", "debug"))
    app.mainloop()
