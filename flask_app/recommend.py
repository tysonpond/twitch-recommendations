import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

DATA_DIR = "data/best_model"
with open(os.path.join(DATA_DIR, "lfm_with_itemfeats_best.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(DATA_DIR, "train_user_items.pkl"), "rb") as f:
    train_user_items = pickle.load(f)
with open(os.path.join(DATA_DIR, "item_features.pkl"), "rb") as f:
    item_features = pickle.load(f)
with open(os.path.join(DATA_DIR, "encode_streamer.pkl"), "rb") as f:
    encode_streamer = pickle.load(f)
    
decode_streamer = {encode_streamer[x]:x for x in encode_streamer}
n_items = 1904

def similar_items(item_id, item_features, model, N=5):
    N += 1 # generate N+1 recommendations and remove the item_id
    item_representations = item_features.dot(model.item_embeddings)

    # Cosine similarity
    scores = item_representations.dot(item_representations[item_id, :])
    item_norms = np.linalg.norm(item_representations, axis=1)
    scores /= item_norms

    best = np.argpartition(scores, -N)[-N:]
    best_tuples = sorted(zip(best, scores[best] / item_norms[item_id]), key=lambda x: -x[1])
    return [decode_streamer[x] for x,i in best_tuples if x != item_id][:N]

def recommend_by_user_CF(follows_ID, N=5):
    # generate interaction vector
    interactions = np.zeros(n_items)
    for ind in follows_ID:
        interactions[ind] = 1

    # get most similar user in training data
    user_sim_scores = cosine_similarity(interactions.reshape(1,-1), train_user_items)
    most_sim_user_ID = np.argmax(user_sim_scores)

    # make recommendations
    recs = model.predict(user_ids=[most_sim_user_ID], item_ids=list(range(n_items)), \
                    user_features=None, item_features=item_features)
    recs = [(decode_streamer[i],x) for i,x in enumerate(recs) if i not in follows_ID] # convert streamer_ID back to streamer_name
    recs = sorted(recs, key=lambda x: -x[1])[:N] # sort by score
    recs = list(list(zip(*recs))[0]) # remove the scores 
    
    return recs

def recommend(follows, N=5):
    if len(follows) < 1:
        return ["Enter a valid streamer"]
    
    else:
        follows_ID = [encode_streamer[x] for x in follows if x in encode_streamer]
        if len(follows_ID) < 1:
            return ["Enter a valid streamer"]
        elif len(follows_ID) == 1:
            return similar_items(item_id=follows_ID[0], item_features=item_features, model=model, N=N)
        else:
            return recommend_by_user_CF(follows_ID, N=N)