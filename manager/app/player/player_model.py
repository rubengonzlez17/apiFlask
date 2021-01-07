# -*- coding: iso-8859-1 -*-
from mongoengine import fields
from mongoengine import ValidationError, Q
from datetime import datetime
from manager.utils import normalize
from manager.app.scraper import web_scraping

positions = {
    1: 'PT',
    2: 'DF',
    3: 'MC',
    4: 'DL',
    'None': ''
}


class CustomDocument(fields.Document):
    """
    Recubrimiento de la clase Document para facilitar guardado y/o validaciones si fuese necesario.
    """

    meta = {
        'allow_inheritance': True,
        'abstract': True,
        'index_cls': False
    }

    def save(self, **kwargs):
        """
        Recubrimiento del metodo Document.save() para validar errores.

        Args:
            **kwargs: los argumentos propios de Document.save()

        Returns (boolean):
            True si el objeto se ha guardado correctamente, False si no.
        """

        try:
            super(CustomDocument, self).save(**kwargs)
            print("Player {} object saved".format(str(type(self))))
            return True
        except ValidationError as error:
            print('Caught this error: {}'.format(str(repr(error))))
            return False

    def update_(self):
        """
        Crea o actualiza un objeto.

        Returns (boolean):
            True si el objeto se ha guardado correctamente, False si no.
        """

        # obj = self.__class__.objects(_id=self._id).first()
        index = self.__class__.list_indexes()[0][0][0]
        obj = self.__class__.objects(**{index: self[index]}).first()

        if obj:
            obj.delete()

        return self.save()


class Team(CustomDocument):
    _id = fields.IntField(primary_key=True, required=True)
    name = fields.StringField(null=True)
    slug = fields.StringField(null=True)
    position = fields.IntField(null=True)
    won = fields.IntField(null=True)
    lost = fields.IntField(null=True)
    tied = fields.IntField(null=True)
    scored = fields.IntField(null=True)
    against = fields.IntField(null=True)
    img = fields.StringField(null=True)
    penalties = fields.ListField(null=True)
    fouls = fields.ListField(null=True)
    line_up = fields.StringField(null=True)
    line_up_players_id = fields.ListField(null=True)
    next_match_id = fields.IntField(null=True)
    last_update = fields.DateTimeField(null=True)

    meta = {
        'collection': 'Teams'
    }

    @classmethod
    def builder(cls, data):
        """
        Crea una instancia de tipo Team.

        Args:
            kwargs (dict): Propiedades del objeto.

        Returns ():
            La instancia del objeto creado.
        """
        slug = data['team'].get('slug', None)
        result = web_scraping.scraper_team(slug)

        team = Team(
            _id=data['team'].get('id', None),
            name=data['team'].get('name', None),
            slug=slug,
            position=data.get('position', None),
            won=data.get('won', None),
            lost=data.get('lost', None),
            tied=data.get('tied', None),
            scored=data.get('scored', None),
            against=data.get('against', None),
            img=result['escudo'],
            penalties=get_lanzadores(result['penalties']),
            fouls=get_lanzadores(result['fouls']),
            line_up=result['line_up'],
            line_up_players_id=result['line_up_players'],
            next_match_id=get_next_match(slug),
            last_update=datetime.now()
        )

        return team


class Player(CustomDocument):
    _id = fields.IntField(primary_key=True, required=True)
    name = fields.StringField(null=True)
    slug = fields.StringField(null=True)
    position = fields.StringField(null=True)
    price = fields.IntField(null=True)
    priceIncrement = fields.IntField(null=True)
    status = fields.StringField(null=True)
    statusInfo = fields.StringField(null=True)
    fitness = fields.ListField(null=True)
    points = fields.IntField(null=True)
    pointsHome = fields.IntField(null=True)
    pointsAway = fields.IntField(null=True)
    pointsLastSeason = fields.IntField(null=True)
    playedHome = fields.IntField(null=True)
    playedAway = fields.IntField(null=True)
    img = fields.StringField(null=True)
    demand = fields.StringField(null=True)
    sale = fields.StringField(null=True)
    use = fields.StringField(null=True)
    reports_id = fields.ListField(null=True)
    prices = fields.ListField(null=True)
    team_id = fields.IntField(null=True)
    last_update = fields.DateTimeField(null=True)

    meta = {
        'collection': 'Players'
    }

    @classmethod
    def builder(cls, data, team_id, player_data):
        """
        Crea una instancia de tipo Player.

        Args:
            kwargs (dict): Propiedades del objeto.

        Returns ():
            La instancia del objeto creado.
        """
        id = data.get('id', None)
        slug = data.get('slug', None)
        statitics = web_scraping.get_statitics(slug)

        player = Player(
            _id=id,
            name=normalize(data.get('name', None)),
            slug=slug,
            position=positions[data.get('position', None)],
            price=data.get('price', None),
            priceIncrement=data.get('priceIncrement', None),
            status=data.get('status', None),
            statusInfo=data.get('statusInfo', None),
            fitness=data['scoreStats']['1'].get('fitness', None),
            points=data['scoreStats']['1'].get('points', None),
            pointsHome=data['scoreStats']['1'].get('pointsHome', None),
            pointsAway=data['scoreStats']['1'].get('pointsAway', None),
            pointsLastSeason=data['scoreStats']['1'].get('pointsLastSeason', None),
            playedHome=player_data['data'].get('playedHome', 0),
            playedAway=player_data['data'].get('playedAway', 0),
            img=web_scraping.get_headshot(slug),
            demand=statitics[3],
            sale=statitics[4],
            use=statitics[5],
            reports_id=get_list_reports(player_data['data']['reports'], id, team_id),
            prices=player_data['data']['prices'],
            team_id=team_id,
            last_update=datetime.now()
        )

        return player


class Team_Round(fields.EmbeddedDocument):
    team_id = fields.IntField(null=True)
    name = fields.StringField(null=True)
    slug = fields.StringField(null=True)
    score = fields.IntField(null=True)
    last_update = fields.DateTimeField(null=True)

    @classmethod
    def builder(cls, data):
        team = Team_Round(
            team_id=data.get('id', None),
            name=data.get('name', None),
            slug=data.get('slug', None),
            score=data.get('score', None),
            last_update=datetime.now()
        )
        return team


class Match(CustomDocument):
    _id = fields.IntField(primary_key=True, required=True)
    date = fields.IntField(null=True)
    status = fields.StringField(null=True)
    round_id = fields.IntField(null=True)
    home = fields.EmbeddedDocumentField(Team_Round)
    away = fields.EmbeddedDocumentField(Team_Round)
    last_update = fields.DateTimeField(null=True)

    meta = {
        'collection': 'Matches'
    }

    @classmethod
    def builder(cls, data):
        m = Match(
            _id=data.get('id', None),
            date=data.get('date', None),
            status=data.get('status', None),
            round_id=Round.get_rounds(data['round']),
            home=Team_Round.builder(data['home']),
            away=Team_Round.builder(data['away']),
            last_update=datetime.now()
        )
        return m


class Round(CustomDocument):
    _id = fields.IntField(primary_key=True, required=True)
    name = fields.StringField(null=True)
    short = fields.StringField(null=True)
    last_update = fields.DateTimeField(null=True)

    meta = {
        'collection': 'Rounds'
    }

    @classmethod
    def get_rounds(cls, data):
        """
        Crea un objeto Round y lo guarda en BBDD. Si ya existe, lo devuelve.

        Args:
            kwargs (dict): Propiedades del objeto.

        Returns ():
            La instancia del objeto creado.
        """
        rounds = Round.objects(_id=data['id']).first()

        if not rounds:
            rounds = Round(
                _id=data.get('id', None),
                name=data.get('name', None),
                short=data.get('short', None),
                last_update=datetime.now()
            )
            rounds.update_()

        return str(rounds.id)


class Reports(CustomDocument):
    report_id = fields.IntField(null=True)
    status = fields.StringField(null=True)
    points = fields.IntField(null=True)
    picas = fields.StringField(null=True)
    mvp = fields.BooleanField(null=True)
    tie = fields.BooleanField(null=True)
    win = fields.BooleanField(null=True)
    lost = fields.BooleanField(null=True)
    yellowCard = fields.IntField(null=True)
    redCard = fields.IntField(null=True)
    goals = fields.IntField(null=True)
    goalsPenalty = fields.IntField(null=True)
    ownGoals = fields.IntField(null=True)
    events = fields.ListField(null=True)
    match_id = fields.IntField(null=True)
    player_id = fields.IntField(null=True)
    last_update = fields.DateTimeField(null=True)

    meta = {
        'collection': 'Reports',
        'indexes': [
            {'fields': ['report_id'], 'unique': True}
        ]
    }

    @classmethod
    def get_reports(cls, data, match, player, team_id):
        """
        Crea un objeto Round y lo guarda en BBDD. Si ya existe, lo devuelve.

        Args:
            kwargs (dict): Propiedades del objeto.

        Returns ():
            La instancia del objeto creado.
        """
        reports = Reports.objects(match_id=match, player_id=player).first()
        elements = []
        elements.append(data)
        elements.append(match)
        elements.append(player)

        if not reports:
            tie = data.get('tie', None)
            win = data.get('win', None)
            lost = data.get('lost', None)
            if win is None:
                result = get_result_match(match, team_id)
                win = result['win']
                lost = result['lost']
                tie = result['tie']
            reports = Reports(
                report_id=hash(str(elements)),
                status=data.get('status', None),
                points=data.get('points', None),
                picas=data.get('picas', None),
                mvp=data.get('mvp', None),
                tie=tie,
                win=win,
                lost=lost,
                yellowCard=data.get('yellowCard', None),
                redCard=data.get('redCard', None),
                goals=data.get('goals', None),
                goalsPenalty=data.get('goalsPenalty', None),
                ownGoals=data.get('ownGoals', None),
                events=data.get('events', None),
                match_id=match,
                player_id=player,
                last_update=datetime.now()
            )
            reports.update_()

        return str(reports.id)


def get_list_reports(reports, player, team_id):
    """
        Obtiene el conjunto de estadisticas de un jugador en cada uno de los partidos disputados.
        Args:
            reports (list): conjunto de estadisticas de cada partido
            player (int): id del jugador
            team_id (int): id del equipo al que pertenece el jugador
        Returns (str):
            list_reports (list): lista de ids de objetos Reports.t

    """
    list_reports = []
    for item in reports:
        points = item.get('points', None)
        raw_stats = item.get('rawStats', None)
        status = item.get('status', None)
        list_reports.append(Reports.get_reports({
                 "status": status.get('status', None) if status else "ok",
                 "points": points['1'] if points else None,
                 "picas": str(raw_stats.get('picas', None)) if raw_stats else None,
                 "mvp": raw_stats.get('mvp', False) if raw_stats else None,
                 "tie": raw_stats.get('tie', False) if raw_stats else None,
                 "win": raw_stats.get('win', False) if raw_stats else None,
                 "lost": raw_stats.get('lost', False) if raw_stats else None,
                 "yellowCard": raw_stats.get('yellowCard', 0) if raw_stats else None,
                 "redCard": raw_stats.get('redCard', 0) if raw_stats else None,
                 "goals": raw_stats.get('goals', 0) if raw_stats else None,
                 "goalsPenalty": raw_stats.get('goalsPenalty', 0) if raw_stats else None,
                 "ownGoals": raw_stats.get('ownGoals', 0) if raw_stats else None,
                 "events": item.get('events', None)},
            item['match']['id'],
            player,
            team_id)
        )

    return list_reports


def get_lanzadores(lanzadores):
    """
        Obtiene todos los ids de los jugadores que existen en BD que coinciden con la lista de nombres
        Args:
            lanzadores (list): lista de nombres de jugadores
        Returns (str):
            lanz (list): lista de ids de jugadores
    """
    lanz = []
    for item in Player.objects(name__in=lanzadores):
        lanz.append(item.id)
    return lanz


def get_line_up_ids(players_line_up):
    """
        Obtiene todos los ids de los jugadores que existen en BD que coinciden con la lista de nombres
        Args:
            players_line_up (list): lista de nombres de jugadores
        Returns (str):
            lanz (list): lista de ids de jugadores
    """
    lanz = []
    for player in players_line_up:
        item = Player.objects(slug=player).first()
        lanz.append(item['_id'])
    return lanz


def get_result_match(match, team_id):
    """
    Recupera el resultado final en  base a un partido y un id de equipo concreto.
    Params:
        match: id del partido.
        team_id: id del equipo.
    Return (dict):
        Devuelve el estado de los tres posibles resultados finales en formato booleano.
    """
    match = Match.objects(_id=match).first()
    win = False
    tie = False
    lost = False
    if match.home.score is not None:
        if match.home.score > match.away.score:
            if match.home.team_id == team_id:
                win = True
                tie = False
                lost = False
            else:
                win = False
                tie = False
                lost = True
        if match.home.score < match.away.score:
            if match.home.team_id == team_id:
                win = False
                tie = False
                lost = True
            else:
                win = True
                tie = False
                lost = False
        if match.home.score == match.away.score:
            win = False
            tie = True
            lost = False
        return {"win": win, "tie": tie, "lost": lost}
    else:
        return {"win": None, "tie": None, "lost": None}


def get_next_match(slug):
    """
    Realiza una busqueda en BD para definir cual es el próximo partido en base a un equipo dado.
    Params:
        slug: slug del equipo.
    Return (dict):
        Devuelve el id del próximo partido.
    """

    match_home = Match.objects.filter((Q(status="pending") | Q(status="preview")))(home__slug=slug).order_by('date')
    match_away = Match.objects.filter((Q(status="pending") | Q(status="preview")))(away__slug=slug).order_by('date')

    if match_home[0].date > match_away[0].date:
        return match_away[0].id
    else:
        return match_home[0].id
