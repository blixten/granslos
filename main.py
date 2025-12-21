import streamlit as st
from openai import OpenAI
import json
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

class Location(BaseModel):
    name: str
    description: str
    adress: str
    location_lat: float
    location_long: float

class Event(BaseModel):
    date: str
    name: str
    description: str
    url: str
    location: Location
    file_reference: str

class ThingsToDo(BaseModel):
    name: str
    description: str
    url: str
    location: Location
    file_reference: str

class Event_Query(BaseModel):
    general_response: str
    events: list [ Event ]
    things_to_do: list [ ThingsToDo ]


st.set_page_config(layout="wide")
client = OpenAI(timeout=60)

def send_chat_message(input, areas):

    history = st.session_state["messages"]
    store_ids = []
    for store in st.session_state["knowledge_sources"]:
        store_ids.append(store  )

    print(f"Using these vector stores: {store_ids}")

    current_time = datetime.now().strftime("%Y-%m-%d") #%H:%M")
    
    print(f"Generating response with input date '{current_time}' and input '{input}'")

    # filters = {}
    # for area in areas:
    #     if area:

    response = client.responses.parse(
        model="gpt-5.2",
        temperature=0.1,
        input=[
            {
                "role": "system",
                "content":  [
                    {
                        "type": "input_text",
                        "text": f"""
                            {st.session_state["settings"][st.session_state["language"]]["main_prompt"]}
                            Du ger svar utifrån de områden som är valda: {areas}
                            """
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": f""" 
                            Conversation history: {history}
                            Current time: {current_time}
                            User prompt: {input}
                    """
                    },
                ]
            }
        ],
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": store_ids
            }
        ],
        text_format=Event_Query
    )   
    return response.output_parsed


if "settings" not in st.session_state.keys():
    with open("settings.json", "r", encoding="utf-8") as file:
        settings = json.load(file)

    st.session_state["settings"] = settings

    if "main_prompt" not in st.session_state["settings"].keys():
        st.session_state["settings"]["main_prompt"] = ""

if "default_language" not in st.session_state.keys():
    st.session_state["default_language"] = "no"

if "language" not in st.session_state.keys():
    st.session_state["language"] = st.session_state["default_language"]
    

if "messages" not in st.session_state.keys():
    st.session_state["messages"] = [({"general_response": st.session_state["settings"][st.session_state["language"]]["greeting"]}, "assistant")]

if "areas" not in st.session_state.keys():
    st.session_state["areas"] = {"Bohuslän": True, "Dalsland": True, "Østfold": True }

if "bot_output" not in st.session_state.keys():
    st.session_state["bot_output"] = ""
if "bot_triggered" not in st.session_state.keys():
    st.session_state["bot_triggered"] = False


if "knowledge_sources" not in st.session_state.keys():
    # stores = client.vector_stores.list()
    st.session_state["knowledge_sources"] = ['vs_68959dfcaa408191abe2ec48d97b0720', 'vs_68959db1faf88191b036dfdde07dc40b']

    files = client.files.list()
    st.session_state["files"] = files
        

def preset_question(q):
    bot_response = send_chat_message(q, st.session_state["areas"])
    return bot_response
    #st.rerun()
        
### Main app ###

st.markdown("""
<style>
/* Sidebar content wrapper */
section[data-testid="stSidebar"] {
  width: 400px !important; # Set the width to your desired value
}

[data-testid="stSidebarContent"] {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Push this container to the bottom */
.st-key-image_container {
  margin-top: auto;
  bottom: 0;
  position: fixed;
  max-width: 300px;
}

            
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(st.session_state["settings"][st.session_state["language"]]["sidebar_info"])

    st.container(height=20, border=False)

    st.markdown(f"**{st.session_state["settings"][st.session_state["language"]]["links_title"]}**")
    st.markdown(f"{st.session_state["settings"][st.session_state["language"]]["links_description"]}")
    
    
    with st.container(horizontal=True):
        st.link_button("Bohuslän", "https://www.vastsverige.com/bohuslan/")
        st.link_button("Dalsland", "https://www.vastsverige.com/dalsland/")
        st.link_button("Østfold", "https://www.visitoestfold.com/")
    
    

    with st.container(key="image_container"):
        st.image("assets/ostfold.jpg", width=75, )
        st.image("https://svinesundskommitten.com/wp-content/uploads/2023/08/logo_clean_heart.svg")
        st.image("https://svinesundskommitten.com/wp-content/uploads/2023/11/Logo-Sweden-Norway-CMYK-Color-02.png")


    lang = st.selectbox("Språk:", ["no", "sv"])
    if lang and lang != st.session_state["language"]:
        st.session_state["language"] = lang
        st.rerun()
        lang = None

# Main chat interface
chatbox = st.container(height=500, vertical_alignment="bottom", )

# repopulate the chat container after rerun/change
for message, user in st.session_state["messages"]:
            if user == "user":
                chatbox.chat_message(user).write(message)
            if user == "assistant":
                try:
                    chatbox.chat_message(user).write(message["general_response"])
                except Exception as e:
                    print("Error", e, message)

# # Choose specific area
# with st.container(border=True):
#     col1, col2 =  st.columns([0.5,1])
#     with col1:
#st.markdown("Avgränsa område:")
areas = st.pills (
    "Avgränsa område till:",
    options=["Bohuslän", "Dalsland", "Østfold"],
    selection_mode="multi",
    label_visibility="visible"
)
if areas:
    st.session_state["areas"] = areas

        # with st.container(border=False, height="stretch"):
        #     st.markdown("**Område**:")
        #     area_1, area_2, area_3 = st.columns(3, width=310, vertical_alignment="center", gap=None )


        #     with area_1:
        #         b_select = st.checkbox("Bohuslän", value=True)
        #     with area_2:
        #         d_select = st.checkbox("Dalsland", value=True)
        #     with area_3:
        #         o_select = st.checkbox("Østfold", value=True)

    # Presets, quick questions
    # with col2:
# with st.container(border=False, height="stretch"):
#     st.markdown("Snabbval:")
#     b_one, b_two, b_three, b_four = st.columns(4, gap="small", width=800)
#     questions = st.session_state["settings"][st.session_state["language"]]["default_questions"]

#     for col, q in zip([b_one, b_two, b_three, b_four], questions):
#         with col:
#             if st.button(q, type="primary"):
#                 st.session_state["bot_triggered"] = q


bot_response = {}

input = st.chat_input("Din fråga") 

query = input or st.session_state["bot_triggered"]

if query:
    with st.status(label="Genererar svar...",   state="running") as status:
    
        st.session_state["messages"].append((query, "user"))
        chatbox.chat_message("user").write(query)

        # areas = {"Bohuslän": b_select, "Dalsland": d_select, "Østfold": o_select }
        st.session_state["areas"] = areas

        bot_response = send_chat_message(input, areas)
            

    status.update(state="complete")
    st.session_state["bot_triggered"] = False
    st.session_state["messages"].append(({"general_response": bot_response.general_response, "bot_response": bot_response}, "assistant"))
    chatbox.chat_message("assistant").write(bot_response.general_response)  


    if hasattr(bot_response, "events") or hasattr(bot_response, "things_to_do"):

        bot_output = ""
        bot_output += ("## Förslag: \n")
        for event in bot_response.events:
            bot_output += f"#### {event.name}   \n"
            bot_output += f"När: {event.date}   \n"
            bot_output += f"Var: {event.location.name}, {event.location.adress}   \n"
            bot_output += f"{event.description}   \n"
            bot_output += f"Hemsida: [{event.name}]({event.url})   \n"

        for thing_to_do in bot_response.things_to_do:
            bot_output += f"#### {thing_to_do.name}   \n"
            bot_output += f"Var: {thing_to_do.location.name}, {thing_to_do.location.adress}   \n"
            bot_output += f"{thing_to_do.description}   \n"
            bot_output += f"Hemsida: [{thing_to_do.name}]({thing_to_do.url})   \n"

        st.session_state["bot_output"] = bot_output
        saved_response = {"generel_response": bot_response.general_response, "details": bot_output}
        with open(f"store/{str(uuid.uuid4())}.json", "w", encoding="utf-8") as file:
            json.dump(saved_response, file)


    st.session_state["bot_triggered"] = None
st.markdown(st.session_state["bot_output"])


       


if st.query_params.get("id"):
    print("got existing trop id:", st.query_params["id"])
    file_path = f"store/{st.query_params["id"]}.json"
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        st.markdown(data["generel_response"])
        st.markdown(data["details"])

    st.query_params["id"] = ""