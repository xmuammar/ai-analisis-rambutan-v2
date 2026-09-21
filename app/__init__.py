from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan masuk untuk melanjutkan."


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.trees import bp as trees_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(trees_bp)

    with app.app_context():
        from app import models  # noqa: F401

        if app.config["AUTO_CREATE_SCHEMA"]:
            db.create_all()
            _seed_database()

    @app.cli.command("seed-data")
    def seed_data_command():
        """Insert the initial garden and 12 trees if they are absent."""
        _seed_database()
        print("Seed data siap.")

    return app


def _seed_database():
    from app.models import Garden, Tree

    garden = db.session.scalar(db.select(Garden).limit(1))
    if garden is None:
        garden = Garden(
            name="Kebun Rambutan Belereng",
            location_name="Kebun utama",
            description="Kebun awal AiAnalisRambutan.",
        )
        db.session.add(garden)
        db.session.flush()

    if db.session.scalar(db.select(Tree).limit(1)) is None:
        db.session.add_all(
            [
                Tree(
                    code=f"RBT-{number:03d}",
                    garden_id=garden.id,
                    species="Rambutan",
                    variety="Belereng",
                    status="SEHAT",
                    active=True,
                )
                for number in range(1, 13)
            ]
        )
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return db.session.get(User, int(user_id))
