from state import ComplaintState
from langgraph.graph import StateGraph, START, END
from nodes import classify_complaint_node, group_duplicate_complaints_node, calculate_priority_node, store_data_node, router
workflow = StateGraph(ComplaintState)

# Add Nodes
workflow.add_node("classify", classify_complaint_node)
workflow.add_node("group_duplicates", group_duplicate_complaints_node)
workflow.add_node("calculate_priority", calculate_priority_node)
workflow.add_node("store_data", store_data_node)

# Set up Edges
workflow.set_entry_point("classify")
workflow.add_edge("classify", "group_duplicates")
workflow.add_edge("group_duplicates", "calculate_priority")

# Add Conditional Edge (The Router)
workflow.add_conditional_edges(
    "calculate_priority",
    router,
    {
        "store_data": "store_data",
        "END": END
    }
)

workflow.add_edge("store_data", END)

graph = workflow.compile()