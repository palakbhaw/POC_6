import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.exc import SQLAlchemyError

def connectDatabase(username, port, host, password, database):
    # Correct the connection string
    mssql_uri = f"mssql+pyodbc://pearls:pearlseps@192.168.0.27:1433/BoschPOC?driver=ODBC+Driver+17+for+SQL+Server"
    try:
        st.session_state.db = SQLDatabase.from_uri(mssql_uri)
        st.success("Database connected successfully!")
    except SQLAlchemyError as e:
        st.error(f"Failed to connect to the database: {str(e)}")

# Run SQL query
def runQuery(query):
    if "db" not in st.session_state or not st.session_state.db:
        return "Please connect to the database first."
    try:
        return st.session_state.db.run(query)
    except SQLAlchemyError as e:
        return f"Error executing query: {str(e)}"

# Get Database Schema
def getDatabaseSchema():
    if "db" not in st.session_state or not st.session_state.db:
        return "Please connect to the database first."
    try:
        # This schema represents the structure of your inventory table
        schema = """
        Table: inventory_transactions
        Columns:
        - PartNo: VARCHAR(50)
        - TransactionDate: DATE
        - InQty: DECIMAL(10, 2)
        - OutQty: DECIMAL(10, 2)
        - Balance: DECIMAL(10, 2)
        """
        return schema
    except SQLAlchemyError as e:
        return f"Error fetching schema: {str(e)}"

# Instantiate ChatOllama model
llm = ChatOllama(model="llama3")

# Get SQL Query from LLM based on question
def getQueryFromLLM(question):
    template1 = """
Below is the schema of the inventory database. Read the schema carefully, paying attention to the table and column names. Also, consider the given conversation context, if available, to write a natural language response based on the query result.

{schema}

### Examples:
question: How many transactions are there for PartNo '0124110001'?
SQL query: SELECT COUNT(*) FROM inventory_transactions WHERE PartNo = '0124110001';
Result: [(3,)]
Response: There are 3 transactions for PartNo '0124110001'.

question: What is the total incoming quantity for PartNo '0124110008'?
SQL query: SELECT SUM(InQty) FROM inventory_transactions WHERE PartNo = '0124110008';
Result: [(0.0,)]
Response: The total incoming quantity for PartNo '0124110008' is 0.0.

### Your Turn:
question: {question}
SQL query: {query}
Result: {result}
Response:
"""
    prompt = ChatPromptTemplate.from_template(template1)
    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "schema": getDatabaseSchema()
    })
    return response.content

# Get response based on query result
def getResponseForQueryResult(question, query, result):
    template2 = """
Below is the schema of a MySQL database. Read the schema carefully, paying attention to the table and column names. Write a natural language response based on the query result, considering the context of the given question and query.

{schema}

### Examples:
question: What is the total incoming quantity for PartNo '0124110008'?
SQL query: SELECT SUM(InQty) FROM transactions WHERE PartNo = '0124110008';
Result: [(10.5,)]
Response: The total incoming quantity for PartNo '0124110008' is 10.5.

question: What is the balance of PartNo '0124110001' on 29-04-2024?
SQL query: SELECT Balance FROM transactions WHERE PartNo = '0124110001' AND TransactionDate = '2024-04-29';
Result: [(0.0,)]
Response: The balance for PartNo '0124110001' on 29-04-2024 is 0.0.

question: How many transactions have a balance less than 0 for PartNo '0124110008'?
SQL query: SELECT COUNT(*) FROM transactions WHERE PartNo = '0124110008' AND Balance < 0;
Result: [(3,)]
Response: There are 3 transactions with a balance less than 0 for PartNo '0124110008'.

### Your Turn:
question: {question}
SQL query: {query}
Result: {result}
Response:
"""

    # Use the template and the LLM
    prompt2 = ChatPromptTemplate.from_template(template2)
    chain2 = prompt2 | llm

    # Pass all the required variables (question, schema, query, result)
    response = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(),  # This gets the database schema
        "query": query,                 # SQL query
        "result": result                # Query result
    })

    return response.content



# Set up Streamlit page
st.set_page_config(
    page_icon="🤖",
    page_title="Chat with Inventory Database",
    layout="centered"
)

question = st.chat_input('Ask about your inventory database')

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

        # Get query from LLM based on the question
        query = getQueryFromLLM(question)

        # Execute the query and fetch the result
        result = runQuery(query)

        # Generate a response based on the query result
        response = getResponseForQueryResult(question, query, result)

        # Append the assistant's response to the chat history
        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })

# Display chat messages
for chat in st.session_state.chat:
    st.chat_message(chat['role']).markdown(chat['content'])

# Sidebar for database connection
with st.sidebar:
    st.title('Connect to Inventory Database')
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
