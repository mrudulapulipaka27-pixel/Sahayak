"""Sahayak: photograph a letter or form and get a simple explanation in
Telugu, Hindi or English, with next steps and spoken audio.

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY="your key from Google AI Studio"
    streamlit run app.py
"""

import io
import json
import os

import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

MODEL = "gemini-2.5-flash"

LANGS = {
    "తెలుగు": {"name": "Telugu (Telugu script)", "tts": "te", "ui": "te"},
    "हिन्दी": {"name": "Hindi (Devanagari script)", "tts": "hi", "ui": "hi"},
    "English": {"name": "simple English", "tts": "en", "ui": "en"},
}

UI = {
    "en": {
        "tag": "Take a photo of a letter or form. Hear what it means, in your language.",
        "camera": "Take a photo",
        "upload": "Choose a photo",
        "sample": "Try a sample letter",
        "explain": "Explain this",
        "reading": "Reading your document. This can take up to a minute.",
        "says": "What it says",
        "facts": "Key details",
        "next": "What to do next",
        "deadline": "Deadline",
        "careful": "Be careful",
        "help": "You can also ask the office about",
        "helpnote": "Ask the office to confirm. Rules can differ by place.",
        "listen": "Listen",
        "unreadable": "The document could not be read.",
        "err": "Something went wrong. Please try again.",
        "nokey": "Add your Gemini API key in the sidebar first.",
        "nophoto": "Add a photo first.",
        "disclaimer": "Sahayak can make mistakes. Check money, medicine and dates with the issuing office or someone you trust.",
    },
    "hi": {
        "tag": "पत्र या फ़ॉर्म की फ़ोटो लीजिए। अपनी भाषा में उसका मतलब सुनिए।",
        "camera": "फ़ोटो खींचें",
        "upload": "फ़ोटो चुनें",
        "sample": "नमूना पत्र आज़माएँ",
        "explain": "समझाएँ",
        "reading": "आपका दस्तावेज़ पढ़ा जा रहा है। इसमें एक मिनट तक लग सकता है।",
        "says": "इसमें क्या लिखा है",
        "facts": "ज़रूरी जानकारी",
        "next": "आगे क्या करें",
        "deadline": "आख़िरी तारीख़",
        "careful": "सावधान रहें",
        "help": "आप दफ़्तर से यह भी पूछ सकते हैं",
        "helpnote": "दफ़्तर से पक्का कर लें। नियम जगह के हिसाब से अलग हो सकते हैं।",
        "listen": "सुनें",
        "unreadable": "दस्तावेज़ पढ़ा नहीं जा सका।",
        "err": "कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।",
        "nokey": "पहले साइडबार में अपनी Gemini API कुंजी डालें।",
        "nophoto": "पहले फ़ोटो जोड़ें।",
        "disclaimer": "सहायक से गलती हो सकती है। पैसे, दवा और तारीख़ की पुष्टि जारी करने वाले दफ़्तर या किसी भरोसेमंद व्यक्ति से करें।",
    },
    "te": {
        "tag": "లేఖ లేదా ఫారమ్ ఫోటో తీయండి. మీ భాషలో దాని అర్థం వినండి.",
        "camera": "ఫోటో తీయండి",
        "upload": "ఫోటో ఎంచుకోండి",
        "sample": "నమూనా లేఖను ప్రయత్నించండి",
        "explain": "వివరించండి",
        "reading": "మీ పత్రాన్ని చదువుతున్నాను. ఒక నిమిషం వరకు పట్టవచ్చు.",
        "says": "ఇందులో ఏముంది",
        "facts": "ముఖ్య వివరాలు",
        "next": "తర్వాత ఏం చేయాలి",
        "deadline": "చివరి తేదీ",
        "careful": "జాగ్రత్త",
        "help": "మీరు కార్యాలయంలో ఇవి కూడా అడగవచ్చు",
        "helpnote": "కార్యాలయంలో నిర్ధారించుకోండి. నియమాలు ప్రాంతాన్ని బట్టి మారవచ్చు.",
        "listen": "వినండి",
        "unreadable": "పత్రాన్ని చదవలేకపోయాను.",
        "err": "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
        "nokey": "ముందుగా సైడ్‌బార్‌లో మీ Gemini API కీ ఇవ్వండి.",
        "nophoto": "ముందుగా ఫోటో జోడించండి.",
        "disclaimer": "సహాయక్ తప్పులు చేయవచ్చు. డబ్బు, మందులు, తేదీల గురించి జారీ చేసిన కార్యాలయంలో లేదా నమ్మకమైన వ్యక్తిని అడిగి నిర్ధారించుకోండి.",
    },
}


def build_prompt(language_name: str) -> str:
    return f"""You are Sahayak, a patient helper for people who find official papers hard to read. The attached image is a photo of a document (a letter, form, certificate, bill, notice, medicine strip or similar).
Write every text value in {language_name}. Use words a ten-year-old would know. Short sentences. No officialese. Keep names, numbers, dates and reference numbers exactly as printed. Write rupee amounts with the word for rupees in the target language.
Rules:
- Use only what is visible in the image. If a part is blurry or cut off, say so in "careful" and do not guess.
- "may_help": at most 3 items, only well-known kinds of help that clearly relate to this document, each phrased as something to ask the local office about. Never state eligibility rules, amounts or deadlines that are not printed on the document. Use an empty list if unsure.
- For medicine, give no dose or advice beyond what is printed. Tell the person to confirm with a pharmacist or doctor.
- If the document asks for money, an OTP, a password or bank details, or sounds threatening, put a clear warning in "careful".
- If the image is not a readable document, set "readable" to false and explain in "summary".
Reply with only one JSON object in this shape:
{{"readable":true,"doc_type":"short name of the document","summary":"2 to 3 short sentences","key_facts":[{{"label":"...","value":"..."}}],"next_steps":["..."],"deadline":null,"may_help":[],"careful":null,"spoken":"a calm script of 60 to 120 words that reads the summary, the next steps and the deadline aloud, with no symbols or bullet marks"}}
key_facts: at most 6 (names, amounts, dates, reference numbers). next_steps: 2 to 6 steps, each one action. deadline and careful are a string or null."""


def make_sample_letter() -> bytes:
    """A fictional letter so the app can be demonstrated without a real document."""
    img = Image.new("RGB", (900, 1180), "#fbfbf8")
    d = ImageDraw.Draw(img)
    try:
        bold = ImageFont.load_default(size=30)
        body = ImageFont.load_default(size=24)
    except TypeError:  # older Pillow
        bold = body = ImageFont.load_default()
    d.text((60, 70), "OFFICE OF THE DISTRICT WELFARE OFFICER", fill="#16202e", font=bold)
    d.text((60, 114), "SAMPLE LETTER - FICTIONAL, FOR DEMONSTRATION", fill="#16202e", font=body)
    d.rectangle((60, 144, 840, 147), fill="#16202e")
    lines = [
        "Ref. No: SAMPLE/PEN/2026/0042", "Date: 02 October 2026", "",
        "To: Smt. Lakshmi Devi", "",
        "Subject: Sanction of monthly disability pension", "",
        "Your application dated 14 August 2026 has been approved.",
        "A monthly pension of Rs. 1,000 will be credited to your",
        "linked bank account from November 2026.", "",
        "Please submit a life certificate at the Mandal office",
        "before 30 November 2026. If it is not submitted, the",
        "pension may be stopped.", "",
        "Documents to bring:", "  1. Aadhaar card", "  2. Bank passbook",
        "  3. Copy of disability certificate", "",
        "No fee is charged for this service.", "", "",
        "District Welfare Officer (sample)",
    ]
    for i, line in enumerate(lines):
        d.text((60, 190 + i * 42), line, fill="#16202e", font=body)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            key = ""
    return key or st.session_state.get("typed_key", "")


def explain(image_bytes: bytes, mime: str, language_name: str, key: str) -> dict:
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), build_prompt(language_name)],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return json.loads(response.text)


@st.cache_data(show_spinner=False)
def speak(text: str, tts_lang: str) -> bytes:
    buf = io.BytesIO()
    gTTS(text=text, lang=tts_lang).write_to_fp(buf)
    return buf.getvalue()


def spoken_text(d: dict) -> str:
    if d.get("spoken"):
        return str(d["spoken"])
    parts = [d.get("summary", "")] + list(d.get("next_steps", [])) + [d.get("deadline") or ""]
    return ". ".join(p for p in parts if p)


def show_result(d: dict, ui: dict, tts_lang: str) -> None:
    if d.get("readable") is False:
        st.warning(d.get("summary") or ui["unreadable"])
        return
    if d.get("doc_type"):
        st.caption(str(d["doc_type"]).upper())
    st.subheader(ui["says"])
    st.markdown(f"### {d.get('summary', '')}")
    if d.get("careful"):
        st.warning(f"**{ui['careful']}**  \n{d['careful']}")
    if d.get("key_facts"):
        st.subheader(ui["facts"])
        for f in d["key_facts"][:6]:
            st.markdown(f"**{f.get('label', '')}:** {f.get('value', '')}")
    if d.get("deadline"):
        st.warning(f"**{ui['deadline']}**  \n{d['deadline']}")
    if d.get("next_steps"):
        st.subheader(ui["next"])
        for i, step in enumerate(d["next_steps"][:6], 1):
            st.markdown(f"**{i}.** {step}")
    if d.get("may_help"):
        st.subheader(ui["help"])
        for item in d["may_help"][:3]:
            st.markdown(f"- {item}")
        st.caption(ui["helpnote"])
    st.subheader(ui["listen"])
    try:
        st.audio(speak(spoken_text(d), tts_lang), format="audio/mp3")
    except Exception:
        st.caption("Audio could not be created. Check your internet connection.")


def main() -> None:
    st.set_page_config(page_title="Sahayak", page_icon="📄", layout="centered")
    st.title("Sahayak")

    choice = st.radio("Language", list(LANGS), horizontal=True, label_visibility="collapsed")
    cfg = LANGS[choice]
    ui = UI[cfg["ui"]]
    st.write(ui["tag"])

    with st.sidebar:
        st.header("Settings")
        if not (os.environ.get("GEMINI_API_KEY")):
            st.text_input("Gemini API key", type="password", key="typed_key",
                          help="Free key from Google AI Studio. It is not stored.")

    photo = st.camera_input(ui["camera"])
    upload = st.file_uploader(ui["upload"], type=["png", "jpg", "jpeg", "webp"])
    if st.button(ui["sample"]):
        st.session_state["sample"] = make_sample_letter()

    image_bytes, mime = None, "image/jpeg"
    if photo is not None:
        image_bytes = photo.getvalue()
    elif upload is not None:
        image_bytes, mime = upload.getvalue(), upload.type or "image/jpeg"
    elif st.session_state.get("sample"):
        image_bytes, mime = st.session_state["sample"], "image/png"
        st.caption("Sample, not real")

    if image_bytes:
        st.image(image_bytes, use_container_width=True)

    if st.button(ui["explain"], type="primary", use_container_width=True):
        key = get_api_key()
        if not image_bytes:
            st.info(ui["nophoto"])
        elif not key:
            st.info(ui["nokey"])
        else:
            with st.spinner(ui["reading"]):
                try:
                    st.session_state["result"] = (explain(image_bytes, mime, cfg["name"], key), choice)
                except Exception:
                    st.session_state.pop("result", None)
                    st.error(ui["err"])

    saved = st.session_state.get("result")
    if saved:
        data, made_in = saved
        if made_in != choice:
            st.info(f"{made_in} → {choice}: tap “{ui['explain']}” again.")
        else:
            show_result(data, ui, cfg["tts"])

    st.caption(ui["disclaimer"])


if __name__ == "__main__":
    main()
