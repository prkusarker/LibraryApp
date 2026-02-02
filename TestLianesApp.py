import streamlit as st
from sqlalchemy import create_engine, text
from datetime import date
import pandas as pd

st.set_page_config(page_title="Liane's Library", page_icon="📚", layout="wide")

st.markdown("""
<style>

:root {
    --primary: #4b79a1;
    --primary-dark: #283e51;
    --accent: #6dd5ed;
    --bg-light: #f7f9fc;
    --card-bg: #ffffff;
    --radius: 12px;
    --shadow: 0 4px 18px rgba(0,0,0,0.12);
    --text-dark: #1f2937;
    --text-light: #6b7280;
}

/* Global background */
body, .stApp {
    background: var(--bg-light);
    font-family: 'Segoe UI', sans-serif;
}

/* Header / Title */
h1, h2, h3 {
    color: var(--text-dark);
    font-weight: 700;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border-radius: var(--radius);
    padding: 0.6rem 1.2rem;
    border: none;
    font-weight: 600;
    box-shadow: var(--shadow);
    transition: 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 22px rgba(0,0,0,0.18);
}

/* Input fields */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input,
textarea {
    border-radius: var(--radius);
    border: 1px solid #d1d5db;
}

/* Cards */
.card {
    background: var(--card-bg);
    padding: 25px;
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    margin-bottom: 20px;
}

/* KPI Metric Cards */
.kpi-card {
    background: var(--card-bg);
    padding: 18px;
    border-radius: var(--radius);
    text-align: center;
    box-shadow: var(--shadow);
}

.kpi-title {
    font-size: 0.9rem;
    color: var(--text-light);
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--primary-dark);
}

/* Dataframe styling */
.dataframe {
    border-radius: var(--radius);
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)

# --- DB Credentials ---
password = st.sidebar.text_input("Enter password", type="password")
schema = "lianes_library"
host = "localhost"
user = "root"
port = 3306

# --- Stop app until password is provided ---
if not password:
    st.warning("Please enter your database password in the sidebar to continue.")
    st.stop()

# --- Create engine only AFTER password is entered ---
connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema}"
engine = create_engine(connection_string)

# # --- Test connection ---
# try:
#     with engine.connect() as conn:
#         conn.execute(text("SELECT 1"))
#     st.success("Database connection established.")
# except Exception as e:
#     st.error(f"Connection failed: {e}")
#     st.stop()

# --- Example update query ---
# update_query = """
#     UPDATE book
#     SET title = :title
#     WHERE book_id = :book_id;
# """

# with engine.connect() as connection:
#     transaction = connection.begin()
#     try:
#         connection.execute(
#             text(update_query),
#             {"title": "The Dream", "book_id": 2}
#         )
#         transaction.commit()
#         st.success("Book updated successfully.")
#     except Exception as e:
#         transaction.rollback()
#         st.error(f"Update failed: {e}")

def fetch_all(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.mappings().all()


def execute_query(query, params=None):
    with engine.connect() as conn:
        conn.execute(text(query), params or {})
        conn.commit()

def books_page():
    st.header("📚 Books")

    # --- Add new book ---
    st.subheader("Add a new book")

    title = st.text_input("Title")
    author = st.text_input("Author")
    genre = st.text_input("Genre")
    publish_year = st.number_input("Publish year", min_value=0, max_value=2100, step=1)
    language = st.text_input("Language")
    isbn = st.text_input("ISBN")

    if st.button("Add Book"):
        if title and author:
            execute_query(
                """
                INSERT INTO book (title, author, genre, publish_year, language, isbn)
                VALUES (:title, :author, :genre, :publish_year, :language, :isbn)
                """,
                {
                    "title": title,
                    "author": author,
                    "genre": genre or None,
                    "publish_year": int(publish_year) if publish_year else None,
                    "language": language or None,
                    "isbn": isbn or None,
                }
            )
            st.success("Book added successfully.")
        else:
            st.error("Title and Author are required.")

    # --- Display all books ---
    st.subheader("All Books")
    books = fetch_all("SELECT * FROM book ORDER BY book_id")
    st.dataframe(books)

    # --- Delete a book ---
    st.subheader("Delete a book")
    if books:
        book_options = {f"{row['title']} (ID {row['book_id']})": row['book_id'] for row in books}
        book_to_delete = st.selectbox("Select book to delete", list(book_options.keys()))
        if st.button("Delete Book"):
            execute_query("DELETE FROM book WHERE book_id = :book_id", {"book_id": book_options[book_to_delete]})
            st.success("Book deleted. Refresh to see changes.")
    else:
        st.info("No books available.")

    # 📥 IMPORT BOOKS FROM EXCEL/CSV
    # -----------------------------
    st.markdown("---")
    st.subheader("📥 Import Books from Excel/CSV")
    
    uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            # Read file
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
    
            st.write("Preview:", df.head())
    
            # Required columns for your schema
            required_cols = {"title", "author", "genre", "publish_year", "language", "isbn"}
    
            if not required_cols.issubset(df.columns):
                st.error(f"File must contain columns: {required_cols}")
            else:
                if st.button("Import Books"):
                    for _, row in df.iterrows():
                        execute_query(
                            """
                            INSERT INTO book (title, author, genre, publish_year, language, isbn)
                            VALUES (:title, :author, :genre, :publish_year, :language, :isbn)
                            """,
                            {
                                "title": row["title"],
                                "author": row["author"],
                                "genre": row["genre"] if not pd.isna(row["genre"]) else None,
                                "publish_year": int(row["publish_year"]) if not pd.isna(row["publish_year"]) else None,
                                "language": row["language"] if not pd.isna(row["language"]) else None,
                                "isbn": row["isbn"] if not pd.isna(row["isbn"]) else None,
                            }
                        )
                    st.success("Books imported successfully!")
    
        except Exception as e:
            st.error(f"Error reading file: {e}")


def friends_page():
    st.header("👥 Friends")

    # --- Add new friend ---
    st.subheader("Add a new friend")

    name = st.text_input("Name")
    contact_number = st.text_input("Contact Number")
    contact_email = st.text_input("Contact Email")

    if st.button("Add Friend"):
        if name:
            execute_query(
                """
                INSERT INTO friends (name, contact_number, contact_email)
                VALUES (:name, :contact_number, :contact_email)
                """,
                {
                    "name": name,
                    "contact_number": contact_number or None,
                    "contact_email": contact_email or None,
                }
            )
            st.success("Friend added successfully.")
        else:
            st.error("Name is required.")

    # --- Display all friends ---
    st.subheader("All Friends")
    friends = fetch_all("SELECT * FROM friends ORDER BY friend_id")
    st.dataframe(friends)

    # --- Delete a friend ---
    st.subheader("Delete a friend")
    if friends:
        friend_options = {
            f"{row['name']} (ID {row['friend_id']})": row['friend_id']
            for row in friends
        }
        friend_to_delete = st.selectbox("Select friend to delete", list(friend_options.keys()))
        if st.button("Delete Friend"):
            execute_query(
                "DELETE FROM friends WHERE friend_id = :friend_id",
                {"friend_id": friend_options[friend_to_delete]}
            )
            st.success("Friend deleted. Refresh to see changes.")
    else:
        st.info("No friends available.")

def loans_page():
    st.header("🔄 Loans")

    # --- Create a new loan ---
    st.subheader("Create a new loan")

    books = fetch_all("SELECT book_id, title FROM book")
    friends = fetch_all("SELECT friend_id, name FROM friends")

    if books and friends:
        book_map = {f"{b['title']} (ID {b['book_id']})": b['book_id'] for b in books}
        friend_map = {f"{f['name']} (ID {f['friend_id']})": f['friend_id'] for f in friends}

        selected_book = st.selectbox("Select Book", list(book_map.keys()))
        selected_friend = st.selectbox("Select Friend", list(friend_map.keys()))
        loan_date = st.date_input("Loan Date")
        expected_return_date = st.date_input("Expected Return Date")

        if st.button("Create Loan"):
            execute_query(
                """
                INSERT INTO loan (book_id, friend_id, loan_date, expected_return_date)
                VALUES (:book_id, :friend_id, :loan_date, :expected_return_date)
                """,
                {
                    "book_id": book_map[selected_book],
                    "friend_id": friend_map[selected_friend],
                    "loan_date": loan_date,
                    "expected_return_date": expected_return_date,
                }
            )
            st.success("Loan created successfully.")
    else:
        st.warning("You need at least one book and one friend to create a loan.")

    # --- View active loans ---
    st.subheader("Active Loans")
    active_loans = fetch_all("""
        SELECT l.loan_id, b.title AS book, f.name AS friend,
               l.loan_date, l.expected_return_date
        FROM loan l
        JOIN book b ON l.book_id = b.book_id
        JOIN friends f ON l.friend_id = f.friend_id
        WHERE l.return_date IS NULL
        ORDER BY l.loan_date DESC
    """)
    st.dataframe(active_loans)

    # --- Mark loan as returned ---
    st.subheader("Mark loan as returned")
    if active_loans:
        loan_options = {
            f"{row['book']} → {row['friend']} (Loan ID {row['loan_id']})": row['loan_id']
            for row in active_loans
        }
        selected_loan = st.selectbox("Select loan to mark returned", list(loan_options.keys()))
        return_date = st.date_input("Return Date", value=date.today())

        if st.button("Mark Returned"):
            execute_query(
                "UPDATE loan SET return_date = :return_date WHERE loan_id = :loan_id",
                {"return_date": return_date, "loan_id": loan_options[selected_loan]}
            )
            st.success("Loan marked as returned.")
    else:
        st.info("No active loans.")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #4b79a1, #283e51);
    padding: 45px 30px;
    border-radius: 14px;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
">
    <h1 style="margin: 0; font-size: 2.6rem;">📚 Liane's Library</h1>
    <p style="font-size: 1.2rem; opacity: 0.9;">My Library, My Management</p>
</div>
""", unsafe_allow_html=True)

def loans_over_time_chart():
    st.subheader("📈 Loans Over Time")

    data = fetch_all("""
        SELECT 
            loan_date,
            COUNT(*) AS loans_made
        FROM loan
        GROUP BY loan_date
        ORDER BY loan_date;
    """)

    if not data:
        st.info("No loan data available yet.")
        return

    df = pd.DataFrame(data)

    # Ensure loan_date is datetime
    df["loan_date"] = pd.to_datetime(df["loan_date"])

    # Line chart
    st.line_chart(df.set_index("loan_date")["loans_made"])


#########----MOST BORROWED BOOKS---############

def most_borrowed_books_chart():
    st.subheader("📊 Most Borrowed Books")

    data = fetch_all("""
        SELECT 
            b.title,
            COUNT(l.loan_id) AS borrow_count
        FROM loan l
        JOIN book b ON l.book_id = b.book_id
        GROUP BY b.book_id, b.title
        ORDER BY borrow_count DESC
        LIMIT 10;
    """)

    if not data:
        st.info("No loan data available yet.")
        return

    df = pd.DataFrame(data)

    st.bar_chart(df.set_index("title")["borrow_count"])

def top_readers_leaderboard():
    st.subheader("🏆 Top Readers")

    data = fetch_all("""
        SELECT 
            f.name,
            COUNT(l.loan_id) AS loans_made
        FROM loan l
        JOIN friends f ON l.friend_id = f.friend_id
        GROUP BY f.friend_id, f.name
        ORDER BY loans_made DESC
        LIMIT 10;
    """)

    if not data:
        st.info("No loan data available yet.")
        return

    df = pd.DataFrame(data)

    st.dataframe(df)

    # Optional: bar chart version
    st.bar_chart(df.set_index("name")["loans_made"])

######----Dashboard-----##################

def dashboard_page():
    st.title("📊 Library Dashboard")

    # --- Fetch counts ---
    total_books = fetch_all("SELECT COUNT(*) AS c FROM book")[0]["c"]
    total_friends = fetch_all("SELECT COUNT(*) AS c FROM friends")[0]["c"]
    active_loans = fetch_all("SELECT COUNT(*) AS c FROM loan WHERE return_date IS NULL")[0]["c"]
    returned_loans = fetch_all("SELECT COUNT(*) AS c FROM loan WHERE return_date IS NOT NULL")[0]["c"]

    overdue = fetch_all("""
        SELECT COUNT(*) AS c
        FROM loan
        WHERE return_date IS NULL
        AND expected_return_date < CURDATE()
    """)[0]["c"]
    
   
    # --- KPI Cards ---################
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Books</div>
            <div class="kpi-value">{total_books}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Friends</div>
            <div class="kpi-value">{total_friends}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Active Loans</div>
            <div class="kpi-value">{active_loans}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Returned Loans</div>
            <div class="kpi-value">{returned_loans}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Overdue Loans</div>
            <div class="kpi-value">{overdue}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

   
    ##### --- Loans Over Time ---#####################
    loans_over_time_chart()

    st.markdown("---")

    # --- Most Borrowed Books ---####################
    most_borrowed_books_chart()

    st.markdown("---")

    # --- Top Readers ---#############
    top_readers_leaderboard()

    st.markdown("---")
        
    # --- Recent Loans Table ---################
    st.subheader("Recent Loan Activity")

    recent_loans = fetch_all("""
        SELECT 
            l.loan_id,
            b.title AS book,
            f.name AS friend,
            l.loan_date,
            l.expected_return_date,
            l.return_date
        FROM loan l
        JOIN book b ON l.book_id = b.book_id
        JOIN friends f ON l.friend_id = f.friend_id
        ORDER BY l.loan_date DESC
        LIMIT 10
    """)

    if recent_loans:
        st.dataframe(recent_loans)
    else:
        st.info("No loan activity yet.")


# --- MAIN APP ---

def main():
    ####st.title("📚 Liane's Library")

    page = st.sidebar.selectbox(
        "Navigate",
        ["Dashboard", "Books", "Friends", "Loans"]
    )

    if page == "Dashboard":
        dashboard_page()
    elif page == "Books":
        books_page()
    elif page == "Friends":
        friends_page()
    elif page == "Loans":
        loans_page()

main()

#####-----Footer: “Made with care by Pradip”------#############

st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    padding: 10px 0;
    background: rgba(0,0,0,0);
    text-align: center;
    font-size: 0.85rem;
    color: #6b7280;
}
</style>

<div class="footer">
    Made with care by <strong>Pradip</strong>
</div>
""", unsafe_allow_html=True)
