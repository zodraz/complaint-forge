import asyncio
from graph import app
from dotenv import load_dotenv

load_dotenv()

async def handle_complaint(complaint_text: str):
    initial_state = {
        "complaint": complaint_text,
        "messages": []
    }
    
    result = await app.ainvoke(initial_state)
    
    print("Complaint handled autonomously!")
    print("\nFinal Response to Customer:\n")
    print(result.get("final_response", "No response generated"))
    print("\nActions Taken:", result.get("actions_taken", []))
    print(
        "\nSalesforce History Used:",
        result.get("customer_history", {}).get("total_recent_cases", 0),
        "recent cases",
    )
    
    return result

# Example usage
if __name__ == "__main__":
    complaint = """
    My order #ORD-98765 never arrived. I'm extremely upset and want a full refund immediately.
    Email: angry.customer@gmail.com
    """
    asyncio.run(handle_complaint(complaint))
