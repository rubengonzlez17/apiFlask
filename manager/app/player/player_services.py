# -*- coding: iso-8859-1 -*-
import requests
from manager.app.core import logger
from manager.app import celery
from manager.app.task_management import tm_services
from manager.app.player import player_model
from manager.app.scraper import web_scraping
from manager.app.player.player_model import Player
from celery.schedules import crontab

import json
import time
import itertools


biwenger_endpoints = {
    'url_all_teams': 'https://cf.biwenger.com/api/v2/competitions/la-liga/',
    'url_team': 'https://cf.biwenger.com/api/v2/teams/la-liga/',
    'url_player': 'https://cf.biwenger.com/api/v2/players/la-liga/',
    'variations': 'https://cf.biwenger.com/api/v2/competitions/la-liga/market?interval=day&includeValues=true',
    'login': 'https://biwenger.as.com/api/v2/auth/login',
    'account': 'https://biwenger.as.com/api/v2/account',
    'market': 'https://biwenger.as.com/api/v2/market',
    'my_team': 'https://biwenger.as.com/api/v2/user?fields=*,lineup(type,playersID),players(*,fitness,team,owner),market(*,userID),offers,trophies',
    'fields_player': "?fields=*%2Cteam%2Cfitness%2Creports(points%2Chome%2Cevents%2Cstatus(status%2CstatusText)%2Cmatch(*%2Cround%2Chome%2Caway)%2Cstar)%2Cprices%2Ccompetition%2Cseasons%2Cnews%2Cthreads&score=1&lang=en",
}

headers = {'content-type': 'application/json'}

slug_teams = {'alaves', 'real-madrid', 'athletic', 'atletico', 'barcelona', 'celta', 'getafe','levante',
               'real-sociedad', 'sevilla', 'villarreal', 'granada', 'elche', 'eibar', 'betis', 'osasuna',
                'real-valladolid', 'sd-huesca', 'cadiz', 'valencia'}

type_to_endpoint = {
    'players': 'players',
    'matches': 'matches',
    'teams': 'teams'
}


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0, hour=3),
        start_update_periodic.s("matches"),
    )
    sender.add_periodic_task(
        crontab(minute=10, hour=3),
        start_update_periodic.s("players")
    )
    sender.add_periodic_task(
        crontab(minute=0, hour=5),
        start_update_periodic.s("teams"),
    )


def start_update_players(active_task_id):
    for team in slug_teams:
        update_players.delay(slug_team=team, tracker_id=active_task_id)


def start_update_teams(active_task_id):
    num = 1
    for team in slug_teams:
        update_team.delay(slug_team=team, num=num, tracker_id=active_task_id)
        num = num + 1


def start_update_matches(active_task_id):
    for team in slug_teams:
        update_match.delay(slug_team=team, tracker_id=active_task_id)


@celery.task
def start_update_periodic(type):
    """
        Comienza el servicio de actualización de datos de forma periodica.

        Args:
            type(str): tipo de tarea a realizar.

    """

    active_task_id = tm_services.start_task_tracker(type, "Update")
    if type == "players":
        start_update_players(active_task_id)
    elif type == "teams":
        start_update_teams(active_task_id)
    else:
        start_update_matches(active_task_id)


@celery.task(bind=True, max_retries=None)
def update_match(self, slug_team, tracker_id=None):
    """
        Persiste los datos de los equipos obtenidos de la API de Biwenger y a partir de los resultados inicia una
        actualización.
        Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
            ActiveTask: id de la Tarea
            slug_team: id del equipo a actualizar
            tracker_id (str): Objeto que hace un seguimiento del estado de la tarea.
    """
    try:
        data, status_code = make_request_get(biwenger_endpoints['url_team'] + slug_team)

        if status_code == 200:
            i = 0
            for match in data['data']['matches']:
                i = i + 1
                tm_services.update_progress(tracker_id, i, len(data['data']['matches']))
                player_model.Match.builder(match).update_()

            tm_services.finish_tracker(tracker_id)
        if status_code == 429:
            logger.error("Task failed due to ConnectionError, retrying in 600s...")
            self.retry(countdown=60)

    except requests.ConnectionError:
        logger.error("Task failed due to ConnectionError, retrying in 120s...")
        self.retry(countdown=120)


@celery.task(bind=True, max_retries=None)
def update_team(self, slug_team, num, tracker_id=None):
    """
        Persiste los datos de los equipos obtenidos de la API de Biwenger y a partir de los resultados inicia una
        actualización.
        Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
            ActiveTask: id de la Tarea
            slug_team: id del equipo a actualizar
            tracker_id (str): Objeto que hace un seguimiento del estado de la tarea.
    """
    try:
        data, status_code = make_request_get(biwenger_endpoints['url_all_teams'])

        if status_code == 200:
            teams = data['data']['standings']
            for item in teams:
                status_code = web_scraping.test()
                if status_code == 200:
                    if item['team']['slug'] == slug_team:
                        tm_services.update_progress(tracker_id, num, len(teams))
                        player_model.Team.builder(item).update_()
                else:
                    logger.error("Error Scraper, retrying in 120 s...")
                    self.retry(countdown=120)
            tm_services.finish_tracker(tracker_id)
        if status_code == 429:
            logger.error("Task failed due to ConnectionError, retrying in 600s...")
            self.retry(countdown=1800)
    except requests.ConnectionError:
        logger.error("Task failed due to ConnectionError, retrying in 120s...")
        self.retry(countdown=120)


@celery.task(bind=True, max_retries=None)
def update_players(self, slug_team, tracker_id=None):
    """
        Persiste los datos de partidos y jugadores de cada equipo obtenidos de la API de Biwenger y a partir de los
        resultados inicia una actualización.
        Los parámetros se pasan por GET y según el parámetro se ejecuta una búsqueda distinta:
            ActiveTask: id de la Tarea
            slug_team: id del equipo a actualizar
            tracker_id (str): Objeto que hace un seguimiento del estado de la tarea.
    """
    try:
        data, status_code = make_request_get(biwenger_endpoints['url_team'] + slug_team)

        if status_code == 200:
            i = 0
            for player in data['data']['players']:
                status_code = web_scraping.test()
                if status_code == 200:
                    if player['position'] != 5:
                        i = i+1
                        time.sleep(10)
                        data_player, status_code_player = make_request_get(biwenger_endpoints['url_player'] + player['slug']
                                                        + biwenger_endpoints['fields_player'])
                        if status_code_player == 200:
                            tm_services.update_progress(tracker_id, i, len(data['data']['players']))
                            player_model.Player.builder(player, data['data']['id'], data_player).update_()
                        if status_code_player == 429:
                            logger.error("Task failed due to ConnectionError, retrying in 600s...")
                            self.retry(countdown=1800)
                else:
                    logger.error("Error Scraper, retrying in 120s...")
                    self.retry(countdown=120)
            tm_services.finish_tracker(tracker_id)
        if status_code == 429:
            logger.error("Task failed due to ConnectionError, retrying in 600s...")
            self.retry(countdown=1800)
    except requests.ConnectionError:
        logger.error("Task failed due to ConnectionError, retrying in 120s...")
        self.retry(countdown=120)


def start_update(type_):
    """
        Comienza el servicio de actualización.

        Args:
            type_(str): Tipo de tarea a realizar.

        Returns (dict):
        Código de estado de respuesta HTTP
        cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    active_task_id = tm_services.start_task_tracker(type_, "Update")

    if type_ == "players":
        start_update_players(active_task_id)
    elif type_ == "teams":
        start_update_teams(active_task_id)
    else:
        start_update_matches(active_task_id)

    return 200, 'Success'


def get_next_match(pr, id_team):
    for item in pr['home']:
        if pr['home'][item] == id_team:
            return pr['id']
    for item in pr['away']:
        if pr['away'][item] == id_team:
            return pr['id']
    return None


def is_user(params={}):
    """
        Comprueba si las credenciales del usuario son correctas
        Args:
            user (str): id de la cuenta del usuario
            password (str): contraseña del usuario
        Returns (dict, dict):
            Acierto:
                La sesion, datos de la peticion
            Fallo:
                None, None
    """
    payload = {
        'email': params['user'],
        'password': params['password']
    }
    try:
        data, status_code, session = make_request_post(biwenger_endpoints['login'], web_scraping.headers_scraper, payload)
        if status_code == 200:
            return session, data
        else:
            return None, None
    except requests.ConnectionError:
        return None, None


def get_user(params={}):
    """
        Obtiene los ids del usuario de Biwenger en el caso de existir.
        Args:
            user (str): id de la cuenta del usuario
            password (str): contraseña del usuario
        Returns (dict):
            Acierto:
                token de acceso
                id de la liga del usuario
                id de usuario en esa liga
            Fallo: None
    """
    if 'user' not in params:
        return 500, 'user parameter is required'
    if 'password' not in params:
        return 500, 'password parameter is required'

    session, data = is_user(params)
    if data:
        data_account = session.get(biwenger_endpoints['account'], headers=create_headers(data['token'], None, None))
        return {'credentials': format_user(json.loads(data_account.text))}
    else:
        return None


def get_market(session, token, params={}):
    """
        Obtiene los jugadores del mercado en base a una liga y usuario determinado.
        Args:
            session (dict): sesion
            token (str): token de acceso
            league (int): id de la liga
            user (int): id del usuario
        Returns (dict):
            Acierto (dict)
            Fallo: None
    """
    if 'league' not in params:
        return 500, 'league parameter is required'
    if 'userLeague' not in params:
        return 500, 'user parameter is required'

    bearer = "Bearer "+token

    headers = {
        'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
        'Authorization': bearer,
        'X-League': str(params['league']),
        'X-User': str(params['userLeague']),
    }

    s = session.get(biwenger_endpoints['market'], headers=headers)
    market = json.loads(s.text)

    if market['status'] == 200:
        return format_market(market, params['userLeague'])

    return None


def get_my_team(session, token, params={}):
    """
        Obtiene los jugadores del equipo en base a una liga y usuario determinado.
        Args:
            session (dict): sesion
            token (str): token de acceso
            league (int): id de la liga
            user (int): id del usuario
        Returns (dict):
            Acierto (dict)
            Fallo: None
    """
    if 'league' not in params:
        return 500, 'league parameter is required'
    if 'userLeague' not in params:
        return 500, 'user parameter is required'

    bearer = "Bearer "+token

    headers = {
        'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
        'Authorization': bearer,
        'X-League': str(params['league']),
        'X-User': str(params['userLeague']),
    }

    s = session.get(biwenger_endpoints['my_team'], headers=headers)
    my_team = json.loads(s.text)

    if my_team['status'] == 200:
        return format_my_team(my_team)

    return None


def get_players_sold(price, my_players=None):
    """
        Devuelve la combinación minima de jugadores pertenecientes al equipo del usuario para superar un precio.
        Args:
            price: precio que se debe superar
            my_players: lista de jugadores que pertenecen al usuario
        Returns (dict):
            Acierto (dict): lista de ids de la combinación minima de jugadores
            Fallo: None
    """
    combinations = []
    players_sold = []
    stuff = {}
    index = 0
    best = 0
    minor = 3

    players = Player.objects(_id__in=my_players[0]['all_players'])
    for player in players:
        if player['position'] != player_model.positions[1] and int(player['use'][:-1]) < 60:
            stuff.update({str(index): [player['price']]})
        index = index + 1
    for L in range(0, len(stuff) + 1):
        for subset in itertools.combinations(stuff, L):
            combinations.append(subset)

    for item in combinations:
        total = sum_total(item, stuff)
        if total >= price:
            if len(item) <= minor:
                minor = len(item)
                best = item

    if best != 0:
        for item in best:
            players_sold.append(players[int(item)]['_id'])
    return players_sold


def sum_total(item, stuff):
    total = 0
    for i in item:
        total = total + stuff[str(i)][0]
    return total


def make_request_get(url):
    """
    Realiza una petición GET a la API de Biwenger.

    Args:
        url (str): Servicio de Biwenger al que se va a enviar la petición.

    Returns (dict, int):
        El resultado de la petición, el código de estado de la petición.
    """

    r = requests.get(url=url, headers=headers,)

    if r.status_code == 200:
        return r.json(), r.status_code
    else:
        return r.text, r.status_code


def make_request_post(url, headers, payload):
    """
    Realiza una petición POST a la API de Biwenger.

    Args:
        url (str): Servicio de Biwenger al que se va a enviar la petición.
        headers (dict): Cabezeras
        payload (dict): credenciales del usuario.

    Returns (dict, int):
        El resultado de la petición, el código de estado de la petición, la sesion.
    """
    session = requests.Session()
    r = session.post(url=url, data=payload, headers=headers)

    if r.status_code == 200:
        return r.json(), r.status_code, session
    else:
        return r.text, r.status_code, session


def create_headers(token, x_user, x_league):
    """
        Genera las cabezeras necesarias para realizar consultas de usuario en la API de Biwenger y lo devuelve,

        Args:
            token (str): Token de acceso
            x_user (int): id del usuario en una liga
            x_league (int): id de la liga
    """
    if x_user and x_league:
        headers = {
            'User-Agent': web_scraping.headers_scraper['User-Agent'],
            'Authorization': 'Bearer ' + token,
            'X-League': x_league,
            'X-User': x_user,
        }
    else:
        headers = {
            'User-Agent': web_scraping.headers_scraper['User-Agent'],
            'Authorization': 'Bearer '+token
        }

    return headers


def format_user(user_data):
    """
        Formatea los parametros de usuario devueltos por la api de Biwenger

        Args:
            user_data (dict): datos del usuario
        Returns (dict or None):
            ids de liga, nombre de liga,  ids de usuario
    """

    list_leagues = []

    for item in user_data['data']['leagues']:
        list_leagues.append({"x_league": item['id'], "name_league": item['name'], "x_user": item['user']['id']})

    credentials = {
        'x_leagues': list_leagues,
    }

    return credentials


def format_market(market, user_biwenger):
    """
        Formatea el resultado obtenido del mercado de fichajes devuelto por la api de Biwenger

        Args:
            market (dict): lista de jugadores que hay en el mercado.
            user_biwenger (int): id del usuario que solicita la lista de ids de los jugadores del mercado.
        Returns (dict): lista de objetos.
            id de cada jugador en el mercado
            price: precio de venta de cada jugador
    """

    players = []
    market_data = []

    for item in market['data']['sales']:
        user_market = item.get('user', None)
        user_market_id = user_market.get('id', None) if user_market else None
        if not str(user_biwenger) == str(user_market_id):
            players.append({"id": item['player']['id'], "price": item['price']})

    market_data.append({
        "balance": market['data']['status']['balance'],
        "maximumBid": market['data']['status']['maximumBid'],
        "players": players,
    })
    return market_data


def format_my_team(my_team):
    """
        Formatea el resultado obtenido del equipo de una usuario devuelto por la api de Biwenger

        Args:
            my_team (dict): resultado de la api de Biwenger.
        Returns (dict):
            name: nombre del usuario en esa liga.
            points: puntos totales obtenidos por el usuario.
            balance: presupuesto para fichajes del usuario.
            lineup: jugadores titulares en el equipo del usuario.
            players: jugadores del usuario.
    """

    my_team_data = []
    line_up_ids = []
    all_players = []

    for item in my_team['data']['lineup']['playersID']:
        line_up_ids.append(item)

    for item in my_team['data']['players']:
        all_players.append(item['id'])

    my_team_data.append({
        "points": my_team['data']['points'],
        "balance": my_team['data']['balance'],
        "type": my_team['data']['lineup']['type'],
        "line_up_ids": line_up_ids,
        "all_players": all_players
    })

    return my_team_data


def format_find_query(query_args):
    """
    Formatea los parametros enviados en la request para que sean utilizables

    Args:
        query_args (mapping): Parámetros enviados en la request que sirven para
                            definir que búsqueda se va a hacer.

    Returns (dict or None):
        Parámetros necesarios para realizar una búsqueda ó
        None si los parámetros enviados en la request no son válidos.
    """

    active_task = query_args.get('activeTask', default=None, type=str)

    search_params = {}

    if active_task:
        search_params['activeTask'] = active_task
    else:
        return None

    return search_params
