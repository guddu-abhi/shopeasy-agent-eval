"""Hand labels from open coding of 141 traces (main branch, qwen2.5:3b). Data only; labels.py analyses it.
LABELS maps (id, rep) -> (first_failure_code or None for pass, note). Secondary codes are in SECONDARY."""

P = None  # pass
LABELS = {
    # --- eval set ---
    (1,0):("A","check_inventory(12345); asks user for name"), (1,1):("A","check_inventory(12345)"), (1,2):("A","check_inventory(12345)"),
    (2,0):(P,""), (2,1):(P,""), (2,2):(P,""),
    (3,0):(P,""), (3,1):(P,""), (3,2):(P,""),
    (4,0):("F","lookup_order only; asks for a reason the user already gave; calls order date the delivery date"), (4,1):("H","return created, but invents 'refund to your original payment method'"), (4,2):("F","lookup_order only; asks for contact info; calls order date the delivery date"),
    (5,0):("E","search 'fitness equipment' -> none; says no fitness products"), (5,1):("E","same; false 'none available'"), (5,2):("E","same"),
    (6,0):(P,"BORDERLINE: speculates delivery 'might take slightly longer' than the estimate"), (6,1):(P,""), (6,2):("J","adds 'not yet available for tracking', contradicting result"),
    (7,0):("A","lookup_order(12345) instead of search_orders"), (7,1):("L","calls order dates ship/delivery dates"), (7,2):("J","swaps status of #4 and #5; calls order dates ship/delivery dates"),
    (8,0):("A","check_inventory(123) -> Cooler Bag"), (8,1):("A","check_inventory(123) -> Cooler Bag; says no product with ID 123 exists"), (8,2):("A","check_inventory(123); then says 80 chargers (ID 123)"),
    (9,0):("C","empty answer, no tool call"), (9,1):("C","empty answer"), (9,2):(P,"BORDERLINE: shipping only, items omitted"),
    (10,0):("B","asks for product ID"), (10,1):("B","asks for product ID"), (10,2):("B","asks for product ID"),
    (11,0):("A","get_product_details(12345)"), (11,1):("A","get_product_details(123456)"), (11,2):("A","get_product_details(12345)"),
    (12,0):(P,""), (12,1):("J","says 'in transit'; tool said out_for_delivery"), (12,2):(P,""),
    (13,0):(P,""), (13,1):(P,"volunteers customer email: 'reach out to her'"), (13,2):("L","calls the order date the delivery date"),
    (14,0):(P,""), (14,1):(P,""), (14,2):(P,""),
    (15,0):(P,""), (15,1):("L","says delivered on 2026-01-30 (the order date)"), (15,2):(P,""),
    (16,0):(P,"lists both sunglasses"), (16,1):("B","asks for brand/model, no search"), (16,2):("B","asks for brand/type, no search"),
    (17,0):("C","empty answer"), (17,1):(P,""), (17,2):("C","empty answer"),
    (18,0):(P,"BORDERLINE: adds generic 'send back within the return period'"), (18,1):("C","empty answer"), (18,2):("H","invents a return tracking number 'provided upon approval'"),
    (19,0):(P,""), (19,1):(P,""), (19,2):(P,""),
    (20,0):("D","search_orders('email:bianca@...')"), (20,1):("D","same"), (20,2):("D","same"),
    (21,0):("I","finds #46, then asks the user to run check_inventory"), (21,1):(P,""), (21,2):(P,""),
    (22,0):("D","search 'category:books category:cooking'"), (22,1):("B","asks which cuisine, no search"), (22,2):("D","search 'category:books AND category:cooking'"),
    (23,0):("F","lookup only; misses existing return, asks to proceed; calls order date the delivery date"), (23,1):("F","lookup only; invents store-credit default"), (23,2):(P,"BORDERLINE: existing return #9 reported; adds generic 'allow a few days'"),
    (24,0):("B","asks what kind of gear"), (24,1):("B","asks what kind of gear"), (24,2):("B","asks what activity"),
    (25,0):(P,""), (25,1):("L","says delivered on 2026-01-18 (the order date)"), (25,2):("L","says delivered as of 2026-01-18 (the order date)"),
    (26,0):(P,""), (26,1):(P,""), (26,2):(P,""),
    (27,0):("D","search 'category:Skincare'"), (27,1):("E","search 'skincare' -> none (category is Beauty)"), (27,2):("D","search 'category:skincare'"),
    (28,0):("A","check_inventory(12345)"), (28,1):("A","check_inventory(123)"), (28,2):("A","check_inventory(123); says no massage guns in stock"),
    (29,0):(P,""), (29,1):(P,""), (29,2):(P,""),
    (30,0):("D","search_orders('email:diana@...')"), (30,1):("D","same"), (30,2):("D","same"),
    (31,0):("F","lookup only; tells user to initiate the return; calls order date the delivery date"), (31,1):("J","calls an approved return 'complete'"), (31,2):("F","lookup only; asks 'shall I proceed?'"),
    (32,0):("A","check_inventory(123); says hammock out of stock"), (32,1):("A","check_inventory(123); says hammock out of stock"), (32,2):("A","check_inventory(12345)"),
    (33,0):(P,""), (33,1):(P,""), (33,2):(P,""),
    (34,0):(P,""), (34,1):(P,"BORDERLINE: 'delivered for $214.97 on 2026-02-15' can be read as a delivery date"), (34,2):("L","calls order dates cancel/delivery dates"),
    (35,0):("B","asks for product_id"), (35,1):(P,""), (35,2):(P,""),
    # --- synthetic edge cases ---
    ("S1",0):("C","empty answer"), ("S1",1):(P,""), ("S1",2):(P,""),
    ("S2",0):("B","asks for the order ID it was given"), ("S2",1):("F","sees 'pending' but asks for contact info to proceed"), ("S2",2):(P,"tool rejects; explained"),
    ("S3",0):("B","asks for the order ID it was given"), ("S3",1):("B","same"), ("S3",2):("B","same"),
    ("S4",0):("B","claims it cannot search by email"), ("S4",1):(P,""), ("S4",2):(P,""),
    ("S5",0):(P,"BORDERLINE: offers Laptop Sleeve; does not say no laptops"), ("S5",1):(P,""), ("S5",2):(P,""),
    ("S6",0):(P,""), ("S6",1):(P,""), ("S6",2):(P,""),
    ("S7",0):(P,"BORDERLINE: order status only; misses out_for_delivery"), ("S7",1):(P,"BORDERLINE: order status only; misses out_for_delivery"), ("S7",2):(P,"BORDERLINE: order status only; misses out_for_delivery"),
    ("S8",0):("A","check_inventory(12345)"), ("S8",1):("A","same"), ("S8",2):("A","same"),
    ("S9",0):("H","invents 30-day return policy"), ("S9",1):("H","invents 30-day policy"), ("S9",2):("H","invents 30-day policy"),
    ("S10",0):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",1):(P,"BORDERLINE: does not confirm the order is pending"), ("S10",2):("C","empty answer"),
    ("S11",0):("A","get_shipping_status(12345) instead of search_orders"), ("S11",1):("A","same"), ("S11",2):("A","same"),
    ("S12",0):("K","search_orders exact match is case-sensitive"), ("S12",1):("K","same"), ("S12",2):("K","same"),
}
# Downstream (non-first) failures worth tracking: G = states a wrong fact built on a wrong tool result.
SECONDARY = {(8,2):"G", (28,2):"G", (32,0):"G", (32,1):"G", (23,1):"H",
             (4,0):"L", (4,2):"L", (23,0):"L", (31,0):"L", (7,2):"L"}

# Traces whose final answer states a fact about the store's data or policies (orders, products,
# stock, returns, policy) that is false or not supported by any data. Claims about the agent's own
# abilities are excluded.
FALSE_CLAIM = {(20,0),(20,1),(20,2),(30,0),(30,1),(30,2),(22,0),(22,2),(27,0),   # D
               (5,0),(5,1),(5,2),(27,1),                                         # E
               ("S12",0),("S12",1),("S12",2),                                   # K
               (6,2),(7,2),(12,1),(31,1),                                        # J
               (13,2),(7,1),(15,1),(25,1),(25,2),(34,2),                         # L
               ("S9",0),("S9",1),("S9",2),(18,2),(4,1),                          # H
               (8,2),(28,2),(32,0),(32,1),(8,1),                                 # A (wrong product returned)
               (23,1),                                                           # F + invented store-credit default
               (4,0),(4,2),(23,0),(31,0)}                                        # F + order date called delivery date
# Step of the agent loop where the first failure happens (simplified from the guide's transition matrix).
STAGE = {"B":"1 decide to use a tool", "A":"2 build tool arguments", "D":"2 build tool arguments",
         "E":"3 retrieval returns the data", "K":"3 retrieval returns the data",
         "F":"4 chain / take the action", "I":"4 chain / take the action",
         "J":"5 answer faithfully", "L":"5 answer faithfully", "H":"5 answer faithfully", "C":"? unknown (empty output)"}

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
}
# Entity the user refers to — a dimension observed while reading traces.
REF = {1:"product_name",8:"product_name",10:"product_name",11:"product_name",21:"product_name",28:"product_name",32:"product_name",35:"product_name","S8":"product_name",
       17:"product_id", 2:"email",7:"email",20:"email",30:"email",34:"email","S4":"email","S11":"email","S12":"email",
       5:"category_browse",16:"category_browse",22:"category_browse",24:"category_browse",27:"category_browse","S5":"category_browse",
       "S6":"none","S9":"none"}

