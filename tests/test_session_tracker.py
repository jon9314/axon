from agent.session_tracker import SessionTracker


def test_create_and_resolve():
    st = SessionTracker()
    token, thread = st.create_session("alice")
    ident, tid = st.resolve(token)
    assert ident == "alice"
    assert tid == thread
