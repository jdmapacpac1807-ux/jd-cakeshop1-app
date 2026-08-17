import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import random
import os
import json
import hashlib
import secrets
from pathlib import Path
import re
from io import BytesIO

# -----------------------
# Configuration & Setup
# -----------------------
APP_TITLE = "JD Cakes & Pastries / Slash Cozy Kitchen"
IMAGE_DIR = Path("./static/images")
ORDERS_FILE = Path("orders.json")
ADMIN_PASS_ENV = "ADMIN_PASS"          # plain-text env var (optional)
ADMIN_PASS_HASH_ENV = "ADMIN_PASS_HASH"  # sha256 hex digest env var (optional)

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="JD Cakes & Pastries / Slash Cozy Kitchen",
                   page_icon="🎂", layout="wide")

# -----------------------
# Utilities
# -----------------------
def load_orders():
    if ORDERS_FILE.exists():
        try:
            with ORDERS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    # fallback default
    return [
        {
            "Ref": "JD-8012", "Customer": "Ana Santos", "Phone": "09061234567",
            "Address": "San Juan, Mabini, Batangas", "Type": "Delivery",
            "Items": "Simple Dedication Cake (x1)", "Subtotal": 30.0, "Fee": 5.0, "Total": 35.0,
            "Payment": "GCash", "Status": "🟣 PREPARING", "Timestamp": "2026-08-16 09:00 AM"
        }
    ]

def save_orders(orders):
    with ORDERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def sha256_hexdigest(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def check_admin_password(input_pw: str) -> bool:
    if not input_pw:
        return False
    # If ADMIN_PASS_HASH set, compare hashed
    env_hash = os.getenv(ADMIN_PASS_HASH_ENV)
    if env_hash:
        return secrets.compare_digest(sha256_hexdigest(input_pw), env_hash)
    # else if ADMIN_PASS set, compare plain-text
    env_plain = os.getenv(ADMIN_PASS_ENV)
    if env_plain:
        return secrets.compare_digest(input_pw, env_plain)
    # no env var provided — fallback to default (with warning)
    return secrets.compare_digest(input_pw, "admin123")

def safe_filename(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)
    return safe

def save_uploaded_image(uploaded_file, product_id, product_name):
    suffix = Path(uploaded_file.name).suffix
    fname = f"{product_id}_{safe_filename(product_name)}_{int(datetime.now().timestamp())}{suffix}"
    out_path = IMAGE_DIR / fname
    with out_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(out_path)

def format_currency(v):
    return f"${v:.2f}"

def generate_ref():
    return f"JD-{random.randint(1000, 9999)}"

def validate_phone(p: str) -> bool:
    digits = re.sub(r"\D", "", p or "")
    return 7 <= len(digits) <= 13  # reasonable range

def validate_email(e: str) -> bool:
    if not e:
        return True
    return re.match(r"[^@]+@[^@]+\.[^@]+", e) is not None

# -----------------------
# Initial App State
# -----------------------
if "catalog" not in st.session_state:
    st.session_state.catalog = [
        # Cakes
        {"id": 1, "category": "🎂 CAKES", "name": "Simple Dedication Cake", "price": 30.0, "available": True, "image": None},
        {"id": 2, "category": "🎂 CAKES", "name": "2-Tier Cake", "price": 80.0, "available": True, "image": None},
        {"id": 3, "category": "🎂 CAKES", "name": "3-Tier Cake", "price": 140.0, "available": True, "image": None},
        {"id": 4, "category": "🎂 CAKES", "name": "Signature Cakes", "price": 45.0, "available": True, "image": None},
        {"id": 5, "category": "🎂 CAKES", "name": "Customized Cake", "price": 60.0, "available": True, "image": None},
        # Breads & Desserts
        {"id": 6, "category": "🍰 BREADS & DESSERTS", "name": "Banana Loaf Bread", "price": 10.0, "available": True, "image": None},
        {"id": 7, "category": "🍰 BREADS & DESSERTS", "name": "Latte Series", "price": 6.0, "available": True, "image": None},
        {"id": 8, "category": "🍰 BREADS & DESSERTS", "name": "Halo-Halo Overload", "price": 8.0, "available": True, "image": None},
        {"id": 9, "category": "🍰 BREADS & DESSERTS", "name": "Mais Con Yelo", "price": 5.0, "available": True, "image": None},
        {"id": 10, "category": "🍰 BREADS & DESSERTS", "name": "Saging Con Yelo", "price": 5.0, "available": True, "image": None},
        # Party Foods
        {"id": 11, "category": "🍱 PARTY FOODS", "name": "Bilao Food (Solo / Bundle)", "price": 35.0, "available": True, "image": None},
        {"id": 12, "category": "🍱 PARTY FOODS", "name": "4-in-1 Party Food Combo", "price": 50.0, "available": True, "image": None},
        # Ready to Eat
        {"id": 13, "category": "🍔 READY-TO-EAT", "name": "Burger", "price": 5.0, "available": True, "image": None},
        {"id": 14, "category": "🍔 READY-TO-EAT", "name": "Spaghetti", "price": 10.0, "available": True, "image": None},
        {"id": 15, "category": "🍔 READY-TO-EAT", "name": "Baked Mac", "price": 12.0, "available": True, "image": None},
        {"id": 16, "category": "🍔 READY-TO-EAT", "name": "Palabok", "price": 10.0, "available": True, "image": None},
        {"id": 17, "category": "🍔 READY-TO-EAT", "name": "Lomi", "price": 8.0, "available": True, "image": None},
        # Others
        {"id": 18, "category": "🎁 OTHERS", "name": "Souvenirs", "price": 4.0, "available": True, "image": None},
    ]

# Cart is a mapping: product_id -> qty
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Orders DB persisted to JSON
if "orders_db" not in st.session_state:
    st.session_state.orders_db = load_orders()

# -----------------------
# Styling
# -----------------------
st.markdown("""
    <style>
    .main { background-color: #FAF5FF; }
    h1, h2, h3 { color: #5B3280; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { 
        background-color: #B5E4D5; 
        color: #064E3B; 
        border-radius: 10px; 
        border: none; 
        font-weight: bold; 
    }
    .stButton>button:hover { background-color: #8AD4BC; color: #064E3B; }
    .header-banner {
        background: linear-gradient(135deg, #B8A2E0 0%, #F8C8DC 100%);
        padding: 20px;
        border-radius: 16px;
        color: #3D1C5A;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .product-card {
        background-color: #FFFFFF;
        border: 1px solid #F8C8DC;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin-bottom: 15px;
    }
    .status-badge {
        background-color: #B5E4D5;
        color: #064E3B;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
    <h1>🎂 JD CAKES AND PASTRIES</h1>
    <h3>SLASH COZY KITCHEN (Est. 2020)</h3>
    <p>📍 San Juan, Mabini, Batangas | 📞 0906-027-7998</p>
</div>
""", unsafe_allow_html=True)

# -----------------------
# Helpers for catalog/cart display
# -----------------------
def get_product_by_id(pid):
    for p in st.session_state.catalog:
        if p["id"] == pid:
            return p
    return None

def add_to_cart(pid, qty=1):
    p = get_product_by_id(pid)
    if not p or not p.get("available", True):
        st.warning("Product unavailable.")
        return
    st.session_state.cart.setdefault(str(pid), 0)
    st.session_state.cart[str(pid)] += qty
    st.success(f"Added {p['name']} (x{qty}) to cart.")

def remove_one_from_cart(pid):
    key = str(pid)
    if key in st.session_state.cart:
        if st.session_state.cart[key] > 1:
            st.session_state.cart[key] -= 1
        else:
            del st.session_state.cart[key]
        st.experimental_rerun()

def remove_all_from_cart(pid):
    key = str(pid)
    if key in st.session_state.cart:
        del st.session_state.cart[key]
        st.experimental_rerun()

# -----------------------
# Top-level Navigation
# -----------------------
tab_store, tab_cart, tab_track, tab_admin = st.tabs([
    "🛍️ Shop Menu",
    f"🛒 Shopping Cart ({sum(st.session_state.cart.values()) if st.session_state.cart else 0})",
    "📍 Track Order",
    "🔐 Admin Portal"
])

# -----------------------
# 1. Customer Storefront
# -----------------------
with tab_store:
    categories = sorted(list({item["category"] for item in st.session_state.catalog}))
    selected_cat = st.radio("Categories", categories, horizontal=True)
    st.divider()

    cat_items = [item for item in st.session_state.catalog if item["category"] == selected_cat]
    cols = st.columns(3)

    for idx, item in enumerate(cat_items):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="product-card">
                <h4>{item['name']}</h4>
                <p><span class="status-badge">{'Available' if item['available'] else 'Sold Out'}</span></p>
                <h3 style="color: #5B3280;">{format_currency(item['price'])}</h3>
            </div>
            """, unsafe_allow_html=True)

            if item.get("image"):
                try:
                    st.image(item["image"], use_column_width=True)
                except Exception:
                    st.info("📷 Image (unavailable)")
            else:
                st.info("📷 Image Upload Pending")

            if item["available"]:
                qty_col, btn_col = st.columns([2,1])
                qty = qty_col.number_input("Qty", min_value=1, value=1, key=f"qty_add_{item['id']}")
                if btn_col.button("Add to Cart 🛒", key=f"add_{item['id']}"):
                    add_to_cart(item["id"], qty)
                    st.experimental_rerun()

# -----------------------
# 2. Cart & Checkout
# -----------------------
with tab_cart:
    st.subheader("Your Shopping Cart")
    if not st.session_state.cart:
        st.info("Your shopping cart is currently empty.")
    else:
        rows = []
        for pid_str, qty in st.session_state.cart.items():
            pid = int(pid_str)
            p = get_product_by_id(pid)
            if p:
                rows.append({
                    "id": pid,
                    "name": p["name"],
                    "category": p["category"],
                    "price": p["price"],
                    "qty": qty,
                    "subtotal": p["price"] * qty
                })
        cart_df = pd.DataFrame(rows)
        display_df = cart_df[["name", "category", "price", "qty", "subtotal"]].copy()
        display_df["price"] = display_df["price"].map(lambda v: format_currency(v))
        display_df["subtotal"] = display_df["subtotal"].map(lambda v: format_currency(v))
        st.dataframe(display_df, use_container_width=True)

        # Quantity controls per item
        for row in rows:
            st.write(f"{row['name']} — {row['qty']} pcs — {format_currency(row['subtotal'])}")
            c1, c2, c3 = st.columns([1,1,2])
            if c1.button("➕", key=f"inc_{row['id']}"):
                add_to_cart(row["id"], 1)
                st.experimental_rerun()
            if c2.button("➖", key=f"dec_{row['id']}"):
                remove_one_from_cart(row["id"])
            if c3.button("Remove", key=f"rem_{row['id']}"):
                remove_all_from_cart(row["id"])

        subtotal = sum(r["subtotal"] for r in rows)
        # Delivery fee depends on order type; default to delivery until checkout selection
        # We'll set fee in form based on user's choice. For preview, assume delivery fee = 5
        preview_delivery_fee = 5.0
        total_preview = subtotal + preview_delivery_fee

        c1, c2 = st.columns(2)
        c1.metric("Subtotal", format_currency(subtotal))
        c2.metric("Total (est.)", format_currency(total_preview))

        if st.button("Clear Cart"):
            st.session_state.cart = {}
            st.experimental_rerun()

        st.divider()
        st.subheader("📝 Checkout & Delivery Form")
        with st.form("checkout_form"):
            col_a, col_b = st.columns(2)
            fullname = col_a.text_input("Full Name*").strip()
            phone = col_b.text_input("Contact Number*").strip()

            email = st.text_input("Email (Optional)").strip()
            address = st.text_area("Complete Address & Nearby Landmark*", "San Juan, Mabini, Batangas").strip()

            order_type = st.radio("Order Type", ["Pickup (San Juan, Mabini, Batangas)", "Delivery"])
            # use date only
            date_needed = st.date_input("Date Needed", min_value=date.today())
            payment_mode = st.selectbox("Payment Option", ["GCash", "Maya", "BDO Bank Transfer", "Cash"])

            proof = st.file_uploader("Upload Payment Proof Screenshot (Optional)", type=["png", "jpg", "jpeg"])
            notes = st.text_area("Special Customization Notes (Optional)")

            submit_order = st.form_submit_button("Submit Order")
            if submit_order:
                # Basic validation
                if not fullname:
                    st.error("Full name is required.")
                elif not validate_phone(phone):
                    st.error("Please provide a valid contact number (7-13 digits).")
                elif not address:
                    st.error("Address is required.")
                elif not validate_email(email):
                    st.error("Please provide a valid email address.")
                elif not st.session_state.cart:
                    st.error("Your cart is empty.")
                else:
                    ref_code = generate_ref()
                    items_list = []
                    subtotal = 0.0
                    for pid_str, qty in st.session_state.cart.items():
                        pid = int(pid_str)
                        p = get_product_by_id(pid)
                        if p:
                            items_list.append(f"{p['name']} (x{qty})")
                            subtotal += p["price"] * qty
                    items_str = ", ".join(items_list)

                    delivery_fee = 0.0 if order_type.startswith("Pickup") else 5.0
                    total = subtotal + delivery_fee

                    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")

                    new_order = {
                        "Ref": ref_code,
                        "Customer": fullname,
                        "Phone": phone,
                        "Email": email or "",
                        "Address": address,
                        "Type": "Pickup" if order_type.startswith("Pickup") else "Delivery",
                        "DateNeeded": date_needed.isoformat(),
                        "Items": items_str,
                        "Subtotal": subtotal,
                        "Fee": delivery_fee,
                        "Total": total,
                        "Payment": payment_mode,
                        "Notes": notes or "",
                        "Status": "🟡 PENDING",
                        "Timestamp": timestamp
                    }

                    # Save proof image if provided
                    if proof:
                        try:
                            img_path = save_uploaded_image(proof, ref_code, "payment_proof")
                            new_order["PaymentProof"] = img_path
                        except Exception:
                            new_order["PaymentProof"] = None

                    st.session_state.orders_db.append(new_order)
                    save_orders(st.session_state.orders_db)
                    st.session_state.cart = {}
                    st.success(f"Order submitted successfully! Reference Number: {ref_code}")
                    st.balloons()

                    # Offer download of receipt (JSON and CSV)
                    receipt_json = json.dumps(new_order, ensure_ascii=False, indent=2)
                    st.download_button("Download Receipt (JSON)", data=receipt_json,
                                       file_name=f"{ref_code}_receipt.json", mime="application/json")

                    # CSV
                    csv_buf = BytesIO()
                    pd.DataFrame([new_order]).to_csv(csv_buf, index=False)
                    csv_buf.seek(0)
                    st.download_button("Download Receipt (CSV)", data=csv_buf,
                                       file_name=f"{ref_code}_receipt.csv", mime="text/csv")

# -----------------------
# 3. Order Tracking
# -----------------------
with tab_track:
    st.subheader("📍 Order Tracking System")
    ref_search = st.text_input("Enter Order Reference Code (e.g., JD-8012)").strip()
    if ref_search:
        results = [o for o in st.session_state.orders_db if o["Ref"].upper() == ref_search.upper()]
        if results:
            order = results[0]
            st.success(f"Order Reference: **{order['Ref']}**")
            st.write(f"**Customer:** {order.get('Customer','')}")
            st.write(f"**Items:** {order.get('Items','')}")
            st.write(f"**Total Amount:** {format_currency(order.get('Total',0.0))}")
            st.write(f"**Current Status:** {order.get('Status','')}")
            st.caption(f"Last Updated: {order.get('Timestamp','')}")
            if order.get("PaymentProof"):
                try:
                    st.image(order.get("PaymentProof"))
                except Exception:
                    pass
        else:
            st.error("Reference number not found.")

# -----------------------
# 4. Admin Portal
# -----------------------
with tab_admin:
    st.subheader("🔐 Admin Management Portal")
    pwd = st.text_input("Enter Admin Password", type="password")

    if pwd:
        is_admin = check_admin_password(pwd)
    else:
        is_admin = False

    if is_admin:
        st.success("Authenticated as Administrator")
        admin_tab1, admin_tab2 = st.tabs(["📸 Menu & Photo Upload Slots", "📋 Order Management"])

        # Menu Upload Slots
        with admin_tab1:
            st.subheader("Upload Product Photos & Manage Prices")
            for idx, prod in enumerate(st.session_state.catalog):
                with st.expander(f"{prod['category']} — {prod['name']}"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    uploaded_file = c1.file_uploader(f"Upload Image for {prod['name']}", type=["jpg", "png", "jpeg"], key=f"up_{prod['id']}")
                    if uploaded_file:
                        try:
                            saved_path = save_uploaded_image(uploaded_file, prod["id"], prod["name"])
                            prod["image"] = saved_path
                            st.success("Photo uploaded and saved.")
                            save_orders(st.session_state.orders_db)  # persist orders file as a simple save point (optional)
                        except Exception as e:
                            st.error(f"Failed to save image: {e}")

                    new_price = c2.number_input("Price ($)", value=float(prod["price"]), key=f"pr_{prod['id']}")
                    prod["price"] = float(new_price)

                    is_avail = c3.checkbox("Available", value=prod["available"], key=f"av_{prod['id']}")
                    prod["available"] = is_avail

        # Order Management
        with admin_tab2:
            st.subheader("Customer Orders Database")
            # Dataframe view
            df_orders = pd.DataFrame(st.session_state.orders_db)
            if not df_orders.empty:
                # Show a compact view
                display_cols = ["Ref", "Customer", "Phone", "Type", "Items", "Total", "Payment", "Status", "Timestamp"]
                present_cols = [c for c in display_cols if c in df_orders.columns]
                st.dataframe(df_orders[present_cols], use_container_width=True)

                st.markdown("### Select an order to update status / view details")
                selected_ref = st.selectbox("Order Reference", options=df_orders["Ref"].tolist())
                selected_order = next((o for o in st.session_state.orders_db if o["Ref"] == selected_ref), None)
                if selected_order:
                    st.write("**Order Details**")
                    st.json(selected_order)
                    new_status = st.selectbox("Update Status", options=["🟡 PENDING", "🟣 PREPARING", "🟠 OUT FOR DELIVERY", "🟢 COMPLETED", "🔴 CANCELLED"], index=0)
                    if st.button("Apply Status Update"):
                        selected_order["Status"] = new_status
                        selected_order["Timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                        save_orders(st.session_state.orders_db)
                        st.success(f"Order {selected_order['Ref']} updated to {new_status}")
                        st.experimental_rerun()

                    # Export CSV of this order
                    buf = BytesIO()
                    pd.DataFrame([selected_order]).to_csv(buf, index=False)
                    buf.seek(0)
                    st.download_button("Download Selected Order (CSV)", data=buf,
                                       file_name=f"{selected_order['Ref']}.csv", mime="text/csv")

                # Export all orders
                all_buf = BytesIO()
                pd.DataFrame(st.session_state.orders_db).to_csv(all_buf, index=False)
                all_buf.seek(0)
                st.download_button("Export All Orders (CSV)", data=all_buf,
                                   file_name="orders_all.csv", mime="text/csv")
            else:
                st.info("No orders available.")

    elif pwd:
        st.error("Incorrect Password")
    else:
        st.info("Enter admin password (set ADMIN_PASS or ADMIN_PASS_HASH env var to avoid using default).")

# -----------------------
# Final housekeeping: persist orders on state change
# -----------------------
# Save orders periodically (lightweight)
save_orders(st.session_state.orders_db)