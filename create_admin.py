import os
import sys
from getpass import getpass

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.mongodb_connector import connect_to_mongodb, add_user  # noqa: E402
from flask import Flask  # noqa: E402

# Create a minimal Flask app to establish an application context
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017")


def create_admin_user():
    """
    A command-line script to create a new user with the 'admin' role.
    """
    with app.app_context():
        # Establish database connection
        users_col, _, _ = connect_to_mongodb()
        if users_col is None:
            print("Erreur: Impossible de se connecter à la base de données MongoDB.")
            return

        print("--- Création d'un nouvel utilisateur administrateur ---")

        # Get username
        while True:
            username = input(
                "Entrez le nom d'utilisateur de l'administrateur: "
            ).strip()
            if username:
                break
            print("Le nom d'utilisateur ne peut pas être vide.")

        # Get password
        while True:
            password = getpass("Entrez le mot de passe de l'administrateur: ")
            if not password:
                print("Le mot de passe ne peut pas être vide.")
                continue

            confirm_password = getpass("Confirmez le mot de passe: ")
            if password == confirm_password:
                break
            print("Les mots de passe ne correspondent pas. Veuillez réessayer.")

        # Add the admin user to the database
        user_id = add_user(users_col, username, password, role="admin")

        if user_id:
            print(f"Succès ! L'utilisateur administrateur '{username}' a été créé.")
        else:
            print(
                f"Erreur: L'utilisateur administrateur '{username}' n'a pas pu être créé. Il se peut qu'il existe déjà."
            )


if __name__ == "__main__":
    create_admin_user()
