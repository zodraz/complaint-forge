from hubspot import HubSpot
from config import HUBSPOT_ACCESS_TOKEN
import json

hs_client = HubSpot(access_token=HUBSPOT_ACCESS_TOKEN)

def get_customer_history(email: str) -> dict:
    """Pulls full HubSpot history for a customer"""
    try:
        # Find contact by email
        contacts = hs_client.crm.contacts.search_api.do_search(
            query=email,
            limit=1,
            properties=["email", "firstname", "lastname", "lifetime_value"]
        )
        if not contacts.results:
            return {"error": "Contact not found", "email": email}

        contact = contacts.results[0]
        contact_id = contact.id

        # Get associations (deals + tickets)
        associations = hs_client.crm.contacts.associations_api.get_all(
            contact_id=contact_id,
            to_object_type=["deals", "tickets"]
        )

        deals = []
        tickets = []

        for assoc in associations.results:
            if assoc.to_object_type == "deal":
                deal = hs_client.crm.deals.basic_api.get_by_id(assoc.id, properties=["dealname", "amount", "dealstage"])
                deals.append(deal.to_dict())
            elif assoc.to_object_type == "ticket":
                ticket = hs_client.crm.tickets.basic_api.get_by_id(assoc.id, properties=["subject", "content", "status"])
                tickets.append(ticket.to_dict())

        return {
            "contact_id": contact_id,
            "name": f"{contact.properties.get('firstname','')} {contact.properties.get('lastname','')}".strip(),
            "email": email,
            "lifetime_value": contact.properties.get("lifetime_value"),
            "deals": deals,
            "tickets": tickets,
            "total_tickets": len(tickets),
            "open_tickets": len([t for t in tickets if t.get("properties", {}).get("status") != "closed"])
        }
    except Exception as e:
        return {"error": str(e)}