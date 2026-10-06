"""Populate the SQLite database with realistic mock data for the e-commerce store."""

from __future__ import annotations

from src.data.database import DB_PATH, get_connection, init_schema


CUSTOMERS = [
    ("Alice Johnson", "alice@example.com", "555-0101"),
    ("Bob Smith", "bob@example.com", "555-0102"),
    ("Carol White", "carol@example.com", "555-0103"),
    ("David Brown", "david@example.com", "555-0104"),
    ("Eva Martinez", "eva@example.com", "555-0105"),
    ("Frank Lee", "frank@example.com", "555-0106"),
    ("Grace Kim", "grace@example.com", "555-0107"),
    ("Henry Davis", "henry@example.com", "555-0108"),
    ("Irene Wilson", "irene@example.com", "555-0109"),
    ("Jake Thompson", "jake@example.com", "555-0110"),
    ("Karen Nguyen", "karen@example.com", "555-0111"),
    ("Leo Ramirez", "leo@example.com", "555-0112"),
    ("Maria Fischer", "maria@example.com", "555-0113"),
    ("Noah Patel", "noah@example.com", "555-0114"),
    ("Olivia Chen", "olivia@example.com", "555-0115"),
    ("Peter Andersen", "peter@example.com", "555-0116"),
    ("Quinn O'Brien", "quinn@example.com", "555-0117"),
    ("Rosa Kapoor", "rosa@example.com", "555-0118"),
    ("Sam Murray", "sam@example.com", "555-0119"),
    ("Tina Johansson", "tina@example.com", "555-0120"),
    ("Ulrich Becker", "ulrich@example.com", "555-0121"),
    ("Vera Kowalski", "vera@example.com", "555-0122"),
    ("Will Harper", "will@example.com", "555-0123"),
    ("Xena Brooks", "xena@example.com", "555-0124"),
    ("Youssef Al-Rashid", "youssef@example.com", "555-0125"),
    ("Zoe Campbell", "zoe@example.com", "555-0126"),
    ("Amir Saleh", "amir@example.com", "555-0127"),
    ("Bianca Torres", "bianca@example.com", "555-0128"),
    ("Caleb Morgan", "caleb@example.com", "555-0129"),
    ("Diana Okafor", "diana@example.com", "555-0130"),
]

PRODUCTS = [
    # --- Footwear ---
    ("Blue Ultraboost Running Shoe", "Footwear", 179.99, "High-performance running shoe with Boost midsole and Primeknit upper in ocean blue.", 45),        # 1
    ("Classic White Sneaker", "Footwear", 89.99, "Minimalist white leather sneaker for everyday wear.", 120),                                                # 2
    ("Trail Hiking Boot", "Footwear", 149.99, "Waterproof hiking boot with Vibram sole for rugged terrain.", 30),                                            # 3
    # --- Electronics ---
    ("Wireless Noise-Cancelling Headphones", "Electronics", 299.99, "Over-ear headphones with active noise cancellation and 30-hour battery.", 60),           # 4
    ("Bluetooth Portable Speaker", "Electronics", 79.99, "Compact waterproof speaker with 12-hour battery life.", 85),                                        # 5
    # --- Clothing ---
    ("Organic Cotton T-Shirt", "Clothing", 34.99, "Soft organic cotton crew-neck tee in charcoal grey.", 200),                                                # 6
    ("Slim Fit Chino Pants", "Clothing", 59.99, "Stretch cotton chinos in navy blue with tapered fit.", 150),                                                 # 7
    ("Merino Wool Sweater", "Clothing", 119.99, "Lightweight merino wool crew-neck sweater in forest green.", 40),                                            # 8
    # --- Accessories ---
    ("Stainless Steel Water Bottle", "Accessories", 29.99, "Double-wall insulated 750ml bottle, keeps drinks cold 24 hours.", 300),                           # 9
    ("Leather Messenger Bag", "Accessories", 189.99, "Full-grain leather messenger bag with padded laptop compartment.", 25),                                 # 10
    # --- Fitness ---
    ("Yoga Mat Premium", "Fitness", 49.99, "Non-slip 6mm thick yoga mat with carrying strap.", 75),                                                           # 11
    ("Adjustable Dumbbell Set", "Fitness", 249.99, "Adjustable dumbbells from 5-52.5 lbs each, space-saving design.", 15),                                    # 12
    # --- Clothing ---
    ("Running Shorts", "Clothing", 44.99, "Lightweight mesh-lined running shorts with zip pocket.", 180),                                                     # 13
    # --- Home ---
    ("Ceramic Coffee Mug", "Home", 14.99, "Handcrafted 12oz ceramic mug in matte black.", 500),                                                              # 14
    ("Bamboo Cutting Board", "Home", 24.99, "Large bamboo cutting board with juice groove, 18x12 inches.", 90),                                               # 15
    # --- Accessories ---
    ("UV Protection Sunglasses", "Accessories", 69.99, "Polarized lenses with lightweight titanium frame.", 110),                                              # 16
    # --- Electronics ---
    ("Fitness Tracker Watch", "Electronics", 149.99, "Heart rate, sleep, and activity tracking with 7-day battery.", 70),                                      # 17
    # --- Clothing ---
    ("Insulated Winter Jacket", "Clothing", 199.99, "700-fill down insulated jacket, water-resistant shell.", 35),                                             # 18
    # --- Outdoor ---
    ("Camping Backpack 60L", "Outdoor", 129.99, "60-liter backpack with rain cover and multiple compartments.", 50),                                           # 19
    # --- Electronics ---
    ("Portable Phone Charger", "Electronics", 39.99, "20000mAh power bank with USB-C and dual USB-A ports.", 200),                                            # 20

    # New products (IDs 21–170)

    # --- Footwear ---
    ("Black Leather Dress Shoes", "Footwear", 159.99, "Oxford-style full-grain leather dress shoes with cushioned insole.", 35),                               # 21
    ("Canvas Slip-On Sneakers", "Footwear", 49.99, "Lightweight canvas slip-on sneakers in navy, elastic gore panels.", 200),                                  # 22
    ("Women's Ballet Flats", "Footwear", 69.99, "Soft leather ballet flats with padded footbed in blush pink.", 80),                                           # 23
    ("Memory Foam House Slippers", "Footwear", 29.99, "Plush house slippers with memory foam insole and rubber outsole.", 150),                                # 24
    ("Waterproof Rain Boots", "Footwear", 79.99, "Tall rubber rain boots with cotton lining, matte black finish.", 65),                                        # 25
    ("Cross-Training Athletic Shoes", "Footwear", 134.99, "Versatile cross-training shoes with wide toe box and rope-grip outsole.", 55),                      # 26
    ("Cork Footbed Sandals", "Footwear", 59.99, "Contoured cork footbed sandals with adjustable buckle straps.", 90),                                          # 27
    ("Steel Toe Work Boots", "Footwear", 129.99, "ASTM-rated steel toe work boots with slip-resistant outsole.", 40),                                          # 28
    ("Lightweight Trail Runners", "Footwear", 119.99, "Zero-drop trail running shoes with rock plate and breathable mesh.", 50),                               # 29
    ("Wool Blend Ankle Boots", "Footwear", 139.99, "Felted wool-blend ankle boots with side zip, charcoal grey.", 30),                                         # 30
    ("Kids' Velcro Sneakers", "Footwear", 39.99, "Easy-on kids' sneakers with double velcro straps, sizes 10-3.", 120),                                        # 31
    ("Platform Espadrilles", "Footwear", 74.99, "Jute-wrapped platform espadrilles in natural canvas.", 60),                                                   # 32

    # --- Electronics ---
    ("Mechanical Gaming Keyboard", "Electronics", 129.99, "Full-size mechanical keyboard with Cherry MX Blue switches and RGB backlighting.", 45),             # 33
    ("Wireless Ergonomic Mouse", "Electronics", 69.99, "Vertical ergonomic mouse with 6 buttons, 2.4GHz and Bluetooth dual-mode.", 80),                       # 34
    ("4K Webcam with Ring Light", "Electronics", 89.99, "Ultra HD webcam with built-in ring light and auto-focus, USB-C.", 60),                                # 35
    ("USB-C Hub 7-in-1", "Electronics", 49.99, "USB-C hub with HDMI 4K, 3x USB-A, SD/microSD, and 100W pass-through charging.", 150),                        # 36
    ("Wireless Earbuds Pro", "Electronics", 159.99, "True wireless earbuds with ANC, transparency mode, and 8-hour battery.", 70),                             # 37
    ("10-inch Android Tablet", "Electronics", 249.99, "10.1-inch IPS display tablet with 64GB storage, octa-core processor.", 25),                             # 38
    ("Smart Home Speaker", "Electronics", 99.99, "Voice-controlled smart speaker with premium sound and home automation hub.", 90),                            # 39
    ("White Noise Sound Machine", "Electronics", 44.99, "Portable sound machine with 20 soothing sounds and timer function.", 110),                            # 40
    ("External SSD 1TB", "Electronics", 89.99, "Portable 1TB SSD with USB 3.2 Gen 2, up to 1050 MB/s read speed.", 55),                                      # 41
    ("Wireless Charging Pad", "Electronics", 29.99, "Qi-certified 15W fast wireless charging pad, slim design.", 200),                                         # 42
    ("LED Desk Lamp with USB", "Electronics", 39.99, "Adjustable LED desk lamp with 5 brightness levels and USB charging port.", 130),                         # 43
    ("Digital Kitchen Scale", "Electronics", 24.99, "Precision digital scale with tare function, measures up to 11 lbs.", 180),                                # 44
    ("Electric Toothbrush", "Electronics", 59.99, "Sonic electric toothbrush with 5 modes, 2-minute timer, and travel case.", 100),                            # 45
    ("Robot Vacuum Cleaner", "Electronics", 349.99, "App-controlled robot vacuum with LiDAR navigation and auto-empty dock.", 20),                             # 46
    ("Streaming Media Player", "Electronics", 49.99, "4K HDR streaming device with voice remote and all major apps.", 140),                                    # 47
    ("Car Phone Mount", "Electronics", 19.99, "Universal dashboard phone mount with one-touch release and 360° rotation.", 250),                               # 48
    ("HDMI Cable 6ft", "Electronics", 12.99, "High-speed HDMI 2.1 cable, 48Gbps, supports 8K/60Hz and 4K/120Hz.", 400),                                      # 49
    ("Surge Protector Power Strip", "Electronics", 34.99, "8-outlet surge protector with 4 USB ports and 6ft cord, 2160 joules.", 170),                        # 50
    ("Portable Mini Projector", "Electronics", 199.99, "Compact 1080p LED projector with HDMI, USB, and built-in speaker.", 30),                               # 51
    ("Smart Plug Wi-Fi 4-Pack", "Electronics", 29.99, "Voice-compatible smart plugs with energy monitoring and scheduling.", 160),                              # 52

    # --- Clothing ---
    ("Fleece Zip-Up Hoodie", "Clothing", 64.99, "Heavyweight fleece hoodie with full zip and kangaroo pockets, heather grey.", 100),                            # 53
    ("Linen Button-Down Shirt", "Clothing", 54.99, "Relaxed-fit linen shirt in sky blue, perfect for warm weather.", 85),                                      # 54
    ("High-Waist Yoga Leggings", "Clothing", 49.99, "Squat-proof high-waist leggings with side pocket, four-way stretch.", 160),                               # 55
    ("Denim Jacket Classic", "Clothing", 89.99, "Medium-wash denim jacket with button front and chest pockets.", 65),                                          # 56
    ("Silk Blend Scarf", "Clothing", 44.99, "Lightweight silk-blend scarf in botanical print, 70x200cm.", 70),                                                 # 57
    ("Thermal Base Layer Top", "Clothing", 39.99, "Moisture-wicking thermal top with flatlock seams, ideal for layering.", 120),                               # 58
    ("Athletic Compression Socks", "Clothing", 19.99, "Graduated compression socks for running and recovery, 3-pack.", 220),                                   # 59
    ("Flannel Pajama Set", "Clothing", 49.99, "Brushed cotton flannel pajama top and pants in red tartan.", 90),                                               # 60
    ("Cashmere Beanie Hat", "Clothing", 39.99, "Pure cashmere ribbed beanie in charcoal, one size fits most.", 50),                                            # 61
    ("Waterproof Rain Poncho", "Clothing", 24.99, "Packable rain poncho with hood, fits in included stuff sack.", 180),                                        # 62
    ("Cargo Jogger Pants", "Clothing", 54.99, "Stretch twill joggers with cargo pockets and elastic cuffs, olive green.", 110),                                # 63
    ("Graphic Print Sweatshirt", "Clothing", 59.99, "Crew-neck sweatshirt with vintage mountain graphic, 100% cotton.", 95),                                   # 64
    ("Breathable Polo Shirt", "Clothing", 44.99, "Performance polo with moisture-wicking fabric and UPF 30, white.", 130),                                     # 65
    ("Quilted Vest", "Clothing", 79.99, "Lightweight quilted vest with synthetic insulation and stand collar.", 60),                                            # 66
    ("Wide Leg Linen Pants", "Clothing", 64.99, "High-rise wide leg linen pants in sand, elastic waistband.", 75),                                             # 67
    ("UPF 50 Sun Hoodie", "Clothing", 59.99, "Lightweight sun protection hoodie with thumb holes, UPF 50+.", 85),                                             # 68
    ("Seamless Sports Bra", "Clothing", 34.99, "Medium-support seamless sports bra with removable pads.", 140),                                                # 69
    ("Corduroy Overalls", "Clothing", 79.99, "Wide-wale corduroy overalls in rust, relaxed fit with adjustable straps.", 35),                                  # 70
    ("Cotton Boxer Briefs 3-Pack", "Clothing", 29.99, "Premium cotton boxer briefs in assorted colors, tagless.", 200),                                        # 71
    ("Merino Wool Hiking Socks", "Clothing", 24.99, "Cushioned merino wool socks with reinforced heel and toe, 2-pack.", 170),                                 # 72
    ("Velvet Blazer", "Clothing", 149.99, "Single-breasted velvet blazer in midnight blue, slim fit.", 20),                                                    # 73
    ("Cropped Cardigan", "Clothing", 54.99, "Ribbed-knit cropped cardigan with pearl buttons, cream.", 55),                                                    # 74

    # --- Accessories ---
    ("Minimalist Leather Wallet", "Accessories", 49.99, "Slim bifold wallet in top-grain leather with RFID blocking.", 100),                                   # 75
    ("Classic Aviator Watch", "Accessories", 179.99, "Stainless steel aviator watch with sapphire crystal and leather strap.", 30),                            # 76
    ("Braided Leather Belt", "Accessories", 39.99, "Hand-braided leather belt with brushed nickel buckle.", 85),                                               # 77
    ("Polarized Clip-On Sunglasses", "Accessories", 24.99, "Flip-up polarized clip-on lenses, fits most prescription frames.", 150),                           # 78
    ("Laptop Sleeve 15-inch", "Accessories", 34.99, "Neoprene laptop sleeve with fleece lining and accessory pocket.", 120),                                   # 79
    ("Canvas Tote Bag", "Accessories", 29.99, "Heavy-duty canvas tote with interior zip pocket and reinforced handles.", 200),                                 # 80
    ("RFID Travel Passport Holder", "Accessories", 19.99, "RFID-blocking passport holder with card slots, vegan leather.", 180),                               # 81
    ("Beaded Stretch Bracelet", "Accessories", 14.99, "Natural stone beaded bracelet set, stretchy cord, 3-piece.", 250),                                      # 82
    ("Silk Pocket Square", "Accessories", 24.99, "Hand-rolled silk pocket square in paisley pattern.", 70),                                                    # 83
    ("Titanium Money Clip", "Accessories", 29.99, "Brushed titanium money clip with spring-loaded grip.", 90),                                                 # 84
    ("Keychain Multi-Tool", "Accessories", 14.99, "10-in-1 stainless steel keychain tool with bottle opener and screwdrivers.", 300),                          # 85
    ("Foldable Travel Umbrella", "Accessories", 24.99, "Compact auto-open/close umbrella with windproof double canopy.", 160),                                 # 86
    ("Packing Cube Set 4-Piece", "Accessories", 34.99, "Lightweight mesh packing cubes in four sizes with carry handle.", 110),                                # 87
    ("Crossbody Phone Bag", "Accessories", 39.99, "Vegan leather crossbody bag sized for phone and essentials.", 95),                                          # 88
    ("Hair Clip Set Assorted", "Accessories", 12.99, "Set of 12 assorted acetate hair clips, tortoiseshell and solid colors.", 220),                           # 89

    # --- Fitness ---
    ("Resistance Band Set 5-Pack", "Fitness", 24.99, "Latex resistance bands in 5 strengths with door anchor and carry bag.", 140),                            # 90
    ("Foam Roller 18-inch", "Fitness", 29.99, "High-density EVA foam roller for deep tissue massage and recovery.", 100),                                      # 91
    ("Speed Jump Rope", "Fitness", 14.99, "Adjustable steel cable jump rope with ball-bearing handles.", 200),                                                 # 92
    ("Kettlebell 25lb Cast Iron", "Fitness", 49.99, "Single cast-iron kettlebell with vinyl coating and wide handle.", 60),                                    # 93
    ("Pull-Up Bar Doorway", "Fitness", 34.99, "No-screw doorway pull-up bar fits frames 26-36 inches, holds 300 lbs.", 70),                                   # 94
    ("Massage Gun Percussion", "Fitness", 129.99, "Handheld percussion massager with 6 heads and 5 speed settings.", 40),                                      # 95
    ("Ab Wheel Roller", "Fitness", 19.99, "Dual-wheel ab roller with padded knee mat and non-slip grips.", 130),                                               # 96
    ("Weighted Jump Rope 2lb", "Fitness", 29.99, "2-pound weighted jump rope for strength and cardio training.", 80),                                          # 97
    ("Gymnastic Rings Wooden", "Fitness", 44.99, "Olympic-grade birch gymnastic rings with adjustable straps.", 35),                                           # 98
    ("Ankle Weights 5lb Pair", "Fitness", 24.99, "Adjustable ankle weights with velcro straps, 2.5 lbs each.", 110),                                          # 99
    ("Balance Board Wooden", "Fitness", 49.99, "Wobble balance board for core training, 15.7-inch diameter.", 55),                                             # 100
    ("Grip Strength Trainer", "Fitness", 12.99, "Adjustable hand grip strengthener, 22-132 lbs resistance.", 190),                                             # 101
    ("Exercise Ball 65cm", "Fitness", 24.99, "Anti-burst PVC exercise ball with pump, supports up to 600 lbs.", 85),                                           # 102

    # --- Home ---
    ("Sherpa Throw Blanket", "Home", 44.99, "Ultra-soft sherpa fleece throw blanket, 50x60 inches, ivory.", 120),                                              # 103
    ("Aromatherapy Candle Set", "Home", 34.99, "Set of 3 soy wax candles in lavender, eucalyptus, and vanilla.", 100),                                         # 104
    ("Cast Iron Skillet 12-inch", "Home", 39.99, "Pre-seasoned cast iron skillet, oven-safe to 500°F.", 70),                                                  # 105
    ("French Press Coffee Maker", "Home", 29.99, "Borosilicate glass French press, 34oz capacity, stainless steel frame.", 90),                                # 106
    ("Bamboo Drawer Organizer", "Home", 24.99, "Expandable bamboo drawer organizer with adjustable dividers.", 110),                                           # 107
    ("Linen Shower Curtain", "Home", 49.99, "Stonewashed linen shower curtain with buttonhole top, natural.", 60),                                             # 108
    ("Ceramic Planter Set 3-Piece", "Home", 39.99, "Matte ceramic planters in small, medium, and large with drainage holes.", 80),                             # 109
    ("Stainless Steel Mixing Bowls", "Home", 34.99, "Nesting set of 5 stainless steel bowls with lids, 1-5 quart.", 65),                                      # 110
    ("Memory Foam Bath Mat", "Home", 29.99, "Non-slip memory foam bath mat, 17x24 inches, charcoal.", 150),                                                   # 111
    ("Wall-Mounted Coat Rack", "Home", 44.99, "Mango wood and iron wall-mounted coat rack with 5 hooks.", 45),                                                # 112
    ("Glass Storage Containers 5-Pack", "Home", 39.99, "Borosilicate glass meal prep containers with snap-lock lids.", 100),                                   # 113
    ("Cotton Duvet Cover Queen", "Home", 79.99, "Percale cotton duvet cover set in white, 300 thread count, queen.", 35),                                      # 114
    ("Silicone Baking Mat Set", "Home", 19.99, "Set of 2 non-stick silicone baking mats, fits half-sheet pans.", 160),                                         # 115
    ("Electric Gooseneck Kettle", "Home", 69.99, "Temperature-control gooseneck kettle for pour-over coffee, 0.8L.", 50),                                      # 116
    ("Throw Pillow Covers 18x18", "Home", 24.99, "Set of 4 linen-blend throw pillow covers in earth tones.", 130),                                            # 117
    ("Acacia Wood Salad Bowl", "Home", 34.99, "Large acacia wood salad bowl, 12-inch diameter, hand-finished.", 55),                                           # 118
    ("Non-Stick Baking Sheet", "Home", 19.99, "Heavy-gauge steel baking sheet with ceramic non-stick coating.", 190),                                          # 119
    ("Vacuum Insulated Tumbler", "Home", 24.99, "20oz stainless steel tumbler with sliding lid, keeps hot 6 hours.", 200),                                     # 120

    # --- Outdoor ---
    ("Lightweight Hammock", "Outdoor", 49.99, "Parachute nylon hammock with carabiners and tree straps, holds 400 lbs.", 70),                                  # 121
    ("Solar Lantern Rechargeable", "Outdoor", 24.99, "Collapsible solar-powered LED lantern with USB charging output.", 130),                                  # 122
    ("Insulated Cooler Bag 24-Can", "Outdoor", 39.99, "Leak-proof insulated cooler bag, keeps ice 48 hours, 24-can capacity.", 80),                            # 123
    ("Trekking Poles Pair", "Outdoor", 69.99, "Adjustable carbon fiber trekking poles with cork grips and tungsten tips.", 45),                                # 124
    ("Dry Bag Waterproof 20L", "Outdoor", 19.99, "Roll-top waterproof dry bag, 20-liter, welded seams.", 160),                                                # 125
    ("Portable Camp Stove", "Outdoor", 34.99, "Lightweight propane camp stove with push-button ignition, 10,000 BTU.", 50),                                   # 126
    ("Packable Rain Jacket", "Outdoor", 79.99, "Ultralight waterproof rain jacket that packs into its own pocket.", 65),                                       # 127
    ("Emergency Survival Kit", "Outdoor", 44.99, "72-hour survival kit with first aid, fire starter, whistle, and compass.", 40),                              # 128
    ("Hammock Strap Set", "Outdoor", 14.99, "Tree-friendly hammock straps with 20 loops each, holds 700 lbs.", 120),                                           # 129
    ("LED Headlamp Rechargeable", "Outdoor", 29.99, "350-lumen rechargeable headlamp with red-light mode, IPX5 rated.", 110),                                 # 130
    ("Collapsible Water Bottle", "Outdoor", 14.99, "Silicone collapsible bottle, 750ml, BPA-free with carabiner clip.", 180),                                  # 131
    ("Outdoor Picnic Blanket", "Outdoor", 34.99, "Water-resistant picnic blanket, 79x79 inches with carry handle.", 90),                                       # 132

    # --- Books ---
    ("The Art of Mindful Living", "Books", 16.99, "Bestselling guide to mindfulness meditation and daily practice.", 90),                                       # 133
    ("Python Programming Cookbook", "Books", 44.99, "Comprehensive Python cookbook with 200+ recipes for intermediate developers.", 40),                         # 134
    ("World Atlas Illustrated", "Books", 34.99, "Full-color illustrated world atlas with 200+ detailed maps.", 50),                                            # 135
    ("Fiction Bestseller Collection Box", "Books", 39.99, "Box set of 4 award-winning fiction novels, paperback.", 60),                                        # 136
    ("Home Gardening Guide", "Books", 22.99, "Complete guide to organic home gardening for every season.", 80),                                                # 137
    ("Sketching for Beginners", "Books", 18.99, "Step-by-step sketching tutorials with 50 exercises, spiral-bound.", 70),                                      # 138
    ("The Science of Nutrition", "Books", 29.99, "Evidence-based guide to nutrition, diet, and metabolic health.", 55),                                         # 139
    ("Travel Photography Handbook", "Books", 27.99, "Professional tips for travel photography with 200 example images.", 45),                                  # 140
    ("Mystery Novel: The Last Key", "Books", 14.99, "Gripping mystery thriller, New York Times bestseller, paperback.", 120),                                  # 141
    ("Board Game Strategy Guide", "Books", 19.99, "In-depth strategy guide for 30 popular modern board games.", 35),                                           # 142
    ("Cookbook: Mediterranean Meals", "Books", 32.99, "150 authentic Mediterranean recipes with full-color photographs.", 65),                                  # 143
    ("Journaling Workbook", "Books", 12.99, "Guided journaling workbook with prompts for self-reflection, 200 pages.", 110),                                   # 144

    # --- Beauty & Personal Care ---
    ("Natural Lip Balm Set", "Beauty", 9.99, "Set of 4 organic lip balms in mint, vanilla, cherry, and coconut.", 250),                                        # 145
    ("Charcoal Face Wash", "Beauty", 14.99, "Activated charcoal facial cleanser for deep pore cleansing, 6oz.", 160),                                          # 146
    ("Argan Oil Hair Serum", "Beauty", 19.99, "Cold-pressed argan oil serum for frizz control and shine, 2oz.", 120),                                          # 147
    ("SPF 50 Daily Moisturizer", "Beauty", 24.99, "Lightweight daily moisturizer with broad-spectrum SPF 50, 3.4oz.", 130),                                    # 148
    ("Bamboo Toothbrush 4-Pack", "Beauty", 9.99, "Biodegradable bamboo toothbrushes with charcoal-infused bristles.", 200),                                    # 149
    ("Tea Tree Essential Oil", "Beauty", 12.99, "100% pure therapeutic-grade tea tree essential oil, 30ml.", 180),                                              # 150
    ("Reusable Makeup Remover Pads", "Beauty", 14.99, "Set of 16 washable bamboo pads with mesh laundry bag.", 140),                                           # 151
    ("Beard Grooming Kit", "Beauty", 34.99, "Beard oil, balm, comb, and scissors set in wooden gift box.", 60),                                                # 152
    ("Silk Sleep Mask", "Beauty", 19.99, "100% mulberry silk sleep mask with adjustable strap, midnight blue.", 100),                                           # 153
    ("Natural Deodorant Stick", "Beauty", 12.99, "Aluminum-free deodorant with activated charcoal and sage, 2.6oz.", 170),                                     # 154
    ("Vitamin C Brightening Serum", "Beauty", 29.99, "20% vitamin C serum with hyaluronic acid for radiant skin, 1oz.", 90),                                   # 155
    ("Dry Shampoo Powder", "Beauty", 16.99, "Volumizing dry shampoo powder with rice starch and lavender, 1.7oz.", 110),                                       # 156
    ("Coconut Body Butter", "Beauty", 18.99, "Rich coconut and shea body butter, deeply moisturizing, 8oz.", 95),                                              # 157
    ("Rose Water Face Mist", "Beauty", 14.99, "Hydrating rose water face mist with aloe vera, 4oz spray bottle.", 150),                                        # 158

    # --- Toys & Games ---
    ("1000-Piece Jigsaw Puzzle", "Toys & Games", 19.99, "Mountain landscape jigsaw puzzle, 1000 pieces, poster included.", 80),                                # 159
    ("Wooden Block Building Set", "Toys & Games", 29.99, "100-piece natural wood building blocks in assorted shapes.", 60),                                    # 160
    ("Strategy Card Game", "Toys & Games", 24.99, "Award-winning strategy card game for 2-6 players, ages 10+.", 100),                                        # 161
    ("Remote Control Car", "Toys & Games", 44.99, "1:16 scale RC car with 2.4GHz remote, 20+ mph speed.", 50),                                                # 162
    ("Magnetic Drawing Board", "Toys & Games", 19.99, "Large magnetic drawing board with stamps and pen, ages 3+.", 120),                                      # 163
    ("Kids' Science Kit", "Toys & Games", 34.99, "STEM science experiment kit with 30 activities, ages 6-12.", 70),                                            # 164
    ("Classic Board Game Collection", "Toys & Games", 39.99, "10-in-1 classic board game set in wooden box.", 45),                                             # 165
    ("Plush Stuffed Bear", "Toys & Games", 24.99, "Super-soft plush teddy bear, 18 inches tall, machine washable.", 90),                                       # 166
    ("Building Brick Set 500pc", "Toys & Games", 29.99, "Compatible building bricks, 500 pieces in 12 colors with base plates.", 75),                         # 167
    ("Outdoor Kite Large", "Toys & Games", 14.99, "Delta-wing kite with 50m line, easy to fly, vibrant rainbow colors.", 110),                                 # 168
    ("Fidget Cube Desk Toy", "Toys & Games", 9.99, "Six-sided fidget cube with click, spin, flip, and roll features.", 300),                                   # 169
    ("Foam Dart Blaster", "Toys & Games", 24.99, "Pump-action foam dart blaster with 20 darts, ages 8+.", 65),                                                # 170
]

# (customer_id, status, created_at, items, shipping, return)
# items: list of (product_id, quantity)
# shipping: None or (carrier, tracking_number, status, estimated_delivery, shipped_at)
# return_info: None or (reason, status, refund_amount)
ORDERS = [

    # Alice (cust 1): 3 orders
    (1, "delivered", "2026-01-15", [
        (1, 1),  # Blue Ultraboost
    ], ("FedEx", "FDX-1001-2026", "delivered", "2026-01-20", "2026-01-16"), None),
    (1, "shipped", "2026-03-20", [
        (4, 1),  # Headphones
        (9, 2),  # Water Bottle x2
    ], ("UPS", "UPS-1002-2026", "in_transit", "2026-04-18", "2026-03-21"), None),
    (1, "pending", "2026-04-10", [
        (6, 3),  # T-Shirts x3
    ], None, None),

    # Bob (cust 2): 3 orders
    (2, "delivered", "2026-02-01", [
        (10, 1),  # Messenger Bag
    ], ("USPS", "USPS-2001-2026", "delivered", "2026-02-06", "2026-02-02"), None),
    (2, "shipped", "2026-03-25", [
        (12, 1),  # Dumbbells
        (11, 1),  # Yoga Mat
    ], ("FedEx", "FDX-2002-2026", "out_for_delivery", "2026-04-14", "2026-03-26"), None),
    (2, "delivered", "2026-01-20", [
        (2, 1),  # White Sneaker
    ], ("UPS", "UPS-2003-2026", "delivered", "2026-01-25", "2026-01-21"),
     ("Wrong size received", "completed", 89.99)),

    # Carol (cust 3): 3 orders
    (3, "shipped", "2026-04-01", [
        (8, 1),  # Merino Sweater
        (7, 1),  # Chino Pants
    ], ("FedEx", "FDX-3001-2026", "in_transit", "2026-04-16", "2026-04-02"), None),
    (3, "delivered", "2026-02-14", [
        (16, 1),  # Sunglasses
    ], ("USPS", "USPS-3002-2026", "delivered", "2026-02-18", "2026-02-15"), None),
    (3, "cancelled", "2026-03-10", [
        (18, 1),  # Winter Jacket
    ], None, None),

    # David (cust 4): 3 orders
    (4, "delivered", "2026-01-05", [
        (14, 4),  # Coffee Mugs x4
        (15, 1),  # Cutting Board
    ], ("UPS", "UPS-4001-2026", "delivered", "2026-01-10", "2026-01-06"), None),
    (4, "shipped", "2026-04-05", [
        (17, 1),  # Fitness Tracker
    ], ("FedEx", "FDX-4002-2026", "delayed", "2026-04-20", "2026-04-06"), None),
    (4, "delivered", "2026-02-28", [
        (3, 1),  # Hiking Boot
    ], ("USPS", "USPS-4003-2026", "delivered", "2026-03-05", "2026-03-01"),
     ("Sole separated after one hike", "approved", 149.99)),

    # Eva (cust 5): 2 orders
    (5, "shipped", "2026-04-08", [
        (1, 1),  # Blue Ultraboost
        (13, 2),  # Running Shorts x2
    ], ("UPS", "UPS-5001-2026", "in_transit", "2026-04-17", "2026-04-09"), None),
    (5, "delivered", "2026-03-01", [
        (5, 1),  # Bluetooth Speaker
    ], ("FedEx", "FDX-5002-2026", "delivered", "2026-03-05", "2026-03-02"), None),

    # Frank (cust 6): 2 orders
    (6, "pending", "2026-04-12", [
        (19, 1),  # Camping Backpack
        (9, 1),  # Water Bottle
    ], None, None),
    (6, "delivered", "2026-02-10", [
        (4, 1),  # Headphones
    ], ("USPS", "USPS-6001-2026", "delivered", "2026-02-15", "2026-02-11"),
     ("Arrived damaged, dent on left ear cup", "requested", None)),

    # Grace (cust 7): 3 orders
    (7, "delivered", "2026-01-30", [
        (6, 2),  # T-Shirts x2
        (7, 1),  # Chino Pants
    ], ("UPS", "UPS-7001-2026", "delivered", "2026-02-04", "2026-01-31"), None),
    (7, "shipped", "2026-04-03", [
        (20, 2),  # Phone Charger x2
    ], ("FedEx", "FDX-7002-2026", "in_transit", "2026-04-15", "2026-04-04"), None),
    (7, "delivered", "2026-03-15", [
        (11, 1),  # Yoga Mat
    ], ("USPS", "USPS-7003-2026", "delivered", "2026-03-19", "2026-03-16"), None),

    # Henry (cust 8): 2 orders
    (8, "shipped", "2026-04-07", [
        (18, 1),  # Winter Jacket
        (8, 1),  # Merino Sweater
    ], ("FedEx", "FDX-8001-2026", "in_transit", "2026-04-19", "2026-04-08"), None),
    (8, "delivered", "2026-02-20", [
        (10, 1),  # Messenger Bag
    ], ("UPS", "UPS-8002-2026", "delivered", "2026-02-25", "2026-02-21"), None),

    # Irene (cust 9): 2 orders
    (9, "delivered", "2026-03-05", [
        (2, 1),  # White Sneaker
        (16, 1),  # Sunglasses
    ], ("FedEx", "FDX-9001-2026", "delivered", "2026-03-10", "2026-03-06"), None),
    (9, "pending", "2026-04-11", [
        (12, 1),  # Dumbbells
    ], None, None),

    # Jake (cust 10): 3 orders
    (10, "delivered", "2026-01-25", [
        (5, 1),  # Bluetooth Speaker
        (20, 1),  # Phone Charger
    ], ("USPS", "USPS-10001-2026", "delivered", "2026-01-30", "2026-01-26"), None),
    (10, "shipped", "2026-04-02", [
        (3, 1),  # Hiking Boot
        (19, 1),  # Camping Backpack
    ], ("UPS", "UPS-10002-2026", "out_for_delivery", "2026-04-13", "2026-04-03"), None),
    (10, "delivered", "2026-02-05", [
        (14, 2),  # Coffee Mugs x2
    ], ("FedEx", "FDX-10003-2026", "delivered", "2026-02-10", "2026-02-06"),
     ("One mug arrived cracked", "completed", 14.99)),


    # --- Karen (cust 11): 3 orders ---
    (11, "delivered", "2025-11-20", [
        (46, 1),   # Robot Vacuum
        (52, 1),   # Smart Plugs
    ], ("FedEx", "FDX-11001-2025", "delivered", "2025-11-26", "2025-11-21"), None),  # 27
    (11, "shipped", "2026-03-28", [
        (55, 2),   # Yoga Leggings x2
        (69, 1),   # Sports Bra
        (59, 1),   # Compression Socks
    ], ("UPS", "UPS-11002-2026", "in_transit", "2026-04-16", "2026-03-29"), None),  # 28
    (11, "pending", "2026-04-13", [
        (134, 1),  # Python Cookbook
        (144, 1),  # Journaling Workbook
    ], None, None),  # 29

    # --- Leo (cust 12): 2 orders ---
    (12, "delivered", "2025-12-10", [
        (33, 1),   # Gaming Keyboard
        (34, 1),   # Ergonomic Mouse
        (49, 2),   # HDMI Cable x2
    ], ("UPS", "UPS-12001-2025", "delivered", "2025-12-15", "2025-12-11"), None),  # 30
    (12, "shipped", "2026-04-01", [
        (41, 1),   # External SSD
    ], ("USPS", "USPS-12002-2026", "in_transit", "2026-04-17", "2026-04-02"), None),  # 31

    # --- Maria (cust 13): 3 orders ---
    (13, "delivered", "2026-01-08", [
        (103, 1),  # Sherpa Throw
        (104, 1),  # Candle Set
        (117, 2),  # Throw Pillow Covers x2
    ], ("FedEx", "FDX-13001-2026", "delivered", "2026-01-14", "2026-01-09"), None),  # 32
    (13, "delivered", "2026-02-22", [
        (23, 1),   # Ballet Flats
        (57, 1),   # Silk Scarf
        (82, 2),   # Beaded Bracelet x2
    ], ("USPS", "USPS-13002-2026", "delivered", "2026-02-28", "2026-02-23"),
     ("Ballet flats too narrow, uncomfortable fit", "approved", 69.99)),  # 33
    (13, "shipped", "2026-04-05", [
        (143, 1),  # Mediterranean Cookbook
        (106, 1),  # French Press
    ], ("UPS", "UPS-13003-2026", "in_transit", "2026-04-18", "2026-04-06"), None),  # 34

    # --- Noah (cust 14): 2 orders ---
    (14, "delivered", "2025-10-30", [
        (21, 1),   # Dress Shoes
        (83, 1),   # Pocket Square
        (73, 1),   # Velvet Blazer
    ], ("FedEx", "FDX-14001-2025", "delivered", "2025-11-05", "2025-10-31"), None),  # 35
    (14, "pending", "2026-04-14", [
        (76, 1),   # Aviator Watch
        (75, 1),   # Leather Wallet
    ], None, None),  # 36

    # --- Olivia (cust 15): 3 orders ---
    (15, "delivered", "2025-12-18", [
        (145, 3),  # Lip Balm Set x3
        (148, 1),  # SPF Moisturizer
        (155, 1),  # Vitamin C Serum
        (153, 1),  # Silk Sleep Mask
    ], ("UPS", "UPS-15001-2025", "delivered", "2025-12-24", "2025-12-19"), None),  # 37
    (15, "shipped", "2026-03-22", [
        (67, 1),   # Wide Leg Linen Pants
        (54, 1),   # Linen Shirt
        (74, 1),   # Cropped Cardigan
    ], ("FedEx", "FDX-15002-2026", "out_for_delivery", "2026-04-14", "2026-03-23"), None),  # 38
    (15, "delivered", "2026-02-05", [
        (89, 1),   # Hair Clip Set
        (88, 1),   # Crossbody Phone Bag
    ], ("USPS", "USPS-15003-2026", "delivered", "2026-02-10", "2026-02-06"), None),  # 39

    # --- Peter (cust 16): 2 orders ---
    (16, "delivered", "2026-01-18", [
        (19, 1),   # Camping Backpack
        (124, 1),  # Trekking Poles
        (130, 1),  # LED Headlamp
        (128, 1),  # Survival Kit
        (125, 1),  # Dry Bag
    ], ("UPS", "UPS-16001-2026", "delivered", "2026-01-25", "2026-01-19"), None),  # 40
    (16, "shipped", "2026-04-09", [
        (121, 1),  # Hammock
        (129, 1),  # Hammock Straps
        (132, 1),  # Picnic Blanket
    ], ("FedEx", "FDX-16002-2026", "in_transit", "2026-04-20", "2026-04-10"), None),  # 41

    # --- Quinn (cust 17): 1 order ---
    (17, "delivered", "2026-03-10", [
        (159, 1),  # Jigsaw Puzzle
        (161, 1),  # Strategy Card Game
        (165, 1),  # Board Game Collection
        (142, 1),  # Board Game Strategy Guide
    ], ("USPS", "USPS-17001-2026", "delivered", "2026-03-16", "2026-03-11"),
     ("Board game collection box was crushed during shipping", "requested", None)),  # 42

    # --- Rosa (cust 18): 2 orders ---
    (18, "delivered", "2025-11-15", [
        (105, 1),  # Cast Iron Skillet
        (110, 1),  # Mixing Bowls
        (118, 1),  # Salad Bowl
        (115, 1),  # Silicone Baking Mat
    ], ("FedEx", "FDX-18001-2025", "delivered", "2025-11-22", "2025-11-16"), None),  # 43
    (18, "shipped", "2026-04-06", [
        (116, 1),  # Gooseneck Kettle
        (106, 1),  # French Press
        (44, 1),   # Kitchen Scale
    ], ("UPS", "UPS-18002-2026", "in_transit", "2026-04-19", "2026-04-07"), None),  # 44

    # --- Sam (cust 19): 3 orders ---
    (19, "delivered", "2025-12-05", [
        (26, 1),   # Cross-Training Shoes
        (90, 1),   # Resistance Bands
        (91, 1),   # Foam Roller
        (92, 1),   # Jump Rope
    ], ("UPS", "UPS-19001-2025", "delivered", "2025-12-12", "2025-12-06"), None),  # 45
    (19, "delivered", "2026-02-15", [
        (95, 1),   # Massage Gun
        (93, 1),   # Kettlebell
        (94, 1),   # Pull-Up Bar
    ], ("FedEx", "FDX-19002-2026", "delivered", "2026-02-22", "2026-02-16"),
     ("Pull-up bar scratched door frame, doesn't fit properly", "approved", 34.99)),  # 46
    (19, "cancelled", "2026-04-10", [
        (12, 1),   # Adjustable Dumbbells
        (98, 1),   # Gymnastic Rings
    ], None, None),  # 47

    # --- Tina (cust 20): 2 orders ---
    (20, "delivered", "2026-01-02", [
        (133, 1),  # Art of Mindful Living
        (137, 1),  # Gardening Guide
        (139, 1),  # Science of Nutrition
    ], ("USPS", "USPS-20001-2026", "delivered", "2026-01-08", "2026-01-03"), None),  # 48
    (20, "shipped", "2026-04-02", [
        (109, 1),  # Ceramic Planters
        (107, 1),  # Drawer Organizer
    ], ("FedEx", "FDX-20002-2026", "in_transit", "2026-04-15", "2026-04-03"), None),  # 49

    # --- Ulrich (cust 21): 2 orders ---
    (21, "delivered", "2026-02-08", [
        (51, 1),   # Mini Projector
        (50, 1),   # Surge Protector
        (47, 1),   # Streaming Media Player
    ], ("UPS", "UPS-21001-2026", "delivered", "2026-02-14", "2026-02-09"), None),  # 50
    (21, "pending", "2026-04-12", [
        (38, 1),   # Android Tablet
        (79, 1),   # Laptop Sleeve
    ], None, None),  # 51

    # --- Vera (cust 22): 2 orders ---
    (22, "delivered", "2025-11-28", [
        (60, 1),   # Flannel Pajamas
        (103, 1),  # Sherpa Throw
        (40, 1),   # White Noise Machine
    ], ("FedEx", "FDX-22001-2025", "delivered", "2025-12-04", "2025-11-29"), None),  # 52
    (22, "shipped", "2026-03-30", [
        (114, 1),  # Duvet Cover
        (108, 1),  # Linen Shower Curtain
        (111, 2),  # Bath Mat x2
    ], ("USPS", "USPS-22002-2026", "in_transit", "2026-04-16", "2026-03-31"), None),  # 53

    # --- Will (cust 23): 3 orders ---
    (23, "delivered", "2025-10-15", [
        (3, 1),    # Trail Hiking Boot
        (72, 2),   # Hiking Socks x2
        (19, 1),   # Camping Backpack
        (126, 1),  # Camp Stove
    ], ("UPS", "UPS-23001-2025", "delivered", "2025-10-22", "2025-10-16"),
     ("Camp stove ignition button broken on arrival", "completed", 34.99)),  # 54
    (23, "delivered", "2026-02-18", [
        (152, 1),  # Beard Grooming Kit
        (77, 1),   # Braided Belt
    ], ("FedEx", "FDX-23002-2026", "delivered", "2026-02-24", "2026-02-19"), None),  # 55
    (23, "shipped", "2026-04-11", [
        (127, 1),  # Packable Rain Jacket
        (131, 1),  # Collapsible Water Bottle
        (29, 1),   # Trail Runners
    ], ("UPS", "UPS-23003-2026", "in_transit", "2026-04-21", "2026-04-12"), None),  # 56

    # --- Xena (cust 24): 2 orders ---
    (24, "delivered", "2026-01-22", [
        (164, 2),  # Kids' Science Kit x2
        (160, 1),  # Wooden Blocks
        (163, 1),  # Magnetic Drawing Board
        (166, 1),  # Plush Bear
    ], ("FedEx", "FDX-24001-2026", "delivered", "2026-01-28", "2026-01-23"), None),  # 57
    (24, "shipped", "2026-04-08", [
        (162, 1),  # RC Car
        (167, 1),  # Building Bricks
        (170, 1),  # Foam Dart Blaster
    ], ("UPS", "UPS-24002-2026", "out_for_delivery", "2026-04-16", "2026-04-09"), None),  # 58

    # --- Youssef (cust 25): 2 orders ---
    (25, "delivered", "2026-03-02", [
        (134, 1),  # Python Cookbook
        (135, 1),  # World Atlas
        (140, 1),  # Travel Photography
    ], ("USPS", "USPS-25001-2026", "delivered", "2026-03-08", "2026-03-03"), None),  # 59
    (25, "pending", "2026-04-15", [
        (141, 2),  # Mystery Novel x2
        (136, 1),  # Fiction Box Set
    ], None, None),  # 60

    # --- Zoe (cust 26): 2 orders ---
    (26, "delivered", "2025-12-22", [
        (147, 1),  # Argan Oil Serum
        (151, 1),  # Makeup Remover Pads
        (158, 1),  # Rose Water Mist
        (156, 1),  # Dry Shampoo
        (146, 1),  # Charcoal Face Wash
    ], ("UPS", "UPS-26001-2025", "delivered", "2025-12-28", "2025-12-23"), None),  # 61
    (26, "shipped", "2026-04-04", [
        (157, 1),  # Coconut Body Butter
        (154, 2),  # Natural Deodorant x2
    ], ("FedEx", "FDX-26002-2026", "in_transit", "2026-04-17", "2026-04-05"), None),  # 62

    # --- Amir (cust 27): 2 orders ---
    (27, "delivered", "2026-01-12", [
        (39, 1),   # Smart Home Speaker
        (52, 1),   # Smart Plugs
        (43, 1),   # LED Desk Lamp
    ], ("FedEx", "FDX-27001-2026", "delivered", "2026-01-18", "2026-01-13"), None),  # 63
    (27, "delivered", "2026-03-18", [
        (45, 1),   # Electric Toothbrush
        (149, 2),  # Bamboo Toothbrush x2
        (150, 1),  # Tea Tree Oil
    ], ("USPS", "USPS-27002-2026", "delivered", "2026-03-24", "2026-03-19"),
     ("Electric toothbrush won't hold charge after two weeks", "requested", None)),  # 64

    # --- Bianca (cust 28): 3 orders ---
    (28, "delivered", "2025-11-05", [
        (56, 1),   # Denim Jacket
        (22, 1),   # Canvas Slip-Ons
        (80, 1),   # Canvas Tote
    ], ("UPS", "UPS-28001-2025", "delivered", "2025-11-11", "2025-11-06"), None),  # 65
    (28, "delivered", "2026-02-12", [
        (53, 1),   # Fleece Hoodie
        (63, 1),   # Cargo Joggers
        (71, 1),   # Boxer Briefs
        (61, 1),   # Cashmere Beanie
    ], ("FedEx", "FDX-28002-2026", "delivered", "2026-02-18", "2026-02-13"), None),  # 66
    (28, "shipped", "2026-04-07", [
        (66, 1),   # Quilted Vest
        (68, 1),   # Sun Hoodie
    ], ("USPS", "USPS-28003-2026", "in_transit", "2026-04-19", "2026-04-08"), None),  # 67

    # --- Caleb (cust 29): 2 orders ---
    (29, "delivered", "2026-01-28", [
        (1, 1),    # Blue Ultraboost
        (13, 1),   # Running Shorts
        (72, 2),   # Hiking Socks x2
        (59, 1),   # Compression Socks
    ], ("UPS", "UPS-29001-2026", "delivered", "2026-02-03", "2026-01-29"), None),  # 68
    (29, "shipped", "2026-04-10", [
        (96, 1),   # Ab Wheel
        (97, 1),   # Weighted Jump Rope
        (100, 1),  # Balance Board
        (101, 2),  # Grip Strength Trainer x2
    ], ("FedEx", "FDX-29002-2026", "delayed", "2026-04-22", "2026-04-11"), None),  # 69

    # --- Diana (cust 30): 3 orders ---
    (30, "delivered", "2025-12-01", [
        (14, 6),   # Coffee Mugs x6
        (120, 4),  # Vacuum Tumbler x4
        (113, 1),  # Glass Storage Containers
    ], ("FedEx", "FDX-30001-2025", "delivered", "2025-12-08", "2025-12-02"), None),  # 70
    (30, "delivered", "2026-02-25", [
        (70, 1),   # Corduroy Overalls
        (74, 1),   # Cropped Cardigan
        (24, 1),   # House Slippers
    ], ("USPS", "USPS-30002-2026", "delivered", "2026-03-03", "2026-02-26"),
     ("House slippers sole came unglued after one day", "approved", 29.99)),  # 71
    (30, "pending", "2026-04-14", [
        (168, 2),  # Outdoor Kite x2
        (169, 3),  # Fidget Cube x3
        (166, 1),  # Plush Bear
    ], None, None),  # 72

    # --- Extra orders for existing customers ---

    # Alice (cust 1): big holiday order
    (1, "delivered", "2025-11-25", [
        (104, 2),  # Candle Set x2
        (103, 1),  # Sherpa Throw
        (14, 3),   # Coffee Mugs x3
        (120, 2),  # Vacuum Tumbler x2
    ], ("UPS", "UPS-1003-2025", "delivered", "2025-12-02", "2025-11-26"), None),  # 73

    # David (cust 4): electronics haul
    (4, "shipped", "2026-04-12", [
        (33, 1),   # Gaming Keyboard
        (34, 1),   # Ergonomic Mouse
        (35, 1),   # 4K Webcam
        (36, 1),   # USB-C Hub
        (50, 1),   # Surge Protector
    ], ("DHL", "DHL-4004-2026", "in_transit", "2026-04-22", "2026-04-13"), None),  # 74

    # Grace (cust 7): book order
    (7, "delivered", "2026-03-01", [
        (138, 1),  # Sketching for Beginners
        (133, 1),  # Mindful Living
        (144, 2),  # Journaling Workbook x2
    ], ("USPS", "USPS-7004-2026", "delivered", "2026-03-07", "2026-03-02"), None),  # 75

    # Jake (cust 10): return scenario
    (10, "delivered", "2026-03-20", [
        (37, 1),   # Wireless Earbuds
        (42, 1),   # Wireless Charging Pad
    ], ("FedEx", "FDX-10004-2026", "delivered", "2026-03-26", "2026-03-21"),
     ("Earbuds right side has no sound, defective", "approved", 159.99)),  # 76
]


def seed() -> None:
    conn = get_connection()
    init_schema(conn)

    # Clear existing data
    for table in ("returns", "shipping", "order_items", "orders", "products", "customers"):
        conn.execute(f"DELETE FROM {table}")  # noqa: S608 — static table names, safe

    # Reset autoincrement counters so IDs start at 1
    conn.execute("DELETE FROM sqlite_sequence")

    # Customers
    conn.executemany(
        "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
        CUSTOMERS,
    )

    # Products
    conn.executemany(
        "INSERT INTO products (name, category, price, description, stock_quantity) VALUES (?, ?, ?, ?, ?)",
        PRODUCTS,
    )

    # Orders, items, shipping, returns
    for customer_id, status, created_at, items, shipping, return_info in ORDERS:
        total = sum(PRODUCTS[pid - 1][2] * qty for pid, qty in items)
        cur = conn.execute(
            "INSERT INTO orders (customer_id, status, created_at, total) VALUES (?, ?, ?, ?)",
            (customer_id, status, created_at, round(total, 2)),
        )
        order_id = cur.lastrowid

        for product_id, quantity in items:
            product = PRODUCTS[product_id - 1]
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                (order_id, product_id, product[0], quantity, product[2]),
            )

        if shipping is not None:
            carrier, tracking, ship_status, est_delivery, shipped_at = shipping
            conn.execute(
                "INSERT INTO shipping (order_id, carrier, tracking_number, status, estimated_delivery, shipped_at) VALUES (?, ?, ?, ?, ?, ?)",
                (order_id, carrier, tracking, ship_status, est_delivery, shipped_at),
            )

        if return_info is not None:
            reason, ret_status, refund_amount = return_info
            conn.execute(
                "INSERT INTO returns (order_id, reason, status, refund_amount) VALUES (?, ?, ?, ?)",
                (order_id, reason, ret_status, refund_amount),
            )

    conn.commit()
    conn.close()

    # Print summary
    conn = get_connection()
    for table in ("customers", "products", "orders", "order_items", "shipping", "returns"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
        print(f"  {table}: {count} rows")
    conn.close()
    print(f"\nDatabase written to {DB_PATH}")


def main() -> None:
    print("Seeding database...")
    seed()
    print("Done.")


if __name__ == "__main__":
    main()
