from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField
from wtforms.validators import (
    DataRequired,
    Length,
    EqualTo,
    ValidationError,
    NumberRange,
)

# from database.mongodb_connector import check_username_exists # No longer import directly
import re
from flask import current_app  # Import current_app to access app.config


# Custom validator for password complexity
class PasswordComplexity:
    def __init__(self, message=None):
        if not message:
            message = "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if len(password) < 8:
            raise ValidationError(self.message)
        if not re.search(r"[A-Z]", password):
            raise ValidationError(self.message)
        if not re.search(r"[a-z]", password):
            raise ValidationError(self.message)
        if not re.search(r"[0-9]", password):
            raise ValidationError(self.message)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(self.message)


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    age = IntegerField(
        "Age",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=120, message="Veuillez entrer un âge valide."),
        ],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), PasswordComplexity()]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Les mots de passe doivent correspondre."),
        ],
    )
    role = SelectField(
        "Role",
        choices=[("patient", "Patient"), ("medecin", "Medecin")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, field):  # Changed from self, username to self, field
        from database.mongodb_connector import (
            check_username_exists,
        )  # Import here to avoid circular dependency

        users_col = current_app.config["USERS_COLLECTION"]
        if check_username_exists(users_col, field.data):  # Pass users_col
            raise ValidationError(
                "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre."
            )


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AdminRegistrationForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField(
        "Mot de passe", validators=[DataRequired(), PasswordComplexity()]
    )
    confirm_password = PasswordField(
        "Confirmer le mot de passe",
        validators=[
            DataRequired(),
            EqualTo("password", message="Les mots de passe doivent correspondre."),
        ],
    )
    submit = SubmitField("Créer le compte administrateur")

    def validate_username(self, field):
        from database.mongodb_connector import check_username_exists

        users_col = current_app.config["USERS_COLLECTION"]
        if check_username_exists(users_col, field.data):
            raise ValidationError(
                "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre."
            )


class AssignDoctorForm(FlaskForm):
    doctor = SelectField("Choisir un médecin", validators=[DataRequired()])
    submit = SubmitField("Assigner le médecin")


class AddDoctorForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur du médecin",
        validators=[DataRequired(), Length(min=2, max=20)],
    )
    password = PasswordField(
        "Mot de passe", validators=[DataRequired(), PasswordComplexity()]
    )
    confirm_password = PasswordField(
        "Confirmer le mot de passe",
        validators=[
            DataRequired(),
            EqualTo("password", message="Les mots de passe doivent correspondre."),
        ],
    )
    submit = SubmitField("Ajouter le médecin")

    def validate_username(self, field):
        from database.mongodb_connector import check_username_exists

        users_col = current_app.config["USERS_COLLECTION"]
        if check_username_exists(users_col, field.data):
            raise ValidationError(
                "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre."
            )
