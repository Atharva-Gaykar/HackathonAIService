from app.graph import graph

from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

complaint_description = "There are exposed electrical wires hanging dangerously close to the ground near the market area, and sparks can be seen when they touch nearby trees."
# These variables must match the arguments passed into the function below
test_lat = 21.125008
test_lng = 79.050025
test_dept = None
user_id=2
complaint_title= "Electrical Hazard near Vegetable Market"


config={
    "configurable": {
        "thread_id": user_id
    }
}

input={
    "complaint_title": complaint_title,
    "complaint_description": complaint_description,
    "latitude": 21.125008,
    "longitude": 79.050025,
    "user_id": user_id
}

# final_send_state = graph.invoke(input, config=config)

# print(final_send_state)

