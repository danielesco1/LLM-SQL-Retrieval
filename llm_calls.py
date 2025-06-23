from server.config import *
import re


# Create a SQL query from user question
def generate_sql_query(dB_context: str, retrieved_descriptions: str, user_question: str) -> str:
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                    You are an SQL assistant for a building panels database. Generate accurate SQL queries for any question about building panels.

                    ### DATABASE CONTEXT ###
                    {dB_context}
                    ### TABLE DESCRIPTIONS ###
                    {retrieved_descriptions}

                    ### QUERY PATTERNS ###
                    Count: SELECT COUNT(*) FROM building_panels WHERE...
                    List items: SELECT column FROM building_panels WHERE...
                    Unique values: SELECT DISTINCT column FROM building_panels WHERE...
                    Group/aggregate: SELECT column, COUNT(*) FROM building_panels GROUP BY column
                    Panel types: panel_id LIKE '%WINDOW%' (or %DOOR%, %WALL%, %FLOOR%, %ROOF%)
                    
                    # Instructions #
                     ## Reasoning Steps: ##
                     - Carefully analyze the users question.
                     - Cross-reference the question with the provided database schema and table descriptions.
                     - Think about which data a query to the database should fetch. Only data related to the question should be fetched.
                     - Pay special atenttion to the names of the tables and properties of the schema. Your query must use keywords that match perfectly.
                     - Create a valid and relevant SQL query, using only the table names and properties that are present in the schema.

                     ## Output Format: ##
                     - Output only the SQL query.
                     - Do not use formatting characters like '```sql' or other extra text.
                     - If the database doesnt have enough information to answer the question, simply output "No information".
                    """
            },
            {
                "role": "user",
                "content": user_question,
            },
        ],
    )
    return response.choices[0].message.content

# Create a natural language response out of the SQL query and result
def build_answer(sql_query: str, sql_result: str, user_question: str) -> str:
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                Interpret SQL query results and provide natural language answers. Extract actual data.

                Examples:
                - SQL Result: [('187',), ('291',), ('385',)] → Answer: "[187, 291, 385]"
                - SQL Result: [(15,)] → Answer: "15 panels"
                - SQL Result: [] → Answer: "No results found"
                - SQL Result: [('187', 'bedroom', 'North')] → Answer: "Found: Unit 187 has a North-facing panel in bedroom"
                - SQL Result: [(187, '3B_WINDOW9'), (173, '3B_WINDOW8'), (173, '3B_WINDOW13')] → Answer: "[(187, '3B_WINDOW9'), (173, '3B_WINDOW8'), (173, '3B_WINDOW13')]"
                
                """
            },
            {
                "role": "user",
                "content": f"""
                User question: {user_question}
                SQL Query: {sql_query}
                SQL Result: {sql_result}
                Return the formatted answer according. do not add anything else.
                
                """,
            },
        ],
    )
    return response.choices[0].message.content

# Fix an SQL query that has failed
def fix_sql_query(dB_context: str, user_question: str, atempted_queries: str, exceptions: str) -> str:

    attemptted_entries = []
    for query, exception in zip(atempted_queries, exceptions):
        attemptted_entries.append(f"#Previously attempted query#:{query}. #SQL Exception error#:{exception}")

    queries_exceptions_content = "\n".join(attemptted_entries)

    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content":
                       f"""
                You are an SQL database expert tasked with correcting a SQL query. A previous attempt to run a query
                did not yield the correct results, either due to errors in execution or because the result returned was empty
                or unexpected. Your role is to analyze the error based on the provided database schema and the details of
                the failed execution, and then provide a corrected version of the SQL query.
                The new query should provide an answer to the question! Dont create queries that do not relate to the question!
                Pay special atenttion to the names of the table and properties. Your query must use keywords that match perfectly.

                # Context Information #
                - The database contains one table, each corresponding to a different panel feature. 
                - Each table row represents an individual instance of a panel feature of that type.
                ## Database Schema: ## {dB_context}

                # Instructions #
                1. Write down in steps why the sql queries might be failling and what could be changed to avoid it. Answer this questions:
                    I. Is the table being fetched the most apropriate to the user question, or could there be another table that might be more suitable?
                    II. Could there be another property in the schema of database for that table that could provide the right answer?
                2. Given your reasoning, write a new query taking into account the various # Failed queries and exceptions # tried before.
                2. Never output the exact same query. You should try something new given the schema of the database.
                3. Your output should come in this format: #Reasoning#: your reasoning. #NEW QUERY#: the new query.
                
                Do not use formatting characters, write only the query string.
                No other text after the query. Do not invent table names or properties. Use only the ones shown to you in the schema.
                """,
            },
            {
                "role": "user",
                "content": f""" 
                #User question#
                {user_question}
                #Failed queries and exceptions#
                {queries_exceptions_content}
                """,
            },
        ],
    )
    
    response_content = response.choices[0].message.content
    #print(response_content)
    match = re.search(r'#NEW QUERY#:(.*)', response_content)
    if match:
        return match.group(1).strip()
    else:
        return None


def questions():
    f""" Which units have the lowest open view scores, and how can I improve them without increasing solar exposure?
        Suggest window design or placement strategies to maximize open view in north-facing units with low scores.
        How can I enhance views for southeast units without compromising solar control or daylight autonomy?
        Which units have high SDA but also high solar radiation? Suggest ways to reduce overheating while maintaining daylight.
        Propose shading strategies for west-facing units with excessive solar gain but good open views.
        Give me facade design ideas for north units with poor daylight and views.
        How should I adapt east-facing facades to balance morning sun and open view potential?
        List the worst-performing units by combining open view score, solar radiation, and SDA. Suggest adaptive facade improvements.
        """



# # Create a SQL query from user question
# def generate_sql_query(dB_context: str, retrieved_descriptions: str, user_question: str) -> str:
#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=[
#             {
#                 "role": "system",
#                 "content":
#                        f"""
#                 You are a SQLite expert.
#                 The database contains a tables with information related to panels of a facade for building . 
#                 Each table row represents an individual instance of a building element of that type.

#                 # Context Information #
#                 ## Database Schema: ## {dB_context}
#                 ## Table Descriptions: ## {retrieved_descriptions}

#                 # Instructions #
#                 ## Reasoning Steps: ##
#                 - Carefully analyze the users question.
#                 - Cross-reference the question with the provided database schema and table descriptions.
#                 - Think about which data a query to the database should fetch. Only data related to the question should be fetched.
#                 - Pay special atenttion to the names of the tables and properties of the schema. Your query must use keywords that match perfectly.
#                 - Create a valid and relevant SQL query, using only the table names and properties that are present in the schema.

#                 ## Output Format: ##
#                 - Output only the SQL query.
#                 - Do not use formatting characters like '```sql' or other extra text.
#                 - If the database doesnt have enough information to answer the question, simply output "No information".
#                 """
#             },
#             {
#                 "role": "user",
#                 "content": f"# User question # {user_question}",
#             },
#         ],
#     )
#     return response.choices[0].message.content

# # Create a natural language response out of the SQL query and result
# def build_answer(sql_query: str, sql_result: str, user_question: str) -> str:
#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=[
#             {
#                 "role": "system",
#                 "content":
#                        f"""
#                         You have to answer a user question according to the SQL query and its result. Your goal is to answer in a concise and informative way, specifying the properties and tables that were relevant to create the answer.
                       
#                         ### EXAMPLE ###
#                         User Question: What is the area of the largest slab?  
#                         SQL Query: SELECT GlobalId, Dimensions_Area FROM IfcSlab ORDER BY Dimensions_Area DESC LIMIT 1;  
#                         SQL Result: [('3qq_RRlZrFqhCIHFKokT7x', 207.1385920365226)]  
#                         Answer: I looked at the Dimensions_Area property of IfcSlab elements and found that the area of the largest slab (GlobalID: '3qq_RRlZrFqhCIHFKokT7x') is 207.13 m².
#                 """,
#             },
#             {
#                 "role": "user",
#                 "content": f""" 
#                 User question: {user_question}
#                 SQL Query: {sql_query}
#                 SQL Result: {sql_result}
#                 Answer:
#                 """,
#             },
#         ],
#     )
#     return response.choices[0].message.content

# # Fix an SQL query that has failed
# def fix_sql_query(dB_context: str, user_question: str, atempted_queries: str, exceptions: str) -> str:

#     attemptted_entries = []
#     for query, exception in zip(atempted_queries, exceptions):
#         attemptted_entries.append(f"#Previously attempted query#:{query}. #SQL Exception error#:{exception}")

#     queries_exceptions_content = "\n".join(attemptted_entries)

#     response = client.chat.completions.create(
#         model=completion_model,
#         messages=[
#             {
#                 "role": "system",
#                 "content":
#                        f"""
#                 You are an SQL database expert tasked with correcting a SQL query. A previous attempt to run a query
#                 did not yield the correct results, either due to errors in execution or because the result returned was empty
#                 or unexpected. Your role is to analyze the error based on the provided database schema and the details of
#                 the failed execution, and then provide a corrected version of the SQL query.
#                 The new query should provide an answer to the question! Dont create queries that do not relate to the question!
#                 Pay special atenttion to the names of the tables and properties. Your query must use keywords that match perfectly.

#                 # Context Information #
#                 - The database contains multiple tables, each corresponding to a different building element type. 
#                 - Each table row represents an individual instance of a building element of that type.
#                 ## Database Schema: ## {dB_context}

#                 # Instructions #
#                 1. Write down in steps why the sql queries might be failling and what could be changed to avoid it. Answer this questions:
#                     I. Is the table being fetched the most apropriate to the user question, or could there be another table that might be more suitable?
#                     II. Could there be another property in the schema of database for that table that could provide the right answer?
#                 2. Given your reasoning, write a new query taking into account the various # Failed queries and exceptions # tried before.
#                 2. Never output the exact same query. You should try something new given the schema of the database.
#                 3. Your output should come in this format: #Reasoning#: your reasoning. #NEW QUERY#: the new query.
                
#                 Do not use formatting characters, write only the query string.
#                 No other text after the query. Do not invent table names or properties. Use only the ones shown to you in the schema.
#                 """,
#             },
#             {
#                 "role": "user",
#                 "content": f""" 
#                 #User question#
#                 {user_question}
#                 #Failed queries and exceptions#
#                 {queries_exceptions_content}
#                 """,
#             },
#         ],
#     )
    
#     response_content = response.choices[0].message.content
#     #print(response_content)
#     match = re.search(r'#NEW QUERY#:(.*)', response_content)
#     if match:
#         return match.group(1).strip()
#     else:
#         return None