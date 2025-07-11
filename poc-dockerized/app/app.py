import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from llm_call import (
    chat,
    ChatResponse,
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
from rag import rag_answer, rag_update_db, pretty_sql

app = Flask(__name__)

# import os


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


# Initialize the database at startup
with get_db_connection() as conn:
    print("Database initialized with required tables")


@app.route("/parse_and_save", methods=["POST"])
def parse_and_save():
    # Récupérer le contenu de la réponse
    response_content = request.form.get("response_content")
    prompt = request.form.get("prompt", "")
    llm_model = request.form.get("llm_model", "llama3.2")

    if not response_content:
        return {"error": "No response content provided"}, 400

    try:
        # Extraction des données
        print("Extracting universe data...")
        univers_data_list = ask_univers_extraction(response_content, model=llm_model)

        # Prendre le premier élément de la liste
        if isinstance(univers_data_list, list) and univers_data_list:
            univers_data = univers_data_list[0]  # ← Correction ici
        else:
            return {"error": "Failed to extract universe data"}, 500

        # Suite du code pour les autres extractions...
        factions_data = ask_faction_extraction(response_content, model=llm_model)
        locations_data = ask_location_extraction(response_content, model=llm_model)
        cultures_data = ask_culture_extraction(response_content, model=llm_model)
        objects_data = ask_objets_extraction(response_content, model=llm_model)
        personnages_data = ask_personnages_extraction(response_content, model=llm_model)

        # Connexion à la base de données
        conn = sqlite3.connect(get_db_path())
        try:
            # Insérer l'univers et récupérer son ID
            insert_univers(univers_data, conn=conn)
            univers_id = get_univers_id(conn=conn)

            # Insérer les autres éléments
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
    print("Route accessed with method:", request.method)

    if request.method == "POST":
        print("Form data received:", request.form)

        # Check if this is a reprompt
        if "reprompt" in request.form:
            # Return to form with the existing prompt for editing
            return render_template(
                "prompt.html",
                prompt=request.form["prompt"],
                previous_response=request.form.get("previous_response", ""),
                is_reprompt=True,
            )

        prompt = request.form["prompt"]
        llm_model = request.form.get("llm_model", "llama3.2")
        print("Prompt:", prompt)
        print("LLM Model:", llm_model)

        # Get response from LLM
        print("Calling LLM...")
        try:
            # Build message list with system prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are a fantasy world builder assistant for Dungeons & Dragons.
                        Create detailed, rich, and coherent descriptions of fantasy worlds, 
                        including factions, locations, cultures, characters, objects, and other elements that would be useful
                        for a Dungeon Master creating a campaign setting. 
                        Your responses should be imaginative, internally consistent, and appropriate for a D&D setting.""",
                }
            ]

            # Si c'est une continuation de conversation, inclure les échanges précédents
            if (
                "previous_response" in request.form
                and request.form.get("is_reprompt") == "true"
            ):
                previous_prompt = request.form.get("original_prompt", prompt)
                previous_response = request.form.get("previous_response", "")

                # Add the previous exchange
                messages.append({"role": "user", "content": previous_prompt})
                messages.append({"role": "assistant", "content": previous_response})

                # Add a system message requesting refinement
                messages.append(
                    {
                        "role": "system",
                        "content": "The user wasn't fully satisfied with your previous response. Please refine your answer based on their new prompt.",
                    }
                )

            # Add the current prompt
            messages.append({"role": "user", "content": prompt})

            # Make the API call
            response: ChatResponse = chat(
                model=llm_model,
                messages=messages,
            )
            print("LLM response received")

            # Extract the response content
            response_content = response.message.content
            print("Response content extracted")

            return render_template(
                "prompt.html",
                prompt=prompt,
                response=response_content,
                selected_model=llm_model,
            )
        except Exception as e:
            print("Error occurred:", str(e))
            return render_template("prompt.html", prompt=prompt, error=str(e))

    return render_template("prompt.html")
    
@app.route("/rag", methods=["GET", "POST"])
def rag_page():
    conn = get_db_connection()
    print("Connected to database")

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

            # Vérification des opérations interdites
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
                    
                    # Vider le cache pour cet univers après mise à jour
                    from rag import clear_cache
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
    """Route pour vider le cache RAG"""
    try:
        from rag import clear_cache
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
        print("Connected to database")

        # Get list of tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        print(f"Found {len(tables)} tables: {[t[0] for t in tables]}")

        # Get list of universes for the new wiki view
        universes = conn.execute("SELECT id, name FROM univers ORDER BY id DESC").fetchall()
        print(f"Found {len(universes)} universes")  

        conn.close()
        return render_template("wiki_home.html", tables=tables, universes=universes)
    except Exception as e:
        print(f"Error in wiki_home: {str(e)}")
        return render_template("wiki_home.html", error=str(e), tables=[], universes=[])

@app.route("/wiki/universe/<int:univers_id>")
def wiki_universe(univers_id):
    try:
        conn = get_db_connection()
        print(f"Connected to database for universe: {univers_id}")
        
        # Get universe details
        universe = conn.execute("SELECT * FROM univers WHERE id = ?", (univers_id,)).fetchone()
        if not universe:
            conn.close()
            return render_template("wiki_universe.html", error="Univers non trouvé", univers_id=univers_id)
        
        # Get all related data using the correct table names
        factions = conn.execute("SELECT * FROM faction WHERE univers_id = ?", (univers_id,)).fetchall()
        locations = conn.execute("SELECT * FROM location WHERE univers_id = ?", (univers_id,)).fetchall()
        cultures = conn.execute("SELECT * FROM culture WHERE univers_id = ?", (univers_id,)).fetchall()
        personnages = conn.execute("SELECT * FROM personnages WHERE univers_id = ?", (univers_id,)).fetchall()
        objets = conn.execute("SELECT * FROM objets WHERE univers_id = ?", (univers_id,)).fetchall()
        
        # Get prompt answers for this universe
        prompt_answers = conn.execute("SELECT * FROM prompt_answers WHERE univers_id = ? ORDER BY created_at DESC", (univers_id,)).fetchall()
        
        # Get all universes for navigation
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
        print(f"Error in wiki_universe route for universe {univers_id}: {str(e)}")
        return render_template("wiki_universe.html", error=str(e), univers_id=univers_id)

@app.route('/wiki/<table>', methods=['GET'])
def wiki_table(table):
    try:
        conn = get_db_connection()
        print(f"Connected to database for table: {table}")

        # Check if specific universe ID is requested
        filter_id = request.args.get("univers_id", "")

        # Construct the query based on whether we're filtering
        if filter_id:
            if table.lower() == "univers":
                # For univers table, filter by id
                query = f"SELECT * FROM {table} WHERE id = ?"
                print(
                    f"Executing filtered query for univers: {query} with ID: {filter_id}"
                )
                cursor = conn.execute(query, (filter_id,))
            else:
                # For all other tables, filter by univers_id
                query = f"SELECT * FROM {table} WHERE univers_id = ?"
                print(f"Executing filtered query: {query} with univers_id: {filter_id}")
                cursor = conn.execute(query, (filter_id,))
        else:
            query = f"SELECT * FROM {table}"
            print(f"Executing query: {query}")
            cursor = conn.execute(query)

        # Get column names before fetching rows
        columns = [description[0] for description in cursor.description]
        print(f"Columns: {columns}")

        # Now fetch the rows
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows in table {table}")

        conn.close()

        # Pass table name, columns, rows, and current filter to template
        return render_template(
            "wiki_table.html",
            table=table,
            rows=rows,
            columns=columns,
            current_filter=filter_id,
        )
    except Exception as e:
        print(f"Error in wiki_table route for table {table}: {str(e)}")
        return render_template("wiki_table.html", table=table, error=str(e))


# Add this to app.py for debugging
@app.route("/dbinfo")
def db_info():
    try:
        conn = get_db_connection()

        # Get all tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        result = {
            "database_path": os.path.abspath(
                conn.execute("PRAGMA database_list").fetchone()[2]
            ),
            "tables": [t[0] for t in tables],
            "table_details": {},
        }

        # Get schema for each table
        for table in result["tables"]:
            schema = conn.execute(f"PRAGMA table_info({table})").fetchall()
            result["table_details"][table] = [dict(row) for row in schema]

        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}


# À la fin du fichier, modifiez la partie où vous démarrez l'application
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=False)