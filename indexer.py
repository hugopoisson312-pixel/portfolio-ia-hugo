import os
import glob
import hashlib
from dotenv import load_dotenv
from upstash_vector import Index

# 1. Configuration et Sécurité
load_dotenv()

def get_index():
    try:
        # Utilise automatiquement UPSTASH_VECTOR_REST_URL et UPSTASH_VECTOR_REST_TOKEN du .env
        return Index.from_env()
    except Exception as e:
        print(f"❌ Erreur de connexion Upstash : {e}")
        return None

def generate_unique_id(content):
    """Crée un ID unique basé sur le contenu pour éviter les doublons."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def chunk_markdown_file(file_path):
    """
    Découpe intelligemment par section et enrichit les métadonnées.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(file_path)
    # Découpage par titre de niveau 2 comme demandé
    sections = content.split('\n## ')
    
    chunks = []
    
    # On traite la première section (souvent le titre # H1)
    first_section = sections[0].strip()
    if first_section:
        chunks.append({
            "id": f"{filename}_header",
            "data": first_section,
            "metadata": {"source": filename, "type": "header", "section": "Introduction"}
        })

    # On traite les sections suivantes (les ## H2)
    for i, section in enumerate(sections[1:], 1):
        full_text = f"## {section.strip()}"
        
        # Extraction du titre de la section pour les métadonnées
        section_title = section.split('\n')[0].strip()
        
        chunks.append({
            "id": f"{filename}_sec_{i}_{generate_unique_id(full_text)[:8]}",
            "data": full_text,
            "metadata": {
                "source": filename,
                "section": section_title,
                "project": "Portfolio Hugo Poisson"
            }
        })
        
    return chunks

def main():
    index = get_index()
    if not index: return

    # Chemin vers ton dossier data
    md_files = glob.glob("data/*.md")
    
    if not md_files:
        print("⚠️ Dossier 'data/' vide. Vérifie tes fichiers .md !")
        return

    all_vectors = []
    print(f"🔍 Analyse de {len(md_files)} fichiers...")

    for file_path in md_files:
        file_chunks = chunk_markdown_file(file_path)
        all_vectors.extend(file_chunks)
        print(f"✅ {os.path.basename(file_path)} : {len(file_chunks)} chunks extraits.")

    # Envoi par paquets (batch) pour plus de stabilité
    if all_vectors:
        print(f"🚀 Upsert de {len(all_vectors)} vecteurs vers Upstash...")
        try:
            # Upsert permet de mettre à jour si l'ID existe déjà
            index.upsert(vectors=all_vectors)
            print("\n✨ Base de données synchronisée avec succès !")
            print(f"💡 Rappel : Modèle utilisé : BAAI/bge-m3 (Hybrid)")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    main()