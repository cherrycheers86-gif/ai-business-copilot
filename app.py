# ---------------- AI ----------------
with tab3:

    st.subheader("🤖 AI Assistant")

    # ---------------- CHAT DISPLAY ----------------
    chat_container = st.container()

    with chat_container:
        for role, msg in st.session_state.history:
            if role == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")

    st.markdown("---")

    # ---------------- CHATGPT STYLE INPUT ----------------
    user_input = st.chat_input("Ask your business question...")

    if user_input:

        q = user_input.lower()
        result = None

        # ---------------- CHARTS FIRST ----------------
        if any(x in q for x in ["chart", "plot", "graph"]):

            if "january" in q:
                data = df[df["date"].dt.month == 1]
            elif "february" in q or "feb" in q:
                data = df[df["date"].dt.month == 2]
            else:
                data = df

            if len(data) > 0:
                if "sales" in q and "expenses" in q:
                    st.line_chart(data.set_index("date")[["revenue", "cost"]])
                else:
                    st.line_chart(data.set_index("date")[["revenue", "cost", "profit"]])

                result = "Chart displayed"
            else:
                result = "No data available."

        # ---------------- CALCULATIONS ----------------
        elif "top 3" in q and "profit" in q:
            top3 = df.nlargest(3, "profit")[["date", "profit"]]
            result = f"Top 3 profit days:\n{top3.to_string(index=False)}"

        elif "compare" in q:
            best = df.loc[df["profit"].idxmax()]
            worst = df.loc[df["profit"].idxmin()]
            result = f"Best: {best['date'].date()} (${best['profit']:.2f}), Worst: {worst['date'].date()} (${worst['profit']:.2f})"

        elif "maximum profit" in q or "max profit" in q:
            if "january" in q:
                data = df[df["date"].dt.month == 1]
            elif "february" in q or "feb" in q:
                data = df[df["date"].dt.month == 2]
            else:
                data = df

            if len(data) > 0:
                row = data.loc[data["profit"].idxmax()]
                result = f"Max profit: {row['profit']} on {row['date'].date()}"
            else:
                result = "No data available."

        elif "lowest profit" in q or "min profit" in q:
            if "january" in q:
                data = df[df["date"].dt.month == 1]
            elif "february" in q or "feb" in q:
                data = df[df["date"].dt.month == 2]
            else:
                data = df

            if len(data) > 0:
                row = data.loc[data["profit"].idxmin()]
                result = f"Lowest profit: {row['profit']} on {row['date'].date()}"
            else:
                result = "No data available."

        elif "total sales" in q:
            result = f"Total sales: {df['revenue'].sum():.2f}"

        elif "average profit" in q:
            result = f"Average profit: {df['profit'].mean():.2f}"

        # ---------------- BLOCK AI FOR NUMBERS ----------------
        if any(x in q for x in ["max","min","total","average","top","compare","profit","sales"]):
            if result is None:
                result = "This calculation is not supported yet."

        # ---------------- AI INSIGHTS ----------------
        if result is None:
            prompt = f"""
            You are a business analyst.

            RULES:
            - No calculations
            - No code
            - Only insights

            Data:
            {df.head(30).to_string()}

            Question:
            {user_input}
            """

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}]
                )
                result = response.choices[0].message.content
            except:
                result = "AI unavailable"

        # Save chat
        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("AI", result))

        st.rerun()
