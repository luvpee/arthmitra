import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def sign_up(email, password, full_name):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        user = response.user
        
        # If the user was successfully created in Supabase Auth,
        # immediately create their profile entry in our custom table!
        if user:
            from database import save_user_profile
            save_user_profile(user.id, 5000, full_name) # Default starting budget = ₹5000
            
        return user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.messages = []
    if "collection" in st.session_state:
        del st.session_state.collection
    st.rerun()

def show_login_page():
    st.markdown("""
    <style>
    .auth-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-header">
        <h1>💰 ArthMitra</h1>
        <p>Your Personal AI Chartered Accountant</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        st.markdown("### Welcome back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True, type="primary"):
            if email and password:
                with st.spinner("Logging in..."):
                    user, error = sign_in(email, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error(f"Login failed: {error}")
            else:
                st.warning("Please enter email and password")

    with tab2:
        st.markdown("### Create your account")
        # ── NEW CODE: Added Full Name input box ──
        new_name = st.text_input("Full Name", key="signup_name", placeholder="e.g. Rahul Sharma")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up", use_container_width=True, type="primary"):
            # Check if all fields (including name) are filled
            if new_name and new_email and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        # Pass new_name along to the updated sign_up function
                        user, error = sign_up(new_email, new_password, new_name)
                        if user:
                            st.success("Account created! Please login. 🎉")
                        else:
                            st.error(f"Signup failed: {error}")
            else:
                st.warning("Please fill all fields")