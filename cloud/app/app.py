import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from llm_call import (
    chat,
    ChatResponse,
    call_custom_llm,
    insert_univers,
    ask_univers_extraction,
    get_univers_id,
    insert_factions,
    ask_faction_extraction,
    insert_location,
    ask_location_extraction,
    insert_cultures,
    ask_culture_extraction,
    insert_prompt_answer,
    ask_objets_extraction,
    insert_objets,
    ask_personnages_extraction,
    insert_personnages,
)
from db_path import get_db_path
from rag import rag_answer, rag_update_db, pretty_sql, clear_cache
import argparse

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/parse_and_save", methods=["POST"])
def parse_and_save():
    response_content = request.form.get("response_content")
    prompt = request.form.get("prompt", "")
    llm_model = request.form.get("llm_model", "llama3.2")

    if not response_content:
        return {"error": "No response content provided"}, 400

    try:
        univers_data_list = ask_univers_extraction(response_content, model=llm_model)

        if isinstance(univers_data_list, list) and univers_data_list:
            univers_data = univers_data_list[0]
        else:
            return {"error": "Failed to extract universe data"}, 500

        factions_data = ask_faction_extraction(response_content, model=llm_model)
        locations_data = ask_location_extraction(response_content, model=llm_model)
        cultures_data = ask_culture_extraction(response_content, model=llm_model)
        objects_data = ask_objets_extraction(response_content, model=llm_model)
        personnages_data = ask_personnages_extraction(response_content, model=llm_model)

        conn = sqlite3.connect(get_db_path())
        try:
            insert_univers(univers_data, conn=conn)
            univers_id = get_univers_id(conn=conn)

            insert_factions(factions_data, univers_id=univers_id, conn=conn)
            insert_location(locations_data, univers_id=univers_id, conn=conn)
            insert_cultures(cultures_data, univers_id=univers_id, conn=conn)
            insert_objets(objects_data, univers_id=univers_id, conn=conn)
            insert_personnages(personnages_data, univers_id=univers_id, conn=conn)
            insert_prompt_answer(prompt, response_content, univers_id=univers_id, conn=conn)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return redirect(url_for("wiki_home"))

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/", methods=["GET", "POST"])
def prompt_page():
    if request.method == "POST":
        if "reprompt" in request.form:
            return render_template(
                "prompt.html",
                prompt=request.form["prompt"],
                previous_response=request.form.get("previous_response", ""),
                is_reprompt=True,
            )

        prompt = request.form["prompt"]
        llm_model = request.form.get("llm_model", "llama3.2")

        if llm_model == "custom-llm":
            try:
                system_prompt = """Vous êtes un assistant créateur d'univers fantastiques pour Donjons & Dragons.
                    Créez des descriptions détaillées, riches et cohérentes d'univers imaginaires,
                    incluant des factions, des lieux, des cultures, des personnages, des objets et d'autres éléments utiles
                    à un Maître du Jeu pour créer un cadre de campagne.
                    Vos réponses doivent être imaginatives, cohérentes et adaptées à un univers de D&D."""
                
                full_prompt = f"{system_prompt}\n\nRequête de l'utilisateur : {prompt}"
                
                response_content = call_custom_llm(full_prompt)
                
                return render_template(
                    "prompt.html",
                    prompt=prompt,
                    response=response_content,
                    selected_model=llm_model,
                )
            except Exception as e:
                return render_template("prompt.html", prompt=prompt, error=str(e), selected_model=llm_model)
        else:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": """Vous êtes un assistant créateur d'univers fantastiques pour Donjons & Dragons.
                            Créez des descriptions détaillées, riches et cohérentes d'univers imaginaires,
                            incluant des factions, des lieux, des cultures, des personnages, des objets et d'autres éléments utiles
                            à un Maître du Jeu pour créer un cadre de campagne.
                            Vos réponses doivent être imaginatives, cohérentes et adaptées à un univers de D&D.""",
                    }
                ]

                # Si c'est une continuation de conversation, inclure les échanges précédents
                if (
                    "previous_response" in request.form
                    and request.form.get("is_reprompt") == "true"
                ):
                    previous_prompt = request.form.get("original_prompt", prompt)
                    previous_response = request.form.get("previous_response", "")

                    messages.append({"role": "user", "content": previous_prompt})
                    messages.append({"role": "assistant", "content": previous_response})

                    messages.append(
                        {
                            "role": "system",
                            "content": "L'utilisateur n'était pas satisfait de votre réponse précédente. Veuillez affiner votre réponse en fonction de leur nouvelle requête.",
                        }
                    )

                messages.append({"role": "user", "content": prompt})

                response: ChatResponse = chat(
                    model=llm_model,
                    messages=messages,
                )

                response_content = response.message.content

                return render_template(
                    "prompt.html",
                    prompt=prompt,
                    response=response_content,
                    selected_model=llm_model,
                )
            except Exception as e:
                return render_template("prompt.html", prompt=prompt, error=str(e))

    return render_template("prompt.html")
    
@app.route("/rag", methods=["GET", "POST"])
def rag_page():
    conn = get_db_connection()

    universes = conn.execute("SELECT * FROM univers").fetchall()

    if request.method == "POST":
        question = request.form.get("question")
        univers_id = request.form.get("universe")
        action = request.form.get("action")

        if action == "update":
            try:
                script = rag_update_db(question, univers_id)
            except Exception as e:
                error = f"❌ Erreur lors de la mise à jour : {str(e)}"
                conn.close()
                return render_template("rag.html",
                                    universes=universes,
                                    question=question,
                                    selected_universe=univers_id,
                                    action="update",
                                    error=error)

            dangerous_keywords = ["drop", "delete", "truncate", "alter"]
            lowered_script = script.lower()
            if any(keyword in lowered_script for keyword in dangerous_keywords):
                error = "⛔ Le script SQL généré contient une opération interdite (DROP, DELETE, etc.). Veuillez reformuler votre requête."
                conn.close()
                return render_template("rag.html",
                                    universes=universes,
                                    question=question,
                                    selected_universe=univers_id,
                                    action="update",
                                    error=error)

            if request.form.get("confirm") == "yes":
                try:
                    conn.execute(script)
                    conn.commit()
                    clear_cache(int(univers_id))
                    
                    conn.close()
                    message = "✅ Mise à jour effectuée avec succès. Le cache a été vidé pour refléter les changements."
                    return render_template("rag.html",
                                           response=message,
                                           universes=universes,
                                           question=question,
                                           selected_universe=univers_id,
                                           action=action)
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    error = f"❌ Erreur lors de la mise à jour : {str(e)}"
                    return render_template("rag.html",
                                        universes=universes,
                                        question=question,
                                        selected_universe=univers_id,
                                        action=action,
                                        error=error)
            else:
                readable_table = pretty_sql(script)
                conn.close()
                return render_template("rag.html",
                                       readable_table=readable_table,
                                       universes=universes,
                                       question=question,
                                       selected_universe=univers_id,
                                       action=action,
                                       generated_sql=script,
                                       pending_validation=True)

        else:
            try:
                response = rag_answer(question, int(univers_id))
                conn.close()
                return render_template("rag.html",
                                       response=response,
                                       universes=universes,
                                       question=question,
                                       selected_universe=univers_id,
                                       action=action)
            except Exception as e:
                conn.close()
                error = f"❌ Erreur lors de la recherche : {str(e)}"
                return render_template("rag.html",
                                    universes=universes,
                                    question=question,
                                    selected_universe=univers_id,
                                    action=action,
                                    error=error)

    return render_template("rag.html", universes=universes)

@app.route("/rag/clear-cache", methods=["POST"])
def clear_rag_cache():
    try:
        univers_id = request.form.get("univers_id")
        
        if univers_id:
            clear_cache(int(univers_id))
            message = f"Cache vidé pour l'univers {univers_id}"
        else:
            clear_cache()
            message = "Cache complètement vidé"
            
        return {"success": True, "message": message}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/wiki")
def wiki_home():
    try:
        conn = get_db_connection()

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()

        universes = conn.execute("SELECT id, name FROM univers ORDER BY id DESC").fetchall()

        conn.close()
        return render_template("wiki_home.html", tables=tables, universes=universes)
    except Exception as e:
        return render_template("wiki_home.html", error=str(e), tables=[], universes=[])

@app.route("/wiki/universe/<int:univers_id>")
def wiki_universe(univers_id):
    try:
        conn = get_db_connection()
        
        universe = conn.execute("SELECT * FROM univers WHERE id = ?", (univers_id,)).fetchone()
        if not universe:
            conn.close()
            return render_template("wiki_universe.html", error="Univers non trouvé", univers_id=univers_id)
        
        factions = conn.execute("SELECT * FROM faction WHERE univers_id = ?", (univers_id,)).fetchall()
        locations = conn.execute("SELECT * FROM location WHERE univers_id = ?", (univers_id,)).fetchall()
        cultures = conn.execute("SELECT * FROM culture WHERE univers_id = ?", (univers_id,)).fetchall()
        personnages = conn.execute("SELECT * FROM personnages WHERE univers_id = ?", (univers_id,)).fetchall()
        objets = conn.execute("SELECT * FROM objets WHERE univers_id = ?", (univers_id,)).fetchall()
        
        prompt_answers = conn.execute("SELECT * FROM prompt_answers WHERE univers_id = ? ORDER BY created_at DESC", (univers_id,)).fetchall()
        
        all_universes = conn.execute("SELECT id, name FROM univers ORDER BY id DESC").fetchall()
        
        conn.close()
        
        return render_template("wiki_universe.html", 
                              universe=universe,
                              factions=factions,
                              locations=locations,
                              cultures=cultures,
                              personnages=personnages,
                              objets=objets,
                              prompt_answers=prompt_answers,
                              all_universes=all_universes,
                              univers_id=univers_id)
    except Exception as e:
        return render_template("wiki_universe.html", error=str(e), univers_id=univers_id)

@app.route('/wiki/<table>', methods=['GET'])
def wiki_table(table):
    try:
        conn = get_db_connection()

        filter_id = request.args.get("univers_id", "")

        if filter_id:
            if table.lower() == "univers":
                query = f"SELECT * FROM {table} WHERE id = ?"
                print(
                    f"Executing filtered query for univers: {query} with ID: {filter_id}"
                )
                cursor = conn.execute(query, (filter_id,))
            else:
                query = f"SELECT * FROM {table} WHERE univers_id = ?"
                print(f"Executing filtered query: {query} with univers_id: {filter_id}")
                cursor = conn.execute(query, (filter_id,))
        else:
            query = f"SELECT * FROM {table}"
            cursor = conn.execute(query)

        columns = [description[0] for description in cursor.description]

        rows = cursor.fetchall()

        conn.close()

        return render_template(
            "wiki_table.html",
            table=table,
            rows=rows,
            columns=columns,
            current_filter=filter_id,
        )
    except Exception as e:
        return render_template("wiki_table.html", table=table, error=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=False)