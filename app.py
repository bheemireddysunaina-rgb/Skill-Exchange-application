import streamlit as st
import pandas as pd

# ---------------- DATA ----------------
def load_data():
    try:
        df = pd.read_excel("users.xlsx")
    except:
        df = pd.DataFrame(columns=["name","password","teach","learn","requests","messages"])

    for col in ["name","password","teach","learn","requests","messages"]:
        if col not in df.columns:
            df[col] = ""

    return df.fillna("")


def save_data(df):
    df.to_excel("users.xlsx", index=False)

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- APP ----------------
st.title("🎓 Skill Exchange App")

# Show logged-in user (top right style)
if st.session_state.user:
    st.markdown(f"""
    <div style='text-align:right; font-weight:bold;'>
    👤 Logged in as: {st.session_state.user}
    </div>
    """, unsafe_allow_html=True)
data = load_data()

menu = ["Login","Signup"] if not st.session_state.user else ["Profile","Find Match","Requests","Chat","Logout"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- SIGNUP ----------------
if choice == "Signup":
    name = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Signup"):
        if name in data["name"].values:
            st.error("User exists")
        else:
            new_user = pd.DataFrame([[name,password,"","","",""]],
                columns=["name","password","teach","learn","requests","messages"])
            data = pd.concat([data,new_user], ignore_index=True)
            save_data(data)
            st.success("Account created")

# ---------------- LOGIN ----------------
elif choice == "Login":
    name = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = data[(data["name"]==name)&(data["password"]==password)]
        if not user.empty:
            st.session_state.user = name
            st.success("Login success")
        else:
            st.error("Invalid")

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.user = None
    st.success("Logged out")

# ---------------- PROFILE ----------------
elif choice == "Profile":
    teach = st.text_input("Skill you teach")
    learn = st.text_input("Skill you want to learn")

    if st.button("Save"):
        data.loc[data["name"]==st.session_state.user,["teach","learn"]] = [teach,learn]
        save_data(data)
        st.success("Saved")

# ---------------- FIND MATCH ----------------
elif choice == "Find Match":
    search = st.text_input("Search skill")

    if search:
        matches = data[data["teach"].astype(str).str.contains(search,case=False)]

        for i,row in matches.iterrows():
            if row["name"]!=st.session_state.user:
                st.write(f"👤 {row['name']} | {row['teach']}")

                if st.button(f"Send Request to {row['name']}",key=i):
                    idx = data[data["name"]==row['name']].index[0]
                    req = str(data.at[idx,"requests"])
                    new_req = f"{st.session_state.user}:pending"

                    if new_req not in req:
                        data.at[idx,"requests"] = req + ";" + new_req
                        save_data(data)
                        st.success("Request sent")

# ---------------- REQUESTS ----------------
elif choice == "Requests":
    user_row = data[data["name"]==st.session_state.user].iloc[0]
    reqs = str(user_row["requests"])

    if reqs.strip()=="":
        st.info("No requests")
    else:
        req_list = [r for r in reqs.split(";") if ":" in r]
        new_list=[]

        for i,r in enumerate(req_list):
            sender,status = r.split(":")

            st.write(f"📩 {sender} → {status}")

            if status=="pending":
                if st.button(f"Accept {sender}",key=f"a{i}"):
                    status="accepted"
                if st.button(f"Reject {sender}",key=f"r{i}"):
                    status="rejected"

            new_list.append(f"{sender}:{status}")

        data.loc[data["name"]==st.session_state.user,"requests"] = ";".join(new_list)
        save_data(data)

# ---------------- CHAT ----------------
elif choice == "Chat":
    st.subheader("💬 Chat (Mutual Acceptance Required)")

    user_row = data[data["name"]==st.session_state.user].iloc[0]
    reqs = str(user_row["requests"])

    # Users whom current user accepted
    accepted_by_me = [r.split(":")[0] for r in reqs.split(";") if ":accepted" in r]

    # Check mutual acceptance
    mutual_users = []

    for other in accepted_by_me:
        other_row = data[data["name"]==other].iloc[0]
        other_reqs = str(other_row["requests"])

        # check if other user also accepted current user
        for r in other_reqs.split(";"):
            if f"{st.session_state.user}:accepted" in r:
                mutual_users.append(other)

    if not mutual_users:
        st.info("No mutual accepted users for chat")
    else:
        selected = st.selectbox("Select user", mutual_users)

        msg = st.text_input("Message")

        if st.button("Send"):
            s_idx = data[data["name"]==st.session_state.user].index[0]
            r_idx = data[data["name"]==selected].index[0]

            text = f"{st.session_state.user}->{selected}:{msg}"

            data.at[s_idx,"messages"] += ";"+text
            data.at[r_idx,"messages"] += ";"+text

            save_data(data)
            st.success("Message sent")

        # display chat
        msgs = str(user_row["messages"]).split(";")
        for m in msgs:
            if selected in m:
                st.write(m)
