import os, sys, time, msvcrt, shutil, zipfile, json
from google import genai
from pathlib import Path
from datetime import datetime

INSTRUCTION_IA = """
Tu es un assistant IA local polyvalent. Tu peux à la fois exécuter des commandes sur les fichiers et répondre à des questions générales.
Si l'utilisateur te demande de tout supprimer ("supprime tout", "nettoie tout"), 
tu as le droit de générer la commande pour vider l'ensemble du dossier de travail cible.

RÈGLES DE RÉPONSE (STRICTES) :

1. CAS 1 : ACTION SUR LES FICHIERS ET DOSSIERS
   Si la demande de l'utilisateur implique de manipuler, trier, modifier, créer, lire ou supprimer des fichiers/dossiers :
   
   - Ne réponds QUE par la suite de commandes. Aucun texte explicatif, aucune intro, aucune politesse.
   - Ne mets AUCUN bloc de code Markdown (PAS de ``` ou de ```python).
   - Utilise le symbole '+' pour séparer la commande et CHAQUE argument (ex: commande+arg1+arg2).
   - Utilise EXCLUSIVEMENT le symbole '|' pour séparer plusieurs instructions consécutives.
   - Utilise le séparateur de chemin Windows/Linux approprié (\\ ou /) uniquement à l'intérieur des arguments de chemin.
   - N'utilise JAMAIS de caractères jokers ou d'étoiles '*' c'est INTERDIT (ex: PAS de 'move+*.pdf+Docs'). Tu dois lister chaque fichier séparément.
   - Ne touche et n'efface JAMAIS les fichiers cachés ou système (.gitignore, desktop.ini, .DS_Store, .git).

   SYNTAXES STRICTEMENT AUTORISÉES (N'en invente AUCUNE autre) :
   • mkdir + nom_dossier
   • move + chemin_source + chemin_destination
   • rename + ancien_nom + nouveau_nom
   • delete + nom_fichier_ou_dossier
   • unzip + chemin_archive_zip
   • zip + dossier_a_zipper
   • summarize + chemin_fichier_source
   • create + chemin_fichier_vide
   • write + chemin_fichier + texte_complet
   • append + chemin_fichier + texte_a_ajouter
   • search + terme_de_recherche
   • open + chemin_fichier
   • lire + chemin_fichier + question

   Exemples valides (Cas 1) :
   create + notes.txt | mkdir + Projets | create + Projets\\index.html | write + config.py + DEBUG = True | summarize + rapport.txt + ton resume | move + rapport-resume.txt + Archives\\ | search + terme_de_recherche | open + test.html | lire + test.txt

2. CAS 2 : QUESTION GÉNÉRALE OU DISCUSSION
   Si la demande de l'utilisateur est une question de culture, d'explication, un problème de code, une discussion générale, meteo et autre ... :
   
   - Tu dois OBLIGATOIREMENT commencer l'intégralité de ta réponse par le préfixe exact 'TEXT:' (sans guillemets, immédiatement suivi du texte).
   - Rédige une réponse TRÈS COURTE (2 à 3 phrases maximum) et va droit au but.
   - Rédige ensuite ta réponse de façon naturelle, claire et concise.
   - Tu peux utiliser le formatage Markdown habituel après le préfixe 'TEXT:'.

   Exemple valide (Cas 2) :
   TEXT: Pour exécuter un script Python, ouvre ton terminal et tape la commande `python mon_script.py`
"""

admin = False

def clear():
    os.system('cls')

def saisie_dynamique(invite="Entre ton texte : "):
    texte = ""

    sys.stdout.write(invite + "[  ]\b\b")
    sys.stdout.flush()

    while True:
        char = msvcrt.getch()

        if char in (b"\r", b"\n"):
            print()
            break

        elif char == b"\x08":
            if len(texte) > 0:
                texte = texte[:-1]

        else:
            try:
                texte += char.decode("utf-8")
            except UnicodeDecodeError:
                pass

        cols = shutil.get_terminal_size().columns
        marge = len(invite) + 5
        max_taille = cols - marge

        texte_affiche = texte if len(texte) < max_taille else texte[-max_taille:]

        ligne = f"\r{invite}[ {texte_affiche} ]"

        espaces_nettoyage = " " * max(0, cols - len(ligne) - 1)
        
        sys.stdout.write(ligne + espaces_nettoyage + "\b" * len(espaces_nettoyage) + "\b\b")
        sys.stdout.flush()

    return texte

def creer_json_config():
    clear()
    rps_api_key = saisie_dynamique("Entrez votre clé d'API de Gemini : ")
    clear()
    rps_chemin_fichier = saisie_dynamique("Entrez le chemin du fichier : ")
    clear()
    valeur_base = {
        "API_KEY" : rps_api_key,
        "chemin_dossier" : rps_chemin_fichier,
        "model_AI" : "models/gemini-3.5-flash-lite",
        "DEBUG" : False
    }
    FICHIER.write_text(json.dumps(valeur_base, indent=3), encoding='utf-8')
    return valeur_base

FICHIER = Path(__file__).parent / "config.json"

if FICHIER.exists():
    config = json.loads(FICHIER.read_text(encoding="utf-8"))
else:
    config = creer_json_config()

API_KEY = config.get('API_KEY')
chemin_dossier = config.get('chemin_dossier')

try:
    client = genai.Client(api_key=API_KEY)
except Exception:
    client = None

if client:
    chat = client.chats.create(
        model=config.get('model_AI'),
        config={"system_instruction": INSTRUCTION_IA}
    )

historique = []

def enregistrer_log(msg):
    dossier_parent = Path(chemin_dossier).parent 
    fichier_log = dossier_parent / "historique.log"
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nouvelle_ligne = f"[{horodatage}] {msg}"

    lignes = []
    if fichier_log.exists():
        lignes = fichier_log.read_text(encoding="utf-8").splitlines()

    lignes.append(nouvelle_ligne)

    if len(lignes) > 1000:
        lignes = lignes[-500:]

    fichier_log.write_text("\n".join(lignes) + "\n", encoding="utf-8")

def commande_help():
    clear()
    print("=" * 60)
    print("                📖 MENU D'AIDE - COMMANDES               ")
    print("=" * 60 + "\n")
    print("  • quitter / exit / shut / shutdown        : Arrêter le programme.")
    print("=" * 60 + "\n")
    print("  • cls / clear        : Supprimer l'historique.")
    print("-" * 60)
    print("  • restart        : Redémarrer le systeme.")
    print("-" * 60)
    print("  • help / aide        : Affiche ce menu d'aide.")
    print("  • admin= [true]         : Permet d'accéder au panneau admin.")
    print("-" * 60)
    print("  • autor= [ suppr ]   : Autorise l'IA à supprimer des fichiers/dossiers.")
    print("  • autor= [ simu ]    : Permet de simuler une ou plusieurs actions de l'IA.")
    print("  • autor= [ filtre ]    : Autorise l'ia a supprimer des fichiers cachés comme .git ou __pycache__")
    print("-" * 60)
    print("  💡 Astuce : Le signe '&' permet de séparer une question\n"
          "              en plusieurs morceaux pour l'envoyer en plusieurs requêtes.")
    print("=" * 60)
    
    print("\n[ Appuyez sur une touche pour continuer... ]")


    msvcrt.getch()
    return True

def lister_fichier(max_profondeur=5, permissions_autorisees=[]):
    dossier = Path(chemin_dossier)
    if not dossier.exists() or not dossier.is_dir():
        return f"le dossier : {chemin_dossier} n'existe pas"

    ligne = []
    ignorer_filtre = "filtre" in permissions_autorisees

    for element in dossier.rglob("*"):
        chemin_relatif = element.relative_to(dossier)

        if not ignorer_filtre:
            if element.name.startswith(".") or element.name.lower() in ["desktop.ini","thumbs.db",".git", "__pycache__", "node_modules", "venv", ".vscode", "AppData"]:
                continue

            if len(chemin_relatif.parts) > max_profondeur:
                continue

            if any(p.lower() in [".git", "__pycache__", "node_modules", "venv", ".vscode", "appdata"] for p in chemin_relatif.parts):
                continue

        if element.is_file():
            extension = element.suffix if element.suffix else "aucun"
            octets = element.stat().st_size
            if octets < 1024:
                taille = f"{octets} B"
            elif octets < 1024 * 1024:
                taille = f"{round(octets / 1024, 1)} KB"
            else:
                taille = f"{round(octets / (1024 * 1024), 2)} MB"

            ligne.append(
                f"[FICHIER] Chemin: {chemin_relatif} | Ext: {extension} | Taille: {taille}"
            )

        elif element.is_dir():
            ligne.append(f"[DOSSIER] Chemin: {chemin_relatif}")

    if not ligne:
        return "Le dossier est complètement vide."

    return "\n".join(ligne)

def admin_acces():
    global admin
    mot_suivant = rps_pour_ia.split("admin=")[1].split()[0].lower() if admin == False else "true"
    admin = False

    if mot_suivant == 'true':
        clear()
        fin_acces_admin = False
        while not fin_acces_admin:
            clear()
            print("--- ACCES ADMIN ---\n")
            print("que voulez vous faire (taper q pour quitter)")
            print("1 : Modifier la clé d'API Gemini")
            print("2 : Changer le model d'IA")
            print("3 : Activer/Désactiver le mode DEBUG")
            print("4 : Modifier le chemin d'accès au dossier")
            print("5 : Voir les dernières logs")
            choix_menue_admin = msvcrt.getch().decode('utf-8')

            if choix_menue_admin == '1':
                clear()
                print(f"Modifier la cle d'API Gemini        [ Actuelle : {config['API_KEY']} ]")
                rps_changement_cle_api = saisie_dynamique("Entrez votre nouvelle cle d'API Gemini")

                if rps_changement_cle_api != "":
                    config['API_KEY'] = rps_changement_cle_api.strip()
                    FICHIER.write_text(json.dumps(config, indent=3), encoding="utf-8")
                    msg = f"🔑 Clé d'API Gemini modifier avec succès : {rps_changement_cle_api}"
                    print(msg)
                    enregistrer_log(msg)
                    print("\nAppuyer sur une touche pour continuer ...")
                    msvcrt.getch()

            elif choix_menue_admin == '2':
                clear()
                model_dispo = {
                    "models/gemini-3.5-flash-lite": " 🚀 Ultra-rapide | Recommandé #1 (500 req/jour)",
                    "models/gemini-3.1-flash-lite": " 🚀 Instantané | Backup rapide (500 req/jour)",
                    "models/gemini-3.6-flash":       " 🧠 Top intelligence Flash (20 req/jour)",
                    "models/gemini-3.5-flash":       " 🎯 Précis pour dossiers complexes (20 req/jour)",
                    "models/gemini-3-flash":         " ⚡ Rapide et logique (20 req/jour)",
                    "models/gemini-2.5-flash":       " ⚡ Stable et rapide (20 req/jour)",
                    "models/gemini-2.5-flash-lite":  " 🚀 Léger / Réserve (20 req/jour)",
                    "models/gemini-3.1-pro":         " 🧠 Raisonnement avancé & Custom Tools",
                    "gemma-4-31b-it":                  " 💥 Modèle 31B puissant (14,4k req/jour)",
                    "gemma-4-26b-it":                  " 💥 Modèle 26B hyper rapide (14,4k req/jour)",
                }
            
                print(f"--- 🤖 MODÈLES DISPONIBLES ---          [ Actuelle : {config['model_AI']} ]\n")
                for i, (model_id, desc) in enumerate(model_dispo.items(), start=1):
                    print(f"  {i:>2}. {model_id:<30} ➔ {desc}")
            
                try:
                    print()
                    choix_ia = saisie_dynamique("Entrez votre choix : ")
                    if choix_ia.isdigit():
                        index = int(choix_ia) - 1
                        if 0 <= index < len(model_dispo):
                            model_choisie = list(model_dispo.keys())[index]
            
                            config['model_AI'] = model_choisie
                            FICHIER.write_text(json.dumps(config, indent=3), encoding="utf-8")
            
                            msg = f"🤖 Model d'IA modifier avec succès : {model_choisie}"
                            print(f"\n{msg}")
                            enregistrer_log(msg)
                            print("\nAppuyer sur une touche pour continuer ...")
                            msvcrt.getch()
            
                except Exception as e:
                    print(f"❌ Erreur : {e}")
                    msvcrt.getch()

            elif choix_menue_admin == '3':
                clear()
                print(f"--- Activer / Désactivé le mode DEBUG ---          [ Actuelle : {config['DEBUG']} ]")
                print("1 : True")
                print("2 : False")
            
                rps_DEBUG = msvcrt.getch().decode('utf-8')
            
                if rps_DEBUG == '1':
                    config['DEBUG'] = True
                    print("\n✅ Mode DEBUG activé.")
                elif rps_DEBUG == '2':
                    config['DEBUG'] = False
                    print("\n✅ Mode DEBUG désactivé.")
                else:
                    print("\n❌ Choix invalide.")
                    continue

                FICHIER.write_text(json.dumps(config, indent=3), encoding="utf-8")

                msg = f"🤖 Mode DEBUG modifier avec succès : {config['DEBUG']}"
                print(f"\n{msg}")
                enregistrer_log(msg)
                print("\nAppuyer sur une touche pour continuer ...")
                msvcrt.getch()

            elif choix_menue_admin == '4':
                clear()
                print(f"Modifier le chemin d'accès du dossier        [ Actuelle : {config['chemin_dossier']} ]")
                rps_changement_chemin_dossier = saisie_dynamique("Entrez votre nouveau chemin d'accès du dossier")

                if rps_changement_chemin_dossier != "":
                    config['chemin_dossier'] = rps_changement_chemin_dossier.strip()
                    FICHIER.write_text(json.dumps(config, indent=3), encoding="utf-8")
                    msg = f"\n🛣️ Chemin d'accès au dossier modifier avec succès : {rps_changement_chemin_dossier}"
                    print(msg)
                    enregistrer_log(msg)
                    print("\nAppuyer sur une touche pour continuer ...")
                    msvcrt.getch()

            elif choix_menue_admin == '5':
                clear()
                print("--- 📜 DERNIÈRE SESSION DE LOGS ---\n")
                dossier_parent = Path(chemin_dossier).parent
                fichier_log = dossier_parent / "historique.log"

                if fichier_log.exists():
                    lignes = fichier_log.read_text(encoding='utf-8').splitlines()
                    if lignes:
                        bloc = []

                        for ligne in reversed(lignes):
                            if ("-" * 40 in ligne) or (ligne.strip().startswith("[ -") and ligne.strip().endswith("- ]")):
                                if len(bloc) > 0:
                                    break
                            bloc.append(ligne)

                        for ligne in reversed(bloc):
                            print(f"  {ligne}")

                    else:
                        print("  Le fichier log me paraît vide.")

                else:
                    print("  Aucun fichier historique.log trouvé.")

                print("\n" + "-" * 40)
                print("Que voules vous faire")
                print("1 : supprimer les logs")
                print("q : quitter")
                choix_logs = msvcrt.getch().decode('utf-8')

                if choix_logs == '1':
                    fichier_log.write_text("", encoding='utf-8')
                    print("\n🧹 Fichier historique.log vidé avec succès !")
                    print("\nAppuyer sur une touche pour cotinuer ...")
                    msvcrt.getch()

            elif choix_menue_admin == 'q':
                fin_acces_admin = True
                break

def extraire_autorisation(saisie):
    saisie_clean = saisie.strip()
    permissions = []
    demande = saisie_clean

    if saisie_clean.startswith("autor="):
        parties = saisie_clean.split(" ", 1)
        valeur_autorisation = parties[0].split("=")[1].lower()
        permissions = valeur_autorisation.split("-")
        demande = parties[1] if len(parties) > 1 else ""

    return permissions, demande

def executer_instruction(chaine_ia, permissions_autorisees=[]):
    est_simulation = "simu" in permissions
    actions_prevues = []

    if not chaine_ia or chaine_ia.strip() == "":
        print("Aucune instruction à exécuter.")
        return

    logs_a_ecrire = []
    chaine_clean = chaine_ia.strip()

    if chaine_clean.startswith("TEXT:"):
        reponse_texte = chaine_clean[5:].strip()
        print(f"\n💬 IA : {reponse_texte}\n")
        return

    actions = chaine_clean.split("|")
    dossier_base = Path(chemin_dossier)

    for action in actions:
        action = action.strip()
        if not action:
            continue

        parties = [p.strip() for p in action.split('+')]
        command = parties[0].lower()

        if est_simulation:
            if command == "move" and len(parties) >= 3:
                actions_prevues.append(f"🚚 [DÉPLACEMENT] {parties[1]} ➔ {parties[2]}")
            elif command == "mkdir" and len(parties) >= 2:
                actions_prevues.append(f"📁 [CRÉATION DOSSIER] {parties[1]}")
            elif command == "delete" and len(parties) >= 2:
                actions_prevues.append(f"🗑️ [SUPPRESSION] {parties[1]}")
            continue

        try:
            if command == 'mkdir' and len(parties) >= 2:
                nom_dossier = parties[1]
                chemin_complet = dossier_base / nom_dossier
                chemin_complet.mkdir(parents=True, exist_ok=True)
                msg = f"📁 Dossier créé : {nom_dossier}"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == "move" and len(parties) >= 3:
                source = dossier_base / parties[1]
                destination = dossier_base / parties[2]

                if not source.exists():
                    msg = f"⚠️ Fichier introuvable : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))

                msg = f"🚚 Fichier/Dossier déplacé : {parties[1]} ➔ {parties[2]}"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == "rename" and len(parties) >= 3:
                source = dossier_base / parties[1]
                destination = dossier_base / parties[2]

                if not source.exists():
                    msg = f"⚠️ Fichier introuvable : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                source.rename(destination)

                msg = f"✏️ Fichier/Dossier renommé : {parties[1]} ➔ {parties[2]}"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == 'delete' and len(parties) >= 2:
                nom_cible = parties[1]

                if nom_cible in ['.', '..', './.', '../..']:
                    msg = f"🚨 SÉCURITÉ : Suppression interdite pour '{nom_cible}'"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                cible = dossier_base / nom_cible

                if not cible.exists():
                    msg = f"❌ Erreur : '{nom_cible}' n'existe pas."
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                if 'suppr' in permissions_autorisees:
                    confirmation_delete = True
                else:
                    print(f"⚠️ Veux-tu vraiment supprimer '{nom_cible}' ? (o/n)")
                    choix = msvcrt.getch().decode('utf-8')
                    confirmation_delete = choix in ['y', 'o']

                if confirmation_delete:
                    if cible.is_file():
                        cible.unlink()
                        msg = f"🗑️ Fichier supprimé : {nom_cible}"
                    elif cible.is_dir():
                        shutil.rmtree(cible)
                        msg = f"🗑️ Dossier supprimé : {nom_cible}"
                    
                    print(msg)
                    logs_a_ecrire.append(msg)
                else:
                    msg = f"🛡️ Suppression annulée pour : {nom_cible}"
                    print(msg)
                    logs_a_ecrire.append(msg)

            elif command == 'unzip' and len(parties) >= 2:
                fichier_zip = dossier_base / parties[1]

                if not fichier_zip.exists():
                    msg = f"⚠️ Fichier ZIP introuvable : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                dossier_destination = fichier_zip.parent

                with zipfile.ZipFile(fichier_zip, "r") as zip_ref:
                    zip_ref.extractall(dossier_destination)

                msg = f"📦 Archive dézipée dans son dossier d'origine : {parties[1]}"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == 'zip' and len(parties) >= 2:
                dossier_cible = dossier_base / parties[1]

                if not dossier_cible.exists():
                    msg = f"⚠️ Dossier ou fichier à ziper introuvable : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                nom_archive_sans_ext = dossier_cible.parent / dossier_cible.name

                shutil.make_archive(
                    base_name=str(nom_archive_sans_ext),
                    format='zip',
                    root_dir=str(dossier_cible.parent),
                    base_dir=str(dossier_cible.name)
                )

                msg = f"📦 Dossier zipé avec succès : {parties[1]}.zip"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == "summarize" and len(parties) >= 2:
                fichier_source = dossier_base / parties[1]

                if not fichier_source.exists():
                    msg = f"⚠️ Fichier source introuvable pour le résumé : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                try:
                    contenu_fichier = fichier_source.read_text(encoding="utf-8", errors="ignore")

                    prompt_resume = f"Fais un résumé clair et concis du contenu du fichier suivant :\n\n{contenu_fichier}"

                    print("🤖 Génération du résumé par l'IA en cours...")
                    response = chat.send_message(prompt_resume)
                    contenu_resume = response.text

                    nom_resume = f"{fichier_source.stem}-resume{fichier_source.suffix}"
                    fichier_dest = fichier_source.parent / nom_resume

                    fichier_dest.write_text(contenu_resume, encoding="utf-8")

                    msg = f"📝 Fichier résumé généré et enregistré avec succès : {nom_resume}"
                    print(msg)
                    logs_a_ecrire.append(msg)

                except Exception as e:
                    msg = f"⚠️ Erreur lors de la génération ou de l'écriture du résumé pour {parties[1]} : {e}"
                    print(msg)
                    logs_a_ecrire.append(msg)

            elif command == 'create' and len(parties) >= 2:
                chemin_relatif = parties[1]
                fichier_cible = dossier_base / chemin_relatif

                fichier_cible.parent.mkdir(parents=True, exist_ok=True)
                fichier_cible.touch(exist_ok=True)
                msg = f"📄 Fichier vide créé : {chemin_relatif}"
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == 'write' and len(parties) >= 3:
                fichier_cible = dossier_base / parties[1]
                contenue = parties[2]

                if not fichier_cible.exists():
                    msg = f"⚠️ Fichier introuvable pour écriture : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                fichier_cible.write_text(contenue, encoding='utf-8')
                msg = f"✏️ Contenu de {parties[1]} mis à jour."
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == 'append' and len(parties) >= 3:
                fichier_cible = dossier_base / parties[1]
                contenue_a_ajouter = parties[2]
                
                if not fichier_cible.exists():
                    msg = f"⚠️ Fichier introuvable pour écriture : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                with open(fichier_cible, "a", encoding='utf-8') as f:
                    f.write("\n" + contenue_a_ajouter)
                msg = f"➕ Contenu ajouté à {parties[1]}."
                print(msg)
                logs_a_ecrire.append(msg)

            elif command == 'search' and len(parties) >= 2:
                recherche = " ".join (parties[1:]).strip().lower()
                fichier_trouver = None
                extrait_texte = ""

                for fichier in dossier_base.rglob("*"):
                    if fichier.is_file() and fichier.suffix in [".txt", ".md", ".json", ".py", "html"]:
                        try:
                            contenu = fichier.read_text(encoding='utf-8', errors='ignore')
                            contenu_lower = contenu.lower()

                            if recherche in contenu.lower():

                                fichier_trouver = fichier.name

                                position = contenu_lower.find(recherche)
                                début = max(0, position - 150)
                                fin = min(len(contenu), position + 150)

                                extrait_texte = contenu[début:fin]
                                break

                        except Exception:
                            continue

                if fichier_trouver:
                    prompt = f"L'utilisateur cherche '{recherche}'. J'ai trouvé ce passage dans le fichier '{fichier_trouver}' :\n\n{extrait_texte}\n\nRéponds-lui brièvement pour lui indiquer ce qu'il cherchait."
                    reponse = chat.send_message(prompt)
                    print(f"\n🤖 Gemini : {reponse.text}\n")

                else:
                    print(f"\n❌ Aucun fichier ne parle de '{recherche}'.\n")

            elif command == 'open'and len(parties) >= 2:
                chemin_cible = dossier_base / parties[1]

                if not chemin_cible.exists():
                    msg = f"⚠️ Fichier introuvable pour ouverture : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                extensions_sensibles = ['.exe', '.bat', '.cmd', '.vbs', '.js', '.ps1', '.msi']

                if chemin_cible.suffix.lower() in extensions_sensibles:
                    print(f"\n⚠️ ATTENTION : Le fichier '{parties[1]}' est un exécutable/script sensible.")
                    confirmation = saisie_dynamique("Voulez-vous vraiment l'ouvrir ? (o/n) : ")

                    if confirmation in ['n', 'non', 'no']:
                        msg = f"❌ Ouverture annulée par l'utilisateur pour : {parties[1]}"
                        print(msg)
                        logs_a_ecrire.append(msg)
                        continue

                try:
                    os.startfile(str(chemin_cible))
                    msg = f"📂 Fichier ouvert sur l'ordinateur : {parties[1]}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                except Exception as e:
                    msg = f"⚠️ Erreur lors de l'ouverture de {parties[1]} : {e}"
                    print(msg)
                    logs_a_ecrire.append(msg)

            elif command == 'lire' and len(parties) >= 3:
                fichier_cible = dossier_base / parties[1]
                question = " ".join(parties[2:]) if len(parties) > 2 else "analyse ce fichier"

                if not fichier_cible.exists():
                    msg = f"⚠️ Fichier introuvable pour la lecture : {fichier_cible}"
                    print(msg)
                    logs_a_ecrire.append(msg)
                    continue

                try:
                    contenu_fichier = fichier_cible.read_text(encoding="utf-8", errors="ignore")
                    prompt_complet = f"Voici le contenu du fichier '{fichier_cible}' :\n\n{contenu_fichier}\n\nMa demande : {question}"

                    print(f"🤖 Envoi du fichier '{fichier_cible}' et de ta demande à l'IA...")
                    response = chat.send_message(prompt_complet)

                    response_propre = response.text.replace("TEXT:", "").strip()

                    print(f"\nIA : {response_propre}\n")

                    msg = f"📖 Fichier '{fichier_cible}' lu et envoyé à l'IA avec succès."
                    logs_a_ecrire.append(msg)

                except Exception as e:
                    msg = f"⚠️ Erreur lors de la lecture ou de l'envoi du fichier {fichier_cible} : {e}"
                    print(msg)
                    logs_a_ecrire.append(msg)

        except Exception as e:
            msg = f"⚠️ Erreur critique sur '{action}' : {e}"
            print(msg)
            logs_a_ecrire.append(msg)

    séparateur = "[ " + "-"*90 + " ]"
    logs_a_ecrire.append(séparateur)

    for ligne_log in logs_a_ecrire:
        enregistrer_log(ligne_log)

    if est_simulation:
        clear()
        print("\n🔍 --- APERÇU DU PLAN D'ACTION (MODE SIMULATION) ---\n")

        if not actions_prevues:
            print("  Aucune action prévue par l'IA.")
            return

        for action in actions_prevues:
            print(f"  {action}")

terminer = False

clear()

while not terminer:
    clear()
    print("--- AI D'ORGANISATION LOCAL ---\n")
    print("( taper quitter pour quitter, taper help pour plus d'aide  )\n")
    if not historique:
        print("")
    else:
        print("Vous : ")
        for i, dem in enumerate(historique, 1):
          suffixe = "ère" if i == 1 else "ème"
          print(f" • {i}{suffixe} demande : {dem}")
        print()

    rps_pour_ia = saisie_dynamique("Entrez votre demande a l'ia : ")

    if rps_pour_ia.strip().lower() in ['quitter', 'shut', 'shutdown', 'exit']:
        terminer = True
        break

    elif rps_pour_ia in ['help', 'aide']:
        clear()
        commande_help()
        continue

    elif rps_pour_ia == 'restart':
        print("\n🔄 Redémarrage du programme en cours...")
        enregistrer_log("🔄 Redémarrage manuel du programme.")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    elif rps_pour_ia in ['cls', 'clear']:
        historique = []
        clear()
        continue

    if not rps_pour_ia.strip():
        continue

    if "admin=" in rps_pour_ia:
        admin_acces()
        continue

    print("\nVeuillez appuyer sur une touche pour valider (cliquer sur 'q' pour annuler)")
    try:
        valider = msvcrt.getch().decode("utf-8").lower()
    except UnicodeDecodeError:
        valider = ""

    if valider == "q":
        print("\nAction annulée.")
        time.sleep(1)
        continue

    historique.append(rps_pour_ia)

    sous_requetes = [req.strip() for req in rps_pour_ia.split("&") if req.strip()]
    total_etape = len(sous_requetes)

    print(f"\n⚙️ {total_etape} étape(s) en cours de traitement...")

    for index, sous_req in enumerate(sous_requetes, start=1):
        permissions, demande_clean = extraire_autorisation(sous_req)

        if not demande_clean:
            continue

        print(f'\n--- [Étape {index}/{total_etape}] Traitement : "{demande_clean}" ---')

        contenu_dossier = lister_fichier(permissions_autorisees=permissions)

        message_complet = (f"Contenu du dossier :\n{contenu_dossier}\n\nMa demande : {demande_clean}\n\n")

        print("🤖 Réflexion de l'IA en cours...\n")
        try:
            reponse = chat.send_message(message_complet)
            executer_instruction(reponse.text, permissions)

            print(f"[ DEBUG ] {reponse.text}") if config.get("DEBUG") else None

        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                msg_erreur = "⚠️ L'IA est surchargée (Erreur 503). Patiente un instant..."
            elif "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                msg_erreur = "⚠️ Vous avez dépassé votre quota par minute"
            elif "404" in str(e):
                msg_erreur = f"⚠️ Le model d'IA choisie est introuvable : {config['model_AI']}"
            else:
                msg_erreur = f"❌ Erreur : {e}"

            if msg_erreur:
                print(msg_erreur)
                enregistrer_log(msg_erreur)

                print("Voulez vous allez dans le pannel admin pour modifier l'AI ( o/n )")
                choix_error = msvcrt.getch().decode('utf-8').strip().lower()

                if choix_error in ['y', 'o']:
                    admin = True
                    admin_acces()
                    continue

    print("\nAppuyez sur une touche pour continuer...")
    msvcrt.getch()