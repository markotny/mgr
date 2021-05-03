import pickle
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import load_clean_df, drop_text, load_file, model_path

df = load_clean_df()
df = drop_text(df)

pickle.dump(df, open('cache/data.pkl', 'wb'))

# from bertopic import BERTopic
# from sentence_transformers import SentenceTransformer
# import pandas as pd
# topic_model = BERTopic.load(f'{model_path}model.pkl', embedding_model=SentenceTransformer("xlm-r-distilroberta-base-paraphrase-v1"))

# plot_topics = topic_model.visualize_topics()
# pickle.dump(plot_topics, open('cache/plots/topics.pkl', 'wb'))

# topics_over_time = pd.read_csv('topics_over_time.csv', index_col=0)

# plot_topics_over_time = topic_model.visualize_topics_over_time(topics_over_time, top_n=30)

# pickle.dump(topics_over_time, open('cache/plots/topics_over_time.pkl', 'wb'))
