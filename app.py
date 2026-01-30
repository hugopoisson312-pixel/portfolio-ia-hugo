import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, function_tool

# 1. Configuration de la page Streamlit
st.set_page_config(
    page_title="Hugo Poisson - Assistant IA", 
    page_icon="📊", 
    layout="wide"
)

# Chargement des variables
load_dotenv()

# --- CONSTANTE : LIMITE DE QUESTIONS ---
MAX_QUESTIONS = 5

# 2. Sidebar : Présentation & Contact
with st.sidebar:
    st.title("👨‍💻 Profil")
    st.image("https://via.placeholder.com/150", caption="Hugo Poisson") 
    st.markdown("""
    **Hugo Poisson**
    Étudiant en BUT Science des Données
    Niort (79)
    
    ---
    ### 🎯 Objectif
    Recherche d'alternance en Data Analyse / Engineering pour Septembre 2025.
    
    ### 🛠️ Tech Stack
    - Python, R, SAS
    - SQL (PostgreSQL)
    - Power BI & Tableau
    """)
    
    # On affiche le compteur dans la sidebar pour info
    if "interaction_count" in st.session_state:
        restantes = MAX_QUESTIONS - st.session_state.interaction_count
        if restantes > 0:
            st.info(f"💬 Questions restantes : **{restantes}**")
        else:
            st.warning("⛔ Session terminée")

    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = []
        st.session_state.interaction_count = 0  # On remet le compteur à 0
        st.rerun()

# 3. Connexion Upstash
@st.cache_resource
def get_index():
    try:
        return Index.from_env()
    except Exception as e:
        st.error(f"Erreur Upstash : {e}")
        return None

index = get_index()

# 4. Définition de l'outil RAG
@function_tool
def rechercher_informations(question: str) -> str:
    """Recherche des infos sur le parcours et les compétences de Hugo Poisson."""
    if not index:
        return "Erreur : La base de données est indisponible."
    
    with st.status("🔍 Analyse du portfolio...", expanded=False) as status:
        res = index.query(data=question, top_k=5, include_metadata=True, include_data=True)
        status.update(label="Information trouvée !", state="complete")
        
    if not res:
        return "Aucune information trouvée."

    contexte = ""
    for r in res:
        contexte += f"---\nSource: {r.metadata.get('source')} | Section: {r.metadata.get('section')}\n{r.data}\n"
    return contexte

# 5. Initialisation de l'Agent, de l'Historique et du COMPTEUR
if "agent" not in st.session_state:
    st.session_state.agent = Agent(
        name="Expert Hugo",
        instructions="""Tu es l'assistant de Hugo Poisson. 
        Réponds de manière pro et concise. 
        Cite ses compétences (Python, R, SQL) et ses projets (RAG, SAé).
        Utilise TOUJOURS 'rechercher_informations' avant de répondre.""",
        model="gpt-4.1-nano",
        tools=[rechercher_informations]
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# NOUVEAU : Initialisation du compteur
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

# 6. Interface de Chat
st.title("🤖 Assistant Virtuel")
st.info("Bonjour ! Je suis l'IA de Hugo. Je peux vous parler de sa formation à Niort, de ses projets BI ou de sa maîtrise de Python.")

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LOGIQUE DE LIMITATION ---

if st.session_state.interaction_count < MAX_QUESTIONS:
    # Tant qu'on n'a pas atteint la limite, on affiche la zone de saisie
    placeholder_text = f"Posez votre question ({MAX_QUESTIONS - st.session_state.interaction_count} restantes)..."
    
    if prompt := st.chat_input(placeholder_text):
        # 1. Incrémenter le compteur
        st.session_state.interaction_count += 1
        
        # 2. Traitement habituel
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = asyncio.run(Runner.run(st.session_state.agent, prompt))
                full_response = response.final_output
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Petit rechargement pour mettre à jour le compteur visuel immédiatement
                st.rerun() 
            except Exception as e:
                st.error(f"Erreur : {e}")

else:
    # Si la limite est atteinte, on affiche le message de contact
    st.markdown("---")
    st.warning("🚫 **Vous avez atteint la limite de 5 questions pour cette session.**")
    st.success("Pour en savoir plus ou convenir d'un entretien, contactez-moi directement :")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        📧 **Email** [hugo.poisson@etu.univ-poitiers.fr](mailto:hugo.poisson@etu.univ-poitiers.fr)
        """)
    with col2:
        st.markdown("""
        🔗 **LinkedIn** [linkedin.com/in/hugo-poisson](https://www.linkedin.com/in/hugo-poisson)
        """)
        
    if st.button("🔄 Recommencer une nouvelle session"):
        st.session_state.messages = []
        st.session_state.interaction_count = 0
        st.rerun()