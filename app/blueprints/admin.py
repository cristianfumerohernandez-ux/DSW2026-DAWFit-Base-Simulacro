import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def verificar_anonimo():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(404)
        

@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    
    if form.validate_on_submit():
        nombre_imagen = None
        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data
            nombre_imagen = secure_filename(archivo.filename)
            
            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_imagen))
        nueva_actividad = Actividad(
            nombre=form.nombre.data,
            deporte = form.deporte.data,
            cuota=form.cuota.data,
            plazas_libres=form.plazas_libres.data,
            imagen=nombre_imagen 
        )
        db.session.add(nueva_actividad)
        db.session.commit()
        return redirect(url_for("public.mostrar_actividades"))
    
    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )



@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    flash("Eliminación pendiente de implementar.", "info")
    return redirect(url_for("public.mostrar_actividades"))
