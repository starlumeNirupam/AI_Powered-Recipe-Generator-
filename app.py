import streamlit as st
import openai
import requests
from fpdf import FPDF
import base64

# ---------- Helper functions ----------

def translate(text, target_lang):
    if target_lang == "en":
        return text
    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": "en",
        "target": target_lang,
        "format": "text"
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.json()["translatedText"]
    except Exception:
        return text  # fallback: show English

def create_pdf(recipe_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in recipe_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest='S').encode('latin-1')

def get_cuisine_prompt(cuisine_list):
    if not cuisine_list:
        return ""
    if len(cuisine_list) == 1:
        return f"The recipe(s) should follow the {cuisine_list[0]} cuisine. "
    return f"The recipe(s) should be inspired by these cuisines: {', '.join(cuisine_list)}. "

# ---------- UI ----------

st.title("🍲 AI Recipe Generator: Recipes from Your Ingredients")
st.markdown("Enter what you have, set preferences, and get delicious, customized recipes!")

# Sidebar for OpenAI key and output language
openai_key = st.sidebar.text_input(
    "Paste your OpenAI API key here",
    type="password",
    help="Your API key is used only for this session and not stored."
)
output_lang = st.sidebar.selectbox(
    "Output recipe language",
    [("English", "en"), ("Hindi", "hi"), ("French", "fr"), ("German", "de"), ("Spanish", "es")],
    format_func=lambda x: x[0]
)[1]

# Main recipe options
col1, col2 = st.columns(2)
with col1:
    servings = st.number_input("Number of servings", min_value=1, max_value=12, value=2)
with col2:
    cuisine = st.multiselect(
        "Preferred cuisine(s)",
        ["Indian", "Italian", "Chinese", "Mexican", "American", "Thai", "Japanese", "Mediterranean", "French", "Other"]
    )

ingredients = st.text_area("Available ingredients (comma-separated, e.g. tomato, paneer, chicken, rice)", "")

allergies = st.text_input("Allergies to avoid (comma-separated, optional)")

diet = st.selectbox(
    "Dietary preference",
    ["No preference", "Vegetarian", "Vegan", "Jain", "Non-Vegetarian"]
)

# Surprise me! button
if st.button("Surprise me!"):
    ingredients = ""  # Clear ingredients for random recipes

if st.button("Generate Recipes"):
    if not openai_key:
        st.warning("Please enter your OpenAI API key in the sidebar!")
    else:
        # Compose the prompt
        prompt = "You are a creative expert chef. Suggest 2 unique recipes "
        if ingredients.strip():
            prompt += f"using the following ingredients: {ingredients}. "
        else:
            prompt += "with any common kitchen ingredients. "
        prompt += f"The recipes should be for {servings} serving(s). "
        prompt += get_cuisine_prompt(cuisine)
        if allergies.strip():
            prompt += f"Avoid these allergens: {allergies}. "
        if diet != "No preference":
            prompt += f"All recipes must strictly follow the '{diet}' dietary rules. "
        prompt += (
            "For each recipe, list: 1) recipe name, 2) ingredients used, "
            "3) step-by-step instructions, and 4) approximate prep time. "
            "If some ingredients can't be used in any recipe, that's fine."
        )

        with st.spinner("Generating your recipes..."):
            try:
                client = openai.OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a creative, friendly recipe expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.85
                )
                recipe_text = response.choices[0].message.content
                translated_recipe = translate(recipe_text, output_lang)
                st.success("Here are your recipes:")
                st.markdown(translated_recipe)

                # PDF download
                pdf_bytes = create_pdf(translated_recipe)
                b64 = base64.b64encode(pdf_bytes).decode()
                st.download_button(
                    label="📄 Download Recipes as PDF",
                    data=pdf_bytes,
                    file_name="ai_recipes.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error generating recipes: {e}")

st.caption("Built with OpenAI GPT, LibreTranslate, and Streamlit. Your API key and data are never stored.")
