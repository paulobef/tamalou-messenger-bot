"""
Author: Romain Benassi
Date: 29/05/2020
"""
import numpy as np
import pandas as pd
import fasttext.util
from keras.utils import np_utils
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dropout, Dense


# fonction auxiliaire de nettoyage de texte
def remove_ponctuation(s):
    s=s.replace("!","")
    s=s.replace(".","")
    s=s.replace(",","")
    s=s.replace(";","")
    s=s.replace(";","")
    s=s.replace("?","")
    s=s.replace("/","")
    s=s.replace("#","")
    return s


# on charge les données associées au corpus Tamalou
df=pd.read_excel('tamalou_6_topics 11052020.xlsx')
df.head()


# on filtre sur les seuls lignes traitees
df_traites = df[df.traites==1]

# on filtre sur les lignes d'interet (en francais) et correspondant aux autres contraintes voulues
list_themes = ["GL_Demande_daide", "GL_Temoignage__Expérien"]
df_fr = df_traites[np.logical_and(df_traites.LG=="fr" , list(map(lambda x: x in list_themes, df_traites.GL)))]

# on fait quelques print pour vérifier que les filtrages ont bien été efficaces et nous permettent de ne récupérer que les 
# lignes voulues
print(set(df_fr.LG))
print(set(df_fr.GL))
print(set(df_fr.traites))
print(len(df_fr.LG))


# on charge le fichier qui permet de faire passer les textes dans un espace vectoriel à 300 dimensions (via un modèle pré-entrainé par équipe IA de Facebook)
ft = fasttext.load_model('cc.fr.300.bin')


# on recupere l'ensemble des mots de chaque texte du corpus
all_words = list(map(lambda x: remove_ponctuation(x).split(" "),df_fr['Corpus']))
# on calcule l'embedding (ie la représentation en 300 dimensions) de chacun des mots (chaque ligne contient l'embedding de chaque mot du texte concerné)
all_words_embeddings = list(map(lambda row : list(map(lambda word: ft.get_word_vector(word),row)),all_words))
# on affiche la représentation du premier mot du premier texte
print(all_words_embeddings[0][0])


# vecteur des thèmes d'interet
vect_topics = ["Humeur", "Inquiétude", "Temporalité", "Contexte", "Evolution", "Intensité"]

# on choisit l'un des thèmes
# l'ensemble des traitements ci-dessous s'effectuent alors sur ce seul thème
topic_of_interest = vect_topics[2]
# on affiche le thème sélectionné
print(topic_of_interest)


# on transforme en {0, 1} l'appartenance ou non au theme choisi (sans cela, on recupererait des 1 et des NaN)
y_topic = list(map(lambda x: 0.0 if np.isnan(x) else x, df_fr[topic_of_interest]))
# on effectue un one hot encoding (non obligatoire mais pour faciliter l'utilisation du réseau de neurones)
y_one_hot= np_utils.to_categorical(y_topic)
# on affiche le résultat de l'enconding
print(y_one_hot)


# nous "déplions" la donnée pour ne plus raisonner au niveau du texte mais du mot
# autrement dit, nous construisons une nouvelle structure avec autant de lignes que de mots
# (alors que jusqu'à présent, chaque ligne correspondait à un texte)

# on va associer chaque valeur de y_topic a chaque mot du texte concerne
length_values = len(y_one_hot)

# initialisation des vecteurs qui seront utilisés en entrée du réseau de neurones
# X : correspond au vecteur dont chaque ligne correspond à une représentation d'un mot dans l'espace à 300 dimensions
# Y : correspond à un vecteur dont chaque ligne correspond à l'appartenance au non du mot au thème sélectionné
X = list()
Y = list()

# on parcourt l'ensemble des mots pour remplir les deux structures X et Y
for i in range(length_values):
    # on recupere l'ensemble des embeddings mots du texte i
    word_embedding_in_text = all_words_embeddings[i]
    # on parcourt l'ensemble des mots
    for word_embed in word_embedding_in_text:
            X.append(word_embed)
            Y.append(y_one_hot[i])

# on transforme les deux structures en array pour leur permettre d'être reconnu en entrée du réseau de neurones
X = np.asarray(X)
Y = np.asarray(Y)
# on affiche la représentation du premier mot dans l'espace à 300 dimensions
print(X[0])


#------- Définition du réseau de neurones
# il y a deux neurones sur la dernière couche (probabilité d'appartenance et de non appartenance au thème)
nb_neurons_last_layer = 2
# nous choisissons le nombre de neurones utilisés dans les couches profondes (grandeur que l'on peut faire varier)
nb_neurons = 512
# la dimension d'entrée correspond à la dimension de la représentation vectoriel des mots (ici 300 via l'utilisation de l'embedding)
input_length = 300
# nous définissons la structure du réseau de neurones
model = Sequential()
model.add(Dense(nb_neurons, input_shape=(input_length,), activation='relu'))
model.add(Dropout(rate=0.25))
model.add(Dense(nb_neurons, input_shape=(nb_neurons,), activation='relu'))
model.add(Dropout(rate=0.25))
model.add(Dense(nb_neurons, input_shape=(nb_neurons,), activation='relu'))
model.add(Dropout(rate=0.25))
model.add(Dense(nb_neurons, input_shape=(nb_neurons,), activation='relu'))
model.add(Dropout(rate=0.25))
model.add(Dense(nb_neurons_last_layer, input_shape=(nb_neurons,), activation='softmax'))
# affichage du résumé des caractéristiques définies
model.summary()

# configuration de l'optimiseur, de la fonction de coût et de la métrique associés à la phase d'apprentissage
optimizer=tf.keras.optimizers.Adam()
  
model.compile(optimizer=optimizer,
              loss='categorical_crossentropy', 
              metrics=["acc"]
             )

# apprentissage du modèle défini sur les données (X, Y) construites plus haut
history_model = model.fit(x=X, y = Y, epochs=100, batch_size=100)


# sauvegarde du modèle entraîné
model.save('my_model_'+topic_of_interest+'.h5')

