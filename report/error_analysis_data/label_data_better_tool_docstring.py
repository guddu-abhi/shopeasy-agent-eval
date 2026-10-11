"""Hand labels from open coding of 141 traces (better_tool_docstring branch: JSON tool outputs and
LangChain-style tool docstrings, qwen2.5:3b). Same structure and codebook as label_data.py, plus code M.
LABELS maps (id, rep) -> (first_failure_code or None for pass, note). Secondary codes are in SECONDARY.
"BORDERLINE: " marks close calls; labels.py counts it only on passes, so fails keep it in the note here."""

P = None  # pass
LABELS = {
    # --- eval set ---
    (1,0):(P,""), (1,1):(P,""), (1,2):(P,""),
    (2,0):(P,""), (2,1):(P,""), (2,2):(P,""),
    (3,0):(P,""), (3,1):(P,""), (3,2):(P,""),
    (4,0):(P,"BORDERLINE: return created; omits refund amount; adds 'you should receive a notification ... shortly'"), (4,1):(P,"BORDERLINE: 'refund is pending approval' then 'you will receive a refund of $79.99' as if certain"), (4,2):(P,"return created; refund amount omitted (not asked)"),
    (5,0):(P,"BORDERLINE: list_categories returns the 15 in-stock Fitness products; lists all with prices, no unit counts (reference has them)"), (5,1):(P,"BORDERLINE: same as run 0"), (5,2):(P,"BORDERLINE: same as run 0"),
    (6,0):(P,""), (6,1):(P,""), (6,2):(P,""),
    (7,0):("L","order dates given as 'Shipped on 2026-03-25' / 'Delivered on ...'; also says shipped #5 is 'still being processed'"), (7,1):("L","order dates labelled 'Shipped Date' / 'Delivered Date'"), (7,2):("J","wrong order dates: #5 'placed on 2026-02-01', #4 '2026-01-20', #6 '2026-02-01'"),
    (8,0):(P,""), (8,1):(P,""), (8,2):(P,""),
    (9,0):("J","BORDERLINE: says order is 'being processed', then 'still shipped'; no carrier/tracking"), (9,1):("J","says shipped order 'is still pending shipment'"), (9,2):("J","says status 'shipped', then 'still pending ... notified once it is processed'"),
    (10,0):(P,""), (10,1):(P,""), (10,2):(P,""),
    (11,0):(P,""), (11,1):(P,""), (11,2):(P,""),
    (12,0):(P,""), (12,1):(P,""), (12,2):(P,""),
    (13,0):(P,"volunteers customer name and email"), (13,1):(P,"volunteers customer name and email"), (13,2):(P,"volunteers customer name and email"),
    (14,0):("L","says 'delivered on 2026-01-05' (the order date); volunteers customer email"), (14,1):("L","says 'delivered on January 5, 2026' (the order date)"), (14,2):(P,""),
    (15,0):("L","says 'delivered on January 30, 2026' (the order date)"), (15,1):(P,""), (15,2):(P,""),
    (16,0):(P,"lists both sunglasses"), (16,1):(P,"lists both sunglasses"), (16,2):(P,"lists both sunglasses"),
    (17,0):(P,""), (17,1):(P,""), (17,2):(P,""),
    (18,0):(P,"existing return #2 reported (approved, $149.99); does not mention its reason differs"), (18,1):(P,"existing return reported"), (18,2):("J","BORDERLINE: says 'you've already had your issue with the wrong color addressed'; the existing return is for a separated sole"),
    (19,0):(P,""), (19,1):(P,""), (19,2):(P,""),
    (20,0):("M","status of #67 written as 'shased'; then #66/#65 'delivered on' their order dates"), (20,1):(P,""), (20,2):("J","#67 'Shipped on 2026-02-12' (#66's order date), status 'Shashted'; #66/#65 'Delivered on' order dates"),
    (21,0):(P,""), (21,1):(P,""), (21,2):(P,""),
    (22,0):("E","search_products('book cooking') -> none; says 'we don't have any books about cooking'"), (22,1):("E","search_products('books cooking') -> none; no retry, asks for details"), (22,2):("E","search_products('books about cooking') -> none; no retry"),
    (23,0):(P,"existing return #9 reported with its reason"), (23,1):(P,"existing return #9 reported with its reason"), (23,2):(P,"existing return #9 reported with its reason"),
    (24,0):(P,"lists all 13 Outdoor products, names only"), (24,1):(P,""), (24,2):("H","BORDERLINE: adds product descriptions no tool returned, e.g. water bottle 'expands to a cup size'"),
    (25,0):("L","says 'delivered on 2026-01-18' (the order date)"), (25,1):("L","says 'delivered ... on 2026-01-18' (the order date)"), (25,2):("L","says 'delivered on 2026-01-18' (the order date)"),
    (26,0):(P,""), (26,1):(P,""), (26,2):(P,""),
    (27,0):("E","BORDERLINE: search_products('skincare') -> none (category is Beauty); no retry. 'no skincare products matching that name' read as the search result, not counted as a false claim"), (27,1):("E","search 'skincare' -> none; says 'there are no products directly related to skincare'"), (27,2):("E","search 'skincare' -> none; no retry, asks for details"),
    (28,0):(P,""), (28,1):(P,""), (28,2):(P,""),
    (29,0):(P,""), (29,1):(P,""), (29,2):(P,""),
    (30,0):("J","order dates swapped: #72 'placed on 2026-02-25', #71 'delivered on 2026-04-14'"), (30,1):("J","dates and totals swapped between orders: #71 $229.89, #70 $164.97, #70 'placed on 2026-04-14'"), (30,2):("J","#72 'placed on 2026-02-25, delivered' (it is pending, placed 2026-04-14)"),
    (31,0):(P,"existing return #7 reported with reason and refund"), (31,1):(P,"existing return #7 reported"), (31,2):(P,"existing return #7 reported"),
    (32,0):(P,""), (32,1):(P,""), (32,2):(P,""),
    (33,0):("L","says 'delivered on 2025-12-01' (the order date)"), (33,1):(P,""), (33,2):("L","says 'delivered on December 1, 2025' (the order date); then asks about a return nobody mentioned"),
    (34,0):("L","order dates given as 'cancelled on' / 'delivered on' dates"), (34,1):(P,""), (34,2):("J","swaps #47 and #46: '#47 delivered on 2026-02-15, $214.97', '#46 cancelled'"),
    (35,0):(P,""), (35,1):(P,""), (35,2):(P,""),
    # --- synthetic edge cases ---
    ("S1",0):(P,""), ("S1",1):(P,""), ("S1",2):(P,""),
    ("S2",0):(P,"tool rejects (pending); explained"), ("S2",1):(P,"tool rejects (pending); explained"), ("S2",2):(P,"tool rejects (pending); explained"),
    ("S3",0):(P,"tool rejects (cancelled); explained"), ("S3",1):(P,"tool rejects (cancelled); explained"), ("S3",2):(P,"tool rejects (cancelled); explained"),
    ("S4",0):(P,""), ("S4",1):(P,""), ("S4",2):(P,""),
    ("S5",0):(P,"BORDERLINE: offers Laptop Sleeve; asks if user wants 'actual laptops' but does not say none are sold"), ("S5",1):(P,"BORDERLINE: offers Laptop Sleeve; does not say no laptops"), ("S5",2):(P,"BORDERLINE: offers Laptop Sleeve; does not say no laptops"),
    ("S6",0):("A","lookup_order(50) with no ID given; presents another customer's order as 'your order', with their name and email"), ("S6",1):("A","lookup_order(14) with no ID given; presents Eva Martinez's order as 'your order'; calls the order date the delivery date"), ("S6",2):("A","lookup_order(12345) with no ID given; then asks the user to check the ID"),
    ("S7",0):("J","calls both tools, but says 'currently in transit'; tool said out_for_delivery"), ("S7",1):("M","status written as 'shased'; no shipping lookup, offers to check delivery"), ("S7",2):(P,"BORDERLINE: order status and total only; misses out_for_delivery, offers to check"),
    ("S8",0):("I","check_inventory only; never gets the price the user asked for"), ("S8",1):("I","check_inventory only; says 'you can find it at your desired price' instead of a price"), ("S8",2):("I","check_inventory only; no price"),
    ("S9",0):("A","lookup_order(1) for a policy question; says 'the order you're referring to is a delivered order' and invents a return procedure"), ("S9",1):("A","initiate_return(order_id=0, reason='I don't want it anymore'): a write call with an invented ID and reason; then asks for the order number"), ("S9",2):(P,"says policy info is not available; no invention"),
    ("S10",0):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",1):(P,"BORDERLINE: does not confirm the order is pending; promises 'I'll check back later'"), ("S10",2):(P,"BORDERLINE: does not confirm the order is pending; promises 'I'll check back later'"),
    ("S11",0):(P,""), ("S11",1):(P,""), ("S11",2):("J","says #2 'shipped and delivered on 2026-03-20' (its order date) and that only #3 has not arrived"),
    ("S12",0):("K","search_orders exact match is case-sensitive; says no orders"), ("S12",1):("K","same"), ("S12",2):("K","same"),
}
# Downstream (non-first) failures worth tracking: L = order date called a ship/delivery date, H = invented fact.
SECONDARY = {(20,0):"L", (20,2):"L", (30,0):"L", (34,2):"L", ("S6",1):"L", ("S9",0):"H", ("S11",2):"L"}

# Traces whose final answer states a fact about the store's data or policies (orders, products,
# stock, returns, policy) that is false or not supported by any data. Claims about the agent's own
# abilities are excluded.
FALSE_CLAIM = {(7,0), (7,1), (7,2), (9,0), (9,1), (9,2), (14,0), (14,1), (15,0), (18,2), (20,0), (20,2), (22,0), (24,2), (25,0), (25,1), (25,2), (27,1), (30,0), (30,1), (30,2), (33,0), (33,2), (34,0), (34,2), ("S6",0), ("S6",1), ("S7",0), ("S9",0), ("S11",2), ("S12",0), ("S12",1), ("S12",2)}
# Step of the agent loop where the first failure happens (simplified from the guide's transition matrix).
STAGE = {"B":"1 decide to use a tool", "A":"2 build tool arguments", "D":"2 build tool arguments",
         "E":"3 retrieval returns the data", "K":"3 retrieval returns the data",
         "F":"4 chain / take the action", "I":"4 chain / take the action",
         "J":"5 answer faithfully", "L":"5 answer faithfully", "H":"5 answer faithfully", "C":"? unknown (empty output)", "M":"5 answer faithfully"}

CODES = {
    "A": "Invents an ID instead of searching",
    "B": "Asks the user instead of looking it up",
    "C": "Empty response",
    "D": "Invents query syntax in search argument",
    "E": "Search term misses catalog vocabulary; no retry",
    "F": "Return action not executed",
    "H": "Invents policy or facts",
    "I": "Stops mid-chain",
    "J": "Misreads tool output (other than dates)",
    "L": "Calls the order date a ship/delivery date",
    "K": "Tool rejects valid input (case-sensitive email)",
    "M": "Garbled word in the reply (e.g. 'shased' for 'shipped')",
}
# Entity the user refers to — a dimension observed while reading traces.
REF = {1:"product_name",8:"product_name",10:"product_name",11:"product_name",21:"product_name",28:"product_name",32:"product_name",35:"product_name","S8":"product_name",
       17:"product_id", 2:"email",7:"email",20:"email",30:"email",34:"email","S4":"email","S11":"email","S12":"email",
       5:"category_browse",16:"category_browse",22:"category_browse",24:"category_browse",27:"category_browse","S5":"category_browse",
       "S6":"none","S9":"none"}

