from glob import glob
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
import re

def generate_posl_dict_2019(okregi):
    link = 'https://pl.wikipedia.org/wiki/Posłowie_na_Sejm_Rzeczypospolitej_Polskiej_IX_kadencji'
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    tab_kluby = soup.find_all("table")[3]
    posl_klub = {}
    for c in tab_kluby.tbody.children:
        if (c == '\n'):
            continue
        klub = c.find("th")
        if klub is not None:
            curr_klub = klub.contents[0].strip()
        else:
            posly = {p.text: curr_klub for p in c.find_all("a")}
            posl_klub.update(posly)
    
    tab_listy = soup.find_all("table")[7]
    all_posly = {}

    for c in tab_listy.tbody.children:
        if (c == '\n'):
            continue
        woj = c.find("h3")
        if woj is not None:
            curr_woj = woj.find("span", {'class': 'mw-headline'}).text
        elif c.find(lambda tag: tag.has_attr('href')) is None:
            continue
        else:
            okreg = okregi[c.find("a").text]
            listy = c.find_all("td", {'valign': 'top'})
            for l in listy:
                lista = l.find("a")['title'].strip()
                posly = {p.text: [okreg, posl_klub.get(p.text, posl_klub.get(p['title'], '')), lista, None] for p in l.find("span").find_all(lambda tag: tag.has_attr("title"))}
                all_posly.update(posly)
    
    return all_posly

def generate_posl_dict():
    kadencje = {}
    folder = 'posl/'
    for path_kadencja in sorted(glob(folder + '[12]*')):
        kadencja = path_kadencja[len(folder):]
        if os.path.exists(f'{folder}dict_{kadencja}'):
            poslowie_kadencji = load_posl_dict(kadencja)
        else:
            with open(path_kadencja, 'r') as kad:
                doc = BeautifulSoup(kad, 'html.parser')
            
            poslowie_kadencji = {}

            for link in doc.find_all(lambda tag: tag.has_attr('href'))[1:]:
                res = requests.get("http://orka.sejm.gov.pl" + link.get('href'))
                res.encoding='ISO-8859-2'
                soup = BeautifulSoup(res.text, 'html.parser')

                klub = soup.find('td', {'class': 'Klub'}).text.strip()

                lista = soup.find('p', string='Lista:')
                if lista is not None:
                    lista = lista.find_next_sibling('p').text.strip()

                partia = soup.find('p', string='Partia (wybory): ')
                if partia is not None:
                    partia = partia.find_next_sibling('p').text.strip()

                okreg = soup.find('p', string='Okręg wyborczy: ')
                if okreg is not None:
                    okreg = okreg.find_next_sibling('p').text.strip()

                # move surname to end
                posel = link.getText()
                names = posel.split(' ')
                names.append(names.pop(0))
                posel = ' '.join(names)

                poslowie_kadencji[posel] = [okreg, klub, lista, partia]

            with open(f'{folder}dict_{kadencja}', 'w') as f:
                print(poslowie_kadencji, file=f)

        rok = kadencja[:4]
        kadencje[rok] = poslowie_kadencji
        print('loaded kad', rok)

    okregi = {okreg.split(' ')[0]: okreg for [okreg, klub, lista, partia] in kadencje['2015'].values()}

    kadencje['2019'] = generate_posl_dict_2019(okregi)

    with open(f'{folder}dict_all','w') as f:
        print(kadencje, file=f)

def load_posl_dict(kadencja = 'all'):
    with open(f'posl/dict_{kadencja}','r') as fr:
        content = fr.read()
        posl_dict = eval(content)
    return posl_dict

def clean_data(df):
    df.fillna("",inplace=True)
    df['okreg'] = [o and re.sub(r'^\d+ ', '', o) for o in df['okreg']]
    df['okreg'] = df['okreg'].replace(
        ['044', 'Bielsko Biała', 'Bielsko- Biała', 'Kędzierzyn Koźle', 'Skarżysko Kamienna'],
        ['Koźle', 'Bielsko-Biała','Bielsko-Biała', 'Kędzierzyn-Koźle', 'Skarżysko-Kamienna'])
    df['okreg'] = df['okreg'].replace(
        ['Kraków Nowa Huta', 'Kraków Nowa-Huta', 'Kraków Podgórze','Kraków Śródmieście','Kraków-Miasto', 'Kraków-Nowa Huta', 'Kraków-Podgórze', 'Kraków-Województwo', 'Kraków-Śródmieście'],
        'Kraków')
    df['okreg'] = df['okreg'].replace(
        ['Poznań Grunwald', 'Poznań Nowe Miasto', 'Poznań Nowe-Miasto', 'Poznań Stare Miasto', 'Poznań Stare-Miasto', 'Poznań-Grunwald', 'Poznań-Nowe Miasto', 'Poznań-Stare Miasto'],
        'Poznań')
    df['okreg'] = df['okreg'].replace(
        ['Warszaw-Ochota', 'Warszawa', 'Warszawa - Praga Północ', 'Warszawa - Wola', 'Warszawa Ochota', 'Warszawa Praga Północ', 'Warszawa Praga-Południe', 'Warszawa Praga-Północ',
        'Warszawa Praga-Sródmieście', 'Warszawa Praga-Śródmieście', 'Warszawa Wola', 'Warszawa Śródmiećcie', 'Warszawa Śródmieście', 'Warszawa-Mokotów', 'Warszawa-Ochota', 'Warszawa-Praga',
        'Warszawa-Praga Południe', 'Warszawa-Praga Północ', 'Warszawa-Praga Śródmieście', 'Warszawa-Sródmieście', 'Warszawa-Stare Miasto', 'Warszawa-Wola', 'Warszawa-Śródmieście', 'Warszawa-Śrómieście', 'Warszawa-Żoliborz', 'Warszwa Wola'],
        'Warszawa')
    df['okreg'] = df['okreg'].replace(
        ['Wrocław Fabryczna', 'Wrocław I', 'Wrocław II', 'Wrocław Krzyki', 'Wrocław Śródmieście', 'Wrocław-Fabryczna', 'Wrocław-Krzyki', 'Wrocław-Miasto', 'Wrocław-Psie Pole', 'Wrocław-Województwo'],
        'Wrocław')
    df['okreg'] = df['okreg'].replace(
        ['Łodź-Miasto', 'Łódź - Bałuty', 'Łódź Bałuty', 'Łódź Śródmieście', 'Łódź-Bałuty', 'Łódź-Bałuty i Polesie', 'Łódź-Chojne', 'Łódź-Chojny', 'Łódź-Górna', 'Łódź-Miasto', 'Łódź-Polesie', 'Łódź-Widzew', 'Łódź-powiat', 'Łódź-Śródmieńcie', 'Łódź-Śródmieście'],
        'Łódź')
    df['okreg'] = df['okreg'].replace(
        ['Lista Kr\x01ajowa','Lista Krajowa', 'lista państwowa nr 1', 'lista państwowa nr 2', 'lista państwowa nr 3', 'lista państwowa nr 4'],
        '')

def posl_dict_to_df():
    posl_dict = load_posl_dict()

    all_posly = []
    for (rok, posly) in posl_dict.items():
        for (posel, [okreg, klub, lista, partia]) in posly.items():
            all_posly.append([rok, posel, okreg, klub, lista, partia])

    df = pd.DataFrame(all_posly, columns=["rok", "posel", "okreg", "klub", "lista", "partia"])

    clean_data(df)
    df.to_csv('parsed/posl.csv')

    return df

def load_posl_df():
    if os.path.isfile('parsed/posl.csv'):
        return pd.read_csv('parsed/posl.csv', index_col=0, na_filter=False)
    elif os.path.isfile('posl/dict_all'):
        return posl_dict_to_df()
    else:
        generate_posl_dict()
        return posl_dict_to_df()