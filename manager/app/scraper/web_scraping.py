# -*- coding: iso-8859-1 -*-
import requests
from bs4 import BeautifulSoup
from manager.utils import normalize_list
from manager.app.player import player_model

scraper_endpoints = {
    'url_team': 'https://www.infobiwenger.com/equipos/',
    'url_players': 'https://biwenger.as.com/blog/jugadores/',
    'url_player': 'https://www.infobiwenger.com/jugador/',
    'test': 'https://www.infobiwenger.com/'
}

headers_scraper = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
}


def test():
    """
        Realiza una prueba de acceso a la web donde se realizará el scraping
        Returns (dict):
            Código de estado de respuesta HTTP
            cf. https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)
    """

    r = requests.get(scraper_endpoints['test'], headers=headers_scraper)
    if r.status_code == 200:
        return r.status_code
    else:
        return r.status_code


def get_headshot(slug_player):
    """
        Obtiene la imagen asociada a cada jugador mediante web scraping.
        Args:
            slug_player (str): slug del nombre del jugador
        Returns (str):
            img (str): imagen del jugador.
    """

    try:
        page = scraper_endpoints['url_player'] + slug_player
        page_tree = requests.get(page, headers=headers_scraper)
        page_soup = BeautifulSoup(page_tree.content, 'html.parser')
        img = page_soup.find("img", {"class": "jugador-ficha-foto"})
        return img['src']
    except ConnectionError as e:
        print("Exception is :", e)


def get_statitics(slug_player):
    """
        Obtiene una lista de estadisticas asociadas a un jugador mediante web scraping.
        Args:
            slug_player (str): slug del nombre del jugador
        Returns (str):
            list_statitics (list): lista de estadisticas en formato str.
    """
    try:
        page = scraper_endpoints['url_players'] + slug_player + "/"
        page_tree = requests.get(page, headers=headers_scraper)
        page_soup = BeautifulSoup(page_tree.content, 'html.parser')

        statitics = page_soup.find_all("div", {"class": "player-stat"})
        list_statitics = []
        item = 0
        for i in range(len(statitics)):
            list_statitics.append(statitics[i].find("span").text.strip())
            item = item + 1
            if item == 6: break

        return list_statitics
    except ConnectionError as e:
        print("Exception is :", e)


def scraper_team(team):
    """
        Obtiene datos sobre un equipo mediante web scraping
        Args:
            team (str): slug del nombre del equipo
            team_id (int): identificador del equipo
        Returns (obj):
            Objeto JSON compuesto por:
                escudo (str): imagen del escudo asociado al equipo.
                fouls (list): lista de ids de los jugadores que lanzan las faltas en el equipo.
                penalties (list): lista de ids de los jugadores que lanzan los penaltis en el equipo.
                line_up (str): dibujo táctico que suele usar el equipo.
                line_up_players (list): lista de los ids de los jugadores que conforman el once titular del equipo.
    """
    try:
        page = scraper_endpoints['url_team'] + team
        page_tree = requests.get(page, headers=headers_scraper)
        page_soup = BeautifulSoup(page_tree.content, 'html.parser')

        fouls = page_soup.find("div", {"class", "lista-lanzadores-falta"})
        penalties = page_soup.find("div", {"class", "lista-lanzadores-penalti"})
        shield = page_soup.find("img", {"class", "equipo-escudo-main"})
        campo = page_soup.find("div", {"class", "campo"})
        linea_delantera = campo.find("div", {"class", "linea delantera"})
        linea_media = campo.find("div", {"class", "linea media"})
        linea_defensa = campo.find("div", {"class", "linea defensa"})
        linea_porteria = campo.find("div", {"class", "linea porteria"})
        list_players_line_up = []
        create_line_up(list_players_line_up, linea_porteria, linea_defensa, linea_media, linea_delantera)

        return {
            "escudo": shield['src'],
            "fouls": normalize_list(fouls.text.strip().split(", ")),
            "penalties": normalize_list(penalties.text.strip().split(", ")),
            "line_up": get_line_up(linea_defensa, linea_media, linea_delantera),
            "line_up_players": player_model.get_line_up_ids(list_players_line_up)
        }
    except ConnectionError as e:
        print("Exception is :", e)


def get_list_line_up(list_players_line_up, players):
    """
        Devuelve una lista de los slugs de los jugadores que pertenecen a la alineacion habitual del equipo
    """
    try:
        players = players.find_all("a")
        for i in range(0, len(players), 2):
            list_players_line_up.append(get_slug_player(players[i]['href']))
        return list_players_line_up
    except ConnectionError as e:
        print("Exception is :", e)


def get_line_up(line1, line2, line3):
    """
        Devuelve un dibujo táctico en formato str. Ejemplo: "4-3-3"
    """
    line_up = str(get_num_players_line(line1)) + '-'
    line_up = line_up + str(get_num_players_line(line2)) + '-'
    line_up = line_up + str(get_num_players_line(line3))
    return line_up


def create_line_up(list_players, linea1, linea2, linea3, linea4):
    get_list_line_up(list_players, linea1)
    get_list_line_up(list_players, linea2)
    get_list_line_up(list_players, linea3)
    get_list_line_up(list_players, linea4)

    return list_players


def get_num_players_line(line):
    """
        Devuelve un int en relación con el número de jugadores que pertenecen a cada linea del dibujo táctico.
    """
    try:
        players = line.find_all('div', {'class': "jugador-once"})
        return len(players)
    except ConnectionError as e:
        print("Exception is :", e)


def get_slug_player(url):
    """
        Devuelve el slug del jugador.
    """
    url = url.split("/")
    return url[len(url) - 1]
