
import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.exc import SQLAlchemyError

def connectDatabase(username, port, host, password, database):
    # Update URI to connect to MSSQL
    mssql_uri = f"mssql+pyodbc://pearls:pearlseps:@192.168.0.27:1433/BoschPOC?driver=ODBC+Driver+17+for+SQL+Server"
    try:
        st.session_state.db = SQLDatabase.from_uri(mssql_uri)
        st.success("Database connected successfully!")
    except SQLAlchemyError as e:
        st.error(f"Failed to connect to the database: {str(e)}")

def runQuery(query):
    if "db" not in st.session_state or not st.session_state.db:
        return "Please connect to the database first."
    try:
        return st.session_state.db.run(query)
    except SQLAlchemyError as e:
        return f"Error executing query: {str(e)}"

def getDatabaseSchema():
    if "db" not in st.session_state or not st.session_state.db:
        return "Please connect to the database first."
    try:
        return st.session_state.db.get_table_info()
    except SQLAlchemyError as e:
        return f"Error fetching schema: {str(e)}"

llm = ChatOllama(model="llama3")

def getQueryFromLLM(question):
    template = """
Below is the schema of an inventory transactions database. Carefully read the schema, which describes the columns and their purposes. Use this schema to generate a precise SQL query based on the user's question. Ensure to handle date formats and numeric operations correctly.

Schema:
- PartNo (STRING): The unique identifier for a part.
- TransactionDate (DATE): The date of the transaction.
- InQty (FLOAT): Quantity of parts added to inventory.
- OutQty (FLOAT): Quantity of parts removed from inventory.
- Balance (FLOAT): Current balance of parts after the transaction.

Please only provide the SQL query and nothing else.

Your turn:
Question: {question}
SQL query:
"""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "schema": getDatabaseSchema()
    })
    return response.content

def getResponseForQueryResult(question, query, result):
    template2 = """
Below is the schema of an inventory transactions database. Carefully read the schema, which describes the columns and their purposes. Use this schema and the given query result to provide a response in natural language that answers the user's question.

Schema:
- PartNo (STRING): The unique identifier for a part.
- TransactionDate (DATE): The date of the transaction.
- InQty (FLOAT): Quantity of parts added to inventory.
- OutQty (FLOAT): Quantity of parts removed from inventory.
- Balance (FLOAT): Current balance of parts after the transaction.

Your turn to write a response in natural language from the given result:
Question: {question}
SQL query: {query}
Result: {result}
Response:
"""
    prompt2 = ChatPromptTemplate.from_template(template2)
    chain2 = prompt2 | llm

    response = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(),
        "query": query,
        "result": result
    })

    return response.content

st.set_page_config(
    page_icon="🤖",
    page_title="Chat with MSSQL DB",
    layout="centered"
)

question = st.chat_input('Chat with your MSSQL database')

if "chat" not in st.session_state:
    st.session_state.chat = []

if question:
    if "db" not in st.session_state or not st.session_state.db:
        st.error('Please connect to the database first.')
    else:
        st.session_state.chat.append({
            "role": "user",
            "content": question
        })

        query = getQueryFromLLM(question)
        result = runQuery(query)
        response = getResponseForQueryResult(question, query, result)

        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })

for chat in st.session_state.chat:
    st.chat_message(chat['role']).markdown(chat['content'])

with st.sidebar:
    st.title('Connect to MSSQL Database')
    st.text_input(label="Host", key="host", value="192.168.0.27")
    st.text_input(label="Port", key="port", value="1433")
    st.text_input(label="Username", key="username", value="pearls")
    st.text_input(label="Password", key="password", value="pearlseps", type="password")
    st.text_input(label="Database", key="database", value="BoschPOC")
    connectBtn = st.button("Connect")

if connectBtn:
    connectDatabase(
        username=st.session_state.username,
        port=st.session_state.port,
        host=st.session_state.host,
        password=st.session_state.password,
        database=st.session_state.database,
    )
