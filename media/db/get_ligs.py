#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#+ Autor:  	Ran#
#+ Creado: 	2022/01/03 21:05:26.106045
#+ Editado:	2022/02/19 18:13:12.910833
# ------------------------------------------------------------------------------

import sys
#import requests as r
from bs4 import BeautifulSoup as bs
from bs4.element import ResultSet
from datetime import datetime
import sqlite3
from sqlite3 import Cursor
from secrets import token_urlsafe as tus
from typing import Optional, Dict, Union

from uteis.imprimir import jprint
from conexions import Proxy

import info_db

# ------------------------------------------------------------------------------

def get_url(pax: int) -> str:
    return f'https://coinmarketcap.com/?page={pax}'

def get_url_novos() -> str:
    return 'https://coinmarketcap.com/new'

def get_url_gan_per() -> str:
    return 'https://coinmarketcap.com/gainers-losers'

def get_url_trending() -> str:
    return 'https://coinmarketcap.com/trending-cryptocurrencies'

def get_url_mais_visitados() -> str:
    return 'https://coinmarketcap.com/most-viewed-pages'

def print_info_db() -> Dict[str, str]:
    print()
    info = info_db.main()
    print(f'{info["cantidade"]} entradas totais na DB.')
    print()

    return info

# ------------------------------------------------------------------------------

def scrape_auxiliar(cur: Cursor, paxina_web: str, info_db_ini: Dict[str, str], pax: Optional[Union[int, str]] = None) -> None:
    global num_engadidos
    cant_engadidos = num_engadidos

    soup = bs(paxina_web.text, 'html.parser')
    taboa = soup.find('table').tbody.find_all('tr')

    for indice, fila in enumerate(taboa, 1):
        # simbolo
        try:
            simbolo = fila.find(class_='crypto-symbol').text
        except:
            try:
                simbolo = fila.find(class_='coin-item-symbol').text
            except Exception as e:
                if DEBUG: print(f'Erro en simbolo: {e}')
                simbolo = 'Erro'
        # simbolo #

        # nome
        try:
            nome = fila.find_all('td')[2].text
            if simbolo not in nome:
                nome = fila.find_all('td')[1].text
            if nome.endswith('Buy'):
                nome = nome[:-3]

            if nome.endswith(simbolo):
                nome = nome[:-len(simbolo)]

            # podería dar problema se fose algo tipo Moeda1 o nome pero bueno
            if not nome.isdigit():
                while nome[-1].isdigit():
                    nome = nome[:-1]
        except Exception as e:
            if DEBUG: print(f'Erro en nome: {e}')
            nome = 'Erro'
        # nome #

        # ligazon
        try:
            ligazon = fila.find(class_='cmc-link').get('href')
        except Exception as e:
            if DEBUG: print(f'Erro en ligazon: {e}')
            ligazon = 'Erro'
        # ligazon #

        try:
            cur.execute('insert into moeda("simbolo", "nome", "ligazon", "data")'\
                f' values("{simbolo}", "{nome}", "{ligazon}", "{datetime.now()}")')
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            raise e
        else:
            if DEBUG:
                num_engadidos += 1
                if pax:
                    print(f'Engadido novo elemento da páxina {pax} coa IP {r.get_proxy().ip}')
                else:
                    print('Engadido novo elemento.')
                jprint({
                    'id': info_db_ini['cantidade']+num_engadidos,
                    'simbolo': simbolo,
                    'nome': nome,
                    'ligazon': ligazon
                    })

    return num_engadidos-cant_engadidos


def scrape(cur: Cursor, info_db_ini: Dict[str, str], auxiliar: str, r: Proxy) -> None:

    auxiliares = {
            'gan_per': ['gañadores/perdedores', get_url_gan_per()],
            'trending': ['trending', get_url_trending()],
            '+visit': ['máis visitados', get_url_mais_visitados()],
            'novos': ['novidades', get_url_novos()]
            }

    try:
        if DEBUG: print(f'{datetime.now()}\n* Páxina de {auxiliares[auxiliar][0]}')
        paxina_web = r.get(auxiliares[auxiliar][1])
    except KeyError:
        raise Exception('Páxina inexistente.')
    except Exception as e:
        raise e

    if paxina_web.status_code != 404:
        cant_engadidos = scrape_auxiliar(cur, paxina_web, info_db_ini, auxiliares[auxiliar][0])
        if DEBUG and cant_engadidos == 0:
            print(f'Non se engadiu ningunha entrada da páxina {auxiliares[auxiliar][0]}.')
    else:
        if DEBUG: print('Páxina inaccesíbel.')

    if DEBUG: print()

def scrape_inicio(cur: Cursor, info_db_ini: dict, r: Proxy) -> None:
    pax = 1

    if DEBUG: print(f'{datetime.now()}\n* Páxina principal')
    while True:
        if DEBUG:
            print(f'{datetime.now()} | Escrapeando a páxina {pax} coa IP {r.get_proxy().ip}')
        #if DEBUG: print(f'Escrapeando a páxina {pax} coa IP {r.get_ip().text.rstrip()}', end='\r')
        paxina_web = r.get(get_url(pax))

        if paxina_web.status_code == 404:
            if DEBUG:
                print('Máximo de páxinas alcanzado.')
                print(f'Escrapeadas un total de {pax-1} páxinas.')
            break

        try:
            scrape_auxiliar(cur, paxina_web, info_db_ini, pax)

            #con.commit()
            pax+=1

        except Exception as e:
            print(pax_web.text)
            if DEBUG: print(f'Erro: {e}'); print(f'Escrapeadas un total de {pax} páxinas')
            break

    if DEBUG: print()

# ------------------------------------------------------------------------------

def main():

    try:
        r = Proxy()
        con = sqlite3.connect(DB)
        cur = con.cursor()


        # mostrar os datos iniciais
        if DEBUG:
            print(datetime.now())
            info_db_ini = print_info_db()

        scrape(cur, info_db_ini, 'gan_per', r)
        scrape(cur, info_db_ini, 'trending', r)
        scrape(cur, info_db_ini, '+visit', r)
        scrape(cur, info_db_ini, 'novos', r)

        scrape_inicio(cur, info_db_ini, r)

        con.commit()
        con.close()

        if DEBUG:
            print(f'Engadidas un total de {num_engadidos} entradas.')
            print_info_db()
            print(datetime.now())
    except KeyboardInterrupt:
        print('\n\nPechando o programa')

        con.commit()
        con.close()

        if DEBUG:
            print(f'Engadidas un total de {num_engadidos} entradas.')
            print_info_db()
            print(datetime.now())

# ------------------------------------------------------------------------------

DEBUG = True
DB = 'ligazons.db'
num_engadidos = 0

if __name__ == '__main__':
    main()

# ------------------------------------------------------------------------------