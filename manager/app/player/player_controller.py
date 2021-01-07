# -*- coding: iso-8859-1 -*-
from flask import Blueprint, request, jsonify
from manager.app.player import player_services
from manager import utils

player = Blueprint('player', __name__, url_prefix='/player')


@player.route('/update/<string:type_>', methods=['GET'])
def update(type_=None):
    """
    Inicia búsqueda sobre unos parámetros y a partir de los resultados inicia una actualización.
    Args:
        type_ (str): Tipo de reporte al que se va a acceder.
                    Disponibles: 'players, 'teams' y 'matches'.
    Returns (dict):
        Código de estado de respuesta HTTP
        cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    if not type_ or type_ not in player_services.type_to_endpoint:
        return utils.make_response(400, 'Bad Request')
    else:
        task_id = player_services.start_update(type_)
        return utils.make_response(200, 'Success')


@player.route('/is_user', methods=['GET'])
def is_user():
    """
        Inicia búsqueda sobre unos parámetros en la API Biwenger y comprueba si el usuario existe.
        Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
            user: id del usuario en su cuenta de Biwenger
            password: constraseña del usuario en la cuenta de Biwenger

        Returns (dict):
            Código de estado de respuesta HTTP
            cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        """

    result = player_services.get_user(request.args)
    if result:
        return utils.make_response(200, 'Success')
    else:
        return utils.make_response(400, 'Bad request')


@player.route('/get_user', methods=['GET'])
def get_user():
    """
    Inicia búsqueda sobre unos parámetros en la API Biwenger y devuelve los ids del usuario.
    Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
        user: id del usuario en su cuenta de Biwenger
        password: constraseña del usuario en la cuenta de Biwenger

    Returns (dict):
        Acierto (dict): credenciales de usuario.
        Fallo:
            Código de estado de respuesta HTTP
            cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    result = player_services.get_user(request.args)
    if result:
        return jsonify(result)
    else:
        return utils.make_response(400, 'Bad request')


@player.route('/get_market', methods=['GET'])
def get_market():
    """
    Inicia búsqueda sobre unos parámetros en la API Biwenger y devuelve los jugadores del mercado de fichajes.
    Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
        user: id del usuario en su cuenta de Biwenger
        password: constraseña del usuario en la cuenta de Biwenger
        league: liga en la que buscar.
        userLeague: usuario de la liga.
    Returns (dict):
        Acierto (dict): lista de ids.
        Fallo:
            Código de estado de respuesta HTTP
            cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    session, data = player_services.is_user(request.args)
    if data:
        market_players = player_services.get_market(session, data['token'], request.args)
        if market_players:
            return jsonify(market_players)
        else:
            return utils.make_response(400, 'Bad request')
    else:
        return utils.make_response(400, 'Bad request')


@player.route('/get_my_team', methods=['GET'])
def get_my_team():
    """
    Inicia búsqueda sobre unos parámetros en la API Biwenger y devuelve los jugadores del mercado de fichajes.
    Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
        user: id del usuario en su cuenta de Biwenger
        password: constraseña del usuario en la cuenta de Biwenger
        league: liga en la que buscar.
        userLeague: usuario de la liga.
    Returns (dict):
        Acierto (dict): lista de ids.
        Fallo:
            Código de estado de respuesta HTTP
            cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    session, data = player_services.is_user(request.args)
    if data:
        my_players = player_services.get_my_team(session, data['token'], request.args)
        if my_players:
            return jsonify(my_players)
        else:
            return utils.make_response(400, 'Bad request')
    else:
        return utils.make_response(400, 'Bad request')


@player.route('/get_players_sold', methods=['GET'])
def get_players_sold():
    """
        Devuelve la combinación minima de jugadores pertenecientes al equipo del usuario para superar un precio. Para
        ello, primero recoge los jugadores que pertenecen al usuario especificado por en los parámetros pasados por GET:
            user: id del usuario en su cuenta de Biwenger
            password: constraseña del usuario en la cuenta de Biwenger
            league: liga en la que buscar.
            userLeague: usuario de la liga.
            price: precio que debe superarse.
        Returns (dict):
            Acierto (dict): lista de ids.
            Fallo:
                Código de estado de respuesta HTTP
                cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        """
    session, data = player_services.is_user(request.args)
    my_players = player_services.get_my_team(session, data['token'], request.args)
    price = request.args.get("price", None, int)
    if my_players:
        players_sold = player_services.get_players_sold(price, my_players=my_players)
        return jsonify(players_sold)
    else:
        return utils.make_response(400, 'Bad request')
