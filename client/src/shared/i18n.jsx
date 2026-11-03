import { createContext, useCallback, useContext, useEffect, useState } from "react";

const FR = {
  "10 cameras at a time": "10 caméras à la fois",
  "Account activated": "Compte activé",
  "Account created. Open the activation link sent to {email}.": "Compte créé. Ouvrez le lien d'activation envoyé à {email}.",
  "Account deleted.": "Compte supprimé.",
  "Actions": "Actions",
  "Add a camera": "Ajouter une caméra",
  "Add a camera whose stream responds, then come back to draw its spots.":
    "Ajoutez une caméra dont le flux répond, puis revenez dessiner ses places.",
  "Add a camera, then draw its spots to create the first zone.":
    "Ajoutez une caméra, puis dessinez ses places pour créer la première zone.",
  "Add the first one to see its zone appear on the network.": "Ajoutez la première pour voir sa zone apparaître sur le réseau.",
  "Add the spot": "Ajouter la place",
  "Administrator": "Administrateur",
  "All cameras are working": "Toutes les caméras fonctionnent",
  "Already have an account?": "Vous avez déjà un compte ?",
  "Available": "Disponible",
  "Camera image of zone {n}": "Image de la caméra de la zone {n}",
  "Camera {ref} deleted.": "Caméra {ref} supprimée.",
  "Cameras": "Caméras",
  "Cancel": "Annuler",
  "Choose a zone": "Choisir une zone",
  "Click two opposite corners to draw a spot. Click a spot to select it, then press Delete or right-click to remove it.":
    "Cliquez deux coins opposés pour dessiner une place. Cliquez une place pour la sélectionner, puis appuyez sur Suppr ou faites un clic droit pour la retirer.",
  "Close": "Fermer",
  "Confirm": "Confirmer",
  "Connecting": "Connexion…",
  "Could not delete camera {ref}.": "Impossible de supprimer la caméra {ref}.",
  "Could not delete this account.": "Impossible de supprimer ce compte.",
  "Could not load the cameras.": "Impossible de charger les caméras.",
  "Create a guest": "Créer un guest",
  "Create an account": "Créer un compte",
  "Create an administrator account": "Créer un compte administrateur",
  "Create one with the form to give someone read-only access.":
    "Créez-en un avec le formulaire pour donner un accès en consultation.",
  "Create the account": "Créer le compte",
  "Create the guest": "Créer le guest",
  "Creating…": "Création…",
  "Data delayed": "Données en retard",
  "Delete": "Supprimer",
  "Delete camera {ref}?": "Supprimer la caméra {ref} ?",
  "Delete the account of {name}?": "Supprimer le compte de {name} ?",
  "Draw the spots of this camera on the Spots page.": "Dessinez les places de cette caméra dans la page Places.",
  "Email": "Email",
  "Enter a reference, for example CAM-01.": "Saisissez une référence, par exemple CAM-01.",
  "Enter a zone number.": "Saisissez un numéro de zone.",
  "Enter the RTSP or HTTP address of the stream.": "Saisissez l'adresse RTSP ou HTTP du flux.",
  "Entrance": "Entrée",
  "Exit": "Quitter",
  "FULL": "COMPLET",
  "Filling up": "Se remplit",
  "First name": "Prénom",
  "Free": "Libre",
  "Free spots in real time, zone by zone, from your existing cameras.":
    "Les places libres en temps réel, zone par zone, à partir de vos caméras.",
  "Full": "Complet",
  "Go to login": "Aller à la connexion",
  "Guest": "Guest",
  "Guest created. An activation email has been sent to {email}.": "Guest créé. Un email d'activation a été envoyé à {email}.",
  "Guests can view the network, the zones and the LCD screen.": "Les guests consultent le réseau, les zones et l'écran LCD.",
  "Invalid activation link": "Lien d'activation invalide",
  "LCD screen": "Écran LCD",
  "Language": "Langue",
  "Last name": "Nom",
  "Left": "Gauche",
  "Line status": "État des lignes",
  "Live, updated every 5 seconds": "En direct, mis à jour toutes les 5 secondes",
  "Log in": "Se connecter",
  "Log out": "Se déconnecter",
  "Log out of Smart Parking?": "Se déconnecter de Smart Parking ?",
  "Logging in…": "Connexion…",
  "Logout failed": "La déconnexion a échoué",
  "Main navigation": "Navigation principale",
  "Name": "Nom",
  "Name this spot": "Nommer cette place",
  "Network": "Réseau",
  "New cameras": "Nouvelles caméras",
  "No account yet?": "Pas encore de compte ?",
  "No camera image available": "Aucune image de caméra disponible",
  "No camera yet": "Aucune caméra",
  "No guest yet": "Aucun guest",
  "No spots in this zone": "Aucune place dans cette zone",
  "No stream": "Pas de flux",
  "No zone yet": "Aucune zone",
  "OUT OF SERVICE": "HORS SERVICE",
  "Occupied": "Occupée",
  "Offline": "Hors ligne",
  "One camera films one zone. Checking each stream can take a few seconds.":
    "Une caméra filme une zone. La vérification de chaque flux peut prendre quelques secondes.",
  "Online": "En ligne",
  "Open zone {code}: {count} free spots": "Ouvrir la zone {code} : {count} places libres",
  "Password": "Mot de passe",
  "Prediction error": "Erreur de prédiction",
  "Reference": "Référence",
  "Registration failed. Check the fields and try again.": "L'inscription a échoué. Vérifiez les champs et réessayez.",
  "Remove this row": "Retirer cette ligne",
  "Right": "Droite",
  "Save the spots": "Enregistrer les places",
  "Save {n} camera(s)": "Enregistrer {n} caméra(s)",
  "Saving…": "Enregistrement…",
  "Spot": "Place",
  "Spot {code} removed.": "Place {code} retirée.",
  "Spots": "Places",
  "Spots saved.": "Places enregistrées.",
  "Status": "Statut",
  "Stream OK": "Flux OK",
  "Stream address": "Adresse du flux",
  "Temporary password": "Mot de passe provisoire",
  "The cameras could not be saved.": "Les caméras n'ont pas pu être enregistrées.",
  "The guest could not be created. Check the highlighted fields.":
    "Le guest n'a pas pu être créé. Vérifiez les champs signalés.",
  "The link has expired or was already used. Ask an administrator for a new one.":
    "Le lien a expiré ou a déjà été utilisé. Demandez-en un nouveau à un administrateur.",
  "The spots could not be saved.": "Les places n'ont pas pu être enregistrées.",
  "This account is not activated yet. Open the link sent by email.":
    "Ce compte n'est pas encore activé. Ouvrez le lien reçu par email.",
  "Undo changes": "Annuler les modifications",
  "Unknown": "Inconnu",
  "Unsaved changes": "Modifications non enregistrées",
  "Updated {ago}": "Mis à jour {ago}",
  "Use a unique name made of letters, digits, spaces, - or _.":
    "Utilisez un nom unique composé de lettres, chiffres, espaces, - ou _.",
  "Username": "Nom d'utilisateur",
  "Users": "Utilisateurs",
  "Wrong username or password.": "Nom d'utilisateur ou mot de passe incorrect.",
  "You can now log in.": "Vous pouvez maintenant vous connecter.",
  "Zone": "Zone",
  "Zone network": "Réseau des zones",
  "Zone {n}": "Zone {n}",
  "Zones": "Zones",
  "free spot": "place libre",
  "free spots": "places libres",
  "free spots out of {n}": "places libres sur {n}",
  "no data yet": "aucune donnée",
  "spots": "places",
  "unsaved change(s)": "modification(s) non enregistrée(s)",
  "{n} camera(s) added.": "{n} caméra(s) ajoutée(s).",
  "{n} min ago": "il y a {n} min",
  "{n} s ago": "il y a {n} s",
  "{n} zone(s) need attention": "{n} zone(s) à surveiller",
};

const LanguageContext = createContext(null);

function storedLanguage() {
  try {
    return localStorage.getItem("language") || "fr";
  } catch {
    return "fr";
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(storedLanguage);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("language", lang);
    } catch {}
  }, [lang]);

  const t = useCallback(
    (text, vars = {}) =>
      Object.entries(vars).reduce(
        (out, [key, value]) => out.replaceAll(`{${key}}`, value),
        (lang === "fr" && FR[text]) || text
      ),
    [lang]
  );

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useT() {
  return useContext(LanguageContext).t;
}

export function LanguageSelect() {
  const { lang, setLang, t } = useContext(LanguageContext);
  return (
    <select aria-label={t("Language")} value={lang} onChange={(e) => setLang(e.target.value)}>
      <option value="fr">Français</option>
      <option value="en">English</option>
    </select>
  );
}
