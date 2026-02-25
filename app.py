from flask import Flask, render_template_string, request
import os
from groq import Groq

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>VAID</title>
<style>
body {
    margin:0;
    font-family: 'Segoe UI', sans-serif;
    background: #111;
    color: white;
    text-align: center;
}

.container {
    padding: 40px;
}

button {
    padding: 15px 25px;
    margin: 10px;
    font-size: 18px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
}

.lang-btn {
    background: white;
    color: black;
    width: 200px;
}

.symptom-btn {
    background: #222;
    color: white;
}

.symptom-btn.active {
    background: #00bfff;
}

.submit-btn {
    background: white;
    color: black;
    margin-top: 20px;
}

#cameraBox {
    position: fixed;
    bottom: 20px;
    right: 20px;
}

video {
    width: 200px;
    border-radius: 10px;
}
</style>
</head>
<body>

<div class="container" id="langScreen">
    <h1>VAID</h1>
    <button class="lang-btn" onclick="setLang('en')">English</button>
    <button class="lang-btn" onclick="setLang('hi')">हिंदी</button>
</div>

<div class="container" id="mainScreen" style="display:none;">
    <h2 id="questionText"></h2>

    <div id="symptoms"></div>

    <div style="margin-top:20px;">
        <input placeholder="Height (cm)" id="height">
        <input placeholder="Weight (kg)" id="weight">
    </div>

    <button class="submit-btn" onclick="submitData()">Analyze</button>

    <div id="result" style="margin-top:30px;"></div>
</div>

<div id="cameraBox">
    <button onclick="toggleCamera()">📷</button>
    <video id="video" autoplay style="display:none;"></video>
</div>

<script>
let language = "en";
let selected = [];

function setLang(lang) {
    language = lang;
    document.getElementById("langScreen").style.display = "none";
    document.getElementById("mainScreen").style.display = "block";

    const question = lang === "en"
        ? "Select your symptoms:"
        : "अपने लक्षण चुनें:";

    document.getElementById("questionText").innerText = question;

    const symptoms = lang === "en"
        ? ["Fever","Cough","Headache","Chest Pain","Breathing Issue","Fatigue"]
        : ["बुखार","खांसी","सिरदर्द","सीने में दर्द","सांस लेने में दिक्कत","कमजोरी"];

    const container = document.getElementById("symptoms");
    container.innerHTML = "";

    symptoms.forEach(s => {
        let btn = document.createElement("button");
        btn.innerText = s;
        btn.className = "symptom-btn";
        btn.onclick = () => toggleSymptom(btn);
        container.appendChild(btn);
    });
}

function toggleSymptom(btn) {
    btn.classList.toggle("active");
    const text = btn.innerText;
    if (selected.includes(text)) {
        selected = selected.filter(x => x !== text);
    } else {
        selected.push(text);
    }
}

function submitData() {
    fetch("/", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            symptoms: selected.join(", "),
            height: document.getElementById("height").value,
            weight: document.getElementById("weight").value
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerText = data.result;
    });
}

function toggleCamera() {
    const video = document.getElementById("video");
    if (video.style.display === "none") {
        navigator.mediaDevices.getUserMedia({video:true})
        .then(stream => {
            video.srcObject = stream;
            video.style.display = "block";
        });
    } else {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.style.display = "none";
    }
}
</script>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        data = request.get_json()
        symptoms = data.get("symptoms")
        height = data.get("height")
        weight = data.get("weight")

        prompt = f"""
        Symptoms: {symptoms}
        Height: {height}
        Weight: {weight}

        Provide:
        - Possible cause
        - Risk level (Low/Medium/High)
        - What to do next
        Keep it short and clinical.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}]
        )

        return {"result": response.choices[0].message.content}

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()