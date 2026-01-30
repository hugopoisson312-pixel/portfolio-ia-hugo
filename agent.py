import os
import asyncio
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, function_tool

# 1. Chargement et vérification des variables d'environnement
load_dotenv()

def get_index():
    try:
        idx = Index.from_env()
        # Test de connexion rapide
        idx.info()
        return idx
    except Exception as e:
        print(f"⚠️ Erreur Upstash : Vérifiez vos clés dans le fichier .env ({e})")
        return None

index = get_index()

# 2. Définition de la Tool avec gestion de contexte améliorée
@function_tool
def rechercher_informations(question: str) -> str:
    """
    Recherche des informations précises sur le profil de Hugo Poisson (compétences, 
    projets, formation, expériences) dans la base de données vectorielle.
    """
    if not index:
        return "Désolé, je ne peux pas accéder à ma base de connaissances pour le moment."
    
    # Recherche hybride (Dense + Sparse) grâce à la config Upstash
    # top_k=5 pour avoir plus de contexte si le sujet est vaste
    resultats = index.query(
        data=question, 
        top_k=5, 
        include_metadata=True, 
        include_data=True
    )
    
    if not resultats:
        return "Aucune information spécifique trouvée sur ce sujet dans le portfolio."

    # Construction du contexte avec séparateurs clairs
    contexte_formate = "Voici les extraits pertinents trouvés dans le portfolio :\n"
    for res in resultats:
        # On ne garde que les résultats avec un score de similarité correct (> 0.5)
        if res.score > 0.5:
            source = res.metadata.get('source', 'Document général')
            section = res.metadata.get('section', 'Inconnu')
            contexte_formate += f"\n[Source: {source} | Section: {section}]\n{res.data}\n"
    
    return contexte_formate

# 3. Configuration de l'Agent avec un "Persona" fort
instructions_expert = """
Tu es l'assistant IA exclusif de Hugo Poisson, étudiant en BUT Science des Données à Niort.
Ton objectif est de valoriser son profil auprès des recruteurs.

CONSIGNES DE RÉPONSE :
1. ANALYSE : Utilise toujours 'rechercher_informations' avant de répondre, sauf pour les salutations.
2. SOURCE : Cite toujours brièvement tes sources (ex: "D'après ses projets académiques...").
3. TON : Reste professionnel, dynamique et encourageant. Utilise le "il" pour parler de Hugo.
4. HONNÊTETÉ : Si une information n'est pas dans la base, réponds : "Je n'ai pas de précision à ce sujet, mais vous pouvez contacter Hugo directement pour en discuter."
5. FORMAT : Utilise des listes à puces si la réponse est longue pour faciliter la lecture.
"""

mon_agent = Agent(
    name="Agent Hugo Poisson",
    instructions=instructions_expert,
    model="gpt-4.1-nano", # Modèle imposé
    tools=[rechercher_informations]
)

# 4. Boucle principale avec gestion de l'historique (Mémoire)
async def main():
    print("🚀 Agent de Hugo Poisson opérationnel !")
    print("💡 Posez-moi des questions sur ses projets, ses technos ou son alternance.")
    
    # Liste pour stocker l'historique des messages et simuler une mémoire
    history = []
    
    while True:
        try:
            user_input = input("\n👤 Vous : ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["q", "quit", "exit"]:
                print("👋 Au revoir !")
                break
            
            print("🤖 Réflexion...", end="\r")
            
            # On passe 'history' pour que l'agent se souvienne des questions précédentes
            result = await Runner.run(mon_agent, user_input, history=history)
            
            # Mise à jour de l'historique pour la prochaine question
            history.extend(result.final_messages)
            
            print(f"🤖 Agent : {result.final_output}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    asyncio.run(main())