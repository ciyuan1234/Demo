import os


class Settings:
    app_name: str = "Aquaculture AIoT Backend"
    database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://aquaculture:aquaculture@mysql:3306/aquaculture")
    do_critical: float = float(os.getenv("DO_CRITICAL", "3.0"))
    do_warning: float = float(os.getenv("DO_WARNING", "4.0"))
    do_recovery: float = float(os.getenv("DO_RECOVERY", "5.0"))
    ph_min: float = float(os.getenv("PH_MIN", "6.5"))
    ph_max: float = float(os.getenv("PH_MAX", "8.5"))
    turbidity_max: float = float(os.getenv("TURBIDITY_MAX", "100.0"))
    rapid_do_drop: float = float(os.getenv("RAPID_DO_DROP", "0.15"))


settings = Settings()
