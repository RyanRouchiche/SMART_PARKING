# Smart Parking

Application de gestion de parking intelligent. Des caméras filment les places de stationnement, un réseau de neurones (Keras) détermine pour chaque place si elle est **libre** ou **occupée**, et le résultat est affiché en temps réel dans une interface web : plan animé du parking, écran LCD des places libres, gestion des caméras et des utilisateurs.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide avec Docker](#démarrage-rapide-avec-docker)
- [Développement sans Docker](#développement-sans-docker)
- [Configuration](#configuration)
- [Utilisation de l'application](#utilisation-de-lapplication)
- [API](#api)
- [Fonctionnement de la détection](#fonctionnement-de-la-détection)
- [Authentification et rôles](#authentification-et-rôles)
- [Limites connues](#limites-connues)

## Fonctionnalités

| Page | Route | Accès | Rôle |
|---|---|---|---|
| Connexion / inscription | `/login` | public | Connexion, création d'un compte admin (activation par email) |
| Activation | `/activate/:uid/:token` | public | Lien reçu par email pour activer un compte |
| Accueil | `/` | connecté | Page d'accueil et accès aux services |
| Statut du parking | `/parking` | connecté | Plan animé par zone : les voitures entrent et sortent selon les prédictions |
| LCD | `/lcd` | connecté | Affichage simplifié du nombre de places libres et de leur direction |
| Gestion | `/management` | admin | Création de guests, liste des caméras, liste des utilisateurs (statut en ligne en direct) |
| Configuration caméras | `/setup` | admin | Ajout de 1 à 10 caméras (zone, référence, URL RTSP/HTTP) |
| Initialisation des places | `/spots` | admin | Dessin des places sur une capture de chaque caméra |

L'interface est disponible en **français** et en **anglais** (sélecteur dans la barre de navigation).

## Architecture

```
                    navigateur
                        │  http://localhost:8080
                        ▼
              ┌───────────────────┐
              │ client (nginx)    │  React compilé
              │ /api /ws /admin   │──────────────┐
              └───────────────────┘              │ proxy
                                                 ▼
                                        ┌───────────────────┐   ┌──────────────┐
                                        │ django            │──▶│ PostgreSQL   │
                                        │ API + WebSockets  │   └──────────────┘
                                        └─────────┬─────────┘           ▲
                                     abonnement   │                     │ zones
                                     zone_<p>_<n> ▼                     │
                                        ┌───────────────────┐   ┌──────────────┐
                                        │ Redis (Channels)  │◀──│ detection    │
                                        └───────────────────┘   │ 1 capture par│
                                                                │ zone         │
┌──────────────┐   HTTP POST /predict                           └──────┬───────┘
│ MODEL_SERVER │◀──────────────────────────────────────────────────────┤ OpenCV
│ Keras :8001  │   lot de crops (.npy)                                  ▼
└──────────────┘                                   caméras (RTSP / HTTP / fichier vidéo)
```

- **`client/`** : application React (Vite). Elle ne parle qu'à Django, via `/api` (HTTP) et `/ws` (WebSockets).
- **`server/DJANGO_SERVER/`** : API REST (Django REST Framework), WebSockets (Django Channels), authentification JWT. Le même code tourne en deux services :
  - `django` : API et WebSockets. Les WebSockets vidéo ne font que s'abonner aux résultats d'une zone.
  - `detection` (`python manage.py run_detection`) : capture chaque zone une seule fois, quel que soit le nombre de spectateurs, et publie l'occupation dans Redis. Il se répartit sur plusieurs instances avec `--shard` et `--shards`.
- **`server/MODEL_SERVER/`** : petit serveur HTTP (bibliothèque standard Python) qui charge le modèle Keras une seule fois et classe un lot d'images de places.
- **PostgreSQL** stocke les utilisateurs, les caméras et les tokens ; **Redis** sert de couche de messages à Channels.

## Structure du dépôt

```
SMART_PARKING/
├── client/                      Frontend React
│   ├── src/
│   │   ├── api.js               Appels API (refresh automatique du token) et WebSockets
│   │   ├── auth.jsx             Contexte d'authentification, garde des routes
│   │   ├── i18n.jsx             Traductions FR/EN
│   │   ├── components/          Navbar, modales (confirmation, saisie, notification)
│   │   ├── pages/               Une page par route
│   │   ├── styles/              Feuilles de style de chaque page
│   │   └── assets/              Images
│   └── vite.config.js           Proxy de développement vers Django
├── server/
│   ├── DJANGO_SERVER/
│   │   ├── smart_parking/       Settings, URLs, ASGI (assemblage des apps)
│   │   ├── users/               Comptes, sessions JWT, opérateurs, présence (WebSocket)
│   │   ├── camera/              Caméras, politique des sources (sources.py), captures
│   │   ├── parking/             Parkings, membres, zones, accès par parking, WebSocket vidéo
│   │   │   └── Spots/coordinates.json   Places du parking pilote (migration initiale)
│   │   ├── detection/           Géométrie des places, capture vidéo, client du modèle, worker
│   │   └── manage.py
│   └── MODEL_SERVER/
│       ├── server.py            Serveur HTTP (/health, /predict)
│       ├── predictor.py         Chargement du modèle et prédiction par lot
│       └── car_classifier_2.keras   Modèle (non versionné, à fournir)
├── docker/                      Dockerfiles, docker-compose, nginx, contraintes de versions
├── requirements.txt             Dépendances Python (les deux serveurs)
└── .env                         Variables d'environnement (non versionné)
```

## Démarrage rapide avec Docker

Prérequis : Docker Desktop (ou Docker Engine + Compose v2), le fichier `server/MODEL_SERVER/car_classifier_2.keras` et un fichier `.env` à la racine (voir [Configuration](#configuration)).

```sh
cd docker
docker compose up -d --build
```

L'application est disponible sur **http://localhost:8080**.

Services lancés :

| Service | Rôle |
|---|---|
| `db` | PostgreSQL 16, données persistées dans le volume `db-data` |
| `redis` | Couche de messages pour les WebSockets |
| `model` | MODEL_SERVER (port interne 8001) |
| `django` | API + WebSockets, applique les migrations au démarrage |
| `client` | nginx : sert le React compilé et fait proxy vers `django` |

### Créer un compte administrateur

```sh
docker compose exec django python manage.py createsuperuser
docker compose exec django python manage.py shell -c "from users.models import User; User.objects.filter(username='admin').update(user_type='admin')"
```

`createsuperuser` demande le nom (ici `admin`) et le mot de passe, la seconde commande lui donne le rôle `admin` de l'application.

L'interface d'administration Django est aussi accessible sur http://localhost:8080/admin/.

### Commandes utiles

```sh
docker compose logs -f django            # logs du backend
docker compose restart django            # redémarrer un service
docker compose down                      # tout arrêter (les données de la base sont conservées)
docker compose down -v                   # tout arrêter ET supprimer la base
```

Variables optionnelles (dans le shell ou un fichier `docker/.env`) :

| Variable | Défaut | Rôle |
|---|---|---|
| `CLIENT_PORT` | `8080` | Port exposé sur la machine |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | À compléter pour ouvrir l'application depuis une autre IP |
| `DB_PASSWORD_DOCKER` | `smart_parking` | Mot de passe de la base du conteneur |
| `REDIS_PASSWORD_DOCKER` | `smart_parking` | Mot de passe du Redis du conteneur |
| `WS_ALLOWED_ORIGINS` | `http://localhost:8080,http://127.0.0.1:8080` | Origines exactes autorisées pour les WebSockets (à compléter avec `ALLOWED_HOSTS`) |

## Développement sans Docker

Prérequis : Python 3.12, Node.js 22, une base PostgreSQL et un Redis accessibles.

```sh
pip install -r requirements.txt

# 1. serveur du modèle
cd server/MODEL_SERVER
python server.py                                     # http://127.0.0.1:8001

# 2. backend
cd server/DJANGO_SERVER
python manage.py migrate
uvicorn smart_parking.asgi:application --port 8000   # runserver ne gère pas les WebSockets

# 3. frontend
cd client
npm install
npm run dev                                          # http://localhost:5173
```

En développement, Vite redirige `/api`, `/ws`, `/admin` et `/static` vers Django (`DJANGO_URL`, par défaut `http://127.0.0.1:8000`). Le navigateur ne voit donc qu'une seule origine, ce qui permet aux cookies d'authentification de fonctionner.

Vérifications :

```sh
cd server/DJANGO_SERVER && python manage.py check
cd server/DJANGO_SERVER && python manage.py test users camera parking
cd client && npm run build
```

## Configuration

Fichier `.env` à la racine du dépôt :

| Variable | Obligatoire | Description |
|---|---|---|
| `SECRET_KEY` | oui | Clé secrète Django (signe aussi les JWT) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | oui hors Docker | Connexion PostgreSQL (remplacées par Docker) |
| `DB_SSL_ROOT_CERT` | non | Certificat CA pour la connexion PostgreSQL |
| `DB_SSLMODE` | non | `require` par défaut, `disable` dans Docker |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | oui pour l'inscription | Compte Gmail SMTP pour les emails d'activation |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | non | Redis de Channels |
| `WS_ALLOWED_ORIGINS` | non | Origines exactes (`schéma://hôte:port`) acceptées par les WebSockets. Vide : seul le nom d'hôte est comparé à `ALLOWED_HOSTS` |
| `MODEL_SERVER_URL` | non | `http://127.0.0.1:8001` par défaut |
| `ALLOWED_HOSTS` | non | Liste séparée par des virgules. Sert aussi à vérifier l'`Origin` des WebSockets |
| `DEBUG` | non | `false` par défaut. `true` uniquement en développement local |
| `SECURE_COOKIES` | non | `false` par défaut. `true` dès que l'application est servie en HTTPS |
| `CAMERA_MEDIA_ROOT` | non | Dossier des vidéos locales, `server/DJANGO_SERVER/parking/Data` par défaut |
| `CAMERA_NETWORKS` | recommandé en production | Réseaux autorisés pour les URL de caméras, séparés par des virgules (ex. `192.168.10.0/24`). Vide : tout sauf loopback, link-local, multicast et réservé |

Côté MODEL_SERVER : `MODEL_SERVER_HOST` (défaut `127.0.0.1`) et `MODEL_SERVER_PORT` (défaut `8001`).

> Le fichier `.env` est lu sans interprétation par Docker : pas d'espace autour du `=`, et les caractères `$` sont conservés tels quels.

## Utilisation de l'application

1. **Se connecter** avec un compte admin.
2. **Setup** (`/setup`) : ajouter les caméras. Une caméra = un numéro de zone, une référence et une URL (`rtsp://…`, `rtsps://…`, `http(s)://…`) ou un fichier vidéo. Les URL vers `localhost`, le loopback ou les adresses link-local sont refusées. Un fichier vidéo doit se trouver dans `CAMERA_MEDIA_ROOT/<id du parking>/` et s'indique par son nom relatif (ex. `parking.mp4`).
3. **Initialisation** (`/spots`) : une capture de chaque caméra active s'affiche.
   - Deux clics gauches = un rectangle (deux coins opposés), puis on nomme la place (par défaut `Spot N`).
   - Clic droit sur un rectangle = suppression.
   - **Enregistrer** sauvegarde toutes les zones dans `coordinates.json`, **Annuler** recharge la dernière version enregistrée.
4. **Statut du parking** (`/parking`) : une diapositive par zone. Les places se mettent à jour toutes les 5 secondes, avec une animation d'entrée et de sortie des voitures.
5. **LCD** (`/lcd`) : choix d'une zone, nombre de places libres et flèche de direction pour chaque place.
6. **Gestion** (`/management`) : créer des comptes guest (un email d'activation leur est envoyé), voir et supprimer les caméras et les guests.

## API

Toutes les routes sont préfixées par `/api` et renvoient du JSON. L'authentification passe par des cookies HttpOnly, il n'y a donc pas d'en-tête `Authorization` à envoyer.

| Méthode | Route | Accès | Description |
|---|---|---|---|
| POST | `/auth/login/` | public | `{username, password}` → pose les cookies, renvoie l'utilisateur |
| POST | `/auth/refresh/` | cookie refresh | Renouvelle les tokens |
| POST | `/auth/logout/` | public | Révoque le refresh token et efface les cookies |
| POST | `/auth/register/` | public | Crée un compte admin inactif et envoie l'email d'activation |
| GET | `/auth/activate/<uid>/<token>/` | public | Active un compte |
| GET | `/auth/me/` | connecté | Utilisateur courant |
| GET / POST | `/users/` | admin | Liste des guests (avec statut en ligne) / création d'un guest |
| DELETE | `/users/<uuid>/` | admin | Supprime un utilisateur et blackliste ses tokens |
| GET / POST | `/cameras/` | admin | Liste (avec `is_active`) / création en lot `[{area, ref, path}]` |
| DELETE | `/cameras/<uuid>/` | admin | Supprime une caméra |
| GET | `/parking/areas/` | public | Zones ayant des places définies |
| GET / POST | `/parking/coordinates/` | lecture publique, écriture admin | Places de toutes les zones |
| GET | `/parking/snapshots/` | admin | Une capture JPEG (base64) par caméra active |

WebSockets :

| Route | Messages |
|---|---|
| `/ws/video/<zone>/` | Toutes les 5 s : `{area, available_spots, spot_details: [{spot, status}]}`, avec `status` ∈ `empty`, `occupied`, `error` |
| `/ws/user-status/` | `{user_id, status}` quand un utilisateur connecté ouvre ou ferme l'application |

MODEL_SERVER :

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| POST | `/predict` | Corps : tableau NumPy `.npy` `uint8` de forme `(N, H, W, 3)` en BGR → `{"statuses": ["empty" \| "occupied", …]}` |

## Fonctionnement de la détection

1. Les places de chaque zone sont des quadrilatères enregistrés dans `server/DJANGO_SERVER/parking/Spots/coordinates.json` :
   ```json
   [{ "area": "1", "coordinates": { "Spot 1": [[x, y], [x, y], [x, y], [x, y]] } }]
   ```
2. Le service `detection` relit les zones toutes les 10 secondes et garde une capture ouverte par zone qui a des places et une caméra.
   - Une boucle lit le flux à sa cadence native, sans décoder ni encoder d'image inutilement, pour qu'une vidéo enregistrée avance en temps réel.
   - Toutes les 5 secondes, l'image courante est découpée : chaque place est redressée en 180×180 par une transformation de perspective.
3. Les crops sont envoyés en un seul lot au MODEL_SERVER, qui renvoie un statut par place (sortie sigmoïde > 0,5 → `occupied`).
4. Le résultat est publié dans le groupe Redis `zone_<parking>_<zone>`. Chaque `/ws/video/<zone>/` abonné le reçoit, après vérification que l'utilisateur est toujours membre du parking.

À l'enregistrement des places, un crop de chaque place est aussi sauvegardé dans `server/DJANGO_SERVER/cropped_spots/area_<zone>/`, ce qui peut servir de jeu de données. Le notebook `server/MODEL_SERVER/model_testing.ipynb` sert à tester le modèle.

## Authentification et rôles

- **Tokens JWT** (SimpleJWT) stockés en cookies `HttpOnly` et `SameSite=Strict` : le token d'accès dure 1 minute, le refresh 1 heure, avec rotation et blacklist. Le frontend renouvelle automatiquement le token sur une réponse 401.
- Un seul refresh token valide par utilisateur (table `users_refreshsession`, stocké haché) : se reconnecter révoque la session précédente.
- La connexion ouvre aussi une **session Django**, utilisée pour authentifier le WebSocket de statut en ligne.
- **Rôles** :
  - `admin` : propriétaire de parking. Créé par l'inscription publique (après activation par email), sans accès à l'admin Django. Seul `createsuperuser` crée un compte d'administration Django.
  - `guest` : créé par un admin, accès en lecture (accueil, statut, LCD).

## Limites connues

- **Gestion des guests** : chaque admin voit et peut supprimer tous les guests, pas seulement ceux qu'il a créés.
- **Versions figées** : le modèle Keras ne se charge pas avec les versions récentes de TensorFlow/Keras, d'où `tensorflow==2.19.0` et `keras==3.5.0` dans `requirements.txt`. L'image Docker utilise en plus `docker/constraints.txt` pour figer les autres dépendances.
- **Liste des caméras lente** : afficher la liste ouvre chaque flux avec OpenCV pour vérifier qu'il est actif.
- **HTTPS** : la stack Docker sert l'application en HTTP. En production, placer un proxy TLS devant nginx et mettre `SECURE_COOKIES=true`.
