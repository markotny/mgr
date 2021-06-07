from bertopic import BERTopic
import pandas as pd
from sentence_transformers import SentenceTransformer
import pickle

model_path = 'model/iii/lexrank-weighted/'

topic_model = BERTopic.load(f'{model_path}model.pkl', embedding_model=SentenceTransformer("xlm-r-distilroberta-base-paraphrase-v1"))

topics_over_time = pd.read_csv(model_path + 'topics_over_time.csv', index_col=0)

plot_topics_over_time = topic_model.visualize_topics_over_time(topics_over_time, top_n=30)

pickle.dump(plot_topics_over_time, open('plot_topics_over_time.pkl', 'wb'))
