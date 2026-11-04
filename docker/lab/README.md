# Labo WireGuard

Reproduit sur un seul PC le tunnel entre un parking et l'hébergement :

| Conteneur | Joue le rôle de | Adresses |
|---|---|---|
| `hub` | Passerelle VPN de l'hébergement | `10.200.0.1` dans le tunnel, `172.30.0.2` sur le faux Internet |
| `site1` | Passerelle du parking (MikroTik) | `10.200.1.1` dans le tunnel, `10.100.1.1` sur le réseau caméras |
| `camera1` | Caméra RTSP du parking (vidéo de test en boucle) | `10.100.1.10`, réseau sans accès Internet |
| Téléphone (optionnel) | Site 2 réel : WireGuard et IP Webcam sur un téléphone du même Wi-Fi | `10.200.2.1`, caméra sur le port 8080 |
| `route-detection` | Route `10.100.0.0/16` du worker de détection vers le hub | une seule fois, au démarrage |

Le site ouvre le tunnel vers le hub (`PersistentKeepalive = 25`) et n'accepte aucune connexion entrante. Le hub ne laisse passer que le port RTSP vers les caméras. Les sites ne peuvent pas se joindre entre eux.

## Lancer

La plateforme doit tourner (`docker compose up -d` dans `docker/`).

```sh
sh docker/lab/setup.sh                       # génère les clés dans docker/lab/generated (ignoré par git)
cd docker/lab && docker compose up -d
```

## Vérifier

```sh
docker compose exec hub wg show                       # dernière poignée de main de moins de 2 min
docker exec smart-parking-detection-1 python -c "import cv2; print(cv2.VideoCapture('rtsp://10.100.1.10:8554/sub').read()[0])"
```

Pour que le parking pilote lise sa caméra à travers le tunnel, mettre le chemin de la caméra `CAM-01` à `rtsp://10.100.1.10:8554/sub` dans l'administration. Pour revenir à la vidéo locale : `/app/DJANGO_SERVER/parking/Data/videoplayback.mp4`.

Si le conteneur `smart-parking-detection-1` redémarre, il perd la route vers le tunnel : relancer `docker compose up -d route-detection`.

## Ajouter un vrai appareil (site 2)

Le hub publie le port UDP 51820 sur le PC. Autoriser ce port dans le pare-feu Windows (profil privé), générer une paire de clés pour l'appareil, l'ajouter comme pair du hub (`AllowedIPs = 10.200.2.1/32`) avec `Endpoint = <IP du PC>:51820` côté appareil. Le hub laisse passer le port 8080 vers `10.200.2.0/24` (IP Webcam).

## Mesuré

- Image 1920×1080 lue par le worker de détection à travers le tunnel en 2,8 s à l'ouverture.
- Environ 2,8 Mbit/s avec le flux principal en continu. En production, utiliser le sous-flux ou le mode instantané (NFR-08 : moins de 0,2 Mbit/s par caméra).
- Téléphone réel (IP Webcam) lu par le worker de détection à travers le tunnel : RTSP en TCP en 2,1 s, flux HTTP en 0,2 s.
- Caméra coupée : le parking passe en « donnée indisponible ». Caméra revenue : données fraîches en quelques secondes.

## Différences avec la production

- Le hub est une VM chez l'hébergeur, avec une IP publique fixe et le port UDP 51820 ouvert.
- La passerelle du site est un MikroTik hEX (RouterOS 7) préconfiguré en atelier.
- Les caméras écoutent sur le port RTSP 554, et leurs mots de passe par défaut sont changés.
- Mettre `CAMERA_NETWORKS=10.100.0.0/16` dans `.env`, pour que la plateforme refuse toute autre adresse de caméra.
- Le worker de détection est routé vers le hub par la configuration réseau du serveur, pas par un conteneur ponctuel.
