# Smart Parking

Application de gestion de parking intelligent. Des caméras filment les places de stationnement, un réseau de neurones (Keras) détermine pour chaque place si elle est **libre** ou **occupée**, et le résultat est affiché en temps réel dans une interface web : plan animé du parking, écran LCD des places libres, gestion des caméras et des utilisateurs.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Architecture du client](#architecture-du-client)
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
| Connexion / inscription | `/login` | public | Connexion, création d'un compte propriétaire (activation par email) |
| Activation | `/activate/:uid/:token` | public | Lien reçu par email pour activer un compte |
| Réseau de zones | `/` | connecté | Vue d'ensemble : places libres par zone, état de chaque ligne (libre, se remplit, complet, hors ligne) |
| Plan de zone | `/zones/:area` | connecté | Plan animé d'une zone (les voitures entrent et sortent selon les prédictions) et tableau des places |
| Écran LCD | `/lcd/:area` | connecté | Affichage plein écran pour une borne : places libres de la zone et direction |
| Caméras | `/cameras` | propriétaire | Ajout, état et suppression des caméras (une caméra filme une zone) |
| Places | `/spots` | propriétaire | Dessin des places sur une capture de chaque caméra |
| Utilisateurs | `/users` | propriétaire | Création et suppression des comptes guest, statut en ligne en direct |

L'interface est en **français** par défaut, avec l'**anglais** disponible depuis le sélecteur de langue. Elle suit le design system décrit dans `SYSTEM_DESIGN.md` ; `PRODUCT.md` résume le produit.

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

- **`client/`** : application React (Vite). Elle ne parle qu'à Django, via `/api` (HTTP) et `/ws` (WebSockets). Elle est découpée en couches, sur le même modèle que le backend (voir [Architecture du client](#architecture-du-client)).
- **`server/DJANGO_SERVER/`** : API REST (Django REST Framework), WebSockets (Django Channels), authentification JWT. Le même code tourne en deux services :
  - `django` : API et WebSockets. Les WebSockets vidéo ne font que s'abonner aux résultats d'une zone.
  - `detection` (`python manage.py run_detection`) : capture chaque zone une seule fois, quel que soit le nombre de spectateurs, et publie l'occupation dans Redis. Il se répartit sur plusieurs instances avec `--shard` et `--shards`.
- **`server/MODEL_SERVER/`** : petit serveur HTTP (bibliothèque standard Python) qui charge le modèle Keras une seule fois et classe un lot d'images de places.
- **PostgreSQL** stocke les utilisateurs, les caméras et les tokens ; **Redis** sert de couche de messages à Channels.

Le backend est un **monolithe modulaire strict** :
- **Modules** : `users` → `parking` → `camera` → `detection`, plus le noyau partagé `shared`.
- **Sens des dépendances** : un module ne dépend que des modules situés avant lui dans cette liste.
- **Point d'entrée unique** : un module ne doit importer d'un autre module que son fichier `interface.py`. Les modèles, services et vues restent privés.
- **Vérification** : le test `smart_parking/tests.py` vérifie ces deux règles.
- **Seul couplage restant** : les clés étrangères en base (base partagée), qui sont déclarées par nom et sans import Python.

## Architecture du client

Le client reprend le découpage du backend : une couche d'assemblage, un noyau partagé et une fonctionnalité par domaine.

```
client/src/
├── app/                 main.jsx, routes (App.jsx), mise en page (AppShell), RequireAuth
├── shared/              ne dépend d'aucune fonctionnalité
│   ├── http.js          api() et openSocket() : cookies, renouvellement du token sur 401
│   ├── i18n.jsx         traductions FR/EN
│   ├── ui/              Feedback (toasts, confirmations, saisies)
│   ├── zones/style.js   couleur de ligne et code de place (Z1-P01)
│   └── styles/          tokens du design system (app.css), formulaires
└── features/
    ├── auth/            api.js (me, login, logout, register, activate) · AuthProvider · Login, Activate
    ├── parking/         api.js (opérateurs, zones) · usePresence (ws/user-status) · Users
    ├── cameras/         api.js (caméras, captures, places) · Cameras, SpotPicker
    └── detection/       ZonesProvider (un ws/video par zone) · Network, ZonePlan, Lcd
```

Règles, vérifiées par `npm run check`, qui est lancé automatiquement avant `npm run build` :
1. **Ordre des fonctionnalités** : `auth` → `parking` → `cameras` → `detection`. Une fonctionnalité ne dépend que de celles qui la précèdent.
2. **Point d'entrée unique** : une fonctionnalité n'importe une autre fonctionnalité que par son `index.js`.
3. **Noyau partagé** : `shared/` n'importe aucune fonctionnalité, et les fonctionnalités n'importent jamais `app/`.
4. **Appels réseau** : les URL de l'API ne sont écrites que dans le `api.js` de chaque fonctionnalité, et seul `shared/http.js` appelle `fetch`.

Les composants (pages) ne font que l'affichage et l'état de l'écran. Pour ajouter un écran, on crée la page dans la fonctionnalité concernée, on l'exporte depuis son `index.js` et on déclare la route dans `app/App.jsx`.

## Structure du dépôt

```
SMART_PARKING/
├── client/                      Frontend React (voir « Architecture du client »)
│   ├── src/
│   │   ├── app/                 Point d'entrée, routes, mise en page, garde d'authentification
│   │   ├── shared/              Client HTTP/WebSocket, traductions, composants et styles communs
│   │   └── features/            auth · parking · cameras · detection (une fonctionnalité par dossier)
│   ├── scripts/check-architecture.mjs   Vérifie les règles de dépendance avant chaque build
│   └── vite.config.js           Proxy de développement vers Django
├── server/
│   ├── DJANGO_SERVER/
│   │   ├── smart_parking/       Settings, URLs, ASGI : assemble les modules, test d'architecture
│   │   ├── users/               Identité : comptes, sessions JWT, inscription, activation
│   │   ├── parking/             Parkings, membres, accès, zones, opérateurs, présence (WebSocket)
│   │   │   └── Spots/coordinates.json   Places du parking pilote (migration initiale)
│   │   ├── camera/              Caméras, politique des sources, capture, tracé des places
│   │   ├── detection/           Worker de détection, client du modèle, flux d'occupation (WebSocket)
│   │   ├── shared/              Noyau partagé sans état : géométrie des places
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
| `WEB_CONCURRENCY` | `2` | Nombre de processus uvicorn du service `django` |
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
cd server/DJANGO_SERVER && python manage.py test users camera parking detection smart_parking
cd client && npm run build                           # lance aussi npm run check (règles d'architecture)
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
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | non | Redis : couche Channels (base 0), cache, sessions et throttling (base 1) |
| `DB_POOL_SIZE` | non | Taille maximale du pool de connexions PostgreSQL par processus (`10` par défaut) |
| `WS_ALLOWED_ORIGINS` | non | Origines exactes (`schéma://hôte:port`) acceptées par les WebSockets. Vide : seul le nom d'hôte est comparé à `ALLOWED_HOSTS` |
| `MODEL_SERVER_URL` | non | `http://127.0.0.1:8001` par défaut |
| `ALLOWED_HOSTS` | non | Liste séparée par des virgules. Sert aussi à vérifier l'`Origin` des WebSockets |
| `DEBUG` | non | `false` par défaut. `true` uniquement en développement local |
| `SECURE_COOKIES` | non | `false` par défaut. `true` dès que l'application est servie en HTTPS |
| `CAMERA_MEDIA_ROOT` | non | Dossier des vidéos locales, `server/DJANGO_SERVER/parking/Data` par défaut |
| `CAMERA_NETWORKS` | recommandé en production | Réseaux autorisés pour les URL de caméras, séparés par des virgules (ex. `192.168.10.0/24`). Vide : tout sauf loopback, link-local, multicast et réservé |

Côté MODEL_SERVER : `MODEL_SERVER_HOST` (défaut `127.0.0.1`), `MODEL_SERVER_PORT` (défaut `8001`), `MODEL_SERVER_CONCURRENCY` (inférences simultanées, défaut `2`) et `MODEL_SERVER_MAX_BODY` (taille maximale d'un lot, défaut 64 Mo).

> Le fichier `.env` est lu sans interprétation par Docker : pas d'espace autour du `=`, et les caractères `$` sont conservés tels quels.

## Utilisation de l'application

1. **Se connecter** avec un compte propriétaire.
2. **Caméras** (`/cameras`) : ajouter les caméras. Une caméra = un numéro de zone, une référence et une adresse (`rtsp://…`, `rtsps://…`, `http(s)://…`) ou un fichier vidéo.
   - Les adresses vers `localhost`, le loopback ou les adresses link-local sont refusées. En production, `CAMERA_NETWORKS` limite les caméras à leurs réseaux.
   - Un fichier vidéo doit se trouver dans `CAMERA_MEDIA_ROOT/<id du parking>/` et s'indique par son nom relatif (ex. `parking.mp4`).
   - L'état de chaque flux est vérifié en parallèle et gardé 30 secondes.
3. **Places** (`/spots`) : une capture de chaque caméra active s'affiche.
   - Deux clics sur deux coins opposés dessinent une place.
   - Clic sur une place pour la sélectionner, puis touche Suppr ou clic droit pour la supprimer.
   - L'enregistrement sauvegarde les places de chaque zone en base et exporte un crop par place dans `cropped_spots/`.
4. **Réseau de zones** (`/`) : état de toutes les zones, mis à jour toutes les 5 secondes.
5. **Plan de zone** (`/zones/<n>`) : plan animé de la zone (entrée et sortie des voitures) et tableau des places (`Z1-P01`, …).
6. **Écran LCD** (`/lcd/<n>`) : vue plein écran pour une borne, avec les places libres et leur direction.
7. **Utilisateurs** (`/users`) : créer des comptes guest (un email d'activation leur est envoyé), voir leur statut en ligne, les supprimer.

## API

Toutes les routes sont préfixées par `/api`, n'acceptent et ne renvoient que du JSON. L'authentification passe par des cookies HttpOnly, il n'y a donc pas d'en-tête `Authorization` à envoyer. Les routes d'un parking prennent un paramètre facultatif `?parking=<uuid>` (par défaut : le premier parking de l'utilisateur) ; un parking dont on n'est pas membre renvoie 403.

| Méthode | Route | Accès | Module | Description |
|---|---|---|---|---|
| POST | `/auth/login/` | public, 10/min | users | `{username, password}` → pose les cookies, renvoie l'utilisateur |
| POST | `/auth/refresh/` | cookie refresh | users | Renouvelle les tokens (refusé si le mot de passe a changé) |
| POST | `/auth/logout/` | public | users | Révoque le refresh token et efface les cookies |
| POST | `/auth/register/` | public, 5/h | users | Crée un compte propriétaire inactif et envoie l'email d'activation (même réponse si le nom est déjà pris) |
| GET | `/auth/activate/<uid>/<token>/` | public | users | Active un compte (lien à usage unique) |
| GET | `/auth/me/` | connecté | users | Utilisateur courant |
| GET / POST | `/users/` | propriétaire | parking | Opérateurs du parking (avec statut en ligne) / création d'un opérateur |
| DELETE | `/users/<uuid>/` | propriétaire | parking | Retire l'opérateur du parking ; le compte n'est supprimé que s'il n'appartient plus à aucun parking |
| GET | `/parking/areas/` | membre | parking | Zones ayant des places définies |
| GET / POST | `/cameras/` | propriétaire | camera | Liste (avec `is_active`) / création en lot `[{area, ref, path}]` |
| DELETE | `/cameras/<uuid>/` | propriétaire | camera | Supprime une caméra |
| GET / POST | `/parking/coordinates/` | lecture membre, écriture propriétaire | camera | Places de toutes les zones |
| GET | `/parking/snapshots/` | propriétaire | camera | Une capture JPEG (base64) par caméra active |

WebSockets :

| Route | Messages |
|---|---|
| `/ws/video/<zone>/` | Membres du parking. Toutes les 5 s : `{area, available_spots, spot_details: [{spot, status}]}`, avec `status` ∈ `empty`, `occupied`, `error` |
| `/ws/user-status/` | `{user_id, status}` quand un membre du parking ouvre ou ferme l'application (seuls les propriétaires de ce parking le reçoivent) |

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
- La connexion ouvre aussi une **session Django**, utilisée pour authentifier les WebSockets. Retirer un membre d'un parking ou désactiver son compte ferme ses flux vidéo ouverts.
- **Rôles** :
  - `admin` : propriétaire de parking. Créé par l'inscription publique (après activation par email), sans accès à l'admin Django. Seul `createsuperuser` crée un compte d'administration Django.
  - `guest` : opérateur créé par un propriétaire pour son parking, accès en lecture (réseau, plan de zone, LCD).
- **Multi-parkings** : chaque utilisateur ne voit que les parkings dont il est membre (propriétaire ou opérateur).

## Limites connues

- **Versions figées** : le modèle Keras ne se charge pas avec les versions récentes de TensorFlow/Keras, d'où `tensorflow==2.19.0` et `keras==3.5.0` dans `requirements.txt`. L'image Docker utilise en plus `docker/constraints.txt` pour figer les autres dépendances.
- **Statut des caméras** : la liste des caméras vérifie chaque flux en parallèle et garde le résultat 30 secondes en cache, donc un changement d'état peut mettre jusqu'à 30 secondes à apparaître.
- **HTTPS** : la stack Docker sert l'application en HTTP. En production, placer un proxy TLS devant nginx et mettre `SECURE_COOKIES=true`.
