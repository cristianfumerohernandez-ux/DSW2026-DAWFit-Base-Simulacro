from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():
    # Bloque 1.1: se leen los criterios de búsqueda enviados por el formulario GET.
    busqueda = request.args.get("busqueda", " ").strip()
    solo_con_plazas  = request.args.get("solo_con_plazas")

    # Ambos filtros se aplican sobre la misma consulta y pueden funcionar juntos.
    consulta = Actividad.query
    if busqueda:
        consulta = consulta.filter(Actividad.nombre.ilike(f"%{busqueda}%"))
    if solo_con_plazas:
        consulta = consulta.filter(Actividad.plazas_libres > 0)

    actividades = consulta.all()

    # Bloque 1.2: la preferencia se recupera de la cookie para resaltarla en el catálogo.
    deporte_fav = request.cookies.get("deporte_fav")

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        busqueda = busqueda,
        solo_con_plazas = solo_con_plazas,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    # Bloque 1.3: get_or_404 convierte un identificador inexistente en un error 404.
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>", methods=["POST"])
def guardar_preferencia(deporte):
    # Bloque 1.2: se crea una respuesta para añadir la cookie antes de redirigir.
    flash("Preferencia guardada.", "info")
    resp = make_response(redirect(url_for("public.home")))
    resp.set_cookie("deporte_fav", value = deporte, max_age=60*60*24*15, httponly=True, samesite="Lax")

    return resp


@public_bp.route("/limpiar-preferencia", methods=["POST"])
def limpiar_preferencia():
    # Bloque 1.2: se elimina la cookie de preferencia y se vuelve al catálogo.
    flash("Preferencia eliminada.", "info")
    resp = make_response(redirect(url_for("public.mostrar_actividades")))
    resp.delete_cookie("deporte_fav")
    return resp


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    # Bloque 3.1: la reserva permanece en la sesión y esta se marca como permanente.
    session.permanent = True
    ids = session.get("reservas", [])
    actividad = db.get_or_404(Actividad,act_id)

    # Se comprueban cupo disponible, duplicados y máximo de tres reservas.
    if(actividad.plazas_libres > 0):
        if(act_id not in ids):
            if(len(ids) < 3):
                session.setdefault("reservas", [])
                session["reservas"].append(act_id)
                session.modified = True
                flash("Se ha reservado correctamente", "exito")
            else:
                flash("Error, has sobrepasado tu máximo de reservas", "error")
        else:
            flash("Error, has intentado meter una reserva que ya tenías" , "error")
    else:
        flash("Error, no te queda espacio en tus reservas", "error")

    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():
    # Bloque 3.2: los identificadores guardados en sesión se buscan con el operador IN.
    ids = session.get("reservas", [])
    if ids:
        actividades = Actividad.query.filter(Actividad.id.in_(ids)).all() 
        total_sin_descuento = sum(act.cuota for act in actividades)

        # El descuento multideporte solo se activa al tener exactamente tres actividades.
        descuento_aplicado = len(actividades) == 3
        total_final = total_sin_descuento * 0.8 if descuento_aplicado else total_sin_descuento
    else:
        actividades = []
        total_sin_descuento = 0.0
        descuento_aplicado = False
        total_final = 0.0
    
        
    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):
    # Bloque 3.3A: remove elimina únicamente el identificador indicado.
    session["reservas"].remove(act_id)
    session.modified = True
    flash("Reserva eliminada", "exito")
    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    # Bloque 3.3B: se confirma la inscripción restando una plaza por reserva.
    ids = session.get("reservas", [])
    if not ids:
        flash("No hay reservas pendientes para confirmar.", "error")
        return redirect(url_for("public.mostrar_actividades"))

    for act_id in ids:
        actividad = db.session.get(Actividad, act_id)
        if actividad is not None:
            actividad.plazas_libres -= 1

    db.session.commit()
    session.pop("reservas", None)
    flash("Inscripciones confirmadas correctamente.", "exito")

    return redirect(url_for("public.mostrar_actividades"))
