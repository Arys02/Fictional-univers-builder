from llm_call import *

print("start")
# Prompt au LLM
response: ChatResponse = chat(model='llama3.2', messages=[
    {
        'role': 'user',
        'content': "Génère moi un univers peuplé de dragons et d'objets qui parlent"
    },
])

# Réponse du LLM
response_content = response.message.content

# On extrait et insere l'univers
print("insert univers")
insert_univers(ask_univers_extraction(response_content))
univers_id = get_univers_id()
print("univers_id", univers_id)
# On insère les factions, les lieux et les cultures dans la base de données
print("insert factions")
insert_factions(ask_faction_extraction(response_content), univers_id=univers_id)
print("insert locations")
insert_location(ask_location_extraction(response_content), univers_id=univers_id)
print("insert cultures")
insert_cultures(ask_culture_extraction(response_content), univers_id=univers_id)
print("done")