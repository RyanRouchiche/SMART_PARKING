# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Agent / gestionnaire de parking (utilisateur principal)** : surveille l'occupation du parking depuis un poste fixe (guichet, salle de contrôle) pendant une bonne partie de la journée. Il a besoin de savoir d'un coup d'œil combien de places sont libres, où, et si une caméra ne répond plus.
- **Administrateur** : configure de temps en temps les caméras, dessine les places de chaque zone et gère les comptes guests.
- **Conducteurs** : ne se connectent pas ; ils lisent l'écran LCD / la borne à l'entrée du parking, de loin, souvent en roulant lentement.

## Product Purpose

Détecter en temps réel les places libres et occupées d'un parking à partir de ses caméras existantes, et rendre cette information immédiatement exploitable : pour l'agent qui gère le parking et pour le conducteur qui cherche une place. Le succès : l'agent n'a pas besoin d'aller vérifier physiquement, et le conducteur sait où aller avant d'entrer.

## Positioning

Pas de capteur par place : la détection se fait par vision (un réseau de neurones classe chaque place redressée à partir de l'image caméra). Une zone = une caméra ; les places sont dessinées une fois par l'admin sur une capture de la caméra.

## Operating Context

- Poste desktop allumé en continu, consulté par intermittence entre d'autres tâches.
- Écran LCD / borne à l'entrée, lu à plusieurs mètres, sans interaction.
- Mise à jour des statuts toutes les 5 secondes par zone.
- Configuration rare : ajout de caméras (URL RTSP/HTTP ou fichier vidéo), dessin des places, création de guests avec activation par email.

## Capabilities and Constraints

- Pages : connexion/inscription, accueil, statut du parking (plan animé par zone), LCD, gestion (guests, caméras, utilisateurs), configuration des caméras (1 à 10 à la fois), initialisation des places.
- Rôles : `admin` (tout) et `guest` (consultation).
- Statuts d'une place : `empty`, `occupied`, `error`. Une caméra peut être inactive (flux injoignable).
- Bilingue français / anglais, choix mémorisé dans le navigateur.
- Stack : React (Vite) côté client, Django + Channels côté serveur.
- Écrans prioritaires : ordinateur de bureau et écran LCD / borne. Le mobile reste utilisable mais n'est pas prioritaire.

## Brand Commitments

- Le nom affiché est « PARKING » / « Smart Parking ».
- L'identité visuelle actuelle (fond noir, dégradés rouge/rose, gros titres) n'est pas conservée : nouvelle identité demandée.

## Evidence on Hand

- Projet de fin d'études (Master 2025) réalisé pendant un stage chez ICOSNET, repris ensuite.
- Pas de clients, de chiffres d'usage ni de témoignages : ne pas en inventer.
- Images existantes dans `client/src/assets/` (photos génériques de parking, caméra, voiture vue de dessus).

## Product Principles

1. L'état du parking se lit en une seconde : nombre de places libres d'abord, détail ensuite.
2. Une information douteuse ne se déguise pas : caméra hors ligne ou prédiction en erreur sont visibles, jamais affichées comme « libre ».
3. La configuration est rare mais doit être sans erreur : chaque étape montre ce qui sera enregistré.
4. L'écran LCD est un panneau de signalisation, pas une page web.

## Accessibility & Inclusion

- Le statut libre/occupé ne doit jamais reposer sur la seule couleur (daltonisme) : forme, texte ou icône en plus.
- L'écran LCD doit rester lisible à distance et avec un fort contraste.
