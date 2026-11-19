from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    ValidationError,
)
from app.models import Actividad, Usuario


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión (Ya implementado)."""

    email = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="Introduce tu correo electrónico."),
            Email(message="Formato de correo no válido."),
        ],
    )
    password = PasswordField(
        "Contraseña",
        validators=[DataRequired(message="Introduce tu contraseña.")],
    )
    remember = BooleanField("Mantener sesión iniciada")
    submit = SubmitField("Entrar al Club")


class ActividadForm(FlaskForm):
    """Formulario para crear y editar actividades deportivas."""

    nombre = StringField(
        "Nombre de la Actividad",
        validators=[
            DataRequired(message="El nombre es obligatorio."),
            Length(min=3, max=100, message="Entre 3 y 100 caracteres."),
        ],
    )
    deporte = StringField(
        "Modalidad Deportiva (ej. Pádel, Natación, Crossfit)",
        validators=[
            DataRequired(message="El deporte es obligatorio."),
            Length(min=3, max=50, message="Entre 3 y 50 caracteres."),
        ],
    )

    cuota = FloatField("Cuota Mensual (€)", validators=[
            # Bloque 2.2: la cuota debe existir y estar comprendida entre 5 y 150 euros.
            DataRequired(message="La cuota es obligatoria"),
            NumberRange(min=5.0, max=150.0 , message= "El precio debe ser mayor que 5 y menor a 150 euros")
        ]
    )
    plazas_libres = IntegerField("Plazas Libres", default=10 , validators=[
            # Bloque 2.2: el número de plazas es obligatorio y nunca puede ser negativo.
            DataRequired (message= "Mostrar las plazas es obligatorio"),
            NumberRange(min=0, message="El valor mínimo es de 0")
        ]
    )
    archivo_imagen = FileField("Cartel de la Actividad (JPG, PNG)", validators=[
            # Bloque 2.2: FileAllowed limita las extensiones aceptadas del cartel.
            FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes (JPG, PNG o JPEG).')
        ]
    )

    submit = SubmitField("Guardar Actividad")

    def validate_nombre(self, field):
        # Bloque 2.2: impide duplicar nombres, salvo el nombre de la actividad que se edita.
        actividades = Actividad.query.filter_by(nombre=field.data)
        actividad_actual_id = getattr(self, "actividad_actual_id", None)
        if actividad_actual_id is not None:
            actividades = actividades.filter(Actividad.id != actividad_actual_id)
        if actividades.first():
            raise ValidationError("Está actividad ya está registrada.")

class RegistroForm(FlaskForm):
    """Formulario de alta para nuevos socios."""

    username = StringField(
        "Nombre de Usuario",
        validators=[
            DataRequired(message="El nombre de usuario es obligatorio."),
            Length(min=3, max=50, message="Debe tener entre 3 y 50 caracteres."),
        ],
    )
    email = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            Email(message="Introduce un correo válido."),
        ],
    )
    # Bloque 4.1: la edad debe ser obligatoria y tener como mínimo 16 años.
    edad = IntegerField(
            "Edad",
            validators=[
                DataRequired(message="La edad es obligatoria."),
                NumberRange(min=16, message="Debes tener 16 años o más."),
            ],
        )

    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Length(min=6, message="Mínimo 6 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(message="Confirma tu contraseña."),
            EqualTo("password", message="Las contraseñas no coinciden."),
        ],
    )
    submit = SubmitField("Registrarme como Socio")

    def validate_username(self, field):
        if Usuario.query.filter_by(username=field.data).first():
            raise ValidationError("Ese nombre de usuario ya está registrado.")
    

    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError("Ese correo electrónico ya está en uso.")


class CambiarPasswordForm(FlaskForm):
    """Formulario para cambiar la contraseña desde el perfil del socio."""

    # Bloque 4.2: la contraseña actual se valida en la vista antes de actualizar el hash.
    password_actual = PasswordField(
        "Contraseña Actual",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Length(min=6, message="Mínimo 6 caracteres."),
        ],
    )
    
    nueva_password = PasswordField(
        "Contraseña Nueva",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Length(min=6, message="Mínimo 6 caracteres."),
        ],
    )
    # EqualTo obliga a que la confirmación coincida exactamente con la nueva contraseña.
    confirmar_password = PasswordField(
        "Confirmar Contraseña Nueva",
         validators=[
            DataRequired(message="Confirma tu contraseña."),
            EqualTo("nueva_password", message="Las contraseñas no coinciden."),
        ],
    )
    submit = SubmitField("Actualizar Contraseña")
