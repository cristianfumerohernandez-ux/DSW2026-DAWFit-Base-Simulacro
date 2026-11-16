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

   
    busqueda = request.args.get("busqueda", " ").strip()
    solo_con_plazas  = request.args.get("solo_con_plazas")
    consulta = Actividad.query
    if busqueda:
        consulta = consulta.filter(Actividad.nombre.ilike(f"%{busqueda}%"))
    if solo_con_plazas:
        consulta = consulta.filter(Actividad.plazas_libres > 0)
        
    actividades = consulta.all()
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
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):
    resp = make_response(redirect(url_for("public.home")))
    resp.set_cookie("deporte_fav", value = deporte, max_age=60*60*24*15, httponly=True, samesite="Lax")
    
    return resp


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():
    resp = make_response(redirect(url_for("public.mostrar_actividades")))
    resp.delete_cookie("deporte_fav")
    return resp


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    session.permanent = True
    ids = session.get("reservas", [])
    actividad = db.get_or_404(Actividad,act_id)

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
    ids = session.get("reservas", [])
    if ids:
        actividades = Actividad.query.filter(Actividad.id.in_(ids)).all() 
        total_sin_descuento = sum(act.cuota for act in actividades)
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
    session["reservas"].remove(act_id)
    session.modified = True
    flash("Reserva eliminada", "exito")
    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    ids = session.get("reservas", [])
    
    for act_id in ids:
        actividad = db.session.get(Actividad, act_id)
        if actividad is not None:
            actividad.plazas_libres -= 1

    db.session.commit()
    session.pop("reservas", None)

    return redirect(url_for("public.mostrar_actividades"))
