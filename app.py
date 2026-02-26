from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os
import re

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAID Adaptive AI Triage</title>

<style>
body {
    margin:0;
    font-family: 'Segoe UI', sans-serif;
    background:#f8c8dc;
    color:#222;
}
.container {
    max-width:700px;
    margin:auto;
    padding:20px;
}
h1 {
    text-align:center;
    font-size:28px;
}
.card {
    background:white;
    padding:20px;
    border-radius:16px;
    margin-top:20px;
}
button {
    width:100%;
    padding:14px;
    margin:8px 0;
    border:none;
    border-radius:12px;
    font-size:16px;
    cursor:pointer;
}
.primary {
    background:#d63384;
    color:white;
}
.secondary {
    background:#eee;
}
input, select {
    width:100%;
    padding:10px;
    margin:6px 0;
    border-radius:8px;
    border:1px solid #ccc;
}
.hidden { display:none; }

.risk-low { color:green; font-weight:bold; }
.risk-medium { color:orange; font-weight:bold; }
.risk-high { color:red; font-weight:bold; }
.risk-emergency { color:darkred; font-weight:bold; font-size:20px; }

</style>
</head>
<body>

<div class="container">

<h1>VAID Adaptive AI Triage</h1>

<div id="languageCard" class="card">
    <button class="primary" onclick="setLanguage('english')">English</button>
    <button class="secondary" onclick="setLanguage('hindi')">हिन्दी</button>
</div>

<div id="formCard" class="card hidden">
    
    <div id="profileSection">
        <h3>Basic Profile</h3>
        <input type="number" id="age" placeholder="Age">
        <select id="sex" onchange="checkPregnancy()">
            <option value="">Sex</option>
            <option>Male</option>
            <option>Female</option>
            <option>Other</option>
        </select>
        <div id="pregnancyDiv" class="hidden">
            <select id="pregnant">
                <option value="">Pregnant?</option>
                <option>Yes</option>
                <option>No</option>
            </select>
        </div>
        <input type="number" id="height" placeholder="Height (cm)">
        <input type="number" id="weight" placeholder="Weight (kg)">
    </div>

    <div id="categorySection">
        <h3>Main Concern</h3>
        <label><input type="checkbox" value="Fever" class="category"> Fever / Infection</label><br>
        <label><input type="checkbox" value="Chest" class="category"> Chest / Heart</label><br>
        <label><input type="checkbox" value="Breathing" class="category"> Breathing</label><br>
        <label><input type="checkbox" value="Stomach" class="category"> Stomach / Digestive</label><br>
        <label><input type="checkbox" value="Head" class="category"> Head / Brain</label><br>
        <label><input type="checkbox" value="Women" class="category"> Women’s Health</label><br>
    </div>

    <div id="symptomSection">
        <h3>Symptoms</h3>
        <label><input type="checkbox" value="Chest pain" class="symptom"> Chest pain</label><br>
        <label><input type="checkbox" value="Shortness of breath" class="symptom"> Shortness of breath</label><br>
        <label><input type="checkbox" value="Sweating" class="symptom"> Sweating</label><br>
        <label><input type="checkbox" value="Severe headache" class="symptom"> Severe headache</label><br>
        <label><input type="checkbox" value="Vision changes" class="symptom"> Vision changes</label><br>
        <label><input type="checkbox" value="Heavy bleeding" class="symptom"> Heavy bleeding</label><br>
        <label><input type="checkbox" value="Fever" class="symptom"> Fever</label><br>
    </div>

    <div>
        <h3>Pain Severity (1-10)</h3>
        <input type="number" id="pain" min="1" max="10">
    </div>

    <div>
        <h3>Chronic Conditions</h3>
        <label><input type="checkbox" value="Diabetes" class="history"> Diabetes</label><br>
        <label><input type="checkbox" value="Hypertension" class="history"> Hypertension</label><br>
        <label><input type="checkbox" value="Heart disease" class="history"> Heart disease</label>
    </div>

    <button class="primary" onclick="analyze()">Analyze</button>
</div>

<div id="resultCard" class="card hidden"></div>

</div>

<script>

let language = "english";

const translations = {
    english: {
        assessment: "Assessment",
        condition: "Condition",
        risk: "Risk",
        action: "Action",
        emergency: "Emergency cardiac risk suspected.",
        seek: "Seek immediate medical care.",
        start: "Start Over"
    },
    hindi: {
        assessment: "मूल्यांकन",
        condition: "संभावित स्थिति",
        risk: "जोखिम स्तर",
        action: "क्या करें",
        emergency: "हृदय संबंधी आपात स्थिति का संदेह।",
        seek: "तुरंत चिकित्सा सहायता लें।",
        start: "फिर से शुरू करें"
    }
};

function setLanguage(lang){
    language = lang;
    document.getElementById("languageCard").classList.add("hidden");
    document.getElementById("formCard").classList.remove("hidden");
}

function checkPregnancy(){
    let sex = document.getElementById("sex").value;
    if(sex === "Female"){
        document.getElementById("pregnancyDiv").classList.remove("hidden");
    } else {
        document.getElementById("pregnancyDiv").classList.add("hidden");
    }
}

function analyze(){

    let symptoms = Array.from(document.querySelectorAll(".symptom:checked")).map(x => x.value);
    let history = Array.from(document.querySelectorAll(".history:checked")).map(x => x.value);

    if(symptoms.includes("Chest pain") && symptoms.includes("Sweating")){
        showResult(
            translations[language].emergency,
            "Emergency",
            translations[language].seek
        );
        return;
    }

    fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            language: language,
            age:document.getElementById("age").value,
            sex:document.getElementById("sex").value,
            pregnant:document.getElementById("pregnant")?.value,
            height:document.getElementById("height").value,
            weight:document.getElementById("weight").value,
            pain:document.getElementById("pain").value,
            symptoms:symptoms,
            history:history
        })
    })
    .then(res=>res.json())
    .then(data=>{
        showResult(data.condition, data.risk, data.action);
    });
}

function showResult(condition,risk,action){

    document.getElementById("formCard").classList.add("hidden");

    let riskClass = "risk-low";
    if(risk==="Medium") riskClass="risk-medium";
    if(risk==="High") riskClass="risk-high";
    if(risk==="Emergency") riskClass="risk-emergency";

    document.getElementById("resultCard").innerHTML = `
        <h2>${translations[language].assessment}</h2>
        <p><strong>${translations[language].condition}:</strong> ${condition}</p>
        <p><strong>${translations[language].risk}:</strong> <span class="${riskClass}">${risk}</span></p>
        <p><strong>${translations[language].action}:</strong> ${action}</p>
        <button onclick="location.reload()">${translations[language].start}</button>
    `;

    document.getElementById("resultCard").classList.remove("hidden");
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    bmi = 0
    if data["height"] and data["weight"]:
        bmi = round(float(data["weight"]) / ((float(data["height"])/100)**2),1)

    if data.get("language") == "hindi":
        instruction = """
आप एक चिकित्सीय ट्रायेज AI हैं।
संक्षिप्त और स्पष्ट उत्तर दें।
उत्तर हिंदी में दें।
"""
    else:
        instruction = """
You are a clinical triage AI.
Be concise.
Respond in English.
"""

    prompt = f"""
{instruction}

AGE: {data.get("age")}
SEX: {data.get("sex")}
PREGNANT: {data.get("pregnant")}
BMI: {bmi}
PAIN SCALE: {data.get("pain")}
SYMPTOMS: {', '.join(data.get("symptoms", []))}
HISTORY: {', '.join(data.get("history", []))}

Respond strictly in this format:

CONDITION: ...
RISK: Low / Medium / High
ACTION: ...
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role":"user","content":prompt}]
    )

    text = response.choices[0].message.content

    condition = re.search(r"CONDITION:\s*(.*)",text)
    risk = re.search(r"RISK:\s*(.*)",text)
    action = re.search(r"ACTION:\s*(.*)",text)

    return jsonify({
        "condition": condition.group(1) if condition else "Unknown",
        "risk": risk.group(1) if risk else "Medium",
        "action": action.group(1) if action else "Consult doctor."
    })
if __name__ == "__main__":
    app.run()