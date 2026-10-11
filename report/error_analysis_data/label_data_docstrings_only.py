"""Hand labels from open coding of 141 traces (iteration 2, docstrings_only: v8 tool outputs with the
new tool docstrings and argument descriptions, qwen2.5:3b). Same structure and codebook as label_data.py,
plus code M from label_data_better_tool_docstring.py.
LABELS maps (id, rep) -> (first_failure_code or None for pass, note). Secondary codes are in SECONDARY.
"BORDERLINE: " marks close calls; labels.py counts it only on passes, so fails keep it in the note here."""

P = None  # pass
LABELS = {
    # --- eval set ---
    (1,0):(P,""), (1,1):(P,""), (1,2):(P,""),
    (2,0):("L","'#2 shipped on March 20', '#1 delivered on January 15', '#73 delivered on ...' (all order dates)"), (2,1):("L","'shipped on 2026-03-20', 'delivered on 2026-01-15' (order dates)"), (2,2):("L","'shipped on 2026-03-20', 'delivered on 2026-01-15' (order dates)"),
    (3,0):(P,""), (3,1):(P,""), (3,2):(P,""),
    (4,0):(P,"return #12 created; refund $79.99 pending approval"), (4,1):(P,""), (4,2):("J","says 'the return has been approved'; the tool said status requested, refund pending approval"),
    (5,0):(P,"BORDERLINE: lists all 15 in-stock Fitness products with prices, no unit counts (reference has them)"), (5,1):(P,"BORDERLINE: same as run 0"), (5,2):(P,"BORDERLINE: same as run 0"),
    (6,0):(P,""), (6,1):(P,""), (6,2):(P,""),
    (7,0):("L","'#5 shipped on 2026-03-25', '#4 delivered on 2026-02-01' (order dates)"), (7,1):("L","same as run 0"), (7,2):("L","same as run 0"),
    (8,0):(P,""), (8,1):(P,""), (8,2):(P,""),
    (9,0):(P,"status 'shipped' with items; no carrier/tracking"), (9,1):("L","says 'it was shipped on April 1, 2026' (the order date)"), (9,2):(P,"status 'shipped'; repeats the tool's neutral 'Date' label"),
    (10,0):(P,"uses search_products; price correct"), (10,1):(P,""), (10,2):(P,""),
    (11,0):(P,""), (11,1):(P,""), (11,2):(P,""),
    (12,0):(P,""), (12,1):(P,""), (12,2):("J","BORDERLINE: says 'out for delivery since 2026-04-03'; that is the ship date"),
    (13,0):(P,""), (13,1):(P,""), (13,2):(P,""),
    (14,0):("L","says 'delivered on 2026-01-05' (the order date)"), (14,1):(P,""), (14,2):("L","says 'delivered on 2026-01-05' (the order date)"),
    (15,0):(P,""), (15,1):(P,""), (15,2):(P,""),
    (16,0):(P,"lists both sunglasses"), (16,1):(P,"lists both sunglasses"), (16,2):(P,"lists both sunglasses"),
    (17,0):(P,""), (17,1):(P,""), (17,2):(P,""),
    (18,0):("J","says the existing return 'is for the wrong color' (it is for a separated sole) and the refund 'has been processed' (status approved)"), (18,1):(P,"BORDERLINE: existing return reported, but calls its reason 'the reason you provided'"), (18,2):(P,"existing return #2 reported with reason and refund"),
    (19,0):(P,""), (19,1):(P,""), (19,2):(P,""),
    (20,0):("L","'#67 shipped on 2026-04-07', '#66 delivered on 2026-02-12' (order dates)"), (20,1):("L","'shipped on 2026-04-07' and dates for delivered orders (order dates)"), (20,2):("L","same as run 0"),
    (21,0):(P,""), (21,1):(P,""), (21,2):(P,""),
    (22,0):(P,"BORDERLINE: search 'cookbook' finds both; calls the Python Programming Cookbook a book about cooking"), (22,1):("E","search_products('book cooking') -> none; says 'there are no books about cooking in our catalog'"), (22,2):("E","same as run 1"),
    (23,0):(P,"existing return #9 reported"), (23,1):(P,"existing return #9 reported"), (23,2):(P,"existing return #9 reported"),
    (24,0):(P,"lists all 13 Outdoor products, names only"), (24,1):(P,""), (24,2):(P,"lists all 13 Outdoor products, names only"),
    (25,0):(P,""), (25,1):(P,""), (25,2):(P,"lists 5 items and the total; no line prices (not asked)"),
    (26,0):(P,""), (26,1):(P,""), (26,2):(P,""),
    (27,0):("E","search_products('skincare') -> none (category is Beauty); no retry, asks for details"), (27,1):("E","search 'skincare' -> none; says 'we don't have any skincare products listed'"), (27,2):("E","list_categories('Skincare') returns all categories; lists them without pointing to Beauty"),
    (28,0):(P,""), (28,1):(P,""), (28,2):(P,""),
    (29,0):(P,""), (29,1):(P,""), (29,2):(P,""),
    (30,0):("L","all three order dates given as 'shipped on', including pending #72"), (30,1):(P,""), (30,2):(P,""),
    (31,0):(P,"existing return #7 reported with reason and refund"), (31,1):(P,"existing return #7 reported"), (31,2):(P,"existing return #7 reported"),
    (32,0):(P,""), (32,1):(P,""), (32,2):(P,""),
    (33,0):("L","says 'delivered on December 1, 2025' (the order date)"), (33,1):(P,""), (33,2):("L","says 'delivered on December 1, 2025' (the order date)"),
    (34,0):(P,""), (34,1):(P,""), (34,2):("L","every order date given as 'delivered on', including cancelled #47"),
    (35,0):(P,""), (35,1):(P,""), (35,2):(P,""),
    # --- synthetic edge cases ---
    ("S1",0):(P,""), ("S1",1):(P,""), ("S1",2):(P,""),
    ("S2",0):(P,"tool rejects (pending); explained"), ("S2",1):(P,"tool rejects (pending); explained"), ("S2",2):(P,"tool rejects (pending); explained"),
    ("S3",0):(P,"tool rejects (cancelled); explained"), ("S3",1):(P,"tool rejects (cancelled); explained"), ("S3",2):(P,"tool rejects (cancelled); explained"),
    ("S4",0):(P,""), ("S4",1):(P,""), ("S4",2):(P,""),
    ("S5",0):(P,"BORDERLINE: offers Laptop Sleeve; suggests the user 'search for laptop products' instead of saying none are sold"), ("S5",1):(P,"BORDERLINE: offers Laptop Sleeve; does not say no laptops"), ("S5",2):("H","says 'we also sell laptops directly'; the store sells none"),
    ("S6",0):("A","lookup_order(12345) with no ID given; then asks for an email"), ("S6",1):("A","lookup_order(12345) with no ID given"), ("S6",2):("A","lookup_order(123456) with no ID given"),
    ("S7",0):(P,"BORDERLINE: status and total only; then asks the user for the tracking information"), ("S7",1):(P,"BORDERLINE: status and total only; asks the user for carrier, tracking and delivery date"), ("S7",2):("J","says the order 'is currently in the shipped status and will soon be shipped'"),
    ("S8",0):("I","check_inventory only; says 'the price is not available'"), ("S8",1):("I","check_inventory only; asks the user for the price"), ("S8",2):("I","check_inventory only; then invents a price of $25.00 (it is $69.99)"),
    ("S9",0):("A","initiate_return(order_id=null) for a policy question; validation error; asks for an order number"), ("S9",1):("A","initiate_return(order_id=1, reason='I changed my mind about the purchase.') for a policy question: CREATES a real return on Alice's order #1 and reports it"), ("S9",2):("A","initiate_return(order_id=0) for a policy question; asks for the order ID"),
    ("S10",0):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",1):(P,"BORDERLINE: does not confirm the order is pending; asks for a tracking number"), ("S10",2):(P,"BORDERLINE: does not confirm the order is pending"),
    ("S11",0):(P,""), ("S11",1):(P,""), ("S11",2):("J","says #2 'was delivered on 2026-03-20' (its order date) and that only #3 has not arrived"),
    ("S12",0):("K","search_orders exact match is case-sensitive; says no orders"), ("S12",1):("K","same"), ("S12",2):("K","same"),
}
# Downstream (non-first) failures worth tracking: L = order date called a ship/delivery date, H = invented fact.
SECONDARY = {("S8",2):"H", ("S11",2):"L"}

# Traces whose final answer states a fact about the store's data or policies (orders, products,
# stock, returns, policy) that is false or not supported by any data. Claims about the agent's own
# abilities are excluded.
FALSE_CLAIM = {(2,0), (2,1), (2,2), (4,2), (7,0), (7,1), (7,2), (9,1), (12,2), (14,0), (14,2), (18,0), (20,0), (20,1), (20,2), (22,1), (22,2), (27,1), (30,0), (33,0), (33,2), (34,2), ("S5",2), ("S7",2), ("S8",2), ("S9",1), ("S11",2), ("S12",0), ("S12",1), ("S12",2)}
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

