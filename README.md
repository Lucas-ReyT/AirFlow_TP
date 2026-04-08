Screen :
<img width="1907" height="781" alt="image" src="https://github.com/user-attachments/assets/d27edc6c-b7b1-4e0f-a886-2767ed9c6a0b" />
 Interface Airflow UI avec le DAG energie_meteo_dag visible et en état succes


<img width="1903" height="758" alt="image" src="https://github.com/user-attachments/assets/64351d90-e98a-4be5-8e78-c1267ded6c1a" />
 Vue Graph du DAG montrant les 5 tâches et leurs dépendances

<img width="1524" height="567" alt="image" src="https://github.com/user-attachments/assets/55809b68-c1fd-44ba-8f5b-d940a6bb32b4" />

<img width="1541" height="230" alt="image" src="https://github.com/user-attachments/assets/52f4ee85-d6ff-4f2e-96e8-70e7eedab7cf" />

<img width="987" height="970" alt="image" src="https://github.com/user-attachments/assets/69fd38dd-6765-43eb-a464-cb978fe89ea7" />


Q1 — Docker Executor Le docker-compose.yaml utilise LocalExecutor . Expliquez la différence entre
LocalExecutor , CeleryExecutor et KubernetesExecutor . Dans quel contexte de production RTE devrait-il
utiliser chacun ? Quelles sont les implications en termes de scalabilité et de ressources ?
---


LocalExecutor : en local sur la machine. Il permet donc d'être facilement mis en place sans dépendances etc, mais dfficilement scalable
=> (Bien pour notre TP)

CeleryExecutor : Plusieurs worker, donc plus fiable si une panne sur un worker et scalabilité meilleure. Mais infastructure plus complexe à mettre en place  
=> Bien pour projet moyen

KubernetesExecutor : Pod Kubernetes pour CHAQUE tâche, détruit une fois terminé. Permet d'isoler chaque tâche et scalabilité au max, consommation de ressource en fonction de la demande.
Mais très complexe nioveau infrastructure + nécessite un cluster dédié donc très gourmand.
=> Bien pour un projet à très grande échelle.

Q2 — Volumes Docker et persistance des DAGs Le volume ./dags:/opt/airflow/dags permet de
modifier les DAGs sans redémarrer le conteneur. Expliquez le mécanisme sous-jacent (bind mount vs volume
nommé). Que se passerait-il si on supprimait ce mapping ? Quel serait l’impact en production sur un cluster
Airflow multi-nœuds (plusieurs workers) 
---

Blind mount = comme utilisé dans le tp, directement dans le chemin. Permet de voir directement les changements (Par ex : Airflow lit chaque 30 sec les nouveaux DAGS)
Volume nommé = dans une bdd, ex postgres. Permet de persister dans le container mais n'est pas accessible depuis la machine directement

Si on supprime le mapping dans ce cas : On perd tout. Plus rien ne serait visible 

Q3 — Idempotence et catchup Le DAG a catchup=False . Expliquez ce que ferait Airflow si
catchup=True et que le DAG est activé aujourd’hui avec un start_date au 1er janvier 2024. Qu’est-ce que
l’idempotence d’un DAG et pourquoi est-ce critique pour un pipeline de données énergétiques ? Comment
rendre les fonctions collecter_* idempotentes ?
---

Q4 — Timezone et données temps-réel L’API éCO2mix retourne des données horodatées. Pourquoi le
paramètre timezone=Europe/Paris est-il essentiel dans le contexte RTE ? Que peut-il se passer lors du
passage à l’heure d’été (dernier dimanche de mars) si la timezone n’est pas correctement gérée dans le
scheduler Airflow et dans les requêtes API ? Donnez un exemple concret de données corrompues ou
manquantes.
---
