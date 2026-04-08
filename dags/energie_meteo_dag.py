from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pendulum
import requests
import logging
import json
from datetime import date


# Timezone Paris pour RTE
local_tz = pendulum.timezone("Europe/Paris")

# Coordonnées des 5 régions cibles
REGIONS = {
    "Île-de-France": {"lat": 48.8566, "lon": 2.3522},
    "Occitanie": {"lat": 43.6047, "lon": 1.4442},
    "Nouvelle-Aquitaine": {"lat": 44.8378, "lon": -0.5792},
    "Auvergne-Rhône-Alpes": {"lat": 45.7640, "lon": 4.8357},
    "Hauts-de-France": {"lat": 50.6292, "lon": 3.0573},
}

default_args = {
    "owner": "rte-data-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def verifier_apis(**context):
    apis = {
        "Open-Meteo": (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=48.8566&longitude=2.3522"
            "&daily=sunshine_duration&timezone=Europe/Paris&forecast_days=1"
        ),
        "éCO2mix": (
            "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
            "/eco2mix-regional-cons-def/records?limit=1&timezone=Europe%2FParis"
        ),
    }

    for nom, url in apis.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                raise ValueError(f"API {nom} indisponible — status code : {response.status_code}")
            logging.info(f"API {nom} disponible ✓")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API {nom} inaccessible — erreur réseau : {e}")

    logging.info("Toutes les APIs sont disponibles. Pipeline autorisé à continuer.")

def collecter_meteo_regions(**context):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    resultats = {}

    for region, coords in REGIONS.items():
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "daily": "sunshine_duration,wind_speed_10m_max",
            "timezone": "Europe/Paris",
            "forecast_days": 1,
        }

        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        ensoleillement = data["daily"]["sunshine_duration"][0] / 3600
        vent = data["daily"]["wind_speed_10m_max"][0]

        resultats[region] = {
            "ensoleillement_h": ensoleillement,
            "vent_kmh": vent,
        }

        logging.info(f"{region} → {ensoleillement:.1f}h de soleil, vent {vent:.1f} km/h")

    return resultats
def collecter_production_electrique(**context):
    BASE_URL = (
        "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
        "/eco2mix-regional-cons-def/records"
    )
    params = {
        "limit": 100,
        "timezone": "Europe/Paris",
    }

    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    records = response.json()["results"]

    accumulation = {region: {"solaire": [], "eolien": []} for region in REGIONS}

    for enregistrement in records:
        region = enregistrement.get("libelle_region")
        if region in REGIONS:
            solaire = float(enregistrement.get("solaire") or 0.0)
            eolien = float(enregistrement.get("eolien") or 0.0)
            accumulation[region]["solaire"].append(solaire)
            accumulation[region]["eolien"].append(eolien)

    production = {}
    for region in REGIONS:
        valeurs = accumulation[region]
        if valeurs["solaire"]:
            solaire_mw = sum(valeurs["solaire"]) / len(valeurs["solaire"])
            eolien_mw = sum(valeurs["eolien"]) / len(valeurs["eolien"])
        else:
            solaire_mw = 0.0
            eolien_mw = 0.0

        production[region] = {
            "solaire_mw": solaire_mw,
            "eolien_mw": eolien_mw,
        }
        logging.info(f"{region} → solaire {solaire_mw:.0f} MW, éolien {eolien_mw:.0f} MW")

    return production


def analyser_correlation(**context):
    ti = context["ti"]
    donnees_meteo = ti.xcom_pull(task_ids="collecter_meteo_regions")
    donnees_production = ti.xcom_pull(task_ids="collecter_production_electrique")

    alertes = {}
    for region in REGIONS:
        meteo = donnees_meteo.get(region, {})
        production = donnees_production.get(region, {})
        alertes_region = []

        ensoleillement = meteo.get("ensoleillement_h", 0)
        vent = meteo.get("vent_kmh", 0)
        solaire = production.get("solaire_mw", 0)
        eolien = production.get("eolien_mw", 0)

        # Règle 1
        if ensoleillement > 6 and solaire <= 1000:
            alertes_region.append(
                f"ALERTE SOLAIRE : {ensoleillement:.1f}h de soleil "
                f"mais seulement {solaire:.0f} MW produits"
            )

        # Règle 2
        if vent > 30 and eolien <= 2000:
            alertes_region.append(
                f"ALERTE ÉOLIEN : vent à {vent:.1f} km/h "
                f"mais seulement {eolien:.0f} MW produits"
            )

        # Bonus Règle 3
        if solaire > 0 and ensoleillement == 0:
            alertes_region.append(
                f"ANOMALIE DONNÉES : production solaire {solaire:.0f} MW "
                f"sans ensoleillement enregistré"
            )

        alertes[region] = {
            "alertes": alertes_region,
            "ensoleillement_h": ensoleillement,
            "vent_kmh": vent,
            "solaire_mw": solaire,
            "eolien_mw": eolien,
            "statut": "ALERTE" if alertes_region else "OK",
        }

    nb_alertes = sum(1 for r in alertes.values() if r["statut"] == "ALERTE")
    logging.warning(f"{nb_alertes} région(s) en alerte sur {len(REGIONS)} analysées.")
    return alertes

def generer_rapport_energie(**context):
    ti = context["ti"]
    analyse = ti.xcom_pull(task_ids="analyser_correlation")
    today = date.today().isoformat()

    print("\n" + "=" * 80)
    print(f" RAPPORT ENERGIE & METEO — RTE — {today}")
    print("=" * 80)
    print(
        f"{'Region':<25} {'Soleil (h)':>10} {'Vent (km/h)':>12} "
        f"{'Solaire (MW)':>13} {'Eolien (MW)':>12} {'Statut':>8}"
    )
    print("-" * 80)

    for region, data in analyse.items():
        print(
            f"{region:<25} {data['ensoleillement_h']:>10.1f} {data['vent_kmh']:>12.1f} "
            f"{data['solaire_mw']:>13.0f} {data['eolien_mw']:>12.0f} {data['statut']:>8}"
        )

    print("=" * 80 + "\n")

    rapport = {
        "date": today,
        "source": "RTE eCO2mix + Open-Meteo",
        "pipeline": "energie_meteo_dag",
        "regions": analyse,
        "resume": {
            "nb_regions_analysees": len(analyse),
            "nb_alertes": sum(1 for r in analyse.values() if r["statut"] == "ALERTE"),
            "regions_en_alerte": [
                r for r, d in analyse.items() if d["statut"] == "ALERTE"
            ],
        },
    }

    chemin = f"/tmp/rapport_energie_{today}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    logging.info(f"Rapport sauvegarde : {chemin}")
    return chemin

with DAG(
    dag_id="energie_meteo_dag",
    default_args=default_args,
    description="Corrélation météo / production énergétique — RTE",
    schedule="0 6 * * *",
    start_date=datetime(2024, 1, 1, tzinfo=local_tz),
    catchup=False,
    tags=["rte", "energie", "meteo", "open-data"],
) as dag:

    t1 = PythonOperator(task_id="verifier_apis", python_callable=verifier_apis)
    t2 = PythonOperator(task_id="collecter_meteo_regions", python_callable=collecter_meteo_regions)
    t3 = PythonOperator(task_id="collecter_production_electrique", python_callable=collecter_production_electrique)
    t4 = PythonOperator(task_id="analyser_correlation", python_callable=analyser_correlation)
    t5 = PythonOperator(task_id="generer_rapport_energie", python_callable=generer_rapport_energie)

    t1 >> [t2, t3] >> t4 >> t5
