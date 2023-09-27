from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
import streamlit as st
from streamlit_chat import message
from utils import *
from config import *
import snowflake.connector
import openai
from streamlit_modal import Modal
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)

st.set_page_config(layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: left ;margin-left: -15px; margin-top: -50px; ">
    <img src="https://stsnowgptimg.blob.core.windows.net/snowgptimage/SnowGTP.png" width="200" />
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    modal = Modal(key="Demo Key",title=" ")
    open_modal = st.button(label='How to use')
    
content = '<p style="color: Black;">Unlock the Power of Snowflake: Your Personal Snowflake Documentation Chatbot. Say hello to your go-to resource for seamless access to Snowflake platform knowledge and instant answers to all your queries.</p>'
st.write(content, unsafe_allow_html=True)


text_color = "#006A53"

if open_modal:
    st.markdown(f"""
                <div  style="position: fixed; top:300px; z-index:9999; right:30px; width: 250px; height: 25%; background-color: #f5f5f0; box-shadow: -5px 0 5px rgba(0, 0, 0, 0.2); color: {text_color};">
                <p style="font-size: 15px;">How to Use: Using our chatbot is effortless – simply type in your Snowflake-related questions, and it will provide you with precise and up-to-date information from the vast Snowflake documentation.</p> """,unsafe_allow_html=True)
    with st.sidebar:
        st.button("close-info")
    st.markdown("""</div>""",unsafe_allow_html=True)

if 'responses' not in st.session_state:
    st.session_state['responses'] = ["How can I help you"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []
    

# Function to check if the API key is valid
def is_valid_api_key(openai_api_key):
    return openai_api_key and openai_api_key.startswith('sk-') and len(openai_api_key) == 51


openai_api_key =  st.secrets["OPENAI_API_KEY"]


if is_valid_api_key(openai_api_key):
    
    openai.api_key = openai_api_key
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)

    if 'buffer_memory' not in st.session_state:
                st.session_state.buffer_memory=ConversationBufferWindowMemory(k=3,return_messages=True)

    system_msg_template = SystemMessagePromptTemplate.from_template(template="""Answer the question as truthfully as possible using the provided context, 
    and if the answer is not contained within the text below, say 'I don't know'""")

    human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")
    prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])
    conversation = ConversationChain(memory=st.session_state.buffer_memory, prompt=prompt_template, llm=llm, verbose=True)

    # container for chat history
    response_container = st.container()
    # container for text box
    textcontainer = st.container()

    with textcontainer:
        query = st.chat_input("Ask me anything in snowflake: ", key="input")
        if query:
            with st.spinner("typing..."):
                conversation_string = get_conversation_string()
                refined_query = query_refiner(conversation_string, query)
                context = find_match(refined_query) 
                response = conversation.predict(input=f"Context:\n {context} \n\n Query:\n{query}")
            st.session_state.requests.append(query)
            st.session_state.responses.append(response)
            add_query_history(query)
         
    with response_container:
            if st.session_state['responses']:
                for i in range(len(st.session_state['responses'])):
                    res = st.chat_message('assistant',avatar='https://stsnowgptimg.blob.core.windows.net/snowgptimage/snowflakeimg.png')
                    res.write(st.session_state['responses'][i],key=str(i))
                    if i < len(st.session_state['requests']):
                        req = st.chat_message('user',avatar='https://stsnowgptimg.blob.core.windows.net/snowgptimage/user.png')
                        req.write(st.session_state['requests'][i],is_user=True,key=str(i)+ '_user')
                        
    with st.sidebar.expander("Query History"):
            history_data = manage_query_history()
            if history_data:
                for i, request in enumerate(history_data):
                    col1,col2=st.columns(2)
                    with col1:
                        st.write(f"{i + 1}. {request}")
                    with col2:
                        delete_button = st.button(f"Delete", key=f"delete_{i}")
                    
                    if delete_button:
                        manage_query_history(i)
                        st.experimental_rerun()
                    
            else:
                st.write("No query history available.")

else:
   with st.sidebar:
        if not openai_api_key:
            st.warning('Please enter your OpenAI API key!', icon='⚠️')
        elif not is_valid_api_key(openai_api_key):
            st.warning('Please enter a valid OpenAI API key!', icon='⚠️')



          