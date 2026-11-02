---
name: Smart Parking
description: Le parking lu comme un plan de réseau de transport, pour l'agent au poste et le conducteur devant l'écran.
colors:
  ink: "#16213A"
  ink-raised: "#24315A"
  ink-muted: "#C9CDD8"
  paper: "#F3F1EA"
  paper-deep: "#ECE9DF"
  surface: "#FFFFFF"
  rule: "#DAD6CB"
  text: "#16213A"
  text-muted: "#5B6478"
  select: "#2B59C3"
  free: "#0F7B6C"
  occupied: "#16213A"
  alert: "#B45309"
  alert-text: "#92400E"
  offline: "#7A8292"
  danger: "#B42318"
  line-1: "#0F7B6C"
  line-2: "#C2410C"
  line-3: "#6D28D9"
  line-4: "#A16207"
  line-5: "#0E7490"
  line-6: "#BE185D"
  lcd-ground: "#0B1222"
  lcd-text: "#FFFFFF"
  lcd-free: "#5EEAD4"
  lcd-alert: "#FBBF24"
typography:
  display:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "4rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  heading:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
  caption:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.04em"
  lcd-count:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "clamp(8rem, 22vh, 16rem)"
    fontWeight: 800
    lineHeight: 0.9
    letterSpacing: "-0.03em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  full: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "48px"
  4xl: "64px"
components:
  rail:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ink-muted}"
    width: "232px"
  rail-item-active:
    backgroundColor: "{colors.ink-raised}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.ink-raised}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
    height: "40px"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
    height: "40px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "10px 12px"
    height: "40px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
  status-row:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "14px 16px"
  station-marker:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.full}"
    size: "44px"
  lcd-screen:
    backgroundColor: "{colors.lcd-ground}"
    textColor: "{colors.lcd-text}"
---

<!-- SEED: établi avec l'équipe avant l'implémentation ; les valeurs seront revérifiées sur le code une fois la refonte construite. -->

# Design System : Smart Parking

## Overview

**Thèse.** Smart Parking se lit comme un plan de réseau de transport. Chaque zone (une caméra) est une **station** posée sur une **ligne** de couleur. La pastille de la station se remplit à mesure que les places sont prises, et un panneau **« État des lignes »** dit, comme dans une station de métro, ce qui fonctionne et ce qui est perturbé. On refuse le back-office générique fait de cartes d'indicateurs, et le vert/rouge plein écran.

**Pour qui, dans quelle lumière.** L'agent de parking garde l'application ouverte toute la journée sur un poste fixe, sous l'éclairage d'un bureau ou d'un guichet, et la consulte entre deux tâches. D'où un **fond clair et chaud** (papier), une encre marine et peu de couleur hors des données. L'écran LCD, lui, est lu à plusieurs mètres, à l'entrée d'un parking souvent sombre : il passe en **fond nuit** avec des chiffres géants.

**Ce que la nouvelle identité remplace.** L'interface actuelle (fond noir `#141414`, dégradés rouge-rose, titres en texte dégradé de 4rem, une feuille de style globale par page, cartes avec photos plein cadre, polices Kumbh Sans / Roboto selon la page) est abandonnée. Seuls restent le nom, les fonctionnalités, les contenus et l'animation des voitures, qui est recomposée dans ce système.

**Mouvement.** Le mouvement sert l'état, jamais la décoration : une pastille qui se remplit, une voiture qui entre se garer, un compteur qui change. Pas de séquence d'apparition au chargement des pages.

**La pièce signature.** L'animation des voitures. En cliquant une station du schéma, on ouvre le plan de la zone : les voitures rejouent leur entrée et se garent sur chaque place occupée, puis l'animation suit le direct (entrées et sorties toutes les 5 s).

**La règle du code unique.** Tout objet porte un code, identique partout : zone `Z1`, place `Z1-P07`, caméra `CAM-01`. Il apparaît dans le schéma, les tableaux, le plan de zone, le sélecteur de places et le LCD. Le nom lisible (« Entrée Nord ») accompagne le code, il ne le remplace pas.

## Colors

Stratégie : **coquille engagée, contenu retenu**. Le rail marine et le fond papier portent l'identité. La couleur vive est réservée à trois usages : les **lignes de zone** (données), les **états** et la **sélection**.

### Primary

- **Encre marine** (`ink`) : rail de navigation, texte principal, boutons principaux, places occupées. C'est la couleur de l'autorité : si quelque chose est marine, c'est soit la structure, soit une action.
- **Encre relevée** (`ink-raised`) : élément actif du rail, survol des boutons principaux.

### Secondary

- **Bleu sélection** (`select`) : uniquement la station ou la place sélectionnée, l'anneau de focus clavier et le rectangle en cours de dessin dans le sélecteur de places. Jamais pour un bouton, un lien ou une décoration.

### Tertiary

Les **couleurs de ligne** (`line-1` à `line-6`) identifient les zones : la zone 1 est toujours sarcelle, la zone 2 vermillon, et ainsi de suite (au-delà de 6 zones, le cycle recommence avec un trait en pointillés). Elles colorent le trait du schéma, l'anneau de la station, la pastille devant le nom de zone dans les tableaux et le contour des places dessinées. Elles ne disent jamais l'état.

États :

- **Libre** (`free`) : place libre sur le plan de zone, compteur de places libres. Toujours accompagné du chiffre.
- **Occupée** (`occupied`) : la place porte la voiture ; aucun rouge ni vert pour opposer libre et occupé.
- **Alerte** (`alert`, texte en `alert-text`) : caméra hors ligne, prédiction en erreur, données de plus de 30 s.
- **Hors ligne** (`offline`) : anneau en pointillés et chiffres remplacés par « — ».
- **Danger** (`danger`) : uniquement les actions destructives (supprimer un utilisateur, une caméra) et les erreurs de formulaire.

### Neutral

- **Papier** (`paper`) : fond de toutes les pages opérateur.
- **Papier profond** (`paper-deep`) : colonnes secondaires (« État des lignes », panneaux latéraux).
- **Surface** (`surface`) : panneaux, lignes de liste, champs, tableaux.
- **Filet** (`rule`) : séparations et bordures d'un pixel.
- **Texte atténué** (`text-muted`) : métadonnées, horodatages, légendes. Contraste mesuré : 5,25:1 sur papier, 4,89:1 sur papier profond.
- **Écran LCD** : `lcd-ground` (fond nuit), `lcd-text`, `lcd-free` pour le compteur et `lcd-alert` pour « Complet » et « Hors service ».

**La règle de la couleur au travail.** Une couleur vive sur l'écran doit répondre à une question : quelle zone, quel état, qu'est-ce qui est sélectionné ? Si elle ne répond à aucune, elle passe à l'encre.

**La règle du jamais seule.** Un état n'est jamais porté par la couleur seule : chiffre, mot (« Complet », « Hors ligne ») ou forme (anneau plein, pointillés, voiture) l'accompagnent toujours, pour les daltoniens et pour l'écran vu de loin.

## Typography

Une seule famille : **Hanken Grotesk**, une grotesque humaniste proche des caractères de signalétique de transport, servie depuis le projet (pas depuis un CDN). Chiffres **tabulaires** partout où des nombres changent (`font-variant-numeric: tabular-nums`), pour que « 18 » devenu « 9 » ne fasse pas danser la ligne.

### Hierarchy

- **Display** (800, 4rem) : le total de places libres en tête du schéma. Un seul par écran.
- **Title** (800, 1,75rem) : titre de page (« Réseau des zones », « Caméras »).
- **Heading** (700, 1,1875rem) : titres de panneaux et de sections.
- **Body** (400, 1rem, interligne 1,5) : texte courant, cellules de tableau, champs.
- **Label** (500, 0,875rem) : libellés de champs, entrées du rail, boutons.
- **Caption** (500, 0,8125rem, interlettrage 0,04em) : codes et métadonnées sous un nom (« CAM-04 · aucun flux depuis 12 min »), légende du schéma.
- **Compteur LCD** (800, de 8 à 16rem selon la hauteur d'écran) : le nombre de places libres d'une zone, lisible à trente mètres.

Échelle fixe en rem, rapport d'environ 1,2. Pas de tailles fluides sur les pages opérateur ; seul le compteur LCD s'adapte à la hauteur de l'écran.

**La règle du chiffre d'abord.** Dans une ligne de statut, le nombre est l'élément le plus gras ; le nom de zone vient ensuite, la caméra et l'horodatage en légende.

## Layout

**Coquille.** Rail marine fixe de 232 px à gauche (logo P, navigation, langue et déconnexion en bas), contenu sur fond papier avec 40 px de marge latérale. Les pages de travail utilisent au besoin une colonne secondaire de 360 px sur papier profond.

**Écran « Réseau des zones »** (page d'accueil de l'agent) :
- en haut, le titre de page à gauche et le total de places libres (« 57 places libres sur 120 ») à droite ;
- au centre, le schéma : les zones posées sur une ou plusieurs lignes, chaque station avec son code, son compteur et son nom ;
- à droite, « État des lignes » : une ligne par zone avec la pastille de couleur, le nom, la caméra, son état et le compteur ; les zones en alerte remontent en tête.
- Avec une ou deux zones seulement, le schéma devient une ligne horizontale unique, avec les stations à grande échelle.

**Plan de zone** (ouvert en cliquant une station) : en-tête avec code, nom, compteur et retour au réseau ; deux rangées de places de part et d'autre d'une voie de circulation, comme dans le plan animé actuel ; liste des places sous le plan, chaque ligne renvoyant à sa place sur le plan et inversement.

**Pages de configuration** (caméras, places, utilisateurs) : titre, une barre d'actions (ajouter, rechercher, filtrer), puis un tableau ou un formulaire pleine largeur. Les formulaires vivent dans la page ou dans un panneau latéral, pas dans des diapositives.

**Écran LCD** : plein écran, aucune navigation. Une zone par écran (choisie dans l'URL ou par un sélecteur discret au survol) : code et nom en haut, compteur géant au centre, flèche de direction et liste des places libres en bas.

**Rythme.** Grille de 4 px : 8 px dans un groupe, 16 à 24 px entre groupes, 32 à 48 px entre sections, toujours plus d'espace au-dessus d'un titre qu'en dessous.

**Adaptation.**
- 1280 px et plus : rail, contenu et colonne secondaire côte à côte.
- De 960 à 1279 px : la colonne secondaire passe sous le contenu.
- Moins de 960 px : le rail devient une barre en haut avec un menu ; le schéma défile horizontalement, les tableaux deviennent des listes de lignes. Le mobile reste utilisable mais n'est pas prioritaire.
- LCD : paysage 16:9 et portrait 9:16, le compteur ne descend jamais sous la moitié de la hauteur utile.

## Elevation & Depth

Le monde est **plat, comme un plan imprimé** : la profondeur vient des filets d'un pixel (`rule`) et du changement de fond (papier → surface), pas des ombres.

**La règle du filet ou de l'ombre.** Un élément a soit une bordure, soit une ombre, jamais les deux. Les panneaux et les lignes ont une bordure ; seuls les éléments qui flottent au-dessus de la page (menu déroulant, boîte de dialogue, notification) ont une ombre, décalée vers le bas et douce : `0 12px 32px rgba(22, 33, 58, 0.18)`.

## Shapes

- **Contrôles** (boutons, champs, sélecteurs) : coins légèrement arrondis (6 px).
- **Lignes de liste et de statut** : 10 px.
- **Panneaux** : 14 px.
- **Pastilles de station, puces d'état, marqueurs** : cercles et pilules complets. Les pilules restent réservées aux petits éléments.
- **Traits de ligne** du schéma : 10 px d'épaisseur, extrémités arrondies, angles à 45° ou 90° uniquement, comme sur un plan de métro.
- **Places** sur le plan de zone : rectangles aux coins de 4 px, contour de la couleur de la ligne de zone.

## Components

### Buttons

- **Principal** : fond marine, texte blanc ; survol en marine relevée ; une seule action principale par zone d'écran.
- **Secondaire** : fond blanc, filet, texte marine.
- **Danger** : fond rouge, réservé à la confirmation d'une suppression.
- **Désactivé** : perd sa couleur (fond papier profond, texte atténué) et le curseur d'action.
- **Chargement** : le libellé reste, un indicateur remplace l'icône, la largeur ne bouge pas.
- Focus clavier : anneau bleu sélection de 2 px, décalé de 2 px, sur tous les éléments interactifs.

### Chips

Puces d'état : fond très clair de la couleur d'état, texte foncé de la même famille, **toujours une icône et un mot** : « Libre », « Complet », « Hors ligne », « Erreur ». Pour les rôles : « Admin » / « Guest » en puces neutres.

### Cards / Containers

- **Panneau** : fond blanc, filet, coins de 14 px ; jamais de panneau dans un panneau.
- **Ligne de statut** : fond blanc, coins de 10 px, pastille de couleur de zone à gauche, nom et légende au centre, compteur à droite. Une ligne en alerte prend un contour ambre de 2 px et passe en tête de liste.

### Inputs / Fields

Libellé au-dessus du champ, champ blanc avec filet. Au focus : anneau bleu sélection. En erreur : bordure rouge et message sous le champ, qui dit le problème et comment le corriger (« Cette URL ne répond pas : vérifiez l'adresse RTSP ou que la caméra est allumée »). La validation se fait à la sortie du champ, pas à chaque frappe.

### Navigation

Rail marine : logo P et « Smart Parking », puis Réseau, Zones, Caméras, Places, Utilisateurs, Écran LCD. L'entrée courante a un fond marine relevé et un texte blanc. Le sélecteur de langue et la déconnexion sont en bas du rail. Les entrées réservées aux admins sont absentes pour un guest, pas grisées.

### Station (pièce signature du schéma)

Un cercle de 44 px posé sur la ligne de la zone : un anneau de 8 px de la couleur de ligne, qui **se remplit comme un camembert** selon le taux d'occupation (vide = presque tout libre, plein = complet). Sous la station : `Z2 · 9` en gras et le nom en légende.
- **Complet** : disque plein et mot « Complet ».
- **Hors ligne** : anneau gris en pointillés et « — » à la place du compteur.
- **Sélectionnée** : contour bleu sélection décalé de 4 px.
- **Survol** : légende enrichie (caméra, dernière mise à jour).
- Quand le compteur change, le remplissage glisse en 400 ms (ease-out) ; le chiffre change sans animation, pour rester lisible.

Un clic sur la station ouvre le plan de la zone.

### Plan de zone animé (pièce signature)

Recomposition de l'animation actuelle dans le nouveau monde :
- **À l'ouverture** (clic sur une station ou entrée « Zones ») : les places sont dessinées vides, puis une voiture **entre par la voie et se gare** sur chaque place occupée. Les voitures partent en léger décalage (60 ms entre deux) pour que l'arrivée se lise comme un flux, pas comme un bloc. Durée par voiture : 1,2 s.
- **En direct** : quand une place se libère, la voiture ressort par la voie ; quand une place se remplit, une voiture entre. Mêmes trajectoires que l'animation actuelle (entrée par la droite, virage à 90° vers la rangée haute ou basse).
- Une place occupée prend le fond marine avec la voiture vue de dessus ; une place libre garde le fond blanc, le contour de couleur de zone et son code (`Z1-P07`) ; une place en erreur prend un contour ambre en pointillés.
- **Mouvement réduit** (préférence système) : pas de trajet, les voitures apparaissent directement à leur place avec un fondu de 150 ms.
- Revenir au réseau puis rouvrir la zone rejoue l'animation d'entrée.

### État des lignes

Panneau sur papier profond qui liste une ligne de statut par zone. Message global en tête : « Toutes les caméras fonctionnent » ou « 1 caméra hors ligne », en ambre si une alerte existe. Sert aussi de liste accessible au clavier pour le schéma (chaque ligne ouvre le plan de zone).

### Tableaux

Utilisés pour les caméras, les places et les utilisateurs : en-têtes en label atténué, triables ; chiffres alignés à droite et tabulaires ; ligne survolée en papier ; actions en fin de ligne (icône et libellé). Le chargement s'affiche en lignes squelettes, pas en indicateur au centre. Un tableau vide explique quoi faire : « Aucune caméra. Ajoutez la première pour voir sa zone apparaître sur le réseau. »

### Notifications et confirmations

- **Notification** (enregistrement réussi, caméra ajoutée) : bandeau éphémère en bas à droite, 4 s, fermable. Remplace les fenêtres « Confirm » actuelles pour les messages de succès.
- **Confirmation** (supprimer, se déconnecter) : boîte de dialogue courte qui nomme l'objet (« Supprimer la caméra CAM-04 ? »), bouton danger à droite, « Annuler » à gauche, la touche Échap annule.

### Sélecteur de places

La capture de la caméra est affichée à sa taille réelle. Le premier clic pose un coin, le second dessine le rectangle en **bleu sélection** ; la place enregistrée prend le contour de la couleur de zone et son code. Le nom proposé par défaut est le code suivant (`Z1-P08`). Un clic droit ou la touche Suppr sur une place sélectionnée la retire. Une barre en bas indique les modifications non enregistrées, avec « Annuler les modifications » et « Enregistrer ».

### Écran LCD

Fond nuit, sans navigation. En haut : `Z1 · Entrée Nord`. Au centre : le compteur géant en `lcd-free`, avec « places libres » en dessous. En bas : la flèche de direction et la liste des places libres (« P03 · P07 · P12 »). États : « COMPLET » en `lcd-alert` à la place du compteur ; « HORS SERVICE » si la caméra ne répond plus. Le compteur change par un fondu enchaîné de 300 ms ; aucune autre animation.

## Do's and Don'ts

### Do:

- **Do** afficher le nombre de places libres avant tout le reste, sur le réseau comme sur le LCD.
- **Do** utiliser le même code (`Z1`, `Z1-P07`, `CAM-01`) dans toutes les vues.
- **Do** garder une couleur de ligne fixe par zone, partout.
- **Do** montrer une donnée douteuse comme douteuse : caméra hors ligne, prédiction en erreur, donnée de plus de 30 s en ambre avec son horodatage.
- **Do** rejouer l'animation des voitures à chaque ouverture d'un plan de zone, et la couper si l'utilisateur préfère un mouvement réduit.
- **Do** traduire chaque libellé en français (vouvoiement) et en anglais, dans un ton court et factuel : verbes d'action sur les boutons (« Ajouter une caméra », « Enregistrer les places »), messages d'erreur qui disent quoi faire, nombres avant les mots (« 18 places libres »).
- **Do** donner un focus clavier visible et un ordre de tabulation logique à chaque écran.

### Don't:

- **Don't** opposer libre et occupé par le vert et le rouge, ni porter un état par la couleur seule.
- **Don't** utiliser le bleu sélection pour autre chose que la sélection et le focus.
- **Don't** utiliser de texte en dégradé, d'effet de verre décoratif ni d'ombre portée dure.
- **Don't** construire une page en grille de cartes « icône + titre + texte », ni empiler des cartes dans des cartes.
- **Don't** mettre de petit sur-titre en capitales au-dessus d'un titre.
- **Don't** ouvrir une fenêtre modale pour un simple message de succès.
- **Don't** animer l'apparition des pages ; seul ce qui change d'état bouge.
- **Don't** remplacer les icônes par des émojis ou des caractères Unicode ; une seule bibliothèque d'icônes au trait.
- **Don't** inventer des chiffres d'usage ou des clients : les données de démonstration sont marquées comme telles.
