import { createContext, useCallback, useContext, useEffect, useState } from "react";

const FR = {
  "Login": "Connexion",
  "Register": "S'inscrire",
  "Username": "Nom d'utilisateur",
  "Password": "Mot de passe",
  "Email": "Email",
  "First Name": "Prénom",
  "Last Name": "Nom",
  "Don't have an account ?": "Vous n'avez pas de compte ?",
  "Already have an account ?": "Vous avez déjà un compte ? Connectez-vous",
  "Login failed. Please check your credentials and try again.":
    "Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.",
  "Registration failed. Please check your credentials and try again.":
    "Échec de l'inscription. Veuillez vérifier vos informations et réessayer.",
  "Registration successful. Please confirm your email.":
    "Inscription réussie. Veuillez confirmer votre adresse e-mail.",
  "Account activated successfully!": "Compte activé avec succès !",
  "Invalid activation link.": "Lien d'activation invalide.",
  "Go to login": "Aller à la connexion",
  "Undo": "Annuler",
  "Confirm": "Confirmer",
  "Yes, Confirm": "Oui, Je confirme.",
  "dashboard": "tableau de bord",
  "parking status": "statut du parking",
  "setup": "configuration",
  "Initialization": "Initialisation",
  "LCD": "LCD",
  "logout": "Déconnexion",
  "Are you sure you want to log out?": "Êtes-vous sûr de vouloir vous déconnecter ?",
  "Logout failed": "Déconnexion échouée",
  "Only admin": "Réservé à l'administrateur",
  "Welcome,": "Bienvenue,",
  "View your parking simulation.": "Voir votre simulation de stationnement.",
  "View Status": "Voir le statut",
  "What are we offering ?": "Que proposons-nous ?",
  "Dashboard": "Tableau de bord",
  "Manage your users database": "Gérez votre base de données d'utilisateurs",
  "Get Started": "Commencer",
  "Setup": "Configuration",
  "Add/Delete cameras from your database": "Ajouter/Supprimer des caméras de votre base de données",
  "Parking data displayed on LCD": "Données de stationnement affichées sur LCD",
  "you can manually change your parking spots!": "Vous pouvez modifier manuellement vos places de stationnement !",
  "About us": "À propos de nous",
  "How it works": "Comment ça fonctionne",
  "Testimonals": "Témoignages",
  "Carrers": "Carrières",
  "Investements": "Investissements",
  "Terms of Service": "Conditions d'utilisation",
  "Contact us": "Contactez-nous",
  "Contact": "Contact",
  "Support": "Support",
  "Destinations": "Destinations",
  "Sponsorships": "Sponsoring",
  "Video": "Vidéo",
  "Submit video": "Soumettre une vidéo",
  "Ambasadors": "Ambassadeurs",
  "Agency": "Agence",
  "Influencer": "Influenceur",
  "Social Media": "Médias sociaux",
  "2025.All rights reserved": "2025. Tous droits réservés",
  "Guest Management": "Gestion Des Guests",
  "Register Guest": "Enregistrer Guest",
  "Guest registration successful. Please confirm your email":
    "Inscription invité réussie. Veuillez confirmer votre adresse e-mail.",
  "Guest registration failed. Please check your credentials and try again.":
    "L'inscription en tant qu'invité a échoué. Veuillez vérifier vos informations et réessayer.",
  "cams List": "Liste des caméras",
  "area": "zone",
  "link": "lien",
  "Status": "statut",
  "Action": "Action",
  "Delete": "Supprimer",
  "Users List": "Liste des utilisateurs",
  "Are you sure you want to delete this user?": "Êtes-vous sûr de vouloir supprimer cet utilisateur ?",
  "User deleted successfully.": "Utilisateur supprimé avec succès.",
  "Error: delete user.": "Erreur : suppression de l'utilisateur.",
  "Are you sure you want to delete this camera?": "Êtes-vous sûr de vouloir supprimer cette caméra ?",
  "Camera deleted successfully!": "Caméra supprimée avec succès !",
  "Error deleting camera.": "Erreur lors de la suppression de la caméra.",
  "Error loading cameras.": "Erreur lors du chargement des caméras.",
  "Camera Configuration": "Configuration de la caméra",
  "Add": "Ajouter",
  "Max slides reached": "Nombre maximum atteint",
  "Validate and send": "Valider et envoyer",
  "Are you sure you want to delete this slide?": "Êtes-vous sûr de vouloir supprimer cette diapositive ?",
  "Do you want to validate and submit all cameras?": "Voulez-vous valider et soumettre toutes les caméras ?",
  "Please fill in all fields for each camera.": "Veuillez remplir tous les champs pour chaque caméra.",
  "Cameras added successfully!": "Caméras ajoutées avec succès !",
  "Error submitting cameras.": "Erreur lors de la soumission des caméras.",
  "Pick a parking spot": "Choisis une place de parking.",
  "Area": "Zone",
  "Areas": "Zones",
  "Undo Changes": "Annuler les modifications",
  "Save Changes": "Enregistrer les modifications",
  "Pick a name for the spot (e.g., Spot 1)": "Choisis un nom pour la place (par exemple : Place 1).",
  "Spot selected: {spot} in area {area}.": "Place sélectionnée : {spot} dans la zone {area}",
  "Spot \"{spot}\" deleted.": "Place {spot} supprimée",
  "Coordinates saved successfully!": "Coordonnées enregistrées avec succès !",
  "Error saving coordinates.": "Erreur lors de l'enregistrement des coordonnées.",
  "Available spots": "Places disponibles",
  "Choose an area": "Choisir une zone",
};

const LanguageContext = createContext(null);

function storedLanguage() {
  try {
    return localStorage.getItem("language") || "en";
  } catch {
    return "en";
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
  const { lang, setLang } = useContext(LanguageContext);
  return (
    <select
      id="lang-select"
      className="navbar__links"
      value={lang}
      onChange={(e) => setLang(e.target.value)}
    >
      <option value="en">English</option>
      <option value="fr">Français</option>
    </select>
  );
}
