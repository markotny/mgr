from bs4 import BeautifulSoup
from glob import glob
import os
import re
import numpy as np
import pickle


def load_data():
    df = pickle.load(open('cache/data.pkl', 'rb'))

    df['temat'] = df['temat'].astype(str)

    e2d = np.asarray(df['embedding_2d'].to_list())
    e3d = np.asarray(df['embedding_3d'].to_list())
    df.drop(columns=['embedding_2d','embedding_3d'], inplace=True)

    df['2x'] = e2d[:, 0]
    df['2y'] = e2d[:, 1]

    df['3x'] = e3d[:, 0]
    df['3y'] = e3d[:, 1]
    df['3z'] = e3d[:, 2]

    return df


def load_plot_topics():
    return pickle.load(open('cache/plots/topics.pkl', 'rb'))


def load_plot_topics_over_time():
    return pickle.load(open('cache/plots/topics_over_time.pkl', 'rb'))


def load_session(doc_id):
    session_id, speech_id = re.search(r"PPC-(.+)-(div-\d+)", doc_id).groups()
    cache_filename = f'cache/sessions/{session_id}.pkl'
    if os.path.exists(cache_filename):
        with open(cache_filename, 'rb') as f:
            title = pickle.load(f)
            texts = pickle.load(f)
        return title, texts, speech_id
    
    folders = glob('../corpus/*/sejm/posiedzenia/pp/' + session_id)
    if len(folders) != 1:
        return None, *3

    title, texts = _parse_folder(folders[0])
    with open(cache_filename, 'wb') as f:
        pickle.dump(title, f)
        pickle.dump(texts, f)

    return title, texts, speech_id


def _parse_folder(folder):
    with open(os.path.join(folder, "header.xml"), 'r') as header_file:
        header = BeautifulSoup(header_file, 'lxml')

    title = header.find("title").text
    speakers = {x["xml:id"]: x.text.strip() for x in header.find_all("person")}

    with open(os.path.join(folder, "text_structure.xml"), 'r') as data_file:
        data = BeautifulSoup(data_file, 'lxml')

    divs = data.find_all('div')

    texts = [{'id': div["xml:id"], 'speeches': [{'speaker': speakers[u['who'][1:]],
                                                 'text': u.text} for u in div.find_all('u')]} for div in data.find_all('div')]
    return title, texts
