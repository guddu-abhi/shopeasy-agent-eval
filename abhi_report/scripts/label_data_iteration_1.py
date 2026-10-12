"""Hand labels from open coding of 141 traces (iteration 1, the optimization_2 agent: v8 prompt and tool
outputs with the original tool docstrings, qwen2.5:3b). Same structure and codebook as
label_data_docstrings_only.py. The traces were collected after iteration 2 with collect_traces.py on an
export of the optimization_2 branch; src/agent differs from iteration 2 only in tools.py docstrings.
LABELS maps (id, rep) -> (first_failure_code or None for pass, note). Secondary codes are in SECONDARY.
"BORDERLINE: " marks close calls; labels.py counts it only on passes, so fails keep it in the note here."""

P = None  # pass
LABELS = {
    # --- eval set ---
    (1,0):(P,""), (1,1):(P,""), (1,2):(P,""),
    (2,0):("L","'#3 pending ... shipped on 2026-04-10', '#2 shipped on 2026-03-20', '#1 delivered on 2026-01-15' (order dates)"), (2,1):("L","'Order #2, shipped on 2026-03-20', 'Order #1, delivered on 2026-01-15' (order dates)"), (2,2):(P,"dates given as 'placed on'"),
    (3,0):(P,""), (3,1):(P,""), (3,2):(P,""),
    (4,0):(P,"BORDERLINE: return #12 created; says it 'has been processed' (status requested); refund correctly pending approval"), (4,1):(P,""), (4,2):(P,"return #12 created; refund $79.99 pending approval"),
    (5,0):("E","list_categories('Electronics') for fitness equipment; wrong category, no retry; calls the Robot Vacuum and Smart Home Speaker fitness equipment"), (5,1):("E","list_categories('Electronics') for fitness equipment; wrong category, no retry; offers Electronics items"), (5,2):(P,"BORDERLINE: lists all 15 in-stock Fitness products with prices, no unit counts (reference has them)"),
    (6,0):(P,""), (6,1):(P,""), (6,2):(P,""),
    (7,0):("L","'#5 shipped on 2026-03-25', '#4 delivered on 2026-02-01' (order dates)"), (7,1):("L","same as run 0"), (7,2):("L","same as run 0"),
    (8,0):(P,""), (8,1):(P,""), (8,2):(P,""),
    (9,0):("L","says 'the order was shipped on 2026-04-01' (the order date)"), (9,1):(P,"status 'shipped' with items; repeats the tool's neutral 'Date' label"), (9,2):(P,"status 'shipped' with items; no carrier/tracking"),
    (10,0):(P,""), (10,1):(P,""), (10,2):(P,""),
    (11,0):(P,""), (11,1):(P,""), (11,2):(P,""),
    (12,0):(P,""), (12,1):(P,""), (12,2):(P,""),
    (13,0):(P,""), (13,1):(P,""), (13,2):(P,""),
    (14,0):(P,""), (14,1):("L","says 'delivered on 2026-01-05' (the order date)"), (14,2):(P,""),
    (15,0):("L","says 'delivered on 2026-01-30' (the order date)"), (15,1):("L","same as run 0"), (15,2):("L","same as run 0"),
    (16,0):(P,"lists both sunglasses"), (16,1):(P,"lists both sunglasses"), (16,2):(P,"BORDERLINE: list_categories('glasses') finds nothing; still says yes, under Accessories, without naming a product"),
    (17,0):(P,""), (17,1):(P,""), (17,2):(P,""),
    (18,0):(P,"BORDERLINE: existing return #2 reported with its reason; says the refund 'has been processed' (status approved)"), (18,1):(P,"existing return #2 reported with reason and refund"), (18,2):("J","says the existing return is because 'the boots were sent with the wrong color' (it is for a separated sole) and 'you have been refunded' (status approved)"),
    (19,0):(P,""), (19,1):(P,""), (19,2):(P,""),
    (20,0):("L","'#67 shipped on 2026-04-07', '#66 delivered on 2026-02-12' (order dates)"), (20,1):("L","same as run 0"), (20,2):("L","same as run 0"),
    (21,0):(P,""), (21,1):(P,""), (21,2):(P,""),
    (22,0):(P,"BORDERLINE: list_categories('books'); names the Mediterranean cookbook but also calls The Science of Nutrition a book about cooking"), (22,1):(P,"BORDERLINE: same as run 0"), (22,2):(P,"BORDERLINE: same as run 0"),
    (23,0):(P,"existing return #9 reported"), (23,1):(P,"BORDERLINE: existing return #9 reported; says it 'is already processed' (status requested)"), (23,2):(P,"existing return #9 reported"),
    (24,0):(P,"lists all 13 Outdoor products with prices"), (24,1):(P,"lists all 13 Outdoor products, names only"), (24,2):(P,"lists all 13 Outdoor products, names only"),
    (25,0):("L","says 'delivered on January 18, 2026' (the order date)"), (25,1):("L","says 'delivered on 2026-01-18' (the order date)"), (25,2):("L","says 'delivered on January 18, 2026' (the order date)"),
    (26,0):(P,""), (26,1):(P,""), (26,2):(P,""),
    (27,0):("E","list_categories('skincare') -> not a category; lists all categories without pointing to Beauty"), (27,1):("E","list_categories('skincare') -> not a category; points to Beauty but lists no products and does not retry"), (27,2):("E","same as run 0"),
    (28,0):(P,""), (28,1):(P,""), (28,2):(P,"BORDERLINE: count right; says they are 'in the Percussion line' (it is part of the product name)"),
    (29,0):(P,""), (29,1):(P,""), (29,2):(P,""),
    (30,0):(P,"dates given as 'placed on'"), (30,1):(P,""), (30,2):(P,""),
    (31,0):(P,"existing return #7 reported with reason and refund"), (31,1):(P,"existing return #7 reported"), (31,2):(P,"BORDERLINE: existing return #7 reported; says 'you have received a refund' (status approved)"),
    (32,0):(P,""), (32,1):(P,""), (32,2):(P,""),
    (33,0):(P,"date given as 'placed on'"), (33,1):("L","says 'delivered on 2025-12-01' (the order date)"), (33,2):("L","same as run 1"),
    (34,0):("L","every order date given as 'delivered on', including cancelled #47"), (34,1):("L","every order date given as 'shipped on', including cancelled #47"), (34,2):("L","same as run 1"),
    (35,0):(P,""), (35,1):(P,""), (35,2):(P,""),
    # --- synthetic edge cases ---
    ("S1",0):(P,""), ("S1",1):(P,""), ("S1",2):(P,""),
    ("S2",0):(P,"tool rejects (pending); explained"), ("S2",1):("F","lookup_order only; sees 'pending' but offers to start a return and asks again for the reason"), ("S2",2):("M","tool rejects (pending); says only 'subscribed' or delivered orders can be returned ('subscribed' for 'shipped')"),
    ("S3",0):("J","tool rejects (cancelled); says only items that 'haven't been shipped or delivered' can be returned (the rule is the opposite)"), ("S3",1):(P,"tool rejects (cancelled); explained"), ("S3",2):("H","tool rejects (cancelled); invents a rule that cancelled orders can be returned after a shop error or customer request"),
    ("S4",0):(P,""), ("S4",1):(P,""), ("S4",2):(P,""),
    ("S5",0):("H","says 'Yes, we sell laptops' and calls the Robot Vacuum Cleaner a laptop option; the store sells none"), ("S5",1):("H","says 'Yes, we sell laptops' and lists a hub, a mouse and headphones"), ("S5",2):("H","says 'Yes, we sell laptops' and lists headphones, earbuds, a sound machine and a mouse as laptops"),
    ("S6",0):("A","lookup_order(55) with no ID given; presents Will Harper's order as the user's"), ("S6",1):("A","same as run 0"), ("S6",2):("A","lookup_order(53) with no ID given; presents Vera Kowalski's order as the user's and says it 'shipped on March 30' (the order date)"),
    ("S7",0):(P,"both tools; status, shipping and total all correct"), ("S7",1):(P,"both tools; status, shipping and total all correct"), ("S7",2):("L","both tools; says 'shipped on March 25th' (the order date; it shipped 2026-03-26) and 'in transit' (it is out for delivery)"),
    ("S8",0):("I","check_inventory only; says the price is not provided and offers to look it up"), ("S8",1):("I","check_inventory only; says the price is not available"), ("S8",2):("I","check_inventory only; no price"),
    ("S9",0):("H","no tool call; invents a 30-day return policy"), ("S9",1):("H","no tool call; invents a 30-day return policy"), ("S9",2):(P,"BORDERLINE: no tool call; says the store has no specific return policy and explains how to start a return"),
    ("S10",0):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",1):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",2):(P,"BORDERLINE: does not confirm the order is pending"),
    ("S11",0):("J","says #2, #1 and #73 'have already arrived'; #2 is shipped, not delivered"), ("S11",1):("J","says #3 is the only order not yet arrived; #2 is shipped, not delivered"), ("S11",2):("J","opens with 'None of your orders have been delivered yet', then lists #1 and #73 as delivered"),
    ("S12",0):("K","search_orders exact match is case-sensitive; says no orders"), ("S12",1):("K","same"), ("S12",2):("K","same"),
}
# Downstream (non-first) failures worth tracking: L = order date called a ship/delivery date, H = invented fact.
SECONDARY = {(5,0):"H", ("S6",2):"L", ("S7",2):"J"}

# Traces whose final answer states a fact about the store's data or policies (orders, products,
# stock, returns, policy) that is false or not supported by any data. Claims about the agent's own
# abilities are excluded.
FALSE_CLAIM = {(2,0), (2,1), (5,0), (7,0), (7,1), (7,2), (9,0), (14,1), (15,0), (15,1), (15,2), (18,2), (20,0), (20,1), (20,2),
               (25,0), (25,1), (25,2), (33,1), (33,2), (34,0), (34,1), (34,2),
               ("S2",2), ("S3",0), ("S3",2), ("S5",0), ("S5",1), ("S5",2), ("S6",0), ("S6",1), ("S6",2), ("S7",2),
               ("S9",0), ("S9",1), ("S11",0), ("S11",1), ("S11",2), ("S12",0), ("S12",1), ("S12",2)}
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

