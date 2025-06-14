from server.config import *
from llm_calls import *
from sql_calls import *
from utils.rag_utils import sql_rag_call

def process_database_query(user_question, db_path="sql/building_panels-database1.db"):
    """Process user question against database and return natural language answer."""
    
    # --- Load SQL Database ---
    # db_path = "sql/building_panels-database1.db"
    db_schema = get_dB_schema(db_path)
    
    # --- Retrieve most relevant table ---
    table_descriptions_path = "knowledge/table_descriptions.json"
    relevant_table, table_description = sql_rag_call(
        user_question, table_descriptions_path, n_results=1
    )
    
    if not relevant_table:
        return "No relevant table found."
    
    # --- Filter Schema to relevant table ---
    filtered_schema = {relevant_table: db_schema.get(relevant_table)}
    db_context = format_dB_context(db_path, filtered_schema)
    
    # --- Generate SQL query from LLM ---
    sql_query = generate_sql_query(db_context, table_description, user_question)
    
    # --- LLM says insufficient info ---
    if "No information" in sql_query:
        return "I'm sorry, but this database does not contain enough information to answer that question."
    
    # --- Execute SQL with self-debugging feature ---
    sql_query, query_result = fetch_sql(sql_query, db_context, user_question, db_path)
    
    # --- If self-debugging failed after max_retries we give up ---
    if not query_result:
        return "I'm sorry but I was not able to find any relevant information to answer your question. Please, try again."
    
    # --- Build natural language answer to user ---
    final_answer = build_answer(sql_query, query_result, user_question)
    return final_answer