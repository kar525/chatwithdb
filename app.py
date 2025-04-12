import streamlit as st
import pathlib
import textwrap
import google.generativeai as genai
import pandas as pd

# ฟังก์ชันสำหรับแปลงข้อความให้แสดงผลเหมือน markdown
def to_markdown(text):
    text = text.replace('•', ' *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# ตั้งค่า API
key = st.secrets['gemini_api_key']  # ต้องใส่ API key ใน .streamlit/secrets.toml
genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-2.0-flash-lite')

st.title("Chat with Your Data 📊💬")

# อัปโหลด data dictionary และ transaction file
uploaded_file = st.file_uploader("Upload your Data Dictionary CSV", type=["csv"])
uploaded_file2 = st.file_uploader("Upload your Transaction Data CSV", type=["csv"])

if uploaded_file and uploaded_file2:
    # โหลดไฟล์
    data_dict_df = pd.read_csv(uploaded_file)
    transaction_df = pd.read_csv(uploaded_file2)
    df_name = "transaction_df"

    # แปลงข้อมูล dictionary ให้เป็นข้อความ
    data_dict_text = '\n'.join(
        '- ' + row['column_name'] + ': ' + row['data_type'] + '. ' + row['description']
        for _, row in data_dict_df.iterrows()
    )
    example_record = transaction_df.head(2).to_string()

    # เตรียม state สำหรับเก็บข้อความแชท
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # แสดงประวัติแชท
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # Input แชท
    user_input = st.chat_input("Ask me anything about the data...")

    if user_input:
        # บันทึกคำถามของผู้ใช้
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # เตรียม prompt
        prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question and the provided DataFrame information.

**User Question:**
{user_input}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. Use the `exec()` function to execute the generated code.
3. Do not import pandas.
4. Change date column type to datetime if needed.
5. Store the result of the executed code in a variable named `ANSWER`.
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`.
7. The code should return a concise and useful result.
        """

        response = model.generate_content(prompt)
        generated_code = response.text.replace("```python", "").replace("```", "").strip()

        try:
            # รันโค้ดที่ได้จากโมเดล
            exec(generated_code)
            # สร้างคำอธิบายผลลัพธ์
            explain_prompt = f"""
The user asked: "{user_input}"
The result is: {str(ANSWER)}

Explain the result, answer the question, and optionally provide insights into the customer's behavior/persona.
"""
            explain_response = model.generate_content(explain_prompt)
            bot_reply = explain_response.text.strip()

        except Exception as e:
            bot_reply = f"⚠️ An error occurred while executing the code:\n```\n{e}\n```"

        # บันทึกและแสดงคำตอบของ bot
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
