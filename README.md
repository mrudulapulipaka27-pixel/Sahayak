# Sahayak

Sahayak helps people understand official papers. The user photographs a letter, form, certificate, bill or medicine strip. The app explains it in simple Telugu, Hindi or English, lists the next steps and the deadline, and reads the explanation aloud.

Built for an AI hackathon in the Accessibility and Inclusive Communities area. It uses Google Gemini to read and explain the document.

## Features

- Take a photo or upload one
- Language choice: Telugu, Hindi, English
- Plain-language summary, key details, next steps, deadline and warnings
- Spoken explanation (audio player)
- A sample letter button for demos (fictional document)

## Run the Python version

```
pip install -r requirements.txt
export GEMINI_API_KEY="your key from Google AI Studio"
streamlit run app.py
```

On Windows PowerShell use `$env:GEMINI_API_KEY="your key"`. You can also paste the key into the sidebar box instead.

Open the address Streamlit prints. On a phone, open the same address while connected to the same Wi-Fi, or deploy it (for example on Streamlit Community Cloud, adding `GEMINI_API_KEY` in the app's secrets).

## Notes

- The AI can make mistakes. The app tells users to confirm money, medicine and dates with the issuing office.
- Spoken audio uses gTTS, which needs an internet connection.
- Photos are sent to Google Gemini for reading. Do not use real people's documents in demos.
- Never commit your API key to GitHub.

## Roadmap

Voice questions, braille display output, offline mode and a verified scheme database for one state.
