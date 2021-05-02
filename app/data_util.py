
import numpy as np
import pickle

def load_data():
    df = pickle.load(open('cache/data.pkl','rb'))

    topics = load_topics()
    df['opis tematu'] = [topics[t] for t in df.temat]

    topic_sizes = df.temat.value_counts().to_dict()
    df['rozmiar tematu'] = [topic_sizes[t] for t in df.temat]

    df['temat_str'] = df['temat'].astype(str)
    
    e2d = np.asarray(df['embedding_2d'].to_list())
    e3d = np.asarray(df['embedding_3d'].to_list())

    df['2x'] = e2d[:,0]
    df['2y'] = e2d[:,1]

    df['3x'] = e3d[:,0]
    df['3y'] = e3d[:,1]
    df['3z'] = e3d[:,2]

    return df

def load_topics():
    return pickle.load(open('/data/model/iii/topic-words.pkl', 'rb'))

def load_plot_topics():
    return pickle.load(open('cache/plots/topics.pkl', 'rb'))

def load_plot_topics_over_time():
    return pickle.load(open('cache/plots/topics_over_time.pkl', 'rb'))

