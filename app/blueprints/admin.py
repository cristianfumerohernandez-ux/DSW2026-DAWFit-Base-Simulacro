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
        archivo = form.archivo_imagen.data
        if archivo and archivo.filename:
            nombre_seguro = secure_filename(archivo.filename)
            deporte_seguro = secure_filename(form.deporte.data).lower()
            nombre_imagen = f"{deporte_seguro}_{nombre_seguro}"

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
    form.actividad_actual_id = actividad.id

    if form.validate_on_submit():
        imagen_anterior = actividad.imagen
        nombre_imagen = imagen_anterior
        archivo = form.archivo_imagen.data
        if archivo and archivo.filename:
            nombre_seguro = secure_filename(archivo.filename)
            deporte_seguro = secure_filename(form.deporte.data).lower()
            nombre_imagen = f"{deporte_seguro}_{nombre_seguro}"

            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_imagen))

        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.cuota = form.cuota.data
        actividad.plazas_libres = form.plazas_libres.data
        actividad.imagen = nombre_imagen
        db.session.commit()

        if imagen_anterior and imagen_anterior != nombre_imagen:
            ruta_anterior = os.path.join(
                current_app.config["UPLOAD_FOLDER"], imagen_anterior
            )
            if os.path.isfile(ruta_anterior):
                os.remove(ruta_anterior)
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    actividad = db.get_or_404(Actividad,act_id)
    if actividad.plazas_libres == 0:
        flash("No se ha podido borrar", "error")
        return redirect(url_for("public.mostrar_actividades"))
    if actividad.plazas_libres > 0:
        if actividad.imagen:
            ruta_imagen = os.path.join(current_app.config["UPLOAD_FOLDER"],actividad.imagen)
        if os.path.isfile(ruta_imagen):
            os.remove(ruta_imagen)
            db.session.delete(actividad)
            db.session.commit()

    return redirect(url_for("public.mostrar_actividades"))
