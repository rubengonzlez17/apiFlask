# -*- coding: iso-8859-1 -*-
import os

from flask import jsonify


def _get_data_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", name)


def make_response(status, message):
    """
    Crea una respuesta del servidor

    Args:
        status (int): Código de estado cf. https://es.wikipedia.org/wiki/Anexo:C%C3%B3digos_de_estado_HTTP
        message (str): Mensaje

    Returns (dict):
        Diccionario con la respuesta del servidor
    """

    message = {
            'status': status,
            'message': message
    }
    resp = jsonify(message)
    resp.status_code = status

    return resp


def normalize(name):
    """
        Elimina los acentos.
        Args:
            name (str): nombre a convertir.
        Returns (str):
            nombre convertido
    """
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("à", "a"),
        ("è", "e"),
        ("ì", "i"),
        ("ò", "o"),
        ("ù", "u"),
    )
    if name:
        for a, b in replacements:
            name = name.replace(a, b).replace(a.upper(), b.upper())
    return name


def normalize_list(list_names):
    """
        Elimina los acentos en una lista de nombres.
        Args:
            list_names (list): lista de nombres a convertir
        Returns (str):
            lista de nombres convertidos
    """
    i = 0
    for item in list_names:
        list_names[i] = normalize(item)
        i = i+1
    return list_names
