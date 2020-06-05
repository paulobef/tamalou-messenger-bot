"""
Author: Romain Benassi
Date: 29/05/2020
"""
import fasttext.util
import numpy as np
import tensorflow as tf
import re


# fonction auxiliaire de nettoyage de texte
def remove_ponctuation(s: str):
    s=s.replace("!","")
    s=s.replace(".","")
    s=s.replace(",","")
    s=s.replace(";","")
    s=s.replace(";","")
    s=s.replace("?","")
    s=s.replace("/","")
    s=s.replace("#","")
    return s


# on charge le fichier qui permet de faire passer les textes dans un espace vectoriel à 300 dimensions (via un modèle pré-entrainé par équipe IA de Facebook)
ft = fasttext.load_model('flaskr/ml_models/cc.fr.300.bin')


# on definit la structure qui va contenir les valeurs de prediction pour chaque thème
# vecteur des topics d'interet
vect_topics = ["Humeur", "Inquiétude", "Temporalité", "Contexte", "Evolution", "Intensité"]

# on charge dans un dictionnaire l'ensemble des modèles pré-entrainés
dict_model = dict()

# pour chaque topic, on enregistre dans le dictionnaire le modèle associé
for topic in vect_topics:
    name_model = "my_model_"+topic+".h5"
    dict_model[topic] = tf.keras.models.load_model('flaskr/ml_models/'+name_model)


# on définit la fonction qui permet de calculer les scores (bruts) pour un texte donné sur l'ensemble des thèmes
# input : 
# - text : la chaîne de caractères correspondant au texte à analyser
# - nb_rank_word : argument optionnel (par défaut 4) qui correspond au rang du mot de référence pour calculer le score
# (par exemple nb_rank_word=4 revient à considérer le 4ième mot, pour le texte en entrée, au score le plus élevé comme référence
# pour un thème donné)
# output :
# - un dictionnaire dont les clés correspondent aux thèmes d'intérêt et les valeurs associées correspondent aux scores bruts
def topic_scoring(text: str, nb_rank_word = 4):
    
    # on enleve la ponctuation du texte
    text_np = remove_ponctuation(text)
    # on recupere l'ensemble des mots 
    all_words =  text_np.split(" ")
    # on calcule les embeddings sur chaque mots
    all_words_embeddings = list(map(lambda word: ft.get_word_vector(word),all_words))
    # on initialise la valeur de sortie qui correspond à un dictionnaire avec une valeur de score par thème
    dict_score_topic = dict()
    for topic_of_interest in vect_topics:
        model_topic = dict_model[topic_of_interest]
        
        # on calcule la valeur du modele pour l'ensemble des mots
        value_model = tf.get_static_value(model_topic.predict(np.asarray(all_words_embeddings)))
        value_model_prob = list(map(lambda x: x[1],value_model))
        
        # on recupere la valeur de proba du nb_rank_word mot au meilleur score
        value_model_prob_sorted_decreasing = sorted(value_model_prob, reverse=True)
        val_score = value_model_prob_sorted_decreasing[nb_rank_word-1]
        # on remplit le dictionnaire avec la valeur de score trouvée pour le thème courant
        dict_score_topic[topic_of_interest] = val_score
    
    return(dict_score_topic)

"""
# TODO: Write this as a test
# Exemple d'utilisation sur un texte issu du corpus Tamalou
text_in = "Bonjour, Pour ma part j'utilise de l'anti cernes uniquement en cas d'imperfections sut le visage. J'ai pourtant des cernes très marquées, avec en plus une peau très fine et des veines assez visibles. J'ai pourtant arrêté de les camoufler. Je trouve que finalement, elles donnent plus de caractère à mon visage. C'est peut être bizarre mais j'aime bien avoir des cernes. Bonne journée! "
topic_scoring(text_in)

{'Humeur': 0.37693778,
 'Inquiétude': 0.2803338,
 'Temporalité': 0.745019,
 'Contexte': 0.99979943,
 'Evolution': 0.37456134,
 'Intensité': 0.22265926}
"""
